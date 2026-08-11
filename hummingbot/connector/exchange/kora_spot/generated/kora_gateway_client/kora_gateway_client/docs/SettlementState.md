# SettlementState

Per fill. `settling` means matched but not yet on-chain — it may still bust. `settled` and `busted` are both terminal.  `busted` and `rejected` are both failures and are deliberately distinct, because the venue's response to them differs. `busted` is not the trader's fault — contention exhausted, a registry outage — and leaves their other orders alone. `rejected` means the party could not fund the fill at settle time, so the engine also **cancels that party's remaining orders**: a balance that could not cover this fill will not cover the others.  A client seeing `rejected` should therefore expect cancellations it did not request, on every market. Collapsing the two would either leave known-unfundable orders resting or cancel a maker's whole book over a transient failure.  Both are excluded from the REST tape and from every published volume figure, but a client that saw the print on the WS tape needs a state that says what became of it — without one the trade simply stops being mentioned, which reads as a lost message. 

## Enum

* `SETTLING` (value: `'settling'`)

* `SETTLED` (value: `'settled'`)

* `BUSTED` (value: `'busted'`)

* `REJECTED` (value: `'rejected'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


