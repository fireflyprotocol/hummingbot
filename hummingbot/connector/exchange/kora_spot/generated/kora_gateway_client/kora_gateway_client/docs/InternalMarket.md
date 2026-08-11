# InternalMarket

A market plus the operational detail the public surface withholds. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**symbol** | **str** |  | 
**base** | **str** |  | 
**quote** | **str** |  | 
**tick_size** | **str** |  | 
**step_size** | **str** |  | 
**min_order_base** | **str** | Floored well above dust: each fill settles as its own on-chain transaction, so a fill whose notional cannot cover its own gas is value-destroying.  | 
**min_notional_quote** | **str** |  | 
**max_order_qty_limit** | **str** | Max base quantity on a LIMIT order. | 
**max_order_qty_market** | **str** | Max base quantity on a MARKET order. Deliberately separate from &#x60;maxOrderQtyLimit&#x60; and typically an order of magnitude smaller — a market order sweeps, so its cap bounds impact rather than exposure.  | 
**mtb_limit_percent** | **str** | Market take bound. A MARKET order is converted to IOC with a limit this far from the touch, and anything beyond it does not fill.  | 
**default_order_ttl_seconds** | **int** | Applied when &#x60;PlaceOrderRequest.expiresAt&#x60; is omitted. Deliberately short — 120 at launch — because the engine restarts clear the book anyway and the desks this venue targets requote well inside it. A client that wants longer asks for it explicitly, up to &#x60;maxOrderTtlSeconds&#x60;.  | 
**max_order_ttl_seconds** | **int** | Ceiling on &#x60;expiresAt&#x60;. An order beyond it is rejected, never clamped: silently shortening an expiry the client asked for is the same class of dishonesty as offering GTC on a venue that cannot honour it.  **The engine enforces this same ceiling**, from the same market config. Read it rather than assuming a value: at v0 it equals &#x60;defaultOrderTtlSeconds&#x60;, so the venue&#39;s maximum order lifetime is two minutes and there is no range to ask upward into. Publishing a larger number than the engine accepts would turn a lifetime a client is entitled to into an unexplained upstream rejection.  | 
**maker_fee_bps** | **int** | **True basis points: 1 bp &#x3D; 0.01%, denominator 10,000.** So &#x60;2&#x60; is 0.02%, and a 1.2 eXAU fill at 0.02% is &#x60;1.2 × 2 / 10000&#x60;.  Stated because the on-chain settlement layer does **not** use this scale: &#x60;RFQ/Types.daml&#x60; sets &#x60;feeDenominator &#x3D; 1_000_000&#x60; while still calling the unit \&quot;bps\&quot;, so one on-chain unit is a hundredth of a basis point. Anything carrying a fee rate from this API to a DAML choice must scale by 100 — and getting it wrong is silent, since fills still settle and conservation still holds. The API side uses the reading every client already assumes; the conversion belongs at the boundary that knows about both.  | 
**taker_fee_bps** | **int** | Same scale as &#x60;makerFeeBps&#x60; — 1 bp &#x3D; 0.01%. | 
**status** | [**MarketStatus**](MarketStatus.md) |  | 
**halt_cause** | [**HaltCause**](HaltCause.md) |  | [optional] 
**config_generation** | **int** | Bumped on every config write. A client that saw an order priced under one generation and rejected under the next can tell a rule change from a bug.  | 

## Example

```python
from kora_gateway_client.models.internal_market import InternalMarket

# TODO update the JSON string below
json = "{}"
# create an instance of InternalMarket from a JSON string
internal_market_instance = InternalMarket.from_json(json)
# print the JSON string representation of the object
print(InternalMarket.to_json())

# convert the object into a dict
internal_market_dict = internal_market_instance.to_dict()
# create an instance of InternalMarket from a dict
internal_market_from_dict = InternalMarket.from_dict(internal_market_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


