# ServerTime


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**server_time** | **int** | Current server time in epoch milliseconds. | 

## Example

```python
from kora_gateway_client.models.server_time import ServerTime

# TODO update the JSON string below
json = "{}"
# create an instance of ServerTime from a JSON string
server_time_instance = ServerTime.from_json(json)
# print the JSON string representation of the object
print(ServerTime.to_json())

# convert the object into a dict
server_time_dict = server_time_instance.to_dict()
# create an instance of ServerTime from a dict
server_time_from_dict = ServerTime.from_dict(server_time_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


