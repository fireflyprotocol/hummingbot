# Order

Quantities satisfy `quantity = remainingQty + filledQty + settlingQty + bustedQty + cancelledQty`.  `cancelledQty` is in that identity because `remainingQty` means *still resting* and nothing else. When an order is cancelled or expires with quantity unfilled, that quantity stops resting without having traded — so without a term of its own the identity silently fails for every terminated order, which is most of them for an active MM. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**order_id** | **str** |  | 
**already_terminal** | **bool** | Set by &#x60;DELETE /trade/orders/{orderId}&#x60; when the order was already terminal — cancelled earlier, filled, expired, or cancelled by the venue on a &#x60;settlement_bust&#x60;. The request succeeded and &#x60;status&#x60; is the order&#39;s existing state; nothing changed. Absent or false everywhere else.  | [optional] 
**client_order_id** | **str** |  | [optional] 
**market** | **str** |  | 
**side** | [**Side**](Side.md) |  | 
**type** | [**OrderType**](OrderType.md) |  | 
**time_in_force** | [**TimeInForce**](TimeInForce.md) |  | [optional] 
**post_only** | **bool** |  | [optional] 
**price** | **str** |  | [optional] 
**quantity** | **str** |  | 
**status** | [**OrderStatus**](OrderStatus.md) |  | 
**cancel_reason** | [**CancelReason**](CancelReason.md) |  | [optional] 
**remaining_qty** | **str** | Still resting on the book. Goes to zero on termination — it is a live quantity, not the unfilled remainder. For \&quot;how much never traded\&quot; on a terminated order, read &#x60;cancelledQty&#x60;.  | 
**cancelled_qty** | **str** | Quantity that stopped resting without trading — cancelled by the client, cancelled by the venue (see &#x60;cancelReason&#x60;), or expired. Zero while the order is open.  | 
**filled_qty** | **str** | **SETTLED fills only.** Does not include &#x60;settlingQty&#x60;. This is the field to drive an inventory model from; counting matched-but-unsettled quantity as owned is the classic porting bug on this venue.  | 
**settling_qty** | **str** | Matched, awaiting on-chain settlement. May still bust. | 
**busted_qty** | **str** | Matched then failed to settle. Not returned to the book. | 
**fills** | [**List[Fill]**](Fill.md) |  | [optional] 
**mkt_epoch** | **int** | Matching-engine session. **If this changes, every order you had on that market is gone** — resubscribe and re-post. Order with the pair &#x60;(mktEpoch, lastUpdateId)&#x60;; &#x60;lastUpdateId&#x60; restarts at 0 each epoch, so a decrease with an epoch increase is a normal restart, not a fault.  | [optional] 
**last_update_id** | **int** |  | [optional] 
**created_at** | **datetime** |  | 

## Example

```python
from kora_gateway_client.models.order import Order

# TODO update the JSON string below
json = "{}"
# create an instance of Order from a JSON string
order_instance = Order.from_json(json)
# print the JSON string representation of the object
print(Order.to_json())

# convert the object into a dict
order_dict = order_instance.to_dict()
# create an instance of Order from a dict
order_from_dict = Order.from_dict(order_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


