# CancelReason

`settlement_bust` and `balance_shortfall` are venue-initiated and have no CEX analogue.  `balance_shortfall` fires when the engine applies a balance delta that leaves `reserved + settling > total` in an asset — note in-flight fills count, not just resting orders. Most often a withdrawal, which is NOT blocked at day 0. The engine cancels newest-first until the shortfall closes, so an MM that withdraws without cancelling first loses queue position on orders it did not choose to cancel. `residual_below_min_fill` is venue-initiated too and specific to a partially-filled order: what is left after a fill is smaller than the market's `minOrderBase`, so it could never trade again and is cancelled rather than left resting as an uncancellable dust order. An MM seeing quotes disappear needs to tell this from an ordinary cancel.  `delegation_revoked` is the third venue-initiated one: settlement moves funds under a standing delegation the trader grants once and can revoke unilaterally at any time. Revoking is instant and makes every resting order unsettleable, so the engine cancels them all. A trader who revokes to stop trading gets this on every open order at once — it is the intended path, not an error. 

## Enum

* `CLIENT_REQUEST` (value: `'client_request'`)

* `SETTLEMENT_BUST` (value: `'settlement_bust'`)

* `BALANCE_SHORTFALL` (value: `'balance_shortfall'`)

* `DELEGATION_REVOKED` (value: `'delegation_revoked'`)

* `SELF_TRADE_PREVENTION` (value: `'self_trade_prevention'`)

* `EXPIRED` (value: `'expired'`)

* `MARKET_HALTED` (value: `'market_halted'`)

* `RESIDUAL_BELOW_MIN_FILL` (value: `'residual_below_min_fill'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


