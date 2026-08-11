"""
User stream data source for the kora_spot connector.

Forwards raw private WS frames (`orders`, `trades`) from `KoraDataSource`'s event queues into
hummingbot's `UserStreamTracker` output queue. `KoraDataSource` owns the actual WebSocket
connection and subscription lifecycle (it calls `subscribe_private()` once during its own
`initialize()`, per CONTRACT.md) — this class does not open a second connection, it only drains
two async queues and races them, mirroring
`bluefin_perpetual_user_stream_data_source.py`'s `asyncio.wait(..., return_when=FIRST_COMPLETED)`
pattern over `BluefinDataSource`'s event getters.

Event-tagging convention (documented here for `kora_spot_exchange.py`, written after this file):
each raw `data` dict put on `output` is wrapped with a `_type` key so
`_process_user_stream_event`/`_user_stream_event_listener` can dispatch without inspecting shape:
    {"_type": "order_update", **orders_frame_data}
    {"_type": "trade_update", **trades_frame_data}

Notes for the consumer of this queue (this file only forwards, it does not act on any of these):
- `trades` fires twice per fill: `settling` at match, then `settled`/`busted`/`rejected` 13-15s
  later. Never treat a `settling` frame as a completed fill.
- `orders` frames are terminal-transition deltas, not a full `Order` — no side/type/quantity/
  createdAt. Combined with `GetOrder` being 501 today, this frame plus the open-orders REST list
  is the only signal for terminal order state.
- `cancelReason` on an `orders` frame can be venue-initiated. `delegation_revoked` in particular
  sweeps every resting order on every market at once for this party — it looks like an outage
  from inside a single strategy and isn't; the consumer should log it distinctly. Logging that
  distinction is the consumer's job, not this file's — see `kora_spot_constants.CANCEL_REASONS`.
- `mktEpoch` (present on both frame types) changing for a market means every resting order on
  that market is gone venue-side. This file only warns on the transition for visibility; purging
  locally tracked orders is `kora_spot_exchange.py`'s job (it owns `InFlightOrder` bookkeeping).
"""
import asyncio
from typing import TYPE_CHECKING, Any, Dict, Optional

from hummingbot.connector.exchange.kora_spot import kora_spot_constants as CONSTANTS
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger

if TYPE_CHECKING:
    from hummingbot.connector.exchange.kora_spot.data_sources.kora_data_source import KoraDataSource
    from hummingbot.connector.exchange.kora_spot.kora_spot_exchange import KoraSpotExchange


class KoraSpotUserStreamDataSource(UserStreamTrackerDataSource):
    """Private user-stream (orders/trades) data source for kora_spot."""

    HEARTBEAT_TIME_INTERVAL = CONSTANTS.HEARTBEAT_TIME_INTERVAL
    _logger: Optional[HummingbotLogger] = None

    def __init__(
        self,
        connector: "KoraSpotExchange",
        data_source: "KoraDataSource",
        domain: str = CONSTANTS.DOMAIN,
    ):
        super().__init__()
        self._connector = connector
        self._data_source = data_source
        self._domain = domain
        self._last_recv_time: float = 0
        # market -> last observed mktEpoch, for the log-on-change warning only (no purging here).
        self._last_mkt_epoch: Dict[str, int] = {}

    @property
    def last_recv_time(self) -> float:
        return self._last_recv_time

    async def _connected_websocket_assistant(self) -> WSAssistant:
        """Dead code by design, mirroring bluefin_perpetual_user_stream_data_source.py: the base
        class's default `listen_for_user_stream` (which would call this) is fully overridden
        below, since KoraDataSource — not this class — owns the actual private WS connection and
        already subscribed via `subscribe_private()` in its own `initialize()`. Implemented only
        to satisfy the framework surface; delegates to the connector's own WebAssistantsFactory
        rather than opening a second connection."""
        factory = getattr(self._connector, "_web_assistants_factory")
        return await factory.get_ws_assistant()

    async def _subscribe_channels(self, websocket_assistant: WSAssistant):
        """No-op: KoraDataSource.initialize() already called subscribe_private() once, and a
        party-scoped subscription is not re-issued per (re)connect from this class."""
        del websocket_assistant

    def _check_mkt_epoch(self, data: Dict[str, Any]) -> None:
        market = data.get("market")
        epoch = data.get("mktEpoch")
        if market is None or epoch is None:
            return
        previous = self._last_mkt_epoch.get(market)
        if previous is not None and epoch != previous:
            self.logger().warning(
                "mktEpoch changed for market %s (%s -> %s) — every resting order on that market"
                " is gone venue-side.",
                market, previous, epoch,
            )
        self._last_mkt_epoch[market] = epoch

    async def listen_for_user_stream(self, output: asyncio.Queue):
        """
        Race the order-update and trade-update event queues and forward whichever arrives first,
        tagged with `_type` per the module docstring's convention. Mirrors
        `BluefinPerpetualUserStreamDataSource.listen_for_user_stream`'s
        `asyncio.wait(..., return_when=FIRST_COMPLETED)` idiom.
        """
        event_getters = {
            "order_update": self._data_source.get_order_update_event,
            "trade_update": self._data_source.get_trade_update_event,
        }

        while True:
            pending_tasks = []
            try:
                pending_tasks = [asyncio.create_task(getter()) for getter in event_getters.values()]
                tags = list(event_getters.keys())
                done, pending = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)

                for task in pending:
                    task.cancel()

                event_type = None
                data = None
                for task, tag in zip(pending_tasks, tags):
                    if task in done and not task.cancelled() and task.exception() is None:
                        event_type = tag
                        data = task.result()
                        break

                if data is None:
                    continue

                self._last_recv_time = self._current_time()
                self._check_mkt_epoch(data)
                output.put_nowait({"_type": event_type, **data})

            except asyncio.CancelledError:
                for task in pending_tasks:
                    task.cancel()
                raise
            except Exception:
                self.logger().exception(
                    "Unexpected error while listening for kora_spot user stream. Retrying after 5 seconds..."
                )
                await asyncio.sleep(5.0)

    @staticmethod
    def _current_time() -> float:
        return asyncio.get_event_loop().time()
