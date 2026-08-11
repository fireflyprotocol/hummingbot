# kora_spot connector — implementation contract

This file is the single source of truth for names/signatures across the files of this
connector. Every file below is being implemented by a separate agent working in parallel — do
**not** deviate from names specified here, even if a different name would read better, because
another agent's file references this exact name. If something needed isn't specified here,
make the smallest reasonable choice and note it in a one-line comment rather than blocking.

Reference implementation to mirror the *shape* of (not copy verbatim — it's a perpetual/derivative
connector wrapping a different exchange's SDK): `hummingbot/connector/derivative/bluefin_perpetual/`
in this same repo (branch `andrew/bluefin`, also visible via `git show andrew/bluefin:hummingbot/connector/derivative/bluefin_perpetual/<file>`). Read it before writing — it establishes the
file-per-responsibility split this connector follows (`_constants.py`, `_auth.py`, `_web_utils.py`,
`_utils.py`, the main exchange/derivative class, order-book data source, user-stream data source,
and a `data_sources/` wrapper around the underlying SDK/client).

Full design rationale lives in `/Users/andrewlawrence/.claude/plans/sketch-out-a-hummingbot-delegated-pond.md` — read it for the "why," this file is the "what."

## Generated REST clients (already generated, do not regenerate)

Two OpenAPI-generator (python, asyncio library) clients live under
`hummingbot/connector/exchange/kora_spot/generated/`:

- `generated/kora_gateway_client/kora_gateway_client/` — from gateway-service's spec. Add
  `generated/kora_gateway_client` to `sys.path` (e.g. in `data_sources/kora_data_source.py`:
  `sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "generated", "kora_gateway_client"))`),
  then `import kora_gateway_client`.
- `generated/kora_auth_client/kora_auth_client/` — from auth-server's spec. Same pattern, add
  `generated/kora_auth_client` to `sys.path`, `import kora_auth_client`.

Both are constructed the same way:
```python
config = kora_gateway_client.Configuration(host="https://spot.api.staging.kora.so")
async with kora_gateway_client.ApiClient(config) as api_client:
    trading_api = kora_gateway_client.TradingApi(api_client)
```
Bearer auth: set `config.access_token = "<jwt>"` on the `Configuration` before creating the
`ApiClient` (it auto-adds `Authorization: Bearer <token>`) — or pass `_headers={"Authorization": f"Bearer {token}"}` per-call if the token can rotate mid-`ApiClient`-lifetime (it will, every 5 minutes — prefer setting a *fresh* `Configuration.access_token` before each call, or mutate `api_client.configuration.access_token` in place, whichever `kora_data_source.py`'s author finds cleaner. Comment the choice).

### Gateway client — exact methods used by this connector

`kora_gateway_client.TradingApi`:
- `await place_order(place_order_request: PlaceOrderRequest) -> Order`
- `await cancel_order(order_id: str) -> Order` — **returns 501 today** (venue has no engine op
  behind it yet); call it for real, let the `ApiException` (status 501) propagate to the caller.
- `await cancel_all_orders() -> CancelAllOrdersResponse` — **returns 501 today**, same as above.
- `await get_order(order_id: str) -> Order` — **returns 501 today**. Do not call this from
  `_request_order_status`; it will always fail right now. Left available for when it lands.
- `await get_open_orders(market: Optional[str] = None, settlement_state: Optional[SettlementState] = None) -> GetOpenOrdersResponse` (has `.orders: List[Order]`, `.as_of_update_id: int`)
- `await get_fills(market=None, order_id=None, settlement_state=None, start_time=None, end_time=None, cursor=None, limit=None) -> GetFillsResponse` (has `.fills: List[Fill]`, `.next_cursor`)

`kora_gateway_client.MarketDataApi`:
- `await get_markets() -> GetMarketsResponse` (check actual field name via
  `kora_gateway_client.models.get_markets_response` — likely `.markets: List[Market]`)
- `await get_depth(market: str, depth: Optional[int] = None) -> DepthResponse`
- `await get_trades(market: str, ...) -> GetTradesResponse`
- `await get_ticker(market: str) -> Ticker`
- `await get_candlesticks(market: str, ...) -> GetCandlesticksResponse`

`kora_gateway_client.WebSocketApi`:
- `await create_ws_ticket() -> CreateWsTicketResponse` — **not used by this connector.** Bots
  authenticate the WS upgrade with a header directly; this exists only for browsers. Do not call
  it, do not implement a ticket flow.

`kora_gateway_client.AccountApi.get_account_events(...)` — **not used**, 501 today (planned).

Model field names on the generated Pydantic models are **snake_case** (the generator aliases
the wire's camelCase — e.g. `Order.filled_qty` serializes as `filledQty`). Use the snake_case
attribute access in Python; you don't need to touch `.model_dump(by_alias=True)` unless you're
re-serializing a model back to a request body the client itself doesn't build for you.

### Auth client — exact methods

`kora_auth_client.DefaultApi`:
- `await post_auth_token(payload_signature: str, login_request: LoginRequest, read_only: Optional[bool] = None) -> LoginResponse`
  - `payload_signature` is a **query parameter** on the generated method (confirmed against
    `auth-server/openapi.yml:40-45`, `in: query`) — the generated client handles that placement
    for you, just pass it as a normal argument.
  - `LoginRequest(account_address: str, signed_at_millis: int, audience: str)`
  - `LoginResponse.access_token`, `.access_token_valid_for_seconds` (300), `.refresh_token`, `.refresh_token_valid_for_seconds` (2592000)
- `await put_auth_token_refresh(refresh_request: RefreshRequest) -> LoginResponse`
  - `RefreshRequest(refresh_token: str)`

### Node-service balance read — hand-written, not generated

Generating a full node-service client for one endpoint is disproportionate (that spec covers
onboarding/topology/delegation too). `KoraDataSource.get_balances()` makes a plain authenticated
GET to `{NODE_SERVICE_URL}/api/v2/balance` using the same `aiohttp` session the WS layer already
needs, and parses the JSON directly: `{"partyId": str, "balances": [{"asset": str, "total": str, "available": str, "locked": str, "engineTotal": str}]}`. No codegen for this one call.

## Auth payload signing (hand-written crypto — no codegen shortcut here)

```python
import hashlib, base64, time
from nacl.signing import SigningKey  # PyNaCl — check it's already a hummingbot dependency;
                                       # if not, this is the one new dependency this connector adds

def build_login_signature(signing_key: SigningKey, account_address: str, audience: str) -> tuple[str, dict]:
    payload = {"accountAddress": account_address, "signedAtMillis": int(time.time() * 1000), "audience": audience}
    body_bytes = json.dumps(payload, separators=(",", ":")).encode()  # must match server's exact byte-for-byte body -- see below
    digest = hashlib.blake2b(body_bytes, digest_size=32).digest()
    sig = signing_key.sign(digest).signature  # 64 bytes, raw Ed25519 signature over the digest
    packed = b"\x00" + sig + bytes(signing_key.verify_key)  # [sigType(1)|sig(64)|pubkey(32)]
    return base64.urlsafe_b64encode(packed).decode(), payload
```
**Important**: the generated `post_auth_token` call takes `login_request: LoginRequest` as a
*model*, which the generated client serializes itself when building the HTTP body — so the
`body_bytes` you sign must be byte-identical to what the generated client will actually send
(same key order, same separators, no extra whitespace). The generated client uses
Pydantic's `model_dump_json(by_alias=True)`-equivalent internally; verify the exact serialization
(check `kora_auth_client/kora_auth_client/api_client.py`'s `sanitize_for_serialization` /
JSON encoding path) rather than assuming `json.dumps(..., separators=(",", ":"))` matches
exactly — if there's any risk of mismatch (key ordering, exact whitespace), build the signed
body_bytes from the *same* serialization the client will use, not a hand-rolled `json.dumps`,
or the server's signature check fails. Flag this in a comment if you can't fully verify it.

Sui address derivation (needed for `account_address` above):
```python
def derive_sui_address(public_key_bytes: bytes) -> str:
    h = hashlib.blake2b(b"\x00" + public_key_bytes, digest_size=32)
    return "0x" + h.hexdigest()[:64].lower().zfill(64)
```

## Shared symbols every file may import

From `kora_spot_constants.py` (do not redefine these elsewhere):
- `EXCHANGE_NAME = "kora_spot"`
- `DOMAIN = "sui_staging"`
- `GATEWAY_REST_URL = "https://spot.api.staging.kora.so"` (confirmed against
  `environment-stack/sui-staging/gateway-service/service/terragrunt.hcl`'s ingress block —
  `gateway.api.sui-staging.kora.so` was an earlier placeholder guess and does not route)
- `GATEWAY_WS_URL = "wss://spot.api.staging.kora.so/api/v1/ws"`
- `AUTH_REST_URL = "https://auth.api.staging.kora.so"` (per `docs/taker-guide.md`)
- `NODE_SERVICE_REST_URL = "https://node.api.staging.kora.so"`
- `JWT_AUDIENCE = "kora-staging"`
- `DEFAULT_ORDER_EXPIRY_SECONDS = 30` (configurable override point — see `kora_spot_utils.py`)
- `HEARTBEAT_TIME_INTERVAL = 30.0`
- `ORDER_STATE: Dict[str, OrderState]` keyed on `settlementState` string: `{"settled": OrderState.FILLED}`; anything else terminal maps to `OrderState.FAILED` — implement the *check* as `state != "settled"` wherever this is consulted for failure, not a reverse lookup on this dict, and say so in a comment on the dict itself so nobody adds a `"busted": OrderState.FAILED` entry and then matches on it by name elsewhere.
- `RATE_LIMITS: List[RateLimit]` — four limit ids: `PUBLIC_REST` (50/s burst 100), `PRIVATE_REST_READ` (20/s burst 40), `PRIVATE_REST_WRITE` (20/s burst 40), `WS_INBOUND` (20/s burst 40). These aren't deeply enforced anyway since the generated client bypasses hummingbot's `AsyncThrottler` (see below) — they exist for `web_utils.py`'s framework-compatibility shim and for documentation.
- `ERROR_CODES` — the full closed set from the plan's "Error codes" section, as a `frozenset[str]` or similar, used only for typed comparison / logging, not behavioral branching.
- `CANCEL_REASONS` — the full closed set from the plan's "CancelReason enum", same treatment.

From `data_sources/kora_data_source.py`, class `KoraDataSource`, the surface every other file
consumes (mirrors `BluefinDataSource`'s shape — narrow methods + event-queue getters):
```python
class KoraDataSource:
    def __init__(self, ed25519_private_key_hex: str, order_expiry_seconds: int = DEFAULT_ORDER_EXPIRY_SECONDS): ...
    async def initialize(self) -> None: ...      # logs in, starts refresh loop, loads markets
    async def shutdown(self) -> None: ...
    # REST, all return the generated-client model objects directly (callers read snake_case fields)
    async def place_order(self, market: str, side: str, order_type: str, price: Optional[str], quantity: Optional[str], quote_order_qty: Optional[str], post_only: bool, client_order_id: Optional[str]) -> "kora_gateway_client.Order": ...
    async def cancel_order(self, order_id: str) -> "kora_gateway_client.Order": ...   # propagates ApiException(status=501) today
    async def get_open_orders(self, market: Optional[str] = None) -> List["kora_gateway_client.Order"]: ...
    async def get_fills(self, market: Optional[str] = None, order_id: Optional[str] = None) -> List["kora_gateway_client.Fill"]: ...
    async def get_markets(self) -> List["kora_gateway_client.Market"]: ...
    async def get_depth(self, market: str, depth: int = 20) -> "kora_gateway_client.DepthResponse": ...
    async def get_balances(self) -> Dict[str, Dict[str, Decimal]]: ...   # {asset: {"available": ..., "locked": ...}} -- from node-service
    # WS event queues -- consumers do `await data_source.get_partial_depth_event()` etc, mirroring BluefinDataSource's get_market_order_book_event()/get_account_order_event() pattern
    async def get_partial_depth_event(self, market: str) -> dict: ...       # raw parsed JSON `data` payload of a partialDepth frame
    async def get_recent_trade_event(self, market: str) -> dict: ...
    async def get_order_update_event(self) -> dict: ...                    # raw `data` payload of an `orders` frame
    async def get_trade_update_event(self) -> dict: ...                    # raw `data` payload of a `trades` frame
    async def subscribe_market(self, market: str) -> None: ...             # subscribes partialDepth.{market}@20 + recentTrade.{market}
    async def subscribe_private(self) -> None: ...                         # subscribes orders + trades (once, party-scoped)
```
If the actual author of `kora_data_source.py` finds a genuinely better shape, it's fine to
adjust *return types*, but keep method **names** and **arguments** stable — two other files are
being written in parallel against exactly this list.

## File assignments (each written by a separate agent, in parallel)

1. `kora_spot_constants.py` + `kora_spot_utils.py` + `kora_spot_web_utils.py`
2. `kora_spot_auth.py` + `data_sources/kora_data_source.py` (+ `data_sources/__init__.py`)
3. `kora_spot_api_order_book_data_source.py`
4. `kora_spot_user_stream_data_source.py`
5. `kora_spot_exchange.py` + `hummingbot/connector/exchange/kora_spot/__init__.py` (written after 1-4 land)
6. `test/hummingbot/connector/exchange/kora_spot/*` + a `Makefile` target `generate-kora-client` that reproduces the two `openapi-generator-cli` invocations already run once by hand (document the exact commands used, see below) — written after 1-5 land.

Codegen commands already run once to produce `generated/` (for the Makefile target, and so
whoever writes it can just transcribe these):
```bash
npx --yes @openapitools/openapi-generator-cli generate \
  -i <path-to-kora-mono>/gateway-service/resources/server/openapi.yaml \
  -g python -o hummingbot/connector/exchange/kora_spot/generated/kora_gateway_client \
  --additional-properties packageName=kora_gateway_client,generateSourceCodeOnly=true,library=asyncio \
  --skip-validate-spec

npx --yes @openapitools/openapi-generator-cli generate \
  -i <path-to-kora-mono>/auth-server/openapi.yml \
  -g python -o hummingbot/connector/exchange/kora_spot/generated/kora_auth_client \
  --additional-properties packageName=kora_auth_client,generateSourceCodeOnly=true,library=asyncio \
  --skip-validate-spec
```

## Non-negotiables carried over from the plan (do not relitigate these)

- `_place_cancel` calls the real endpoint; a 501 today propagates as an ordinary failed cancel.
  Never a silent no-op returning `False`.
- Fills: only emit/settle on `settlementState == "settled"`; treat any other terminal state as
  failure via `!= "settled"`, never an enumerated `== "busted"` check.
- `partialDepth` frames are absolute snapshots — replace the local book wholesale, never merge,
  no tombstone handling needed.
- `mktEpoch` change ⇒ purge locally tracked orders for that market + force a fresh snapshot.
- Balances come from node-service, never gateway-service. `available` → free, `locked` → locked,
  directly, no arithmetic — and `total != free + locked` on this venue, don't cross-check.
- No WS ticket flow — bots set the `Authorization` header on the `/api/v1/ws` upgrade directly.
- Reconnect-before-expiry for the private WS session, not in-band re-auth (there's no ticket to
  re-auth with for a header-authenticated session).
