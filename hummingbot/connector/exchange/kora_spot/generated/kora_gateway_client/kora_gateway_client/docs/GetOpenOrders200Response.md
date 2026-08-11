# GetOpenOrders200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**orders** | [**List[Order]**](Order.md) |  | 
**as_of_update_id** | **int** |  | 

## Example

```python
from kora_gateway_client.models.get_open_orders200_response import GetOpenOrders200Response

# TODO update the JSON string below
json = "{}"
# create an instance of GetOpenOrders200Response from a JSON string
get_open_orders200_response_instance = GetOpenOrders200Response.from_json(json)
# print the JSON string representation of the object
print(GetOpenOrders200Response.to_json())

# convert the object into a dict
get_open_orders200_response_dict = get_open_orders200_response_instance.to_dict()
# create an instance of GetOpenOrders200Response from a dict
get_open_orders200_response_from_dict = GetOpenOrders200Response.from_dict(get_open_orders200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


