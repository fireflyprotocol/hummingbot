# ErrorCode

Machine-readable. Switch on this, never on `error`.  The first five exist because the input is valid on a perps or CEX client and must fail loudly here rather than being coerced into something that behaves differently.  `BELOW_MIN_NOTIONAL` is separate from `BELOW_MIN_ORDER_QTY`: the quantity can be perfectly valid while `price x quantity` is not, and the two have different fixes — raise the size versus raise the price. It is enforced on LIMIT orders only, because a MARKET order has no price and its notional is knowable only after the sweep.  `EXPIRY_OUT_OF_RANGE` means `expiresAt` is in the past or beyond the market's `maxOrderTtlSeconds`. Distinct from `FIELD_NOT_SUPPORTED`, which says the venue does not honour the field at all: here the field is honoured and the value is not allowed, and only the second is fixed by sending a different one. The order is rejected rather than clamped to the ceiling — see `maxOrderTtlSeconds`.  `SELF_TRADE_PREVENTED` is the synchronous counterpart of the `self_trade_prevention` cancel reason: the incoming order would have matched the sender's own resting order and was refused instead. It is not an error the sender can fix by resending — the fix is to cancel the resting side first — so it must not be collapsed into `POST_ONLY_WOULD_CROSS`, which a client retries by repricing.  `SPOT_DELEGATION_REQUIRED` is the one a frontend must special-case. Settlement moves funds under a standing per-trader delegation granted once during onboarding, and an existing RFQ user does **not** have one for spot — the RFQ delegation is a different contract. Until it exists the party cannot settle, so no order can be accepted. This is a first-run state, not a failure: the correct response is an onboarding prompt, not an error toast. It is distinct from `UNKNOWN_PARTY`, which means the engine has never seen the party at all and is an operational condition rather than something the user can resolve.  `WS_TICKET_UNAVAILABLE` is deliberately not `ENGINE_UNAVAILABLE`. The ticket store has nothing to do with the matching engine, and a code naming the wrong subsystem sends whoever reads it to the wrong dashboard — which is the entire cost of getting a machine-readable code wrong. It affects browsers only: a bot authenticates with a header on the upgrade and never mints a ticket. 

## Enum

* `SPOT_DELEGATION_REQUIRED` (value: `'SPOT_DELEGATION_REQUIRED'`)

* `TIF_NOT_SUPPORTED` (value: `'TIF_NOT_SUPPORTED'`)

* `FIELD_NOT_SUPPORTED` (value: `'FIELD_NOT_SUPPORTED'`)

* `POST_ONLY_REQUIRES_RESTING_TIF` (value: `'POST_ONLY_REQUIRES_RESTING_TIF'`)

* `QUOTE_QTY_MARKET_ONLY` (value: `'QUOTE_QTY_MARKET_ONLY'`)

* `QUANTITY_AMBIGUOUS` (value: `'QUANTITY_AMBIGUOUS'`)

* `BELOW_MIN_ORDER_QTY` (value: `'BELOW_MIN_ORDER_QTY'`)

* `ABOVE_MAX_ORDER_QTY` (value: `'ABOVE_MAX_ORDER_QTY'`)

* `BELOW_MIN_NOTIONAL` (value: `'BELOW_MIN_NOTIONAL'`)

* `EXPIRY_OUT_OF_RANGE` (value: `'EXPIRY_OUT_OF_RANGE'`)

* `INVALID_TICK_SIZE` (value: `'INVALID_TICK_SIZE'`)

* `INVALID_STEP_SIZE` (value: `'INVALID_STEP_SIZE'`)

* `UNKNOWN_MARKET` (value: `'UNKNOWN_MARKET'`)

* `MARKET_HALTED` (value: `'MARKET_HALTED'`)

* `POST_ONLY_WOULD_CROSS` (value: `'POST_ONLY_WOULD_CROSS'`)

* `SELF_TRADE_PREVENTED` (value: `'SELF_TRADE_PREVENTED'`)

* `INSUFFICIENT_AVAILABLE_BALANCE` (value: `'INSUFFICIENT_AVAILABLE_BALANCE'`)

* `BALANCE_VIEW_STALE` (value: `'BALANCE_VIEW_STALE'`)

* `UNKNOWN_PARTY` (value: `'UNKNOWN_PARTY'`)

* `DUPLICATE_CLIENT_ORDER_ID` (value: `'DUPLICATE_CLIENT_ORDER_ID'`)

* `DUPLICATE_SUBMISSION` (value: `'DUPLICATE_SUBMISSION'`)

* `ORDER_NOT_FOUND` (value: `'ORDER_NOT_FOUND'`)

* `RATE_LIMITED` (value: `'RATE_LIMITED'`)

* `ENGINE_UNAVAILABLE` (value: `'ENGINE_UNAVAILABLE'`)

* `CANTON_OVERLOADED` (value: `'CANTON_OVERLOADED'`)

* `WS_TICKET_UNAVAILABLE` (value: `'WS_TICKET_UNAVAILABLE'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


