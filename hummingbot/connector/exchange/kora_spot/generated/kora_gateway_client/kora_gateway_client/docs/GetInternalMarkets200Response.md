# GetInternalMarkets200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**markets** | [**List[InternalMarket]**](InternalMarket.md) |  | 

## Example

```python
from kora_gateway_client.models.get_internal_markets200_response import GetInternalMarkets200Response

# TODO update the JSON string below
json = "{}"
# create an instance of GetInternalMarkets200Response from a JSON string
get_internal_markets200_response_instance = GetInternalMarkets200Response.from_json(json)
# print the JSON string representation of the object
print(GetInternalMarkets200Response.to_json())

# convert the object into a dict
get_internal_markets200_response_dict = get_internal_markets200_response_instance.to_dict()
# create an instance of GetInternalMarkets200Response from a dict
get_internal_markets200_response_from_dict = GetInternalMarkets200Response.from_dict(get_internal_markets200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


