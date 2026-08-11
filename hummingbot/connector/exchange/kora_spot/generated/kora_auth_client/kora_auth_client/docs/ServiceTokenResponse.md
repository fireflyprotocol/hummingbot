# ServiceTokenResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**token** | **str** | RS256 service JWT for the requested audience. Cached — TTL 15 minutes. | 

## Example

```python
from kora_auth_client.models.service_token_response import ServiceTokenResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ServiceTokenResponse from a JSON string
service_token_response_instance = ServiceTokenResponse.from_json(json)
# print the JSON string representation of the object
print(ServiceTokenResponse.to_json())

# convert the object into a dict
service_token_response_dict = service_token_response_instance.to_dict()
# create an instance of ServiceTokenResponse from a dict
service_token_response_from_dict = ServiceTokenResponse.from_dict(service_token_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


