"""
Tests for `KoraDataSource`: the WS ack/error/data-frame router, the reconnect-before-expiry
timer, and `place_order`'s MARKET-vs-LIMIT `expiresAt` handling.

No network is exercised anywhere in this file -- `KoraDataSource.__init__` does no I/O (it only
constructs a `KoraSpotAuth` and some `Configuration` objects), so every test below builds a real
`KoraDataSource` and reaches directly into its WS-frame parser or replaces just the generated
`TradingApi` client with a mock, rather than mocking the whole class out per `bluefin_perpetual`'s
own style for testing an SDK wrapper's internals.
"""
import asyncio
import json
import unittest
from test.isolated_asyncio_wrapper_test_case import IsolatedAsyncioWrapperTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from hummingbot.connector.exchange.kora_spot.data_sources.kora_data_source import (
    _WS_RECONNECT_MARGIN_SECONDS,
    KoraDataSource,
)

import kora_gateway_client  # noqa: E402  (sys.path wired by kora_data_source's own import)


class KoraDataSourceTests(IsolatedAsyncioWrapperTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.data_source = KoraDataSource(ed25519_private_key_hex="22" * 32)

    # -- WS ack/error/data-frame routing across all four channel shapes ---------------------

    async def test_route_data_frame_dispatches_each_channel_shape_to_its_own_queue(self):
        table = [
            ("orders", {"orderId": "O-1"}, lambda: self.data_source.get_order_update_event()),
            ("trades", {"fillId": "F-1"}, lambda: self.data_source.get_trade_update_event()),
            (
                "partialDepth.eXAU-USDCx@20",
                {"market": "eXAU-USDCx", "bids": [["10", "1"]]},
                lambda: self.data_source.get_partial_depth_event("eXAU-USDCx"),
            ),
            (
                "partialDepth.eXAU-USDCx@5",
                {"market": "eXAU-USDCx", "bids": [["11", "2"]]},
                lambda: self.data_source.get_partial_depth_event("eXAU-USDCx"),
            ),
            (
                "recentTrade.eXAU-USDCx",
                {"tradeId": "T-1"},
                lambda: self.data_source.get_recent_trade_event("eXAU-USDCx"),
            ),
        ]
        for channel, data, getter in table:
            with self.subTest(channel=channel):
                self.data_source._route_data_frame(channel, data)
                result = await asyncio.wait_for(getter(), timeout=1)
                self.assertEqual(data, result)

    async def test_route_data_frame_ignores_an_unrecognised_channel(self):
        # diffDepth/balances have no producer and are refused server-side at subscribe -- if one
        # ever arrived anyway, this must not raise or silently create a queue nobody reads.
        self.data_source._route_data_frame("balances", {"asset": "eXAU"})  # must not raise
        self.assertTrue(self.data_source._order_update_queue.empty())
        self.assertTrue(self.data_source._trade_update_queue.empty())

    async def test_handle_ws_message_resolves_pending_ack_and_error_frames(self):
        table = [
            ("ack", {"type": "ack", "op": "subscribe", "reqId": "7", "channels": ["orders"]}),
            ("error", {"type": "error", "reqId": "8", "code": "UNKNOWN_MARKET", "message": "nope"}),
        ]
        for label, msg in table:
            with self.subTest(label=label):
                req_id = msg["reqId"]
                fut: "asyncio.Future" = asyncio.get_event_loop().create_future()
                self.data_source._pending_acks[req_id] = fut
                self.data_source._handle_ws_message(json.dumps(msg))
                self.assertTrue(fut.done())
                self.assertEqual(msg, fut.result())

    async def test_handle_ws_message_drops_undecodable_json_without_raising(self):
        self.data_source._handle_ws_message("not json")  # must not raise
        self.assertTrue(self.data_source._order_update_queue.empty())

    async def test_handle_ws_message_drops_a_frame_missing_channel_or_data(self):
        # Neither an ack/error type nor a {channel, data} data-frame envelope -- must be dropped,
        # not routed as if channel/data were merely empty.
        self.data_source._handle_ws_message(json.dumps({"channel": "orders"}))  # no "data"
        self.assertTrue(self.data_source._order_update_queue.empty())

    # -- reconnect-before-expiry timing: must fire ahead of the token's actual expiry, with the
    # documented margin -- a header-authenticated bot has no in-band re-auth, so this reconnect
    # is the only recovery path and firing late means racing (or losing to) the server's own
    # close of the stale session.

    async def test_reconnect_before_expiry_loop_sleeps_to_land_before_expiry_with_margin(self):
        now = 1_700_000_000.0
        table = [300.0, 60.0]  # seconds until access_token_expiry, from "now"
        for seconds_until_expiry in table:
            with self.subTest(seconds_until_expiry=seconds_until_expiry):
                self.data_source._auth.access_token_expiry = now + seconds_until_expiry
                expected_sleep_for = seconds_until_expiry - _WS_RECONNECT_MARGIN_SECONDS
                sleep_mock = AsyncMock(side_effect=asyncio.CancelledError)
                with patch("time.time", return_value=now), patch("asyncio.sleep", new=sleep_mock):
                    with self.assertRaises(asyncio.CancelledError):
                        await self.data_source._reconnect_before_expiry_loop()
                sleep_mock.assert_awaited_once_with(expected_sleep_for)
                self.assertLess(expected_sleep_for, seconds_until_expiry)

    async def test_reconnect_before_expiry_loop_sleep_has_a_one_second_floor(self):
        # Expiry already inside the reconnect margin (e.g. a slow login) must not compute a
        # negative or zero sleep and busy-loop reconnecting.
        now = 1_700_000_000.0
        self.data_source._auth.access_token_expiry = now + 5.0  # < _WS_RECONNECT_MARGIN_SECONDS
        sleep_mock = AsyncMock(side_effect=asyncio.CancelledError)
        with patch("time.time", return_value=now), patch("asyncio.sleep", new=sleep_mock):
            with self.assertRaises(asyncio.CancelledError):
                await self.data_source._reconnect_before_expiry_loop()
        sleep_mock.assert_awaited_once_with(1.0)

    # -- place_order must never send expiresAt/timeInForce on a MARKET order -----------------

    async def test_place_order_sends_expires_at_and_time_in_force_on_limit_only(self):
        self.data_source._trading_api = AsyncMock()
        self.data_source._gateway_api_client = MagicMock()
        table = [
            # (order_type, kwargs, expect_expires_at, expect_time_in_force)
            ("LIMIT", {"price": "10", "quantity": "1", "quote_order_qty": None}, True, True),
            ("MARKET", {"price": None, "quantity": "1", "quote_order_qty": None}, False, False),
            ("MARKET", {"price": None, "quantity": None, "quote_order_qty": "50"}, False, False),
        ]
        for order_type, kwargs, expect_expires_at, expect_time_in_force in table:
            with self.subTest(order_type=order_type, quote_order_qty=kwargs.get("quote_order_qty")):
                self.data_source._trading_api.place_order.reset_mock()
                await self.data_source.place_order(
                    market="eXAU-USDCx",
                    side="BUY",
                    order_type=order_type,
                    post_only=False,
                    client_order_id=None,
                    **kwargs,
                )
                request = self.data_source._trading_api.place_order.call_args.args[0]
                self.assertIsInstance(request, kora_gateway_client.PlaceOrderRequest)
                self.assertEqual(expect_expires_at, request.expires_at is not None)
                self.assertEqual(expect_time_in_force, request.time_in_force is not None)


if __name__ == "__main__":
    unittest.main()
