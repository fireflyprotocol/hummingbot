# HaltCause

Why a market is not trading. **Internal surface only** — a client needs to know a market is halted, not why, and these name our own failure modes.  Required whenever status is not `active`, and forbidden when it is: an active market carrying a halt cause is a state nobody can interpret.  `operator` is the gateway's own halt switch. The other three are the engine's and call for different responses: `produce_failure` means the engine cannot publish, so the book is running blind; `integrity_violation` means it detected state it cannot reconcile and should not be restarted without a look; `stale_balance_view` means it is matching against balances it no longer trusts. 

## Enum

* `OPERATOR` (value: `'operator'`)

* `PRODUCE_FAILURE` (value: `'produce_failure'`)

* `INTEGRITY_VIOLATION` (value: `'integrity_violation'`)

* `STALE_BALANCE_VIEW` (value: `'stale_balance_view'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


