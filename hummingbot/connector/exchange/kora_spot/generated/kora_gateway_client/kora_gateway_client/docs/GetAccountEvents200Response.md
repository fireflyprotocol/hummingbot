# GetAccountEvents200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**events** | [**List[GetAccountEvents200ResponseEventsInner]**](GetAccountEvents200ResponseEventsInner.md) |  | 
**next_seq** | **int** |  | 
**truncated** | **bool** | Retention window exceeded; resynchronise from snapshots. | 

## Example

```python
from kora_gateway_client.models.get_account_events200_response import GetAccountEvents200Response

# TODO update the JSON string below
json = "{}"
# create an instance of GetAccountEvents200Response from a JSON string
get_account_events200_response_instance = GetAccountEvents200Response.from_json(json)
# print the JSON string representation of the object
print(GetAccountEvents200Response.to_json())

# convert the object into a dict
get_account_events200_response_dict = get_account_events200_response_instance.to_dict()
# create an instance of GetAccountEvents200Response from a dict
get_account_events200_response_from_dict = GetAccountEvents200Response.from_dict(get_account_events200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


