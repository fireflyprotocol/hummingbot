# GetExchangeStats200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**entries** | [**List[ExchangeStatsEntry]**](ExchangeStatsEntry.md) |  | 

## Example

```python
from kora_gateway_client.models.get_exchange_stats200_response import GetExchangeStats200Response

# TODO update the JSON string below
json = "{}"
# create an instance of GetExchangeStats200Response from a JSON string
get_exchange_stats200_response_instance = GetExchangeStats200Response.from_json(json)
# print the JSON string representation of the object
print(GetExchangeStats200Response.to_json())

# convert the object into a dict
get_exchange_stats200_response_dict = get_exchange_stats200_response_instance.to_dict()
# create an instance of GetExchangeStats200Response from a dict
get_exchange_stats200_response_from_dict = GetExchangeStats200Response.from_dict(get_exchange_stats200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


