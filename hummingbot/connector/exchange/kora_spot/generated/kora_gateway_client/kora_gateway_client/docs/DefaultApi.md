# kora_gateway_client.DefaultApi

All URIs are relative to *https://api.kora.so*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_server_time**](DefaultApi.md#get_server_time) | **GET** /public/v1/time | Current server time


# **get_server_time**
> ServerTime get_server_time()

Current server time

Server clock in epoch milliseconds. Lets clients measure clock drift before relying on time-sensitive fields elsewhere in the API.


### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import kora_gateway_client
from kora_gateway_client.models.server_time import ServerTime
from kora_gateway_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.kora.so
# See configuration.py for a list of all supported configuration parameters.
configuration = kora_gateway_client.Configuration(
    host = "https://api.kora.so"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = kora_gateway_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
async with kora_gateway_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = kora_gateway_client.DefaultApi(api_client)

    try:
        # Current server time
        api_response = await api_instance.get_server_time()
        print("The response of DefaultApi->get_server_time:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_server_time: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**ServerTime**](ServerTime.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Current server time. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

