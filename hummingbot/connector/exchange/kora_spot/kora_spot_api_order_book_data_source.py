"""
Public market-data (order book) data source for the kora_spot connector.

Consumes `KoraDataSource`'s public REST calls and WS event queues (CONTRACT.md) and adapts them
into hummingbot `OrderBookMessage`s. Mirrors the event-queue-consumption / `_parse_*_message`
split in `bluefin_perpetual_api_order_book_data_source.py`, dropping everything funding/position
related since this is a spot connector.

Three venue-specific rules drive the shape of this file (plan doc: "No diffDepth producer in
v0", the partialDepth frame shape / "replace wholesale, never merge, no tombstones" rule, and the
mktEpoch purge-and-resnapshot rule):

- There is no `diffDepth` producer in kora v0 — only `partialDepth.{market}@N`, an absolute
  snapshot on a 1s cadence. So `listen_for_order_book_diffs` is a deliberate no-op (mirrors
  bluefin_perpetual's own stub for "nothing to diff against"), and `listen_for_order_book_snapshots`
  is where partialDepth frames land, each one replacing the local book wholesale — there are no
  tombstones on this channel, so a level absent from the latest frame is just gone, never merged
  against the previous frame.
- `mktEpoch` changing for a market means the book (and every resting order on it) is gone
  venue-side. This file only reacts on the market-data side: it force-refetches a REST snapshot
  for that market rather than trying to reconcile the stale WS frame. Purging locally tracked
  orders is `kora_spot_exchange.py` / `kora_spot_user_stream_data_source.py`'s job.
- `recentTrade` fills are gated on `settlementState == "settled"`. A print starts `settling` at
  match and is never emitted for that state, so a later `busted`/`rejected` frame on the same
  `tradeId` has nothing to retract — dropping every non-`settled` frame is correct and complete.
"""
import asyncio
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import pandas as pd

from hummingbot.connector.exchange.kora_spot import kora_spot_constants as CONSTANTS
from hummingbot.core.data_type.common import TradeType
from hummingbot.core.data_type.order_book_message import OrderBookMessage, OrderBookMessageType
from hummingbot.core.data_type.order_book_tracker_data_source import OrderBookTrackerDataSource
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger

if TYPE_CHECKING:
    from hummingbot.connector.exchange.kora_spot.data_sources.kora_data_source import KoraDataSource
    from hummingbot.connector.exchange.kora_spot.kora_spot_exchange import KoraSpotExchange


def _levels_to_pairs(levels: Any) -> List[List[str]]:
    """Normalizes depth levels to `[[price, qty], ...]` of strings. Handles both the WS frame's
    raw `[["price","qty"], ...]` JSON and the generated REST client's model objects, whose exact
    attribute names aren't confirmed yet (data_sources/kora_data_source.py is being written in
    parallel) — falls back to `.price`/`.quantity` (or `.qty`) if a level isn't already a
    list/tuple."""
    pairs: List[List[str]] = []
    for level in levels or []:
        if isinstance(level, (list, tuple)):
            if len(level) < 2:
                continue
            price, qty = level[0], level[1]
        else:
            price = getattr(level, "price", None)
            qty = getattr(level, "quantity", getattr(level, "qty", None))
            if price is None or qty is None:
                continue
        pairs.append([str(price), str(qty)])
    return pairs


class KoraSpotAPIOrderBookDataSource(OrderBookTrackerDataSource):
    """Order book data source for kora_spot."""

    _logger: Optional[HummingbotLogger] = None

    def __init__(
        self,
        trading_pairs: List[str],
        connector: "KoraSpotExchange",
        data_source: "KoraDataSource",
        domain: str = CONSTANTS.DOMAIN,
    ):
        super().__init__(trading_pairs)
        self._connector = connector
        self._data_source = data_source
        self._domain = domain

        # market (exchange symbol) -> last observed mktEpoch. Fed by both partialDepth and
        # recentTrade frames, per the plan doc's JSON examples carrying it on both.
        self._mkt_epochs: Dict[str, int] = {}
        # Set while listen_for_order_book_snapshots is running, so a mktEpoch change observed
        # from *either* frame type (depth or trade) can push a fresh REST snapshot onto the same
        # queue the tracker is already draining, without this class owning a second queue.
        self._snapshot_output_queue: Optional["asyncio.Queue"] = None
        self._trade_output_queue: Optional["asyncio.Queue"] = None
        # trading_pair -> its per-market listener task. listen_for_order_book_snapshots/
        # listen_for_trades gather over these at startup, but a pair added later via
        # subscribe_to_trading_pair (e.g. OrderBookTracker.add_trading_pair) has no other way to
        # get a listener spun up, and a pair removed via unsubscribe_from_trading_pair has no
        # other way to get its listener stopped -- both go through these dicts instead.
        self._depth_listener_tasks: Dict[str, asyncio.Task] = {}
        self._trade_listener_tasks: Dict[str, asyncio.Task] = {}

    async def _connected_websocket_assistant(self) -> WSAssistant:
        """Dead code by design, mirroring kora_spot_user_stream_data_source.py's identical
        override: the base class's default `listen_for_subscriptions` (which would call this)
        is never reached because `listen_for_order_book_snapshots`/`listen_for_trades` are fully
        overridden below — KoraDataSource, not this class, owns the actual public WS connection
        and already subscribed via `subscribe_market()`. Without this override, the base class's
        default raises `NotImplementedError` out of `listen_for_subscriptions()` and the tracker
        retries it every second forever, logging an exception each time for no reason."""
        factory = getattr(self._connector, "_web_assistants_factory")
        return await factory.get_ws_assistant()

    async def _subscribe_channels(self, websocket_assistant: WSAssistant):
        """No-op: KoraDataSource.subscribe_market() already subscribed partialDepth/recentTrade
        for every configured trading pair during connector startup; this class never (re)issues
        that subscription itself."""
        del websocket_assistant

    async def get_last_traded_prices(
        self, trading_pairs: List[str], domain: Optional[str] = None
    ) -> Dict[str, float]:
        # Best-effort only: KoraDataSource exposes no ticker/last-trade-price call (CONTRACT.md's
        # narrow surface has get_depth but no get_ticker), so this approximates from the best
        # bid/ask midpoint. A market that fails to answer is simply omitted, not defaulted to 0.
        del domain
        prices: Dict[str, float] = {}
        for trading_pair in trading_pairs:
            try:
                market = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)
                depth = await self._data_source.get_depth(market, depth=1)
                bid = getattr(depth, "best_bid_price", None)
                ask = getattr(depth, "best_ask_price", None)
                if bid is None or ask is None:
                    continue
                prices[trading_pair] = float((Decimal(str(bid)) + Decimal(str(ask))) / 2)
            except Exception:
                # Best-effort: a market that fails to answer is omitted, not defaulted to 0.
                self.logger().debug(f"Could not derive a last traded price for {trading_pair}", exc_info=True)
        return prices

    async def _request_order_book_snapshot(self, trading_pair: str) -> Any:
        market = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)
        return await self._data_source.get_depth(market, depth=20)

    async def _order_book_snapshot(self, trading_pair: str) -> OrderBookMessage:
        snapshot = await self._request_order_book_snapshot(trading_pair)
        # GetDepth's lastUpdateId is not a diff-sync anchor here (plan doc) — it's only used to
        # order two snapshots against each other, which is exactly what update_id needs to do.
        last_update_id = getattr(snapshot, "last_update_id", None)
        update_id = int(last_update_id) if last_update_id is not None else int(self._time() * 1000)
        return OrderBookMessage(
            OrderBookMessageType.SNAPSHOT,
            {
                "trading_pair": trading_pair,
                "update_id": update_id,
                "bids": _levels_to_pairs(getattr(snapshot, "bids", [])),
                "asks": _levels_to_pairs(getattr(snapshot, "asks", [])),
            },
            timestamp=self._time(),
        )

    def _check_mkt_epoch(self, market: str, epoch: Optional[int]) -> bool:
        """Records `epoch` for `market` and returns True the first time it differs from the
        previously observed value (never on first sight). Logs the transition either way it's
        called from, since a purge is required regardless of which frame type surfaced it."""
        if epoch is None:
            return False
        previous = self._mkt_epochs.get(market)
        self._mkt_epochs[market] = epoch
        if previous is None or previous == epoch:
            return False
        self.logger().warning(
            "kora_spot: mktEpoch changed for market %s (%s -> %s) — the book and every resting"
            " order on that market are gone venue-side; forcing a fresh order book snapshot"
            " rather than reconciling the stale one.",
            market, previous, epoch,
        )
        return True

    def _force_resnapshot(self, market: str) -> None:
        if self._snapshot_output_queue is None:
            # Reachable if the depth listener's task is down/restarting while the trade listener
            # (which can also observe the epoch bump) is still up -- the warning logged just above
            # this call already asserted a resnapshot would happen, so say plainly that it didn't
            # rather than leaving that warning as the only, misleading signal.
            self.logger().warning(
                "kora_spot: cannot force a fresh order book snapshot for market %s -- the order"
                " book snapshot listener isn't running; it will resnapshot on its own restart.",
                market,
            )
            return
        asyncio.create_task(self._push_fresh_snapshot(market, self._snapshot_output_queue))

    async def _push_fresh_snapshot(self, market: str, queue: "asyncio.Queue") -> None:
        try:
            trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(symbol=market)
            queue.put_nowait(await self._order_book_snapshot(trading_pair))
        except asyncio.CancelledError:
            raise
        except Exception:
            self.logger().exception(f"Failed to force a fresh order book snapshot for market {market}")

    async def _parse_order_book_snapshot_message(self, raw_message: Dict[str, Any], message_queue: "asyncio.Queue"):
        market = raw_message.get("market")
        if market is None:
            return
        trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(symbol=market)

        if self._check_mkt_epoch(market, raw_message.get("mktEpoch")):
            # Don't trust this frame against a book that just changed epoch venue-side — refetch
            # instead of converting it, and drop this frame.
            self._force_resnapshot(market)
            return

        message_queue.put_nowait(
            OrderBookMessage(
                OrderBookMessageType.SNAPSHOT,
                {
                    "trading_pair": trading_pair,
                    # partialDepth carries no update id (no diff-sync anchor exists for it at
                    # all, per the plan doc) — receipt time orders successive full replacements
                    # against each other, which is all update_id is used for here.
                    "update_id": int(self._time() * 1000),
                    "bids": raw_message.get("bids", []),
                    "asks": raw_message.get("asks", []),
                },
                timestamp=self._time(),
            )
        )

    async def listen_for_order_book_snapshots(self, ev_loop: asyncio.AbstractEventLoop, output: "asyncio.Queue"):
        self._snapshot_output_queue = output
        self._depth_listener_tasks = {
            trading_pair: asyncio.create_task(self._listen_for_partial_depth(trading_pair, output))
            for trading_pair in self._trading_pairs
        }
        try:
            await asyncio.gather(*self._depth_listener_tasks.values())
        finally:
            self._snapshot_output_queue = None
            for task in self._depth_listener_tasks.values():
                task.cancel()
            self._depth_listener_tasks = {}

    async def _listen_for_partial_depth(self, trading_pair: str, output: "asyncio.Queue"):
        market = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)
        while True:
            try:
                event = await self._data_source.get_partial_depth_event(market)
                await self._parse_order_book_snapshot_message(raw_message=event, message_queue=output)
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().exception(f"Error processing partialDepth stream for {trading_pair}")
                await asyncio.sleep(5)

    async def listen_for_order_book_diffs(self, ev_loop: asyncio.AbstractEventLoop, output: "asyncio.Queue"):
        # Deliberate no-op: diffDepth has no producer in kora v0 (plan doc, "No diffDepth
        # producer in v0"). partialDepth's absolute snapshots are consumed in
        # listen_for_order_book_snapshots instead. Mirrors bluefin_perpetual's own stub for the
        # symmetric case (there, it's the snapshot loop that's the no-op).
        while True:
            await asyncio.sleep(3600)

    async def _parse_trade_message(self, raw_message: Dict[str, Any], message_queue: "asyncio.Queue"):
        market = raw_message.get("market")
        if market is None:
            return

        if self._check_mkt_epoch(market, raw_message.get("mktEpoch")):
            self._force_resnapshot(market)
            # Fall through: the epoch bump doesn't invalidate this trade print itself, only the
            # book/order state, which is handled above.

        # Gate on settlementState == "settled" only, never on an enumerated failure name — the
        # failure set (busted, rejected, ...) is open by design (CONTRACT.md). Nothing was ever
        # emitted for this tradeId while settling, so a busted/rejected frame here has nothing to
        # retract; silently dropping it is correct and complete, not a shortcut.
        if raw_message.get("settlementState") != "settled":
            return

        side = str(raw_message.get("side", "")).upper()
        if side not in ("BUY", "SELL"):
            self.logger().warning("kora_spot: recentTrade frame with unrecognised side %r; dropping: %s", side, raw_message)
            return
        trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(symbol=market)
        trade_type = float(TradeType.BUY.value) if side == "BUY" else float(TradeType.SELL.value)

        message_queue.put_nowait(
            OrderBookMessage(
                message_type=OrderBookMessageType.TRADE,
                content={
                    "trade_id": raw_message.get("tradeId"),
                    "trading_pair": trading_pair,
                    "trade_type": trade_type,
                    "amount": raw_message.get("quantity"),
                    "price": raw_message.get("price"),
                },
                timestamp=self._parse_trade_timestamp(raw_message),
            )
        )

    def _parse_trade_timestamp(self, raw_message: Dict[str, Any]) -> float:
        # `matchedAt` field name follows the Fill shape's naming convention (CONTRACT.md/plan
        # doc) — not directly confirmed for PublicTrade, hence the defensive fallback to receipt
        # time rather than raising on an unexpected shape.
        matched_at = raw_message.get("matchedAt")
        if matched_at:
            try:
                return pd.Timestamp(matched_at).timestamp()
            except (ValueError, TypeError):
                pass
        return self._time()

    async def listen_for_trades(self, ev_loop: asyncio.AbstractEventLoop, output: "asyncio.Queue"):
        self._trade_output_queue = output
        self._trade_listener_tasks = {
            trading_pair: asyncio.create_task(self._listen_for_recent_trades(trading_pair, output))
            for trading_pair in self._trading_pairs
        }
        try:
            await asyncio.gather(*self._trade_listener_tasks.values())
        finally:
            self._trade_output_queue = None
            for task in self._trade_listener_tasks.values():
                task.cancel()
            self._trade_listener_tasks = {}

    async def _listen_for_recent_trades(self, trading_pair: str, output: "asyncio.Queue"):
        market = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)
        while True:
            try:
                event = await self._data_source.get_recent_trade_event(market)
                await self._parse_trade_message(raw_message=event, message_queue=output)
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().exception(f"Error processing recentTrade stream for {trading_pair}")
                await asyncio.sleep(5)

    async def subscribe_to_trading_pair(self, trading_pair: str) -> bool:
        try:
            market = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)
            await self._data_source.subscribe_market(market)
            self.add_trading_pair(trading_pair)
            # listen_for_order_book_snapshots/listen_for_trades only spin up listener tasks for
            # the trading_pairs known at their own startup gather() -- a pair added afterward (e.g.
            # OrderBookTracker.add_trading_pair) needs its own task started here, or the venue can
            # push frames into KoraDataSource's queues for it forever with nothing ever consuming
            # them.
            if self._snapshot_output_queue is not None and trading_pair not in self._depth_listener_tasks:
                self._depth_listener_tasks[trading_pair] = asyncio.create_task(
                    self._listen_for_partial_depth(trading_pair, self._snapshot_output_queue)
                )
            if self._trade_output_queue is not None and trading_pair not in self._trade_listener_tasks:
                self._trade_listener_tasks[trading_pair] = asyncio.create_task(
                    self._listen_for_recent_trades(trading_pair, self._trade_output_queue)
                )
            return True
        except asyncio.CancelledError:
            raise
        except Exception:
            self.logger().exception(f"Error subscribing to {trading_pair}")
            return False

    async def unsubscribe_from_trading_pair(self, trading_pair: str) -> bool:
        # CONTRACT.md's KoraDataSource surface has no unsubscribe method: partialDepth and
        # recentTrade share one subscribe_market() call per market, and the WS protocol doc gives
        # no per-market unsubscribe for it either. Best-effort: call it if a later revision of
        # KoraDataSource adds one, otherwise just drop local bookkeeping — the subscription stays
        # live venue-side, so KoraDataSource keeps enqueueing frames for it (bounded, see
        # data_sources/kora_data_source.py's _MAX_MARKET_QUEUE_SIZE) even after the listener tasks
        # below are cancelled.
        unsubscribe = getattr(self._data_source, "unsubscribe_market", None)
        try:
            if unsubscribe is not None:
                market = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)
                await unsubscribe(market)
            self.remove_trading_pair(trading_pair)
            for task in (self._depth_listener_tasks.pop(trading_pair, None), self._trade_listener_tasks.pop(trading_pair, None)):
                if task is not None:
                    task.cancel()
            return True
        except asyncio.CancelledError:
            raise
        except Exception:
            self.logger().exception(f"Error unsubscribing from {trading_pair}")
            return False
