# JwksResponseKeysInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**kty** | **str** |  | [optional] 
**use** | **str** |  | [optional] 
**alg** | **str** |  | [optional] 
**kid** | **str** |  | [optional] 
**n** | **str** |  | [optional] 
**e** | **str** |  | [optional] 

## Example

```python
from kora_auth_client.models.jwks_response_keys_inner import JwksResponseKeysInner

# TODO update the JSON string below
json = "{}"
# create an instance of JwksResponseKeysInner from a JSON string
jwks_response_keys_inner_instance = JwksResponseKeysInner.from_json(json)
# print the JSON string representation of the object
print(JwksResponseKeysInner.to_json())

# convert the object into a dict
jwks_response_keys_inner_dict = jwks_response_keys_inner_instance.to_dict()
# create an instance of JwksResponseKeysInner from a dict
jwks_response_keys_inner_from_dict = JwksResponseKeysInner.from_dict(jwks_response_keys_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


