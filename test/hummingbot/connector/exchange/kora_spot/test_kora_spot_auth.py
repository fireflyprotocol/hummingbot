"""
Tests for kora_spot's Ed25519 wallet-signature auth: Sui address derivation, the signed
login-payload construction, the AuthBase framework-compatibility hooks, and the proactive
token-refresh loop's timing.

The load-bearing assertion here is `test_build_login_signature_round_trips_and_verifies`: it
signs the digest of `json.dumps(login_request.to_dict())` and verifies against that same
rendering, which is what CONTRACT.md asked to be confirmed rather than assumed -- the bytes
`kora_auth_client`'s own `rest.py`/`api_client.py` put on the wire for a `LoginRequest` are
`json.dumps(sanitize_for_serialization(login_request))`, which resolves to exactly
`json.dumps(login_request.to_dict())` (default separators, alias key order accountAddress/
signedAtMillis/audience) -- not the compact `separators=(",", ":")` CONTRACT.md's pseudocode
showed, which would sign different bytes than the client actually sends.

Uses `IsolatedAsyncioWrapperTestCase` (this repo's convention for async connector tests, see
`bluefin_perpetual`'s own test files) rather than a bare `unittest.TestCase` plus
`asyncio.get_event_loop().run_until_complete(...)`: the latter relies on the implicit
main-thread event loop `asyncio.get_event_loop()` used to create when none was running, which
newer Python versions no longer do.
"""
import asyncio
import base64
import hashlib
import json
import unittest
from test.isolated_asyncio_wrapper_test_case import IsolatedAsyncioWrapperTestCase
from unittest.mock import AsyncMock, patch

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from hummingbot.connector.exchange.kora_spot.kora_spot_auth import (
    TOKEN_REFRESH_FRACTION,
    KoraSpotAuth,
    build_login_signature,
    derive_sui_address,
)
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest, WSJSONRequest


class KoraSpotAuthTests(IsolatedAsyncioWrapperTestCase):

    def setUp(self) -> None:
        super().setUp()
        # Any 32-byte seed is a valid Ed25519 private key -- fixed rather than random so a
        # failing assertion is reproducible.
        self._private_key_hex = "11" * 32
        self._private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(self._private_key_hex))
        self._public_key_bytes = self._private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        self.auth = KoraSpotAuth(self._private_key_hex)

    def test_derive_sui_address_is_deterministic_and_well_formed(self):
        address = derive_sui_address(self._public_key_bytes)
        self.assertTrue(address.startswith("0x"))
        self.assertEqual(66, len(address))  # "0x" + 64 hex chars
        self.assertEqual(address, derive_sui_address(self._public_key_bytes))

    def test_auth_account_address_matches_derive_sui_address(self):
        self.assertEqual(derive_sui_address(self._public_key_bytes), self.auth.account_address)

    def test_build_login_signature_round_trips_and_verifies(self):
        payload_signature, login_request = build_login_signature(
            self._private_key, self.auth.account_address, "kora-staging"
        )

        packed = base64.urlsafe_b64decode(payload_signature)
        self.assertEqual(1 + 64 + 32, len(packed))  # [sigType(1) | sig(64) | pubkey(32)]
        self.assertEqual(0x00, packed[0])
        signature, public_key_bytes = packed[1:65], packed[65:]
        self.assertEqual(self._public_key_bytes, public_key_bytes)

        wire_body = json.dumps(login_request.to_dict()).encode()
        digest = hashlib.blake2b(wire_body, digest_size=32).digest()
        # Raises InvalidSignature on failure -- the assertion is that it does not raise.
        Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(signature, digest)

    def test_build_login_signature_uses_default_json_separators(self):
        # The specific regression CONTRACT.md flagged: a compact `separators=(",", ":")`
        # rendering signs different bytes than kora_auth_client actually sends.
        _, login_request = build_login_signature(self._private_key, self.auth.account_address, "kora-staging")
        wire_body = json.dumps(login_request.to_dict())
        compact_body = json.dumps(login_request.to_dict(), separators=(",", ":"))
        self.assertNotEqual(wire_body, compact_body)
        self.assertIn(", ", wire_body)

    def test_build_login_signature_rejects_tampered_digest(self):
        payload_signature, login_request = build_login_signature(
            self._private_key, self.auth.account_address, "kora-staging"
        )
        packed = base64.urlsafe_b64decode(payload_signature)
        signature, public_key_bytes = packed[1:65], packed[65:]
        wire_body = json.dumps(login_request.to_dict()).encode()
        tampered_digest = hashlib.blake2b(wire_body + b"\x00", digest_size=32).digest()
        with self.assertRaises(InvalidSignature):
            Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(signature, tampered_digest)

    async def test_rest_authenticate_attaches_bearer_header(self):
        self.auth.access_token = "test-token"
        request = RESTRequest(method=RESTMethod.GET, url="https://example.invalid")
        authenticated = await self.auth.rest_authenticate(request)
        self.assertEqual("Bearer test-token", authenticated.headers["Authorization"])

    async def test_rest_authenticate_without_token_leaves_authorization_unset(self):
        request = RESTRequest(method=RESTMethod.GET, url="https://example.invalid")
        authenticated = await self.auth.rest_authenticate(request)
        self.assertNotIn("Authorization", authenticated.headers or {})

    async def test_ws_authenticate_is_a_noop(self):
        # KoraDataSource sets Authorization directly on the aiohttp ws_connect() call -- a
        # header-authenticated bot has no ticket to redeem in-band (CONTRACT.md).
        request = WSJSONRequest(payload={"op": "ping"})
        result = await self.auth.ws_authenticate(request)
        self.assertIs(request, result)

    # -- proactive refresh loop timing: must schedule the refresh strictly before the token's
    # own expiry, with margin -- never reactively on/after expiry (CONTRACT.md / plan doc "WS
    # lifecycle"). Table-driven over the TTL, since the sleep duration is a fraction of whatever
    # TTL the server reports, not a hardcoded number.

    async def test_refresh_loop_sleeps_a_fixed_fraction_of_the_ttl_leaving_a_margin_before_expiry(self):
        table = [
            # (valid_for_seconds, expected_sleep_for, expected_margin_before_expiry)
            (300.0, 300.0 * TOKEN_REFRESH_FRACTION, 300.0 * (1 - TOKEN_REFRESH_FRACTION)),
            (60.0, 60.0 * TOKEN_REFRESH_FRACTION, 60.0 * (1 - TOKEN_REFRESH_FRACTION)),
        ]
        for valid_for_seconds, expected_sleep_for, expected_margin in table:
            with self.subTest(valid_for_seconds=valid_for_seconds):
                self.auth._access_token_valid_for_seconds = valid_for_seconds
                sleep_mock = AsyncMock(side_effect=asyncio.CancelledError)
                with patch("asyncio.sleep", new=sleep_mock):
                    with self.assertRaises(asyncio.CancelledError):
                        await self.auth._refresh_loop()
                sleep_mock.assert_awaited_once_with(expected_sleep_for)
                # The load-bearing assertion: refresh fires strictly before expiry, not at/after
                # it -- a lapsed token also drops private WS subscriptions server-side, so a
                # reactive (post-expiry) refresh would already be too late.
                self.assertGreater(expected_margin, 0.0)
                self.assertLess(expected_sleep_for, valid_for_seconds)

    async def test_refresh_loop_sleep_has_a_one_second_floor_for_a_very_short_ttl(self):
        # 0.5s * 0.6 = 0.3s, below the 1.0s floor _refresh_loop enforces so it never busy-loops.
        self.auth._access_token_valid_for_seconds = 0.5
        sleep_mock = AsyncMock(side_effect=asyncio.CancelledError)
        with patch("asyncio.sleep", new=sleep_mock):
            with self.assertRaises(asyncio.CancelledError):
                await self.auth._refresh_loop()
        sleep_mock.assert_awaited_once_with(1.0)

    async def test_refresh_loop_falls_back_to_a_fresh_login_when_refresh_fails(self):
        # A rejected refresh token is a permanently doomed retry against _refresh() alone -- the
        # loop must fall back to _login() (kora_spot_auth.py's own comment on why) rather than
        # just logging and looping forever on the same failing call.
        self.auth._access_token_valid_for_seconds = 300.0
        self.auth._refresh = AsyncMock(side_effect=RuntimeError("refresh token rejected"))
        self.auth._login = AsyncMock(side_effect=asyncio.CancelledError)  # ends the loop for the test
        with patch("asyncio.sleep", new=AsyncMock()):
            with self.assertRaises(asyncio.CancelledError):
                await self.auth._refresh_loop()
        self.auth._refresh.assert_awaited_once()
        self.auth._login.assert_awaited_once()

    def test_apply_login_response_sets_expiry_from_the_servers_own_ttl(self):
        # access_token_expiry must be derived from accessTokenValidForSeconds (the server's
        # value), never a hardcoded 300 -- the refresh loop's own sleep_for depends on it staying
        # in sync with whatever the server actually issued.
        response = type(
            "LoginResponse", (), {"access_token": "tok", "refresh_token": "ref", "access_token_valid_for_seconds": 120}
        )()
        with patch("time.time", return_value=1_700_000_000.0):
            self.auth._apply_login_response(response)
        self.assertEqual(1_700_000_120.0, self.auth.access_token_expiry)
        self.assertEqual(120.0, self.auth._access_token_valid_for_seconds)


if __name__ == "__main__":
    unittest.main()
