"""
Ed25519 wallet-signature auth for kora_spot.

There is no SDK for this: gateway-service and node-service sit behind auth-server, which issues
short-lived JWTs (5 min access / 30 day refresh) in exchange for a wallet signature over a login
payload — the same flow RFQ takers use (docs/taker-guide.md Phase 1). This module owns that
signature, the resulting token pair, and a proactive refresh loop that keeps the token from ever
lapsing mid-session (a lapse also drops private WS subscriptions server-side, so refreshing
reactively on 401 is a strictly worse design here — see CONTRACT.md / the plan doc's "WS
lifecycle" section).

Signing library: PyNaCl is NOT a hummingbot dependency (checked setup.py / setup/environment.yml);
`cryptography>=41.0.2` already is, and its `hazmat.primitives.asymmetric.ed25519` module covers
everything CONTRACT.md's PyNaCl sketch needs (raw Ed25519 sign + raw public-key bytes). Per the
ladder, an already-installed dependency beats adding a new one for the same job, so this file uses
`cryptography` and adds no new third-party dependency to the repo.
"""
import asyncio
import base64
import hashlib
import json
import logging
import os
import sys
import time
from typing import Optional, Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

import hummingbot.connector.exchange.kora_spot.kora_spot_constants as CONSTANTS
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest
from hummingbot.logger import HummingbotLogger

# kora_auth_client is generated source, not an installed package — add its parent dir to
# sys.path the same way data_sources/kora_data_source.py does for kora_gateway_client
# (CONTRACT.md "Generated REST clients"). Guarded so importing this module twice (or importing
# it after kora_data_source.py already ran the equivalent insert) doesn't duplicate the path.
_AUTH_CLIENT_PARENT = os.path.join(os.path.dirname(__file__), "generated", "kora_auth_client")
if _AUTH_CLIENT_PARENT not in sys.path:
    sys.path.insert(0, _AUTH_CLIENT_PARENT)

import kora_auth_client  # noqa: E402

# Refresh at a fixed fraction of the server-reported TTL rather than a hardcoded second count, so
# this stays correct if accessTokenValidForSeconds ever changes server-side. 0.6 of a 300s token
# refreshes at the 180s mark -- 120s of margin before the real 300s expiry, comfortably "well
# inside the window" per CONTRACT.md, while leaving KoraDataSource's reconnect-before-expiry timer
# (which reads access_token_expiry directly) room to fire after the refresh has already landed.
TOKEN_REFRESH_FRACTION = 0.6

# Retry cadence for a failed login/refresh call. Deliberately not exponential backoff:
# ponytail: fixed 5s retry, upgrade to exponential backoff if repeated auth-server outages make
# this noisy in practice -- not something to design for speculatively today.
_RETRY_DELAY_SECONDS = 5.0


def derive_sui_address(public_key_bytes: bytes) -> str:
    """Sui address derivation from a raw 32-byte Ed25519 public key (CONTRACT.md)."""
    h = hashlib.blake2b(b"\x00" + public_key_bytes, digest_size=32)
    return "0x" + h.hexdigest()[:64].lower().zfill(64)


def build_login_signature(
    private_key: Ed25519PrivateKey, account_address: str, audience: str
) -> Tuple[str, "kora_auth_client.LoginRequest"]:
    """
    Builds the signed login payload and the exact `LoginRequest` object that must be passed to
    `post_auth_token` alongside it.

    Why the object is returned (not just the signature): the bytes we sign must be byte-identical
    to what `kora_auth_client` actually puts on the wire, and re-deriving the "same" JSON twice —
    once to sign, once when the generated client serializes its own copy — risks the two drifting
    (different key order, different whitespace, a re-rolled `signedAtMillis`). Returning the one
    `LoginRequest` instance we signed and having the caller pass that exact instance into
    `post_auth_token` removes the risk instead of trusting two independent renderings to agree.

    Verified serialization path (kora_auth_client/rest.py `RESTClientObject.request`,
    kora_auth_client/api_client.py `sanitize_for_serialization`): for a pydantic model, the client
    sends `json.dumps(sanitize_for_serialization(login_request))`, which resolves to
    `json.dumps(login_request.to_dict())` (`sanitize_for_serialization` recurses into the dict
    `to_dict()` already returned, but a dict of str/int primitives round-trips unchanged). Two
    things follow, and both matter:
      1. `to_dict()` uses `model_dump(by_alias=True, exclude_none=True)`, so the wire keys are
         `accountAddress`/`signedAtMillis`/`audience` in that declaration order, not the snake_case
         attribute names.
      2. `json.dumps(...)` here uses Python's *default* separators (`", "` / `": "`), not the
         compact `separators=(",", ":")` CONTRACT.md's pseudocode shows. That pseudocode form
         would sign different bytes than the client actually sends and every login would fail
         signature verification server-side — this is the exact risk CONTRACT.md flagged and asked
         to be verified rather than assumed.
    Building `body_bytes` from the real `LoginRequest.to_dict()` (instead of a hand-rolled dict)
    is what keeps this correct if the generated client's serialization ever changes shape.
    """
    login_request = kora_auth_client.LoginRequest(
        account_address=account_address,
        signed_at_millis=int(time.time() * 1000),
        audience=audience,
    )
    body_bytes = json.dumps(login_request.to_dict()).encode()
    digest = hashlib.blake2b(body_bytes, digest_size=32).digest()
    signature = private_key.sign(digest)  # cryptography returns the raw 64-byte signature directly
    public_key_bytes = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    packed = b"\x00" + signature + public_key_bytes  # [sigType(1) | sig(64) | pubkey(32)]
    payload_signature = base64.urlsafe_b64encode(packed).decode()
    return payload_signature, login_request


class KoraSpotAuth(AuthBase):
    """
    Holds the Ed25519 keypair and the current access/refresh token pair, and drives the
    proactive refresh loop. Constructed and owned internally by `KoraDataSource` (which is the
    only place CONTRACT.md fixes a constructor signature for — it takes the raw hex key, not an
    auth object — so `KoraDataSource` builds one `KoraSpotAuth` and both its own REST calls and
    its WS reconnect-before-expiry timer read `access_token`/`access_token_expiry` off this single
    instance, rather than each keeping separate timing state).
    """

    _logger: Optional[HummingbotLogger] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._logger is None:
            cls._logger = logging.getLogger(__name__)
        return cls._logger

    def __init__(
        self,
        ed25519_private_key_hex: str,
        auth_rest_url: str = CONSTANTS.AUTH_REST_URL,
        audience: str = CONSTANTS.JWT_AUDIENCE,
    ):
        self._private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(ed25519_private_key_hex))
        self._public_key_bytes = self._private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        self.account_address: str = derive_sui_address(self._public_key_bytes)

        self._auth_rest_url = auth_rest_url
        self._audience = audience

        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        # Epoch seconds. 0 until the first successful login -- callers that read this before
        # `start()` completes should treat 0 as "not yet authenticated", not as an expired token.
        self.access_token_expiry: float = 0.0
        self._access_token_valid_for_seconds: float = 300.0  # overwritten from the server's own value

        self._refresh_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Logs in and starts the proactive-refresh loop. Idempotent."""
        if self._refresh_task is not None:
            return
        await self._login()
        self._refresh_task = asyncio.create_task(self._refresh_loop())

    async def stop(self) -> None:
        if self._refresh_task is not None:
            self._refresh_task.cancel()
            self._refresh_task = None

    def _configuration(self) -> "kora_auth_client.Configuration":
        # A fresh Configuration/ApiClient per call rather than one held open: login/refresh are
        # rare (every ~180s at most) so the connection-reuse cost that matters for the gateway
        # client (see kora_data_source.py's comment on mutating Configuration.access_token in
        # place) doesn't apply here -- neither call needs a bearer token anyway.
        return kora_auth_client.Configuration(host=self._auth_rest_url)

    async def _login(self) -> None:
        async with kora_auth_client.ApiClient(self._configuration()) as api_client:
            api = kora_auth_client.DefaultApi(api_client)
            payload_signature, login_request = build_login_signature(
                self._private_key, self.account_address, self._audience
            )
            response = await api.post_auth_token(payload_signature=payload_signature, login_request=login_request)
        self._apply_login_response(response)
        self.logger().info("kora_spot: logged in as %s", self.account_address)

    async def _refresh(self) -> None:
        async with kora_auth_client.ApiClient(self._configuration()) as api_client:
            api = kora_auth_client.DefaultApi(api_client)
            response = await api.put_auth_token_refresh(
                kora_auth_client.RefreshRequest(refresh_token=self.refresh_token)
            )
        self._apply_login_response(response)

    def _apply_login_response(self, response: "kora_auth_client.LoginResponse") -> None:
        self.access_token = response.access_token
        self.refresh_token = response.refresh_token
        self._access_token_valid_for_seconds = float(response.access_token_valid_for_seconds)
        self.access_token_expiry = time.time() + self._access_token_valid_for_seconds

    async def _refresh_loop(self) -> None:
        while True:
            sleep_for = max(self._access_token_valid_for_seconds * TOKEN_REFRESH_FRACTION, 1.0)
            await asyncio.sleep(sleep_for)
            try:
                await self._refresh()
                continue
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().warning("kora_spot: token refresh failed; falling back to a fresh login")
            # A rejected refresh token (auth-server restart, key rotation, explicit revocation) is
            # a permanently doomed retry if we keep calling _refresh() -- unlike a REST client with
            # no other credential, this connector still holds the Ed25519 private key, so a fresh
            # `_login()` is a real recovery path, not just a second thing to also retry forever.
            try:
                await self._login()
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().exception("kora_spot: fresh login also failed; retrying in %ss", _RETRY_DELAY_SECONDS)
                await asyncio.sleep(_RETRY_DELAY_SECONDS)

    # -- hummingbot AuthBase surface --------------------------------------------------------
    # Framework-compatibility only (see kora_spot_web_utils.py's build_api_factory docstring):
    # the generated kora_gateway_client/kora_auth_client clients issue the actual HTTP calls and
    # attach Authorization themselves, bypassing WebAssistantsFactory entirely. These two methods
    # exist so kora_spot still satisfies AuthBase's abstract surface; they're harmless if the
    # framework ever does route a request through them, since they attach the live token.

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        headers = dict(request.headers or {})
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        request.headers = headers
        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        # No-op: KoraDataSource sets the Authorization header directly on its own aiohttp
        # ws_connect() call (data_sources/kora_data_source.py) -- a header-authenticated bot has
        # no ticket to redeem in-band, so there's nothing for a WSRequest-level hook to add here.
        return request


if __name__ == "__main__":
    # ponytail self-check: the crypto path (signing + address derivation) has no test coverage
    # elsewhere and is the one piece of this connector with no codegen or framework safety net.
    # Round-trips a signature through the real verify key rather than trusting the sign call alone.
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    _sk = Ed25519PrivateKey.generate()
    _pub_bytes = _sk.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    _addr = derive_sui_address(_pub_bytes)
    assert _addr.startswith("0x") and len(_addr) == 66, _addr
    assert _addr == derive_sui_address(_pub_bytes), "derive_sui_address must be deterministic"

    _sig_b64, _login_request = build_login_signature(_sk, _addr, "kora-staging")
    _packed = base64.urlsafe_b64decode(_sig_b64)
    assert len(_packed) == 1 + 64 + 32, len(_packed)
    assert _packed[0] == 0x00
    _sig, _pub = _packed[1:65], _packed[65:]
    assert _pub == _pub_bytes

    _digest = hashlib.blake2b(json.dumps(_login_request.to_dict()).encode(), digest_size=32).digest()
    Ed25519PublicKey.from_public_bytes(_pub).verify(_sig, _digest)  # raises InvalidSignature on failure

    try:
        Ed25519PublicKey.from_public_bytes(_pub).verify(_sig, _digest + b"\x00")
        raise AssertionError("verify() should have rejected a tampered digest")
    except InvalidSignature:
        pass

    print("kora_spot_auth self-check passed")
