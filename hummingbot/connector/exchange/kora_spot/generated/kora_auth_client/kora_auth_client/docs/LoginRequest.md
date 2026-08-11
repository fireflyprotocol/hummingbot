# LoginRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**account_address** | **str** | The user&#39;s wallet address (Ed25519 public key derived address) | 
**signed_at_millis** | **int** | Unix timestamp in milliseconds at time of signing. Must be within 5 minutes of server time. | 
**audience** | **str** | JWT audience — must match server config (e.g. \&quot;kora-prod\&quot;) | 

## Example

```python
from kora_auth_client.models.login_request import LoginRequest

# TODO update the JSON string below
json = "{}"
# create an instance of LoginRequest from a JSON string
login_request_instance = LoginRequest.from_json(json)
# print the JSON string representation of the object
print(LoginRequest.to_json())

# convert the object into a dict
login_request_dict = login_request_instance.to_dict()
# create an instance of LoginRequest from a dict
login_request_from_dict = LoginRequest.from_dict(login_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


