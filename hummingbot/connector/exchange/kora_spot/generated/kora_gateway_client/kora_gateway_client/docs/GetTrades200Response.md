# GetTrades200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**market** | **str** |  | 
**trades** | [**List[PublicTrade]**](PublicTrade.md) |  | 

## Example

```python
from kora_gateway_client.models.get_trades200_response import GetTrades200Response

# TODO update the JSON string below
json = "{}"
# create an instance of GetTrades200Response from a JSON string
get_trades200_response_instance = GetTrades200Response.from_json(json)
# print the JSON string representation of the object
print(GetTrades200Response.to_json())

# convert the object into a dict
get_trades200_response_dict = get_trades200_response_instance.to_dict()
# create an instance of GetTrades200Response from a dict
get_trades200_response_from_dict = GetTrades200Response.from_dict(get_trades200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


