"""
kora_spot main connector class.

`KoraSpotExchange` is an `ExchangePyBase` that owns exactly one `KoraDataSource` (the wrapper
around the two generated OpenAPI clients plus the hand-rolled WS channel client, see
`data_sources/kora_data_source.py`) and hands that single instance to both
`KoraSpotAPIOrderBookDataSource` and `KoraSpotUserStreamDataSource`, per CONTRACT.md's wiring.
Everything venue-specific that isn't already handled inside those four files lives here:

- Placing/cancelling orders and mapping hummingbot's OrderType/TradeType onto the
  "LIMIT"/"MARKET" and "BUY"/"SELL" strings `KoraDataSource.place_order` expects.
- Balances from node-service (never gateway-service -- it has none), mapped directly with no
  arithmetic (`total != free + locked` on this venue).
- Trading rules/fees from `KoraDataSource.markets` (loaded once at `initialize()`; markets.yaml
  changes need a restart anyway, so there is nothing to re-poll for -- CLAUDE.md).
- `_request_order_status`, since `GetOrder` is 501 today: derive from the open-orders list, and
  only fall back to a `GetFills` lookup -- never assume filled -- when an order has disappeared
  from it with no terminal WS frame having resolved it yet.
- `mktEpoch` purge: `kora_spot_api_order_book_data_source.py` and
  `kora_spot_user_stream_data_source.py` both only *log* a mktEpoch change on the frames that
  carry it; this file is where the actual InFlightOrder bookkeeping gets corrected, because it's
  the only file that owns `_order_tracker`.
"""
import asyncio
import os
import sys
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from bidict import bidict

from hummingbot.connector.constants import s_decimal_NaN
from hummingbot.connector.exchange.kora_spot import kora_spot_constants as CONSTANTS
from hummingbot.connector.exchange.kora_spot.data_sources.kora_data_source import KoraDataSource
from hummingbot.connector.exchange.kora_spot.kora_spot_api_order_book_data_source import (
    KoraSpotAPIOrderBookDataSource,
)
from hummingbot.connector.exchange.kora_spot.kora_spot_user_stream_data_source import (
    KoraSpotUserStreamDataSource,
)
from hummingbot.connector.exchange.kora_spot import kora_spot_web_utils as web_utils
from hummingbot.connector.exchange_py_base import ExchangePyBase
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.connector.utils import combine_to_hb_trading_pair
from hummingbot.core.api_throttler.data_types import RateLimit
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderState, OrderUpdate, TradeUpdate
from hummingbot.core.data_type.order_book_tracker_data_source import OrderBookTrackerDataSource
from hummingbot.core.data_type.trade_fee import AddedToCostTradeFee, TokenAmount, TradeFeeBase
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.utils.estimate_fee import build_trade_fee
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory

# kora_gateway_client is generated source under generated/, not an installed package
# (CONTRACT.md "Generated REST clients"). This file needs real runtime access to it (enum
# members, ApiException) rather than just type-checking imports, so it guards its own
# sys.path insert the same way data_sources/kora_data_source.py and kora_spot_auth.py do,
# instead of relying on those modules having already run theirs as an import-order side effect.
_GATEWAY_CLIENT_PARENT = os.path.join(os.path.dirname(__file__), "generated", "kora_gateway_client")
if _GATEWAY_CLIENT_PARENT not in sys.path:
    sys.path.insert(0, _GATEWAY_CLIENT_PARENT)

import kora_gateway_client  # noqa: E402

# OrderStatus (Order.status, open-orders-list signal) -> hummingbot OrderState. Keyed by the
# plain string value, not by the enum member, since it's used against both the generated
# client's enum (get_open_orders) and the raw WS `orders` frame's JSON string -- one dict serves
# both without a second lookup table. Deliberately separate from CONSTANTS.ORDER_STATE, which is
# keyed on Fill.settlementState (a different field on a different object) and only ever answers
# "is this fill settled" -- CONTRACT.md's "!= settled" non-negotiable applies to that one, not to
# this one; an OrderStatus has its own closed, small set (CONTRACT.md's Order shape) and mapping
# it in full here is correct, not a violation of the open-failure-set rule.
_KORA_ORDER_STATUS_TO_STATE: Dict[str, OrderState] = {
    "open": OrderState.OPEN,
    "partially_filled": OrderState.PARTIALLY_FILLED,
    "filled": OrderState.FILLED,
    "cancelled": OrderState.CANCELED,
    "expired": OrderState.CANCELED,
    "rejected": OrderState.FAILED,
}


class KoraSpotExchange(ExchangePyBase):
    """Spot connector for Kora's Canton-based CLOB gateway (sui-staging only, see CONTRACT.md)."""

    # NOT unused: _status_polling_loop calls _update_time_synchronizer() every cycle regardless
    # of is_trading_required, which reads self.web_utils.get_current_server_time(...) -- setting
    # this to None would make that raise AttributeError before _update_all_balances/
    # _update_order_status (the same loop's actual payload) ever ran, silently starving the REST
    # polling backup path. kora_spot_web_utils.get_current_server_time() returns local time
    # (its own docstring explains why: no request here needs server-skew correction badly enough
    # to route it through the generated client) -- that's the one hook this module's
    # build_api_factory docstring says still applies despite the generated-client bypass.
    web_utils = web_utils

    def __init__(
        self,
        kora_spot_ed25519_private_key: str,
        trading_pairs: Optional[List[str]] = None,
        trading_required: bool = True,
        balance_asset_limit: Optional[Dict[str, Dict[str, Decimal]]] = None,
        rate_limits_share_pct: Decimal = Decimal("100"),
    ):
        self._trading_pairs = trading_pairs or []
        self._trading_required = trading_required
        self._is_starting_network = False
        self._data_source_started = False
        # market (exchange symbol) -> last observed mktEpoch. Fed from orders/trades WS frames
        # and from GetOpenOrders' Order.mktEpoch field -- every place in this file that reads an
        # mktEpoch goes through _check_mkt_epoch_and_purge below.
        self._mkt_epochs: Dict[str, int] = {}

        # One KoraDataSource per connector instance. It owns the one KoraSpotAuth (login/token
        # refresh) and the one private WS connection this connector needs; both data-source
        # classes below are handed this same instance rather than each building their own
        # (CONTRACT.md's wiring).
        self._data_source = KoraDataSource(ed25519_private_key_hex=kora_spot_ed25519_private_key)

        super().__init__(balance_asset_limit, rate_limits_share_pct)

        # No `balances` channel exists on this venue -- it's refused at subscribe, never acked
        # (CONTRACT.md). _update_balances' REST poll is the only balance signal there will ever
        # be, not a backstop for a push channel real_time_balance_update would otherwise assume
        # exists. ConnectorBase.__init__ (invoked above via super().__init__) defaults this to
        # True; the assignment has to come after that call runs or it's silently overwritten.
        self.real_time_balance_update = False

    # === Required properties ===

    @property
    def name(self) -> str:
        return CONSTANTS.EXCHANGE_NAME

    @property
    def authenticator(self) -> AuthBase:
        # KoraDataSource builds and owns exactly one KoraSpotAuth -- CONTRACT.md fixes its
        # constructor to take the raw private key, not an auth object, specifically so there is
        # one source of truth for the token/expiry this connector runs on. Reaching through the
        # underscore here (rather than constructing a second KoraSpotAuth) is intentional: this
        # framework-compatibility hook and KoraDataSource's own REST/WS calls are two views onto
        # that one instance, not two independent authenticators that could each hold their own,
        # independently-expiring token.
        return self._data_source._auth

    @property
    def rate_limits_rules(self) -> List[RateLimit]:
        return CONSTANTS.RATE_LIMITS

    @property
    def domain(self) -> str:
        return CONSTANTS.DOMAIN

    @property
    def client_order_id_max_length(self) -> int:
        return 64  # PlaceOrderRequest.clientOrderId's ceiling (CONTRACT.md).

    @property
    def client_order_id_prefix(self) -> str:
        return ""

    @property
    def trading_rules_request_path(self) -> str:
        # Unused: _make_trading_rules_request is overridden below to read KoraDataSource.markets
        # directly rather than issuing an _api_get against a path (markets.yaml requires a
        # restart to change anyway -- there is nothing to poll a URL for, CLAUDE.md).
        return ""

    @property
    def trading_pairs_request_path(self) -> str:
        return ""  # See trading_rules_request_path above; same override, same reason.

    @property
    def check_network_request_path(self) -> str:
        return ""  # Unused: _make_network_check_request is overridden below.

    @property
    def trading_pairs(self) -> List[str]:
        return self._trading_pairs

    @property
    def is_cancel_request_in_exchange_synchronous(self) -> bool:
        # DELETE /trade/orders/{orderId} returns the updated Order synchronously once it lands
        # (CONTRACT.md) -- the terminal status is in the same response, no separate confirmation
        # round trip to wait for. This property is inert today regardless: cancel answers 501, so
        # _place_cancel's ApiException short-circuits _execute_order_cancel before this is ever
        # read (see _is_order_not_found_during_cancelation_error's comment for the related trap).
        return True

    @property
    def is_trading_required(self) -> bool:
        return self._trading_required

    def supported_order_types(self) -> List[OrderType]:
        # No LIMIT_MAKER: post-only on this venue is PlaceOrderRequest.postOnly, a flag on a
        # LIMIT order, not a distinct order type (CONTRACT.md). A strategy that wants maker-only
        # semantics passes post_only=True as a kwarg to buy()/sell() -- see _place_order.
        return [OrderType.LIMIT, OrderType.MARKET]

    # === Error classification ===

    def _is_request_exception_related_to_time_synchronizer(self, request_exception: Exception) -> bool:
        # No client-signed, clock-synced request scheme lives on this path. auth-server's
        # +/-5min signedAtMillis window is entirely internal to kora_spot_auth.py's login/refresh
        # calls, not something hummingbot's TimeSynchronizer/_update_time_synchronizer touches.
        return False

    def _is_order_not_found_during_status_update_error(self, status_update_exception: Exception) -> bool:
        # Only a real 404 means "not found." CancelOrder and GetOrder both currently answer 501
        # (not implemented, CONTRACT.md) -- that must never be classified as not-found, or a few
        # polls against an unimplemented endpoint would mark a perfectly live order FAILED purely
        # because the venue hasn't shipped the op yet.
        return isinstance(status_update_exception, kora_gateway_client.ApiException) and status_update_exception.status == 404

    def _is_order_not_found_during_cancelation_error(self, cancelation_exception: Exception) -> bool:
        return isinstance(cancelation_exception, kora_gateway_client.ApiException) and cancelation_exception.status == 404

    # === Network lifecycle ===

    async def _ensure_data_source_started(self) -> None:
        if not self._data_source_started:
            await self._data_source.initialize()
            self._data_source_started = True

    async def start_network(self) -> None:
        self._is_starting_network = True
        try:
            await self._ensure_data_source_started()
            await super().start_network()
            # Market-data channels (partialDepth/recentTrade) are subscribed here, once, for the
            # configured pairs -- KoraDataSource.subscribe_market() is called directly rather than
            # through KoraSpotAPIOrderBookDataSource.subscribe_to_trading_pair(), which additionally
            # registers the pair with the data source's own dynamic-add bookkeeping; that path is
            # for pairs added *after* the tracker has already started (OrderBookTracker.add_trading_pair),
            # and calling it here too on pairs the tracker's own _init_order_books() already set up
            # would double-register them. KoraDataSource._reconnect_ws replays _subscribed_channels
            # on every reconnect, so this one-time subscribe is reconnect-safe with no extra hook.
            for trading_pair in self._trading_pairs:
                try:
                    market = await self.exchange_symbol_associated_to_pair(trading_pair=trading_pair)
                    await self._data_source.subscribe_market(market)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    self.logger().exception(f"kora_spot: failed to subscribe market channels for {trading_pair}")
        finally:
            self._is_starting_network = False

    async def stop_network(self) -> None:
        await super().stop_network()
        if not self._is_starting_network and self._data_source_started:
            await self._data_source.shutdown()
            self._data_source_started = False

    async def _make_network_check_request(self) -> None:
        # check_network() runs before start_network() in NetworkIterator's own loop, so this is
        # also where KoraDataSource gets its first initialize() call (login, market load, WS
        # connect+subscribe_private) -- gating this behind a market-data call that would
        # otherwise hit `self._market_data_api is None` before initialize() ever ran would make
        # check_network() permanently answer NOT_CONNECTED and start_network() would never run.
        await self._ensure_data_source_started()
        await self._data_source.get_markets()

    def _create_web_assistants_factory(self) -> WebAssistantsFactory:
        return web_utils.build_api_factory(throttler=self._throttler, auth=self._auth)

    def _create_order_book_data_source(self) -> OrderBookTrackerDataSource:
        return KoraSpotAPIOrderBookDataSource(
            trading_pairs=self._trading_pairs,
            connector=self,
            data_source=self._data_source,
            domain=self.domain,
        )

    def _create_user_stream_data_source(self) -> UserStreamTrackerDataSource:
        return KoraSpotUserStreamDataSource(
            connector=self,
            data_source=self._data_source,
            domain=self.domain,
        )

    async def _get_last_traded_price(self, trading_pair: str) -> float:
        # Reuse the order book data source's own best-effort midpoint rather than duplicating a
        # second get_depth call here -- KoraDataSource exposes no ticker/last-trade-price method
        # (CONTRACT.md's narrow surface), so both call sites approximate the same way.
        prices = await self._orderbook_ds.get_last_traded_prices([trading_pair])
        if trading_pair not in prices:
            raise IOError(f"kora_spot: no last traded price available for {trading_pair}")
        return prices[trading_pair]

    # === Trading pairs / trading rules / fees ===
    #
    # All three read KoraDataSource.markets (populated once at initialize() time) rather than
    # issuing their own REST calls: markets.yaml is loaded once by gateway-service at its own
    # startup and changing it needs a terragrunt apply plus a restart (CLAUDE.md), so re-polling
    # it here on ExchangePyBase's 30-minute trading-rules timer would just re-parse an unchanging
    # snapshot. _ensure_data_source_started() is called defensively in both _make_*_request
    # overrides because _initialize_trading_pair_symbol_map() (which calls
    # _make_trading_pairs_request) can run before start_network() has.

    async def _make_trading_rules_request(self) -> Dict[str, "kora_gateway_client.Market"]:
        await self._ensure_data_source_started()
        return self._data_source.markets

    async def _make_trading_pairs_request(self) -> Dict[str, "kora_gateway_client.Market"]:
        await self._ensure_data_source_started()
        return self._data_source.markets

    def _initialize_trading_pair_symbols_from_exchange_info(
        self, exchange_info: Dict[str, "kora_gateway_client.Market"]
    ) -> None:
        if not exchange_info:
            # Called before initialize() has loaded markets (or a transient empty response)
            # would otherwise cache an empty map here -- trading_pair_symbol_map_ready() flips
            # True regardless of dict contents, and every symbol lookup then fails for the rest
            # of the process's life. Leave whatever map already exists and let the next refresh
            # populate it for real, per the plan doc ("still populate trading_pair_symbol_map for
            # real, it's required plumbing" -- an empty map defeats that even though the mapping
            # itself is close to identity).
            return
        mapping = bidict()
        for symbol, market in exchange_info.items():
            mapping[symbol] = combine_to_hb_trading_pair(base=market.base, quote=market.quote)
        self._set_trading_pair_symbol_map(mapping)

    async def _format_trading_rules(self, exchange_info: Dict[str, "kora_gateway_client.Market"]) -> List[TradingRule]:
        trading_rules: List[TradingRule] = []
        for symbol, market in exchange_info.items():
            try:
                trading_pair = combine_to_hb_trading_pair(base=market.base, quote=market.quote)
                trading_rules.append(
                    TradingRule(
                        trading_pair=trading_pair,
                        min_order_size=Decimal(market.min_order_base),
                        # TradingRule has one max_order_size; the venue has two order-type-specific
                        # ceilings (maxOrderQtyLimit/maxOrderQtyMarket, deliberately different --
                        # CONTRACT.md). Using the LIMIT ceiling doesn't silently wave a MARKET order
                        # through above maxOrderQtyMarket: _create_order()'s gate only ever checks
                        # min_order_size/min_notional_size against trading_rule, never
                        # max_order_size, so an oversized MARKET order still gets rejected venue-side
                        # (ABOVE_MAX_ORDER_QTY) -- this field isn't the thing standing between it and
                        # the wire either way.
                        max_order_size=Decimal(market.max_order_qty_limit),
                        min_price_increment=Decimal(market.tick_size),
                        min_base_amount_increment=Decimal(market.step_size),
                        min_notional_size=Decimal(market.min_notional_quote),
                    )
                )
            except Exception:
                self.logger().exception(f"Error parsing trading rule for market {symbol}. Skipping.")
        return trading_rules

    async def _update_trading_fees(self) -> None:
        # Real per-market maker/taker bps, read from the cached markets dict rather than a
        # separate fees endpoint -- kora_spot has none. Cached here by trading_pair (rather than
        # having _get_fee index self._data_source.markets directly by trading_pair) because
        # _get_fee is a sync method and can't do an async exchange-symbol lookup if the mapping
        # were ever not identity; this dict is built once, asynchronously, right here.
        for symbol, market in self._data_source.markets.items():
            trading_pair = combine_to_hb_trading_pair(base=market.base, quote=market.quote)
            self._trading_fees[trading_pair] = {"maker": market.maker_fee_bps, "taker": market.taker_fee_bps}

    def _get_fee(
        self,
        base_currency: str,
        quote_currency: str,
        order_type: OrderType,
        order_side: TradeType,
        amount: Decimal,
        price: Decimal = s_decimal_NaN,
        is_maker: Optional[bool] = None,
    ) -> AddedToCostTradeFee:
        is_maker = bool(is_maker) if is_maker is not None else False
        trading_pair = combine_to_hb_trading_pair(base=base_currency, quote=quote_currency)
        fee_bps = self._trading_fees.get(trading_pair)
        if fee_bps is not None:
            bps = fee_bps["maker"] if is_maker else fee_bps["taker"]
            return TradeFeeBase.new_spot_fee(
                fee_schema=self.trade_fee_schema(),
                trade_type=order_side,
                percent=Decimal(bps) / Decimal(10000),  # true bps, denominator 10000 (CLAUDE.md)
            )
        # Markets/fees not loaded yet (pre-initialize(), or an unlisted pair) -- DEFAULT_FEES
        # schema estimate, per CONTRACT.md / plan doc.
        return build_trade_fee(
            self.name,
            is_maker,
            base_currency=base_currency,
            quote_currency=quote_currency,
            order_type=order_type,
            order_side=order_side,
            amount=amount,
            price=price,
        )

    # === Balances ===

    async def _update_balances(self) -> None:
        # node-service, never gateway-service (it has none -- pulled entirely, CLAUDE.md).
        # get_balances() raise_for_status()es on a non-2xx (e.g. the 503 this endpoint answers
        # unless both the engine URL and the balance projector are configured); that propagates
        # out of this method uncaught, and ExchangePyBase._update_all_balances is the catch site
        # -- it logs and leaves the previous balances in place. Nothing here must catch it and
        # substitute zeros: "unknown" must never render as zero (CLAUDE.md's node-service notes
        # make the same point about this exact endpoint).
        balances = await self._data_source.get_balances()
        remote_asset_names = set(balances.keys())
        local_asset_names = set(self._account_balances.keys())
        for asset, entry in balances.items():
            # available -> free, directly; never derive against total (total != free + locked on
            # this venue -- CONTRACT.md / plan doc non-negotiable).
            self._account_balances[asset] = entry["total"]
            self._account_available_balances[asset] = entry["available"]
        for asset in local_asset_names - remote_asset_names:
            del self._account_balances[asset]
            del self._account_available_balances[asset]

    # === Orders: placement, cancellation, status ===

    async def _place_order(
        self,
        order_id: str,
        trading_pair: str,
        amount: Decimal,
        trade_type: TradeType,
        order_type: OrderType,
        price: Decimal,
        **kwargs: Any,
    ) -> Tuple[str, float]:
        market = await self.exchange_symbol_associated_to_pair(trading_pair=trading_pair)
        side = "BUY" if trade_type == TradeType.BUY else "SELL"
        kora_order_type = "LIMIT" if order_type == OrderType.LIMIT else "MARKET"
        post_only = bool(kwargs.get("post_only", False))

        price_str: Optional[str] = None
        quantity_str: Optional[str] = None
        quote_order_qty_str: Optional[str] = None
        if kora_order_type == "LIMIT":
            price_str, quantity_str = str(price), str(amount)
        else:
            quote_order_qty_kwarg = kwargs.get("quote_order_qty")
            if quote_order_qty_kwarg is not None:
                # Swap-screen path ("spend N quote units") -- mutually exclusive with quantity;
                # sending both gets QUANTITY_AMBIGUOUS (CONTRACT.md), so leave quantity_str unset.
                quote_order_qty_str = str(quote_order_qty_kwarg)
            else:
                quantity_str = str(amount)

        order = await self._data_source.place_order(
            market=market,
            side=side,
            order_type=kora_order_type,
            price=price_str,
            quantity=quantity_str,
            quote_order_qty=quote_order_qty_str,
            post_only=post_only,
            client_order_id=order_id,
        )
        return order.order_id, self.current_timestamp

    async def _place_cancel(self, order_id: str, tracked_order: InFlightOrder) -> bool:
        # Calls the real endpoint and lets a 501 ApiException propagate -- CONTRACT.md and the
        # plan doc are explicit this must never become a silent no-op. The catch site is
        # ExchangePyBase._execute_order_cancel: unless _is_order_not_found_during_cancelation_error
        # matches (a real 404, never a 501 -- see that method's comment), it logs the error and
        # returns None, leaving the tracked order's state untouched. That's "an ordinary failed
        # cancel," which is exactly what today's environment state should look like from here.
        exchange_order_id = tracked_order.exchange_order_id or await tracked_order.get_exchange_order_id()
        cancelled_order = await self._data_source.cancel_order(exchange_order_id)
        # already_terminal + status="filled" means this cancel raced a fill that settled first --
        # returning True here would write a CANCELED transition over an order that already
        # completed. Checking equality against CANCELLED specifically (not "was already_terminal")
        # gets this right without a separate branch.
        return cancelled_order.status == kora_gateway_client.OrderStatus.CANCELLED

    async def _request_order_status(self, tracked_order: InFlightOrder) -> OrderUpdate:
        exchange_order_id = tracked_order.exchange_order_id or await tracked_order.get_exchange_order_id()
        market = await self.exchange_symbol_associated_to_pair(trading_pair=tracked_order.trading_pair)
        open_orders = await self._data_source.get_open_orders(market=market)
        matching = next((o for o in open_orders if o.order_id == exchange_order_id), None)

        if matching is not None:
            if await self._check_mkt_epoch_and_purge(market, matching.mkt_epoch):
                # tracked_order (and everything else on this market) was just marked FAILED by
                # the purge above -- don't immediately contradict that with this order's
                # pre-epoch-bump "still resting" verdict from the same response.
                return OrderUpdate(
                    trading_pair=tracked_order.trading_pair,
                    update_timestamp=self._time(),
                    new_state=OrderState.FAILED,
                    client_order_id=tracked_order.client_order_id,
                    exchange_order_id=exchange_order_id,
                )
            new_state = _KORA_ORDER_STATUS_TO_STATE.get(matching.status.value, OrderState.OPEN)
            return OrderUpdate(
                trading_pair=tracked_order.trading_pair,
                update_timestamp=self._time(),
                new_state=new_state,
                client_order_id=tracked_order.client_order_id,
                exchange_order_id=exchange_order_id,
            )

        # Missing from the open-orders list: GetOrder is 501 today (CONTRACT.md), so GetFills is
        # the only remaining REST signal. Ask whether this order produced a settled fill rather
        # than assuming filled -- it's just as often gone because it was cancelled, expired, or
        # busted.
        fills = await self._data_source.get_fills(order_id=exchange_order_id)
        was_filled = any(f.settlement_state == kora_gateway_client.SettlementState.SETTLED for f in fills)
        return OrderUpdate(
            trading_pair=tracked_order.trading_pair,
            update_timestamp=self._time(),
            new_state=OrderState.FILLED if was_filled else OrderState.CANCELED,
            client_order_id=tracked_order.client_order_id,
            exchange_order_id=exchange_order_id,
        )

    async def _all_trade_updates_for_order(self, order: InFlightOrder) -> List[TradeUpdate]:
        exchange_order_id = order.exchange_order_id or await order.get_exchange_order_id()
        fills = await self._data_source.get_fills(order_id=exchange_order_id)
        trade_updates: List[TradeUpdate] = []
        for fill in fills:
            # Only "settled" is a trade. Checked as an equality against SETTLED here (equivalent
            # to "!= settled" gating the continue) -- never a reverse lookup on
            # CONSTANTS.ORDER_STATE, which is keyed the other way and whose dict deliberately has
            # no "busted"/"rejected" entries (CONTRACT.md non-negotiable: the failure set is open).
            if fill.settlement_state != kora_gateway_client.SettlementState.SETTLED:
                continue
            trade_updates.append(self._trade_update_from_fill(order, fill, exchange_order_id))
        return trade_updates

    def _trade_update_from_fill(
        self, order: InFlightOrder, fill: "kora_gateway_client.Fill", exchange_order_id: str
    ) -> TradeUpdate:
        fee_asset = fill.fee_asset or (order.base_asset if order.trade_type == TradeType.BUY else order.quote_asset)
        fee_amount = Decimal(fill.fee) if fill.fee else Decimal("0")
        fee = TradeFeeBase.new_spot_fee(
            fee_schema=self.trade_fee_schema(),
            trade_type=order.trade_type,
            percent_token=fee_asset,
            flat_fees=[TokenAmount(amount=fee_amount, token=fee_asset)] if fee_amount != Decimal("0") else [],
        )
        fill_price = Decimal(fill.price)
        fill_base_amount = Decimal(fill.quantity)
        fill_quote_amount = Decimal(fill.quote_qty) if fill.quote_qty else fill_price * fill_base_amount
        return TradeUpdate(
            trade_id=fill.fill_id,
            client_order_id=order.client_order_id,
            exchange_order_id=exchange_order_id,
            trading_pair=order.trading_pair,
            fill_timestamp=fill.matched_at.timestamp(),
            fill_price=fill_price,
            fill_base_amount=fill_base_amount,
            fill_quote_amount=fill_quote_amount,
            fee=fee,
            is_taker=not fill.is_maker,
        )

    # === mktEpoch purge -- this file's responsibility specifically ===
    #
    # kora_spot_api_order_book_data_source.py and kora_spot_user_stream_data_source.py both only
    # log a mktEpoch change on the frames that carry it (CONTRACT.md: "purging locally tracked
    # orders is kora_spot_exchange.py's job"), because neither owns _order_tracker. This is the
    # one place that does, so this is the one place that corrects it.

    async def _check_mkt_epoch_and_purge(self, market: Optional[str], epoch: Optional[int]) -> bool:
        """Records `epoch` for `market`; if it differs from the previously observed value (never
        on first sight), marks every locally tracked order on that market FAILED -- the venue has
        already dropped the book and every resting order on it, so there is nothing to reconcile
        against, only local bookkeeping to correct (CONTRACT.md / plan doc). Returns whether a
        purge happened, so callers that were about to act on a now-stale snapshot can bail out
        instead of immediately contradicting it."""
        if market is None or epoch is None:
            return False
        previous = self._mkt_epochs.get(market)
        self._mkt_epochs[market] = epoch
        if previous is None or previous == epoch:
            return False

        self.logger().warning(
            "kora_spot: mktEpoch changed for market %s (%s -> %s) -- the venue has already "
            "dropped the book and every resting order on it; purging local order bookkeeping "
            "for that market instead of reconciling against a session that no longer exists.",
            market, previous, epoch,
        )
        trading_pair = await self.trading_pair_associated_to_exchange_symbol(symbol=market)
        # Snapshot before iterating: process_order_update can stop-tracking an order as a side
        # effect, and the base class treats "iterate a copy" as the safe pattern for exactly that
        # reason (_update_orders / _update_lost_orders both copy first).
        for order in list(self._order_tracker.all_updatable_orders.values()):
            if order.trading_pair == trading_pair:
                self._order_tracker.process_order_update(
                    OrderUpdate(
                        trading_pair=order.trading_pair,
                        update_timestamp=self._time(),
                        new_state=OrderState.FAILED,
                        client_order_id=order.client_order_id,
                        exchange_order_id=order.exchange_order_id,
                    )
                )
        return True

    # === User stream ===

    async def _user_stream_event_listener(self) -> None:
        async for event_message in self._iter_user_event_queue():
            try:
                event_type = event_message.get("_type")
                if event_type == "order_update":
                    await self._process_order_update(event_message)
                elif event_type == "trade_update":
                    await self._process_trade_update(event_message)
                else:
                    self.logger().debug(f"kora_spot: unrecognised user stream event type {event_type!r}")
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().exception("Unexpected error in user stream listener loop.")
                await self._sleep(5.0)

    async def _process_order_update(self, data: Dict[str, Any]) -> None:
        market = data.get("market")
        if await self._check_mkt_epoch_and_purge(market, data.get("mktEpoch")):
            return  # every resting order on this market, including whichever this frame names, is already gone

        exchange_order_id = data.get("orderId")
        tracked_order = self._order_tracker.all_updatable_orders_by_exchange_order_id.get(exchange_order_id)
        if tracked_order is None:
            return

        status = data.get("status")
        new_state = _KORA_ORDER_STATUS_TO_STATE.get(status)
        if new_state is None:
            self.logger().warning(f"kora_spot: unrecognised order status {status!r} on an orders frame for {exchange_order_id}; ignoring.")
            return

        if data.get("cancelReason") == "delegation_revoked":
            # Sweeps every resting order on every market for this party at once -- the trader's
            # own kill switch, not a venue outage. Worth a distinct log line so on-call doesn't
            # chase it as one (CONTRACT.md / plan doc).
            self.logger().warning(
                "kora_spot: delegation_revoked cancelled every resting order for this party at "
                "once; re-posting will keep failing until a new delegation is granted."
            )

        self._order_tracker.process_order_update(
            OrderUpdate(
                trading_pair=tracked_order.trading_pair,
                update_timestamp=self._time(),
                new_state=new_state,
                client_order_id=tracked_order.client_order_id,
                exchange_order_id=exchange_order_id,
            )
        )

    async def _process_trade_update(self, data: Dict[str, Any]) -> None:
        market = data.get("market")
        # An epoch bump doesn't invalidate this trade print itself, only resting-order state
        # (handled inside the purge) -- fall through to the settlement gate regardless.
        await self._check_mkt_epoch_and_purge(market, data.get("mktEpoch"))

        if data.get("settlementState") != "settled":
            return  # settling isn't final yet; busted/rejected never becomes a trade (open failure set)

        exchange_order_id = data.get("orderId")
        tracked_order = self._order_tracker.all_fillable_orders_by_exchange_order_id.get(exchange_order_id)
        if tracked_order is None:
            return

        is_maker = bool(data.get("isMaker", False))
        fee_asset = data.get("feeAsset") or (
            tracked_order.base_asset if tracked_order.trade_type == TradeType.BUY else tracked_order.quote_asset
        )
        # Fee is optional on this frame (still settling, or simply not populated). Absent
        # collapses to 0 here because TradeFeeBase has no "unknown fee" representation to use
        # instead -- GetFills.fee is the figure to reconcile against later if a frame ever ships
        # without one and the true fee wasn't actually zero.
        fee_amount = Decimal(data["fee"]) if data.get("fee") else Decimal("0")
        fee = TradeFeeBase.new_spot_fee(
            fee_schema=self.trade_fee_schema(),
            trade_type=tracked_order.trade_type,
            percent_token=fee_asset,
            flat_fees=[TokenAmount(amount=fee_amount, token=fee_asset)] if fee_amount != Decimal("0") else [],
        )
        fill_price = Decimal(data["price"])
        fill_base_amount = Decimal(data["quantity"])
        fill_quote_amount = Decimal(data["quoteQty"]) if data.get("quoteQty") else fill_price * fill_base_amount

        self._order_tracker.process_trade_update(
            TradeUpdate(
                trade_id=data.get("fillId"),
                client_order_id=tracked_order.client_order_id,
                exchange_order_id=exchange_order_id,
                trading_pair=tracked_order.trading_pair,
                fill_timestamp=self._parse_iso_timestamp(data.get("matchedAt")),
                fill_price=fill_price,
                fill_base_amount=fill_base_amount,
                fill_quote_amount=fill_quote_amount,
                fee=fee,
                is_taker=not is_maker,
            )
        )

    @staticmethod
    def _parse_iso_timestamp(value: Optional[str]) -> float:
        if not value:
            return time.time()
        try:
            return pd.Timestamp(value).timestamp()
        except (ValueError, TypeError):
            return time.time()


if __name__ == "__main__":
    # ponytail self-check: exercises the two bits of non-trivial logic that don't need a network
    # to verify -- the mktEpoch-triggered purge (does it actually mark the right orders FAILED
    # and leave others alone?) and the OrderStatus mapping table (every value in CONTRACT.md's
    # closed Order.status set resolves to something, not to a KeyError).
    for _status in ("open", "partially_filled", "filled", "cancelled", "expired", "rejected"):
        assert _status in _KORA_ORDER_STATUS_TO_STATE, f"missing OrderStatus mapping for {_status!r}"

    async def _run_self_check() -> None:
        from unittest.mock import AsyncMock, MagicMock

        exchange = object.__new__(KoraSpotExchange)  # bypass __init__: no network, no auth needed
        exchange._mkt_epochs = {}
        exchange._order_tracker = MagicMock()
        exchange._logger = None
        exchange.trading_pair_associated_to_exchange_symbol = AsyncMock(return_value="eXAU-USDCx")
        exchange._time = MagicMock(return_value=1234.0)

        # First sighting of an epoch never purges.
        purged = await exchange._check_mkt_epoch_and_purge("eXAU-USDCx", 1)
        assert purged is False
        exchange._order_tracker.process_order_update.assert_not_called()

        # Same epoch again: still no purge.
        purged = await exchange._check_mkt_epoch_and_purge("eXAU-USDCx", 1)
        assert purged is False

        # A changed epoch purges every tracked order on that market and nothing else.
        order_same_market = MagicMock(trading_pair="eXAU-USDCx", client_order_id="A", exchange_order_id="O-1")
        order_other_market = MagicMock(trading_pair="OTHER-USDCx", client_order_id="B", exchange_order_id="O-2")
        exchange._order_tracker.all_updatable_orders = {"A": order_same_market, "B": order_other_market}
        purged = await exchange._check_mkt_epoch_and_purge("eXAU-USDCx", 2)
        assert purged is True
        calls = exchange._order_tracker.process_order_update.call_args_list
        assert len(calls) == 1, f"expected exactly one purge update, got {len(calls)}"
        update = calls[0].args[0]
        assert update.client_order_id == "A"
        assert update.new_state == OrderState.FAILED

        print("kora_spot_exchange self-check passed")

    asyncio.run(_run_self_check())
