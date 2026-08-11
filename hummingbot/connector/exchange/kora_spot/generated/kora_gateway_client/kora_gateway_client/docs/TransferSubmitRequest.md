# TransferSubmitRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**transfer_id** | **str** |  | 
**signature** | **str** | Hex-encoded signature over &#x60;preparedTransactionHash&#x60;. | 

## Example

```python
from kora_gateway_client.models.transfer_submit_request import TransferSubmitRequest

# TODO update the JSON string below
json = "{}"
# create an instance of TransferSubmitRequest from a JSON string
transfer_submit_request_instance = TransferSubmitRequest.from_json(json)
# print the JSON string representation of the object
print(TransferSubmitRequest.to_json())

# convert the object into a dict
transfer_submit_request_dict = transfer_submit_request_instance.to_dict()
# create an instance of TransferSubmitRequest from a dict
transfer_submit_request_from_dict = TransferSubmitRequest.from_dict(transfer_submit_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


