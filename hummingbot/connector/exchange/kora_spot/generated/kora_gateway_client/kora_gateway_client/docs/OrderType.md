# OrderType

`MARKET` is accepted at the API and converted to IOC with a **market take bound** — an engine-derived limit, from a per-market slippage tolerance in the book config — before it reaches the book. An unbounded market order is never resting or matchable. The bound is a book feature, not gateway validation.  Costed pessimistically for the balance check: at the worst-case notional derivable from the book plus a slippage buffer, not at the touch. A market order that sweeps deeper than it was costed is a real overcommitment source, and the engine is the only component holding the book it would sweep. 

## Enum

* `LIMIT` (value: `'LIMIT'`)

* `MARKET` (value: `'MARKET'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


