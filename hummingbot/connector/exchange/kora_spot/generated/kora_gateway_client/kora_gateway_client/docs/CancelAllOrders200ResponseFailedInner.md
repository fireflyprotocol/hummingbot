# CancelAllOrders200ResponseFailedInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**order_id** | **str** |  | 
**reason** | **str** |  | 

## Example

```python
from kora_gateway_client.models.cancel_all_orders200_response_failed_inner import CancelAllOrders200ResponseFailedInner

# TODO update the JSON string below
json = "{}"
# create an instance of CancelAllOrders200ResponseFailedInner from a JSON string
cancel_all_orders200_response_failed_inner_instance = CancelAllOrders200ResponseFailedInner.from_json(json)
# print the JSON string representation of the object
print(CancelAllOrders200ResponseFailedInner.to_json())

# convert the object into a dict
cancel_all_orders200_response_failed_inner_dict = cancel_all_orders200_response_failed_inner_instance.to_dict()
# create an instance of CancelAllOrders200ResponseFailedInner from a dict
cancel_all_orders200_response_failed_inner_from_dict = CancelAllOrders200ResponseFailedInner.from_dict(cancel_all_orders200_response_failed_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


