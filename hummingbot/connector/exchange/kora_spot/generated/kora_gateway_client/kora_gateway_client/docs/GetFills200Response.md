# GetFills200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fills** | [**List[Fill]**](Fill.md) |  | 
**next_cursor** | **str** |  | [optional] 

## Example

```python
from kora_gateway_client.models.get_fills200_response import GetFills200Response

# TODO update the JSON string below
json = "{}"
# create an instance of GetFills200Response from a JSON string
get_fills200_response_instance = GetFills200Response.from_json(json)
# print the JSON string representation of the object
print(GetFills200Response.to_json())

# convert the object into a dict
get_fills200_response_dict = get_fills200_response_instance.to_dict()
# create an instance of GetFills200Response from a dict
get_fills200_response_from_dict = GetFills200Response.from_dict(get_fills200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


