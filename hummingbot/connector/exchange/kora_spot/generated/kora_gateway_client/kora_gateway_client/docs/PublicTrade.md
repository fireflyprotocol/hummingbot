# PublicTrade

Over REST this is always `settled`. On the WS tape it prints at match, so `settlementState` may be `settling` and may later resolve to any terminal state.  **A print can be retracted.** Treat every terminal state that is not `settled` as a removal of a `tradeId` already shown, not as a new trade. There are two today — `busted` and `rejected` — and both are excluded from REST and from every published aggregate, so a client retracting only on `busted` keeps phantom volume and disagrees with this API permanently. Match on `settlementState != \"settled\"` rather than on a list: the set is deliberately open, so a new terminal failure mode arrives as data rather than as a client release. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**trade_id** | **str** |  | 
**price** | **str** |  | 
**quantity** | **str** |  | 
**side** | [**Side**](Side.md) | Aggressor side. | 
**at** | **datetime** |  | 
**settlement_state** | [**SettlementState**](SettlementState.md) | Always &#x60;settled&#x60; over REST. On the WS tape may be &#x60;settling&#x60;, or any terminal state — anything other than &#x60;settled&#x60; retracts the print.  | [optional] 
**mkt_epoch** | **int** |  | [optional] 
**last_update_id** | **int** |  | [optional] 

## Example

```python
from kora_gateway_client.models.public_trade import PublicTrade

# TODO update the JSON string below
json = "{}"
# create an instance of PublicTrade from a JSON string
public_trade_instance = PublicTrade.from_json(json)
# print the JSON string representation of the object
print(PublicTrade.to_json())

# convert the object into a dict
public_trade_dict = public_trade_instance.to_dict()
# create an instance of PublicTrade from a dict
public_trade_from_dict = PublicTrade.from_dict(public_trade_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


