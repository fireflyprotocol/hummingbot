# CancelAllOrders200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cancelled** | **List[str]** |  | 
**failed** | [**List[CancelAllOrders200ResponseFailedInner]**](CancelAllOrders200ResponseFailedInner.md) |  | 

## Example

```python
from kora_gateway_client.models.cancel_all_orders200_response import CancelAllOrders200Response

# TODO update the JSON string below
json = "{}"
# create an instance of CancelAllOrders200Response from a JSON string
cancel_all_orders200_response_instance = CancelAllOrders200Response.from_json(json)
# print the JSON string representation of the object
print(CancelAllOrders200Response.to_json())

# convert the object into a dict
cancel_all_orders200_response_dict = cancel_all_orders200_response_instance.to_dict()
# create an instance of CancelAllOrders200Response from a dict
cancel_all_orders200_response_from_dict = CancelAllOrders200Response.from_dict(cancel_all_orders200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


