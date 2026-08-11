# OrderStatus

**There is no `busted` order status.** A settlement bust is a property of a *fill*, not of an order — see `SettlementState`. When a bust kills an order, the order machine reports it as an ordinary `cancelled` with `cancelReason: settlement_bust`, and the busted quantity is NOT returned to the book. 

## Enum

* `OPEN` (value: `'open'`)

* `PARTIALLY_FILLED` (value: `'partially_filled'`)

* `FILLED` (value: `'filled'`)

* `CANCELLED` (value: `'cancelled'`)

* `EXPIRED` (value: `'expired'`)

* `REJECTED` (value: `'rejected'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


