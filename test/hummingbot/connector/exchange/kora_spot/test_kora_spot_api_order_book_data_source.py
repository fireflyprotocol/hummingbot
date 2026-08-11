"""
Tests for `KoraSpotAPIOrderBookDataSource`: partialDepth's "replace wholesale, never merge"
contract, `listen_for_order_book_diffs` being a genuine no-op (no `diffDepth` producer exists),
`listen_for_trades`'s settlement-state gate, and the mktEpoch-change forced-resnapshot path.

Mirrors `bluefin_perpetual_api_order_book_data_source.py`'s own test style: `connector` and
`data_source` are both plain `MagicMock`s, and the class under test is real.
"""
import asyncio
import unittest
from test.isolated_asyncio_wrapper_test_case import IsolatedAsyncioWrapperTestCase
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from hummingbot.connector.exchange.kora_spot.kora_spot_api_order_book_data_source import (
    KoraSpotAPIOrderBookDataSource,
)
from hummingbot.core.data_type.order_book_message import OrderBookMessageType


class KoraSpotAPIOrderBookDataSourceTests(IsolatedAsyncioWrapperTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.trading_pair = "eXAU-USDCx"
        cls.market = "eXAU-USDCx"

    def setUp(self) -> None:
        super().setUp()
        self.connector = MagicMock()
        self.connector.exchange_symbol_associated_to_pair = AsyncMock(return_value=self.market)
        self.connector.trading_pair_associated_to_exchange_symbol = AsyncMock(return_value=self.trading_pair)
        self.data_source = MagicMock()

        self.order_book_source = KoraSpotAPIOrderBookDataSource(
            trading_pairs=[self.trading_pair],
            connector=self.connector,
            data_source=self.data_source,
        )

    # -- partialDepth frames replace the book wholesale, never merge -------------------------

    async def test_partial_depth_frames_replace_the_book_wholesale_never_merge(self):
        output: "asyncio.Queue" = asyncio.Queue()
        first = {"market": self.market, "mktEpoch": 1, "bids": [["10", "1"]], "asks": [["11", "1"]]}
        second = {"market": self.market, "mktEpoch": 1, "bids": [["9", "5"]], "asks": [["12", "5"]]}

        await self.order_book_source._parse_order_book_snapshot_message(first, output)
        await self.order_book_source._parse_order_book_snapshot_message(second, output)

        first_message = output.get_nowait()
        second_message = output.get_nowait()
        self.assertEqual(first["bids"], first_message.content["bids"])
        self.assertEqual(first["asks"], first_message.content["asks"])
        # The load-bearing assertion: the second frame's message carries only the second frame's
        # levels -- nothing from the first frame survives into it, because there are no
        # tombstones on this channel and every frame is a full replacement.
        self.assertEqual(second["bids"], second_message.content["bids"])
        self.assertEqual(second["asks"], second_message.content["asks"])
        self.assertNotIn(first["bids"][0], second_message.content["bids"])
        self.assertTrue(output.empty())

    # -- listen_for_order_book_diffs is a genuine no-op: no diffDepth producer exists ---------

    async def test_listen_for_order_book_diffs_is_a_genuine_noop(self):
        output: "asyncio.Queue" = asyncio.Queue()
        task = asyncio.get_event_loop().create_task(
            self.order_book_source.listen_for_order_book_diffs(asyncio.get_event_loop(), output)
        )
        try:
            with self.assertRaises(asyncio.TimeoutError):
                await asyncio.wait_for(asyncio.shield(task), timeout=0.05)
            self.assertTrue(output.empty())
        finally:
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

    # -- listen_for_trades gates on settlementState == "settled" and drops everything else,
    # including a value this build has never seen -- the failure set is open by design.

    async def test_parse_trade_message_emits_only_on_settled_and_drops_every_other_state(self):
        table = [
            ("settled", True),
            ("settling", False),
            ("busted", False),
            ("rejected", False),
            ("some_future_unknown_state", False),  # the open-failure-set case
            (None, False),
        ]
        for settlement_state, expect_emitted in table:
            with self.subTest(settlement_state=settlement_state):
                output: "asyncio.Queue" = asyncio.Queue()
                message = {
                    "market": self.market,
                    "mktEpoch": 5,
                    "tradeId": "T-1",
                    "side": "BUY",
                    "quantity": "1",
                    "price": "10",
                    "settlementState": settlement_state,
                }
                await self.order_book_source._parse_trade_message(message, output)
                self.assertEqual(expect_emitted, not output.empty())
                if expect_emitted:
                    emitted = output.get_nowait()
                    self.assertEqual(OrderBookMessageType.TRADE, emitted.type)
                    self.assertEqual("T-1", emitted.content["trade_id"])

    # -- mktEpoch change forces a fresh REST snapshot and drops the stale frame itself -------

    async def test_mkt_epoch_change_forces_a_fresh_snapshot_and_drops_the_stale_frame(self):
        fresh_snapshot = SimpleNamespace(bids=[["7", "1"]], asks=[["8", "1"]], last_update_id=99)
        self.data_source.get_depth = AsyncMock(return_value=fresh_snapshot)

        output: "asyncio.Queue" = asyncio.Queue()
        self.order_book_source._snapshot_output_queue = output
        self.order_book_source._mkt_epochs[self.market] = 1  # a prior sighting, so epoch 2 below is a real change

        stale_frame = {"market": self.market, "mktEpoch": 2, "bids": [["999", "1"]], "asks": [["1000", "1"]]}
        await self.order_book_source._parse_order_book_snapshot_message(stale_frame, output)
        await asyncio.sleep(0.05)  # let the fire-and-forget resnapshot task run

        message = output.get_nowait()
        self.assertEqual(fresh_snapshot.bids, message.content["bids"])
        self.assertEqual(fresh_snapshot.asks, message.content["asks"])
        self.assertTrue(output.empty())  # the stale frame itself was dropped, not queued

    async def test_mkt_epoch_unchanged_does_not_force_a_resnapshot(self):
        self.data_source.get_depth = AsyncMock()
        output: "asyncio.Queue" = asyncio.Queue()
        self.order_book_source._snapshot_output_queue = output
        self.order_book_source._mkt_epochs[self.market] = 1

        frame = {"market": self.market, "mktEpoch": 1, "bids": [["1", "1"]], "asks": [["2", "1"]]}
        await self.order_book_source._parse_order_book_snapshot_message(frame, output)
        await asyncio.sleep(0.05)

        self.data_source.get_depth.assert_not_called()
        message = output.get_nowait()
        self.assertEqual(frame["bids"], message.content["bids"])
        self.assertTrue(output.empty())


if __name__ == "__main__":
    unittest.main()
