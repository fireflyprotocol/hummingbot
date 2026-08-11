# TransferPrepared


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**transfer_id** | **str** |  | 
**prepared_transaction_hash** | **str** | Hex. Sign this client-side and post it to &#x60;/transfer/submit&#x60;. | 

## Example

```python
from kora_gateway_client.models.transfer_prepared import TransferPrepared

# TODO update the JSON string below
json = "{}"
# create an instance of TransferPrepared from a JSON string
transfer_prepared_instance = TransferPrepared.from_json(json)
# print the JSON string representation of the object
print(TransferPrepared.to_json())

# convert the object into a dict
transfer_prepared_dict = transfer_prepared_instance.to_dict()
# create an instance of TransferPrepared from a dict
transfer_prepared_from_dict = TransferPrepared.from_dict(transfer_prepared_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


