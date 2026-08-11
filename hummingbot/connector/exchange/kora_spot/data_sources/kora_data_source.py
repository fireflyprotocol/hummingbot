"""
KoraDataSource: wraps the generated gateway/auth REST clients plus a hand-rolled WebSocket
client for gateway-service's channel protocol (OpenAPI 3.0 can't express WS frames, so that half
of the surface was never going to be generated -- see CONTRACT.md and the plan doc).

Mirrors `BluefinDataSource`'s shape (narrow REST methods + event-queue getters for streaming
data), but where Bluefin's SDK owns login, refresh and the socket entirely, none of that exists
pre-built for Kora: this file *is* that SDK, for exactly the two things codegen cannot give a
client -- Ed25519 signing (kora_spot_auth.py) and the WS channel protocol (below).
"""
import asyncio
import itertools
import json
import logging
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, DefaultDict, Dict, List, Optional

import aiohttp

import hummingbot.connector.exchange.kora_spot.kora_spot_constants as CONSTANTS
from hummingbot.connector.exchange.kora_spot.kora_spot_auth import KoraSpotAuth
from hummingbot.logger import HummingbotLogger

# The two generated clients are checked-in source, not installed packages (CONTRACT.md "Generated
# REST clients") -- add each client's own top-level directory to sys.path before importing it.
# kora_auth_client is imported by kora_spot_auth.py the same way; both inserts are idempotent.
_THIS_DIR = os.path.dirname(__file__)
_GATEWAY_CLIENT_PARENT = os.path.join(_THIS_DIR, "..", "generated", "kora_gateway_client")
if _GATEWAY_CLIENT_PARENT not in sys.path:
    sys.path.insert(0, _GATEWAY_CLIENT_PARENT)

import kora_gateway_client  # noqa: E402

# Reconnect this many seconds ahead of the *current* reading of access_token_expiry. Comfortably
# inside the margin kora_spot_auth.py's own refresh loop already keeps (it refreshes at 60% of the
# token TTL), so in the common case the token has already been refreshed by the time this fires --
# this loop is reconnecting the *socket* to carry a header-authenticated session across a token
# rotation it cannot re-auth in-band for, not racing the token's real expiry.
_WS_RECONNECT_MARGIN_SECONDS = 15.0
_WS_SUBSCRIBE_ACK_TIMEOUT_SECONDS = 10.0
_WS_RECONNECT_RETRY_DELAY_SECONDS = 5.0


class KoraDataSource:
    """See CONTRACT.md's "Shared symbols" section for the exact method surface other files
    (order-book / user-stream data sources) are written against -- names and arguments here are
    load-bearing, not just this file's own style choice."""

    _logger: Optional[HummingbotLogger] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._logger is None:
            cls._logger = logging.getLogger(__name__)
        return cls._logger

    def __init__(self, ed25519_private_key_hex: str, order_expiry_seconds: int = CONSTANTS.DEFAULT_ORDER_EXPIRY_SECONDS):
        # KoraDataSource's constructor takes the raw key, not an auth object, per CONTRACT.md --
        # so it builds its own KoraSpotAuth here rather than receiving one. That's still "one
        # source of truth for token expiry" in the sense the plan doc asks for: this is the only
        # KoraSpotAuth instance in the connector, and the WS reconnect timer below reads its
        # access_token_expiry directly rather than tracking a second copy of that timing.
        self._auth = KoraSpotAuth(ed25519_private_key_hex)
        self._order_expiry_seconds = order_expiry_seconds

        self._gateway_config = kora_gateway_client.Configuration(host=CONSTANTS.GATEWAY_REST_URL)
        self._gateway_api_client: Optional[kora_gateway_client.ApiClient] = None
        self._trading_api: Optional[kora_gateway_client.TradingApi] = None
        self._market_data_api: Optional[kora_gateway_client.MarketDataApi] = None

        self._http_session: Optional[aiohttp.ClientSession] = None
        self._markets: Dict[str, kora_gateway_client.Market] = {}

        # WS state.
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._ws_read_task: Optional[asyncio.Task] = None
        self._ws_reconnect_task: Optional[asyncio.Task] = None
        self._closing = False  # suppresses the read loop's own reconnect-on-drop during shutdown
        # Serializes reconnects: the on-drop path (fire-and-forget task off the read loop) and the
        # reconnect-before-expiry loop can otherwise race each other into two concurrent
        # _reconnect_ws() calls tearing down/rebuilding the same socket.
        self._reconnect_lock = asyncio.Lock()
        self._req_ids = itertools.count(1)
        self._pending_acks: Dict[str, "asyncio.Future[Dict[str, Any]]"] = {}
        self._subscribed_channels: set = set()

        # Event queues, per CONTRACT.md's KoraDataSource surface. Depth/trade queues are
        # per-market (a caller must know the market to ask for its events, same as
        # subscribe_market(market)); orders/trades are single queues since those channels are
        # party-scoped, not market-scoped.
        self._partial_depth_queues: DefaultDict[str, "asyncio.Queue[dict]"] = defaultdict(asyncio.Queue)
        self._recent_trade_queues: DefaultDict[str, "asyncio.Queue[dict]"] = defaultdict(asyncio.Queue)
        self._order_update_queue: "asyncio.Queue[dict]" = asyncio.Queue()
        self._trade_update_queue: "asyncio.Queue[dict]" = asyncio.Queue()

    # -- lifecycle --------------------------------------------------------------------------

    async def initialize(self) -> None:
        await self._auth.start()  # logs in, starts the proactive REST-token refresh loop

        self._gateway_api_client = kora_gateway_client.ApiClient(self._gateway_config)
        self._trading_api = kora_gateway_client.TradingApi(self._gateway_api_client)
        self._market_data_api = kora_gateway_client.MarketDataApi(self._gateway_api_client)
        self._http_session = aiohttp.ClientSession()

        await self._load_markets()
        await self._connect_ws()
        await self.subscribe_private()
        self._ws_reconnect_task = asyncio.create_task(self._reconnect_before_expiry_loop())

    async def shutdown(self) -> None:
        self._closing = True
        if self._ws_reconnect_task is not None:
            self._ws_reconnect_task.cancel()
            self._ws_reconnect_task = None
        await self._close_ws()
        if self._http_session is not None:
            await self._http_session.close()
            self._http_session = None
        if self._gateway_api_client is not None:
            await self._gateway_api_client.close()
            self._gateway_api_client = None
        await self._auth.stop()

    # -- REST: trading ------------------------------------------------------------------------

    def _sync_gateway_token(self) -> None:
        # One long-lived Configuration/ApiClient per generated client rather than a fresh one per
        # call (that would drop and rebuild the underlying aiohttp connection pool every request).
        # The token rotates every ~5 minutes while calls happen far more often, so instead of a
        # fresh Configuration per call, mutate the held Configuration's access_token in place --
        # kora_gateway_client's ApiClient reads `self.configuration.access_token` fresh at call
        # time (Configuration.auth_settings(), evaluated inside call_api / update_params_for_auth),
        # so this is picked up correctly on the very next call with no reconnect needed.
        self._gateway_api_client.configuration.access_token = self._auth.access_token

    async def place_order(
        self,
        market: str,
        side: str,
        order_type: str,
        price: Optional[str],
        quantity: Optional[str],
        quote_order_qty: Optional[str],
        post_only: bool,
        client_order_id: Optional[str],
    ) -> "kora_gateway_client.Order":
        self._sync_gateway_token()
        # GTT is the only client-selectable TIF and is LIMIT-only; MARKET forbids timeInForce
        # entirely (it's implicitly IOC with an engine-derived market take bound) -- see
        # Market/PlaceOrderRequest field docs in the generated models.
        time_in_force = kora_gateway_client.TimeInForce.GTT if order_type == "LIMIT" else None
        # expiresAt is forbidden on MARKET, not merely ignored: gateway-service's
        # validateExpiry (gateway-service/internal/services/order_validation.go) rejects a
        # non-nil ExpiresAt on a MARKET order outright ("a MARKET order never rests") rather than
        # dropping it -- a MARKET order never rests, so there's nothing for an expiry to apply to.
        # Sending it unconditionally would fail every MARKET order this connector places.
        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=self._order_expiry_seconds)
            if order_type == "LIMIT"
            else None
        )
        request = kora_gateway_client.PlaceOrderRequest(
            market=market,
            side=kora_gateway_client.Side(side),
            type=kora_gateway_client.OrderType(order_type),
            time_in_force=time_in_force,
            price=price,
            quantity=quantity,
            quote_order_qty=quote_order_qty,
            post_only=post_only,
            expires_at=expires_at,
            client_order_id=client_order_id,
        )
        return await self._trading_api.place_order(request)

    async def cancel_order(self, order_id: str) -> "kora_gateway_client.Order":
        # Calls the real endpoint. It answers 501 today (no engine op yet, CONTRACT.md) -- that
        # ApiException propagates to the caller as an ordinary failed cancel, deliberately never
        # swallowed into a silent no-op here.
        self._sync_gateway_token()
        return await self._trading_api.cancel_order(order_id)

    async def get_open_orders(self, market: Optional[str] = None) -> List["kora_gateway_client.Order"]:
        self._sync_gateway_token()
        response = await self._trading_api.get_open_orders(market=market)
        return response.orders

    async def get_fills(
        self, market: Optional[str] = None, order_id: Optional[str] = None
    ) -> List["kora_gateway_client.Fill"]:
        self._sync_gateway_token()
        response = await self._trading_api.get_fills(market=market, order_id=order_id)
        return response.fills

    # -- REST: market data (public, no bearer token needed) ------------------------------------

    async def get_markets(self) -> List["kora_gateway_client.Market"]:
        response = await self._market_data_api.get_markets()
        return response.markets

    @property
    def markets(self) -> Dict[str, "kora_gateway_client.Market"]:
        """Cached symbol -> Market map from the last get_markets() call (populated at
        initialize() time). markets.yaml changes require a terragrunt apply + a restart, not a
        live push (CLAUDE.md), so a request-time consumer (e.g. trading-rule lookups) can read
        this instead of paying a network round trip for data that doesn't change mid-session."""
        return self._markets

    async def get_depth(self, market: str, depth: int = 20) -> "kora_gateway_client.GetDepth200Response":
        # CONTRACT.md's sketch calls this type "DepthResponse"; the generated model is actually
        # named GetDepth200Response (openapi-generator's operation-response naming convention) --
        # using the real name here rather than the paraphrase.
        return await self._market_data_api.get_depth(market=market, depth=depth)

    async def _load_markets(self) -> None:
        markets = await self.get_markets()
        self._markets = {market.symbol: market for market in markets}

    # -- REST: balances (node-service, hand-written -- CONTRACT.md "Node-service balance read") --

    async def get_balances(self) -> Dict[str, Dict[str, Decimal]]:
        """Balances live in node-service, never gateway-service (it has none -- pulled entirely).
        Every numeric field is returned as Decimal, never derived: `available` is free,
        `locked` is locked, directly, and `total != free + locked` on this venue -- don't cross
        check one against the others (CLAUDE.md, CONTRACT.md non-negotiables)."""
        url = f"{CONSTANTS.NODE_SERVICE_REST_URL}/api/v2/balance"
        headers = {"Authorization": f"Bearer {self._auth.access_token}"}
        async with self._http_session.get(url, headers=headers) as response:
            response.raise_for_status()
            payload = await response.json()

        balances: Dict[str, Dict[str, Decimal]] = {}
        for entry in payload.get("balances", []):
            balances[entry["asset"]] = {
                "total": Decimal(entry["total"]),
                "available": Decimal(entry["available"]),
                "locked": Decimal(entry["locked"]),
                "engine_total": Decimal(entry["engineTotal"]),
            }
        return balances

    # -- WebSocket: connection lifecycle ---------------------------------------------------

    async def _connect_ws(self) -> None:
        headers = {"Authorization": f"Bearer {self._auth.access_token}"}
        # autoping defaults to True: aiohttp answers the server's ping frames with pong
        # automatically, which is all the gateway's 10s-ping/15s-pong heartbeat needs (close code
        # 4008 on timeout) -- no manual ping/pong handling required on this side.
        self._ws = await self._http_session.ws_connect(CONSTANTS.GATEWAY_WS_URL, headers=headers)
        self._ws_read_task = asyncio.create_task(self._ws_read_loop())

    async def _close_ws(self) -> None:
        if self._ws_read_task is not None:
            self._ws_read_task.cancel()
            self._ws_read_task = None
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        self._ws = None

    async def _reconnect_ws(self) -> None:
        async with self._reconnect_lock:
            self.logger().info("kora_spot: reconnecting WS session")
            channels_to_resubscribe = list(self._subscribed_channels)
            await self._close_ws()
            await self._connect_ws()
            self._subscribed_channels.clear()
            if channels_to_resubscribe:
                await self._subscribe(channels_to_resubscribe)

    async def _guarded_reconnect(self) -> None:
        """Retries `_reconnect_ws()` until it succeeds (or this task is cancelled), rather than
        surfacing one failure and stopping. Shared by both reconnect paths below so a failure
        mid-resubscribe is never left half-wired: without this, the on-drop path's fire-and-forget
        task could raise out of a failed `_subscribe()` (ack timeout, error frame) into an
        unretrieved exception, leaving a *connected* socket subscribed to nothing -- an
        acked-then-silent failure with no retry and no signal, which is the worst failure mode
        this WS layer has (CONTRACT.md / plan doc)."""
        while True:
            try:
                await self._reconnect_ws()
                return
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().exception("kora_spot: WS reconnect failed; retrying in %ss", _WS_RECONNECT_RETRY_DELAY_SECONDS)
                await asyncio.sleep(_WS_RECONNECT_RETRY_DELAY_SECONDS)

    async def _reconnect_before_expiry_loop(self) -> None:
        """A header-authenticated bot has no ticket to redeem in-band, so there is no way to
        re-auth an already-upgraded socket (CONTRACT.md / plan doc "WS lifecycle" -- the ticket
        based mid-session recovery path is browser-only). Reconnecting with a fresh Authorization
        header ahead of expiry, then resubscribing everything, is the substitute: the same thing
        any reconnect has to do anyway (fresh `seq`, full resnapshot), just done proactively
        instead of after the server has already closed the socket out from under us."""
        while True:
            sleep_for = max(self._auth.access_token_expiry - time.time() - _WS_RECONNECT_MARGIN_SECONDS, 1.0)
            await asyncio.sleep(sleep_for)
            await self._guarded_reconnect()

    async def _ws_read_loop(self) -> None:
        ws = self._ws
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    self._handle_ws_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.logger().warning("kora_spot: WS error frame: %s", ws.exception())
                    break
        except asyncio.CancelledError:
            # Intentional close (see _close_ws): the read loop is being torn down on purpose,
            # nothing left to do -- do NOT fall through to the reconnect-on-drop path below.
            return
        except Exception:
            self.logger().exception("kora_spot: WS read loop crashed")

        if not self._closing:
            self.logger().warning("kora_spot: WS connection dropped unexpectedly; reconnecting")
            asyncio.create_task(self._guarded_reconnect())

    # -- WebSocket: subscribe protocol -------------------------------------------------------

    async def subscribe_market(self, market: str) -> None:
        """Subscribes partialDepth.{market}@20 + recentTrade.{market}, per CONTRACT.md."""
        await self._subscribe([f"partialDepth.{market}@20", f"recentTrade.{market}"])

    async def subscribe_private(self) -> None:
        """Subscribes orders + trades once, party-scoped (no market suffix, no per-channel auth
        beyond the upgrade's own Authorization header)."""
        await self._subscribe(["orders", "trades"])

    async def _subscribe(self, channels: List[str]) -> None:
        req_id = str(next(self._req_ids))
        fut: "asyncio.Future[Dict[str, Any]]" = asyncio.get_event_loop().create_future()
        self._pending_acks[req_id] = fut
        try:
            await self._ws.send_str(json.dumps({"op": "subscribe", "reqId": req_id, "channels": channels}))
            # ponytail: resolves on the first frame carrying this reqId. The protocol can in
            # principle emit an ack for the channels that succeeded *and* a separate error frame
            # for others sharing one reqId (partial per-channel failure) -- every channel this
            # connector actually requests is one it already validated (a known market from
            # get_markets(), or the fixed orders/trades pair), so partial failure isn't a real
            # path here today. Upgrade to accumulating all frames for a reqId over a short window
            # if a caller ever subscribes a mix of known-good and unvalidated channels.
            result = await asyncio.wait_for(fut, timeout=_WS_SUBSCRIBE_ACK_TIMEOUT_SECONDS)
        finally:
            self._pending_acks.pop(req_id, None)

        if result.get("type") == "error":
            raise RuntimeError(f"kora_spot WS subscribe rejected: {result}")
        self._subscribed_channels.update(result.get("channels", channels))

    def _resolve_pending(self, req_id: Optional[str], msg: Dict[str, Any]) -> None:
        fut = self._pending_acks.get(req_id)
        if fut is not None and not fut.done():
            fut.set_result(msg)

    def _handle_ws_message(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            self.logger().error("kora_spot: undecodable WS frame: %s", raw)
            return

        msg_type = msg.get("type")
        if msg_type in ("ack", "error"):
            self._resolve_pending(msg.get("reqId"), msg)
            if msg_type == "error":
                self.logger().warning("kora_spot: WS error frame: %s", msg)
            return

        # Data frame envelope: {"channel": "<name>", "seq": <uint64>, "data": {...}}. mktEpoch
        # bookkeeping and settlement-state gating are the order-book/user-stream data sources'
        # job (CONTRACT.md) -- this layer only routes the raw `data` payload by channel.
        channel = msg.get("channel")
        data = msg.get("data")
        if channel is None or data is None:
            self.logger().debug("kora_spot: unrecognised WS frame shape: %s", msg)
            return
        self._route_data_frame(channel, data)

    def _route_data_frame(self, channel: str, data: Dict[str, Any]) -> None:
        if channel == "orders":
            self._order_update_queue.put_nowait(data)
        elif channel == "trades":
            self._trade_update_queue.put_nowait(data)
        elif channel.startswith("partialDepth."):
            market = channel[len("partialDepth."):].split("@", 1)[0]
            self._partial_depth_queues[market].put_nowait(data)
        elif channel.startswith("recentTrade."):
            market = channel[len("recentTrade."):]
            self._recent_trade_queues[market].put_nowait(data)
        else:
            self.logger().debug("kora_spot: unhandled WS channel %s", channel)

    # -- WebSocket: event queue getters (CONTRACT.md KoraDataSource surface) -----------------

    async def get_partial_depth_event(self, market: str) -> dict:
        return await self._partial_depth_queues[market].get()

    async def get_recent_trade_event(self, market: str) -> dict:
        return await self._recent_trade_queues[market].get()

    async def get_order_update_event(self) -> dict:
        return await self._order_update_queue.get()

    async def get_trade_update_event(self) -> dict:
        return await self._trade_update_queue.get()


if __name__ == "__main__":
    # ponytail self-check: exercises the WS frame parser/router without any network -- the one
    # piece of non-trivial logic in this file (ack/error/data-frame dispatch, channel-prefix
    # routing) that neither the generated clients nor the framework cover for us.
    async def _run_self_check() -> None:
        ds = object.__new__(KoraDataSource)  # bypass __init__ (needs a real private key + network)
        ds._pending_acks = {}
        ds._subscribed_channels = set()
        ds._partial_depth_queues = defaultdict(asyncio.Queue)
        ds._recent_trade_queues = defaultdict(asyncio.Queue)
        ds._order_update_queue = asyncio.Queue()
        ds._trade_update_queue = asyncio.Queue()

        # ack resolves a pending subscribe future.
        fut = asyncio.get_event_loop().create_future()
        ds._pending_acks["7"] = fut
        ds._handle_ws_message(json.dumps({"type": "ack", "op": "subscribe", "reqId": "7", "channels": ["orders"]}))
        assert fut.done() and fut.result()["type"] == "ack"

        # error resolves the same way (see _subscribe's ponytail note).
        fut2 = asyncio.get_event_loop().create_future()
        ds._pending_acks["8"] = fut2
        ds._handle_ws_message(
            json.dumps({"type": "error", "reqId": "8", "code": "UNKNOWN_MARKET", "message": "nope"})
        )
        assert fut2.done() and fut2.result()["code"] == "UNKNOWN_MARKET"

        # data frames route by channel prefix, private channels have no market suffix.
        ds._handle_ws_message(json.dumps({"channel": "orders", "seq": 1, "data": {"orderId": "O-1"}}))
        assert (await ds.get_order_update_event())["orderId"] == "O-1"

        ds._handle_ws_message(json.dumps({"channel": "trades", "seq": 2, "data": {"fillId": "F-1"}}))
        assert (await ds.get_trade_update_event())["fillId"] == "F-1"

        ds._handle_ws_message(
            json.dumps({"channel": "partialDepth.eXAU-USDCx@20", "seq": 3, "data": {"market": "eXAU-USDCx"}})
        )
        assert (await ds.get_partial_depth_event("eXAU-USDCx"))["market"] == "eXAU-USDCx"

        ds._handle_ws_message(
            json.dumps({"channel": "recentTrade.eXAU-USDCx", "seq": 4, "data": {"tradeId": "T-1"}})
        )
        assert (await ds.get_recent_trade_event("eXAU-USDCx"))["tradeId"] == "T-1"

        print("kora_data_source self-check passed")

    asyncio.run(_run_self_check())
