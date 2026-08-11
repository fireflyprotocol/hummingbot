# TransferPrepareRequest

Mirrors `node-service`'s request so the proxy stays a pass-through.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**receiver_party_id** | **str** |  | 
**amount** | **str** | Decimal string, to avoid float precision loss. | 
**token_symbol** | **str** |  | 
**description** | **str** | Optional human-readable note. | [optional] 

## Example

```python
from kora_gateway_client.models.transfer_prepare_request import TransferPrepareRequest

# TODO update the JSON string below
json = "{}"
# create an instance of TransferPrepareRequest from a JSON string
transfer_prepare_request_instance = TransferPrepareRequest.from_json(json)
# print the JSON string representation of the object
print(TransferPrepareRequest.to_json())

# convert the object into a dict
transfer_prepare_request_dict = transfer_prepare_request_instance.to_dict()
# create an instance of TransferPrepareRequest from a dict
transfer_prepare_request_from_dict = TransferPrepareRequest.from_dict(transfer_prepare_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


