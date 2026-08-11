# GetAccountEvents200ResponseEventsInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**account_seq** | **int** |  | 
**type** | **str** |  | 
**payload** | **Dict[str, object]** |  | 
**at** | **datetime** |  | 

## Example

```python
from kora_gateway_client.models.get_account_events200_response_events_inner import GetAccountEvents200ResponseEventsInner

# TODO update the JSON string below
json = "{}"
# create an instance of GetAccountEvents200ResponseEventsInner from a JSON string
get_account_events200_response_events_inner_instance = GetAccountEvents200ResponseEventsInner.from_json(json)
# print the JSON string representation of the object
print(GetAccountEvents200ResponseEventsInner.to_json())

# convert the object into a dict
get_account_events200_response_events_inner_dict = get_account_events200_response_events_inner_instance.to_dict()
# create an instance of GetAccountEvents200ResponseEventsInner from a dict
get_account_events200_response_events_inner_from_dict = GetAccountEvents200ResponseEventsInner.from_dict(get_account_events200_response_events_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


