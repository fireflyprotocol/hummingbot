from typing import Dict, List

from hummingbot.core.api_throttler.data_types import RateLimit
from hummingbot.core.data_type.in_flight_order import OrderState

EXCHANGE_NAME = "kora_spot"
DOMAIN = "sui_staging"

# Confirmed against kora-mono's environment-stack/sui-staging/*/service/terragrunt.hcl
# ingress blocks (the actual deployed hostnames, not a guess) — gateway-service's public
# ingress is "spot.api.staging.kora.so", NOT "gateway.api.sui-staging.kora.so"; the latter
# doesn't route anywhere. Re-check here if this connector ever targets another environment.
GATEWAY_REST_URL = "https://spot.api.staging.kora.so"
GATEWAY_WS_URL = "wss://spot.api.staging.kora.so/api/v1/ws"
AUTH_REST_URL = "https://auth.api.staging.kora.so"
NODE_SERVICE_REST_URL = "https://node.api.staging.kora.so"

JWT_AUDIENCE = "kora-staging"

# Client-chosen order TTL (PlaceOrderRequest.expiresAt). A short, deliberate value used as an
# approximation of active requoting until CancelOrder lands venue-side; becomes a safety net
# underneath real cancellation once it does. See kora_spot_utils.py for why this constant lives
# here rather than in the ConfigMap.
DEFAULT_ORDER_EXPIRY_SECONDS = 30

HEARTBEAT_TIME_INTERVAL = 30.0

# Keyed on Fill/Order.settlementState, not a generic status enum. Only "settled" maps here —
# every other terminal state (busted, rejected, ...) is failure, checked as `!= "settled"`
# wherever this is consulted. Do NOT add e.g. "busted": OrderState.FAILED below and then have a
# caller match on it by name — the failure set is open by design (CONTRACT.md, plan doc "Why the
# rest still isn't a straight port"); a name-based match silently stops covering new reasons the
# venue adds.
ORDER_STATE: Dict[str, OrderState] = {
    "settled": OrderState.FILLED,
}

# Rate-limit ids. Documentation/framework-compatibility only: the generated OpenAPI client
# (kora_data_source.py) issues the actual HTTP calls and bypasses hummingbot's AsyncThrottler
# entirely, so these are never enforced against real traffic today (see kora_spot_web_utils.py).
PUBLIC_REST_LIMIT_ID = "PublicRest"
PRIVATE_REST_READ_LIMIT_ID = "PrivateRestRead"
PRIVATE_REST_WRITE_LIMIT_ID = "PrivateRestWrite"
WS_INBOUND_LIMIT_ID = "WsInbound"

# RateLimit has no separate burst window, only limit/time_interval — modeled as the burst count
# over a 1s interval (the tighter of the two numbers in each pair), since that's the more
# conservative reading against `AsyncThrottler`'s API. Values from the plan doc's "Rate limits"
# section: 50/s burst 100; 20/s burst 40 (x2); 20/s burst 40.
RATE_LIMITS: List[RateLimit] = [
    RateLimit(limit_id=PUBLIC_REST_LIMIT_ID, limit=100, time_interval=1.0),
    RateLimit(limit_id=PRIVATE_REST_READ_LIMIT_ID, limit=40, time_interval=1.0),
    RateLimit(limit_id=PRIVATE_REST_WRITE_LIMIT_ID, limit=40, time_interval=1.0),
    RateLimit(limit_id=WS_INBOUND_LIMIT_ID, limit=40, time_interval=1.0),
]

# ErrorResponse.code closed set (spot_gateway_order_outcome_total{reason}). For typed
# comparison/logging context only — never branch behavior on membership beyond "is this a known
# code", per CONTRACT.md.
ERROR_CODES = frozenset({
    "SPOT_DELEGATION_REQUIRED",
    "TIF_NOT_SUPPORTED",
    "FIELD_NOT_SUPPORTED",
    "POST_ONLY_REQUIRES_RESTING_TIF",
    "QUOTE_QTY_MARKET_ONLY",
    "QUANTITY_AMBIGUOUS",
    "BELOW_MIN_ORDER_QTY",
    "ABOVE_MAX_ORDER_QTY",
    "BELOW_MIN_NOTIONAL",
    "EXPIRY_OUT_OF_RANGE",
    "INVALID_TICK_SIZE",
    "INVALID_STEP_SIZE",
    "UNKNOWN_MARKET",
    "MARKET_HALTED",
    "POST_ONLY_WOULD_CROSS",
    "SELF_TRADE_PREVENTED",
    "INSUFFICIENT_AVAILABLE_BALANCE",
    "BALANCE_VIEW_STALE",
    "UNKNOWN_PARTY",
    "DUPLICATE_CLIENT_ORDER_ID",
    "DUPLICATE_SUBMISSION",
    "ORDER_NOT_FOUND",
    "RATE_LIMITED",
    "ENGINE_UNAVAILABLE",
    "CANTON_OVERLOADED",
    "WS_TICKET_UNAVAILABLE",
})

# CancelReason closed set (order-status transitions, including venue-initiated ones). Same
# typed-comparison/logging treatment as ERROR_CODES — "delegation_revoked" additionally warrants
# a distinct warning log wherever it's handled, since it sweeps every resting order on every
# market at once and looks like an outage from inside a single strategy.
CANCEL_REASONS = frozenset({
    "client_request",
    "settlement_bust",
    "balance_shortfall",
    "delegation_revoked",
    "self_trade_prevention",
    "expired",
    "market_halted",
    "residual_below_min_fill",
})
