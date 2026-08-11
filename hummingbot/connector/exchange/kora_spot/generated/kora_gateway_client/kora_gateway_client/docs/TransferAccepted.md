# TransferAccepted


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**transfer_id** | **str** |  | 
**status** | **str** |  | 

## Example

```python
from kora_gateway_client.models.transfer_accepted import TransferAccepted

# TODO update the JSON string below
json = "{}"
# create an instance of TransferAccepted from a JSON string
transfer_accepted_instance = TransferAccepted.from_json(json)
# print the JSON string representation of the object
print(TransferAccepted.to_json())

# convert the object into a dict
transfer_accepted_dict = transfer_accepted_instance.to_dict()
# create an instance of TransferAccepted from a dict
transfer_accepted_from_dict = TransferAccepted.from_dict(transfer_accepted_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


