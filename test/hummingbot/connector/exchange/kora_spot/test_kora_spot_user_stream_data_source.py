"""
Tests for `KoraSpotUserStreamDataSource`: the order-update/trade-update event race and its
`_type` tagging convention, and the mktEpoch-change log-only behavior.

The mktEpoch test is a regression guard in the direction CONTRACT.md calls out explicitly: this
file must only *log* an mktEpoch change, never purge -- purging tracked orders is
`kora_spot_exchange.py`'s job, since it's the only file that owns `_order_tracker`. A change that
quietly added purging here (e.g. by reaching into `self._connector`) would be exactly the kind of
regression this test is meant to catch; contrast with `test_kora_spot_exchange.py`'s mktEpoch
test, where a purge is exactly what's expected.
"""
import asyncio
import unittest
from test.isolated_asyncio_wrapper_test_case import IsolatedAsyncioWrapperTestCase
from unittest.mock import AsyncMock, MagicMock

from hummingbot.connector.exchange.kora_spot.kora_spot_user_stream_data_source import (
    KoraSpotUserStreamDataSource,
)


async def _never_resolves():
    # Stands in for "the other event queue has nothing yet" in the FIRST_COMPLETED race below --
    # an AsyncMock with a long sleep would still eventually resolve and flake the test; this
    # genuinely never does within the test's lifetime, so exactly one getter can win.
    await asyncio.Event().wait()


class KoraSpotUserStreamDataSourceTests(IsolatedAsyncioWrapperTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.market = "eXAU-USDCx"

    def setUp(self) -> None:
        super().setUp()
        self.connector = MagicMock()
        self.data_source = MagicMock()
        self.user_stream_source = KoraSpotUserStreamDataSource(
            connector=self.connector,
            data_source=self.data_source,
        )

    async def _listen_once(self, timeout: float = 1.0) -> dict:
        output: "asyncio.Queue" = asyncio.Queue()
        task = asyncio.get_event_loop().create_task(self.user_stream_source.listen_for_user_stream(output))
        try:
            return await asyncio.wait_for(output.get(), timeout=timeout)
        finally:
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

    # -- the order-update/trade-update race and its _type tagging convention ----------------

    async def test_listen_for_user_stream_tags_whichever_event_arrives_first(self):
        table = [
            ("order_update", {"orderId": "O-1"}),
            ("trade_update", {"fillId": "F-1"}),
        ]
        for winning_tag, payload in table:
            with self.subTest(winning_tag=winning_tag):
                self.data_source.get_order_update_event = (
                    AsyncMock(return_value=payload) if winning_tag == "order_update" else _never_resolves
                )
                self.data_source.get_trade_update_event = (
                    AsyncMock(return_value=payload) if winning_tag == "trade_update" else _never_resolves
                )

                event = await self._listen_once()

                self.assertEqual(winning_tag, event["_type"])
                for key, value in payload.items():
                    self.assertEqual(value, event[key])

    # -- mktEpoch changing is logged only -- this file must never purge tracked orders -------

    async def test_mkt_epoch_change_is_logged_only_and_never_touches_the_connector(self):
        self.data_source.get_order_update_event = AsyncMock(
            return_value={"market": self.market, "mktEpoch": 2, "orderId": "O-1", "status": "cancelled"}
        )
        self.data_source.get_trade_update_event = _never_resolves
        # A prior sighting, so epoch 2 above is a genuine change and not first-sight bookkeeping.
        self.user_stream_source._last_mkt_epoch[self.market] = 1

        event = await self._listen_once()

        self.assertEqual("order_update", event["_type"])
        self.assertEqual(2, self.user_stream_source._last_mkt_epoch[self.market])
        # The load-bearing assertion: nothing on this path calls through to the connector (which
        # is what would purge tracked orders) -- only local `_last_mkt_epoch` bookkeeping and a
        # log line. `kora_spot_exchange.py` owns the purge, not this file.
        self.assertEqual([], self.connector.mock_calls)

    async def test_mkt_epoch_first_sighting_does_not_warn_or_touch_the_connector(self):
        self.data_source.get_order_update_event = AsyncMock(
            return_value={"market": self.market, "mktEpoch": 1, "orderId": "O-1", "status": "open"}
        )
        self.data_source.get_trade_update_event = _never_resolves

        event = await self._listen_once()

        self.assertEqual("order_update", event["_type"])
        self.assertEqual(1, self.user_stream_source._last_mkt_epoch[self.market])
        self.assertEqual([], self.connector.mock_calls)


if __name__ == "__main__":
    unittest.main()
