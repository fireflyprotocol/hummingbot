# Balance

Invariant: `available = total - reserved - settling`.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**asset** | **str** |  | 
**total** | **str** | Held on-chain. | 
**reserved** | **str** | Committed to resting orders. Recoverable by cancelling. | 
**settling** | **str** | Committed to matched but unsettled fills — held in escrow until the settlement outcome arrives. Not recoverable by any client action. On a bust this returns to &#x60;available&#x60;, NOT to inventory.  | 
**value_usd** | **str** | &#x60;total × oracle price&#x60;. The Holdings tab&#39;s Value column, and with PnL out of MVP the only USD figure that screen shows. Requires an oracle price, which is the one dependency the balances path did not previously have.  | [optional] 
**available** | **str** | Free to place new orders against.  **Not enforced on withdrawal at day 0.** A user may withdraw funds backing resting orders; the engine reacts by cancelling those orders (&#x60;balance_shortfall&#x60;) rather than the transfer being refused. Withdrawal-layer protection is a post-launch addition.  Admission is biased toward rejection when this view is stale: a *sufficient* balance stops counting as sufficient past the staleness budget (&#x60;BALANCE_VIEW_STALE&#x60;), while an insufficient one rejects normally. Staleness can only ever produce the recoverable failure, never a fill that busts on someone else&#39;s order.  | 
**decimals** | **int** |  | 
**as_of** | [**BalanceAsOf**](BalanceAsOf.md) |  | 

## Example

```python
from kora_gateway_client.models.balance import Balance

# TODO update the JSON string below
json = "{}"
# create an instance of Balance from a JSON string
balance_instance = Balance.from_json(json)
# print the JSON string representation of the object
print(Balance.to_json())

# convert the object into a dict
balance_dict = balance_instance.to_dict()
# create an instance of Balance from a dict
balance_from_dict = Balance.from_dict(balance_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


