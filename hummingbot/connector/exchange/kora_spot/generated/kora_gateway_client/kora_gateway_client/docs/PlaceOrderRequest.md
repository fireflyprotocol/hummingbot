# PlaceOrderRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**market** | **str** |  | 
**side** | [**Side**](Side.md) |  | 
**type** | [**OrderType**](OrderType.md) |  | 
**time_in_force** | [**TimeInForce**](TimeInForce.md) | LIMIT only, default &#x60;GTT&#x60;. Forbidden on MARKET, which is implicitly IOC with a market take bound.  | [optional] 
**price** | **str** | Required for LIMIT, forbidden for MARKET. Must be &#x60;tickSize&#x60;-aligned. | [optional] 
**quantity** | **str** | Base units. &#x60;stepSize&#x60;-aligned and at least &#x60;minOrderBase&#x60;. Mutually exclusive with &#x60;quoteOrderQty&#x60;.  | [optional] 
**quote_order_qty** | **str** | MARKET only. Quote units — the swap-screen path, \&quot;spend 5000 USDCx\&quot;. Mutually exclusive with &#x60;quantity&#x60;. Sending both returns &#x60;QUANTITY_AMBIGUOUS&#x60;; the venue never guesses which was meant.  | [optional] 
**post_only** | **bool** | **Kept in MVP** despite TIF being reduced to GTT, because it is not a TIF — it is one comparison before insert, and the day-one makers need it. Self-trade prevention cancels the *newest* order, so an MM re-quoting across its own resting order loses the new one with no way to protect itself. It is also the mechanism a market reopen after a halt is built from.  REJECTS if the order would cross; it never slides the price.  | [optional] [default to False]
**expires_at** | **datetime** | When the order expires. **Optional** — omitted, it defaults to &#x60;defaultOrderTtlSeconds&#x60; from &#x60;/public/v1/markets&#x60; (2 minutes at launch), which is why &#x60;GTT&#x60; is usable as the everyday order type rather than something only a client tracking clocks can send.  Bounded above by the market&#39;s &#x60;maxOrderTtlSeconds&#x60;; beyond that the order is rejected rather than clamped, because silently shortening an expiry a client explicitly asked for is the failure this whole change exists to avoid.  Every resting order has one. There is no way to place an order that outlives its market&#39;s ceiling.  | [optional] 
**client_order_id** | **str** | Idempotency key. Unique per party. | [optional] 

## Example

```python
from kora_gateway_client.models.place_order_request import PlaceOrderRequest

# TODO update the JSON string below
json = "{}"
# create an instance of PlaceOrderRequest from a JSON string
place_order_request_instance = PlaceOrderRequest.from_json(json)
# print the JSON string representation of the object
print(PlaceOrderRequest.to_json())

# convert the object into a dict
place_order_request_dict = place_order_request_instance.to_dict()
# create an instance of PlaceOrderRequest from a dict
place_order_request_from_dict = PlaceOrderRequest.from_dict(place_order_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


