# BalanceAsOf

Replaces a `stale` boolean. The engine builds its balance view from the transfer-event stream, so it trails the node by some amount. A boolean encodes a tolerance the client cannot see; the lag is reported so each client sets its own. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**event_offset** | **int** |  | 
**at** | **datetime** |  | 
**lag_seconds** | **float** |  | 

## Example

```python
from kora_gateway_client.models.balance_as_of import BalanceAsOf

# TODO update the JSON string below
json = "{}"
# create an instance of BalanceAsOf from a JSON string
balance_as_of_instance = BalanceAsOf.from_json(json)
# print the JSON string representation of the object
print(BalanceAsOf.to_json())

# convert the object into a dict
balance_as_of_dict = balance_as_of_instance.to_dict()
# create an instance of BalanceAsOf from a dict
balance_as_of_from_dict = BalanceAsOf.from_dict(balance_as_of_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


