# TimeInForce

**MVP offers `GTT` only.** Client-selectable `IOC` is post-MVP and returns `TIF_NOT_SUPPORTED` until then. A MARKET order is still an IOC internally, with a market take bound — the engine has the behaviour, clients just cannot select it.  **`GTC` is absent deliberately, and this reverses an earlier decision.** A previous revision offered GTC and nothing else. It was removed because this venue cannot honour the promise in the name: `mktEpoch` is venue-wide, so a matching-engine restart clears **every order on every market**, and restarts are expected to be routine. A TIF called *good till cancelled* on a venue that cancels everything on a deploy is a label that will be discovered to be false at the worst moment.  The alternative considered — accept `GTC` and translate it internally to a far-future `GTT` — was rejected for the same reason in a different place: it makes every order carry a hidden expiry the client never agreed to. An explicit short TTL is honest where both of those are not, and the desks this venue is for requote well inside it regardless.  `GTC` therefore returns `TIF_NOT_SUPPORTED` rather than being silently downgraded, so a ported client fails loudly instead of resting orders that quietly expire.  `FOK` is absent permanently, not deferred. It promises all-or-nothing, but a match here is not a trade: an FOK order can match in full and settle in part, producing exactly the outcome the order type forbids. Never a silent downgrade to IOC. 

## Enum

* `GTT` (value: `'GTT'`)

* `IOC` (value: `'IOC'`)

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


