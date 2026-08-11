"""
Tests for `KoraSpotExchange`.

Builds a real `KoraSpotExchange` (real `_order_tracker`, real `ExchangePyBase` machinery) and
swaps out only `exchange._data_source` for a `MagicMock` -- constructing the real connector
class exercises the actual wiring (trade fee schema lookup, order tracker event triggers,
mktEpoch bookkeeping) rather than a hand-rolled stand-in, and `KoraDataSource.__init__` performs
no network I/O, so there is nothing to fake at construction time. `KoraSpotExchange`'s own
`__main__` self-check block already demonstrates this pattern for the mktEpoch purge; this file
extends it into real, run-under-pytest table-driven coverage of everything CONTRACT.md calls out.

`_place_cancel` propagating a 501 (`test_place_cancel_propagates_a_501_rather_than_returning_false`)
is the single most important behavioral guarantee in the whole connector -- see CONTRACT.md's
"Non-negotiables" -- so it is the first test in this file.
"""
import asyncio
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from test.isolated_asyncio_wrapper_test_case import IsolatedAsyncioWrapperTestCase
from unittest.mock import AsyncMock, MagicMock

from hummingbot.connector.exchange.kora_spot.kora_spot_exchange import KoraSpotExchange
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderState

# kora_spot_exchange's own import already inserted generated/kora_gateway_client onto sys.path --
# this must come after the connector import above, not before, or the bare `import
# kora_gateway_client` below can't resolve it.
import kora_gateway_client  # noqa: E402

PRIVATE_KEY_HEX = "33" * 32  # any 32-byte seed is a valid Ed25519 key; fixed for reproducibility
TRADING_PAIR = "eXAU-USDCx"
OTHER_TRADING_PAIR = "OTHER-USDCx"
MARKET = "eXAU-USDCx"


def _order(**overrides) -> "kora_gateway_client.Order":
    fields = dict(
        orderId="O-1",
        market=MARKET,
        side="BUY",
        type="LIMIT",
        quantity="1",
        status="open",
        remainingQty="1",
        cancelledQty="0",
        filledQty="0",
        settlingQty="0",
        bustedQty="0",
        createdAt=datetime.now(timezone.utc),
    )
    fields.update(overrides)
    return kora_gateway_client.Order(**fields)


def _fill(**overrides) -> "kora_gateway_client.Fill":
    fields = dict(
        fillId="F-1",
        orderId="O-1",
        market=MARKET,
        side="BUY",
        price="10",
        quantity="1",
        isMaker=True,
        settlementState="settled",
        matchedAt=datetime.now(timezone.utc),
    )
    fields.update(overrides)
    return kora_gateway_client.Fill(**fields)


def _in_flight_order(**overrides) -> InFlightOrder:
    fields = dict(
        client_order_id="C-1",
        trading_pair=TRADING_PAIR,
        order_type=OrderType.LIMIT,
        trade_type=TradeType.BUY,
        amount=Decimal("1"),
        creation_timestamp=1.0,
        price=Decimal("10"),
        exchange_order_id="O-1",
        initial_state=OrderState.OPEN,
    )
    fields.update(overrides)
    return InFlightOrder(**fields)


class KoraSpotExchangeTests(IsolatedAsyncioWrapperTestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.exchange = KoraSpotExchange(
            kora_spot_ed25519_private_key=PRIVATE_KEY_HEX,
            trading_pairs=[TRADING_PAIR, OTHER_TRADING_PAIR],
            trading_required=True,
        )
        # KoraDataSource does no network I/O in __init__, but every REST/WS call it would make
        # is replaced here -- these tests are about kora_spot_exchange.py's own logic, not the
        # data source's (that's data_sources/kora_data_source.py's own test file).
        self.exchange._data_source = MagicMock()
        self.exchange.exchange_symbol_associated_to_pair = AsyncMock(side_effect=lambda trading_pair: trading_pair)
        self.exchange.trading_pair_associated_to_exchange_symbol = AsyncMock(side_effect=lambda symbol: symbol)

    # -- _place_cancel must propagate a 501 as an ordinary failed cancel, never a silent no-op

    async def test_place_cancel_propagates_a_501_rather_than_returning_false(self):
        tracked_order = _in_flight_order()
        self.exchange._data_source.cancel_order = AsyncMock(
            side_effect=kora_gateway_client.ApiException(status=501, reason="Not Implemented")
        )

        with self.assertRaises(kora_gateway_client.ApiException) as ctx:
            await self.exchange._place_cancel("C-1", tracked_order)
        self.assertEqual(501, ctx.exception.status)

    async def test_place_cancel_returns_true_only_when_the_order_is_actually_cancelled(self):
        tracked_order = _in_flight_order()
        table = [
            (_order(status="cancelled"), True),
            # already_terminal + filled: this cancel raced a fill that settled first. Must not
            # report True (which would write a CANCELED transition over a completed order).
            (_order(status="filled", alreadyTerminal=True), False),
            (_order(status="open"), False),
        ]
        for order, expected in table:
            with self.subTest(status=order.status):
                self.exchange._data_source.cancel_order = AsyncMock(return_value=order)
                result = await self.exchange._place_cancel("C-1", tracked_order)
                self.assertEqual(expected, result)

    # -- fills only ever count as trades when settlementState == "settled" ------------------

    async def test_all_trade_updates_for_order_only_includes_settled_fills(self):
        table = [
            ("settled", True),
            ("settling", False),
            ("busted", False),
            ("rejected", False),
        ]
        order = _in_flight_order()
        for settlement_state, expect_included in table:
            with self.subTest(settlement_state=settlement_state):
                fill = _fill(settlementState=settlement_state)
                self.exchange._data_source.get_fills = AsyncMock(return_value=[fill])
                updates = await self.exchange._all_trade_updates_for_order(order)
                self.assertEqual(expect_included, len(updates) == 1)

    async def test_all_trade_updates_for_order_only_returns_settled_fills_from_a_mixed_batch(self):
        order = _in_flight_order()
        settled = _fill(fillId="F-settled", settlementState="settled")
        settling = _fill(fillId="F-settling", settlementState="settling")
        busted = _fill(fillId="F-busted", settlementState="busted")
        self.exchange._data_source.get_fills = AsyncMock(return_value=[settled, settling, busted])

        updates = await self.exchange._all_trade_updates_for_order(order)

        self.assertEqual(1, len(updates))
        self.assertEqual("F-settled", updates[0].trade_id)

    # -- order-status mapping (open-orders-list signal, since GetOrder is 501 today) ---------

    async def test_request_order_status_maps_every_known_order_status(self):
        tracked_order = _in_flight_order()
        table = [
            ("open", OrderState.OPEN),
            ("partially_filled", OrderState.PARTIALLY_FILLED),
            ("filled", OrderState.FILLED),
            ("cancelled", OrderState.CANCELED),
            ("expired", OrderState.CANCELED),
            ("rejected", OrderState.FAILED),
        ]
        for status, expected_state in table:
            with self.subTest(status=status):
                self.exchange._data_source.get_open_orders = AsyncMock(return_value=[_order(status=status)])
                update = await self.exchange._request_order_status(tracked_order)
                self.assertEqual(expected_state, update.new_state)

    async def test_request_order_status_falls_back_to_fills_when_missing_from_open_orders(self):
        tracked_order = _in_flight_order()
        self.exchange._data_source.get_open_orders = AsyncMock(return_value=[])  # order not resting anymore
        table = [
            ([_fill(settlementState="settled")], OrderState.FILLED),
            ([_fill(settlementState="busted")], OrderState.CANCELED),
            ([], OrderState.CANCELED),  # gone with no settled fill: cancelled/expired, never assumed filled
        ]
        for fills, expected_state in table:
            with self.subTest(fills=[f.settlement_state.value for f in fills] or "none"):
                self.exchange._data_source.get_fills = AsyncMock(return_value=fills)
                update = await self.exchange._request_order_status(tracked_order)
                self.assertEqual(expected_state, update.new_state)

    # -- balances: available -> free, locked -> locked, directly, never cross-checked against
    # total (total != free + locked is a real invariant on this venue, not a bug to "fix" here)

    async def test_update_balances_maps_available_to_free_without_deriving_from_total(self):
        # Deliberately total != available + locked (100 != 30 + 80) -- a correct implementation
        # must not notice or "fix" this; it is documented venue behavior (CONTRACT.md).
        self.exchange._data_source.get_balances = AsyncMock(
            return_value={
                "eXAU": {
                    "total": Decimal("100"),
                    "available": Decimal("30"),
                    "locked": Decimal("80"),
                    "engine_total": Decimal("90"),
                }
            }
        )

        await self.exchange._update_balances()

        self.assertEqual(Decimal("100"), self.exchange._account_balances["eXAU"])
        self.assertEqual(Decimal("30"), self.exchange._account_available_balances["eXAU"])

    async def test_update_balances_drops_assets_no_longer_present_remotely(self):
        self.exchange._account_balances["STALE"] = Decimal("1")
        self.exchange._account_available_balances["STALE"] = Decimal("1")
        self.exchange._data_source.get_balances = AsyncMock(
            return_value={"eXAU": {"total": Decimal("5"), "available": Decimal("5"), "locked": Decimal("0")}}
        )

        await self.exchange._update_balances()

        self.assertNotIn("STALE", self.exchange._account_balances)
        self.assertNotIn("STALE", self.exchange._account_available_balances)
        self.assertEqual(Decimal("5"), self.exchange._account_balances["eXAU"])

    # -- mktEpoch change purges every tracked order on that market, and only that market -----

    async def test_mkt_epoch_change_purges_tracked_orders_on_that_market_only(self):
        same_market_order = _in_flight_order(client_order_id="A", exchange_order_id="O-1", trading_pair=TRADING_PAIR)
        other_market_order = _in_flight_order(
            client_order_id="B", exchange_order_id="O-2", trading_pair=OTHER_TRADING_PAIR
        )
        self.exchange._order_tracker.start_tracking_order(same_market_order)
        self.exchange._order_tracker.start_tracking_order(other_market_order)

        first_sighting = await self.exchange._check_mkt_epoch_and_purge(MARKET, 1)
        self.assertFalse(first_sighting)  # never purges on the first observed epoch

        same_epoch_again = await self.exchange._check_mkt_epoch_and_purge(MARKET, 1)
        self.assertFalse(same_epoch_again)

        purged = await self.exchange._check_mkt_epoch_and_purge(MARKET, 2)
        self.assertTrue(purged)
        await asyncio.sleep(0.05)  # process_order_update schedules via safe_ensure_future

        self.assertEqual(OrderState.FAILED, same_market_order.current_state)
        self.assertEqual(OrderState.OPEN, other_market_order.current_state)  # untouched

    async def test_process_order_update_does_not_apply_its_own_status_after_an_epoch_purge(self):
        # An mktEpoch bump arriving on the same `orders` frame as a status must not immediately
        # contradict the purge it just performed with that frame's own "still resting" status --
        # `_process_order_update` must bail out right after the purge, never reaching the
        # tracked-order lookup/process_order_update call below it.
        tracked_order = _in_flight_order(exchange_order_id="O-1", trading_pair=TRADING_PAIR)
        self.exchange._order_tracker.start_tracking_order(tracked_order)
        self.exchange._order_tracker.process_order_update = MagicMock()
        self.exchange._check_mkt_epoch_and_purge = AsyncMock(return_value=True)  # simulate a purge just happened

        await self.exchange._process_order_update({"market": MARKET, "mktEpoch": 2, "orderId": "O-1", "status": "open"})

        self.exchange._order_tracker.process_order_update.assert_not_called()

    async def test_process_trade_update_ignores_non_settled_states(self):
        tracked_order = _in_flight_order(exchange_order_id="O-1", trading_pair=TRADING_PAIR)
        self.exchange._order_tracker.start_tracking_order(tracked_order)
        for settlement_state in ("settling", "busted", "rejected"):
            with self.subTest(settlement_state=settlement_state):
                await self.exchange._process_trade_update(
                    {
                        "market": MARKET,
                        "mktEpoch": 1,
                        "orderId": "O-1",
                        "settlementState": settlement_state,
                        "price": "10",
                        "quantity": "1",
                        "fillId": "F-x",
                    }
                )
                self.assertEqual({}, tracked_order.order_fills)


if __name__ == "__main__":
    unittest.main()
