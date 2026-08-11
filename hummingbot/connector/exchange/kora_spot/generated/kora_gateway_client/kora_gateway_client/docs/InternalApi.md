# kora_gateway_client.InternalApi

All URIs are relative to *https://api.kora.so*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_internal_markets**](InternalApi.md#get_internal_markets) | **GET** /internal/config/markets | Market registry with operational detail.


# **get_internal_markets**
> GetInternalMarkets200Response get_internal_markets()

Market registry with operational detail.

The same markets as `/public/v1/markets`, plus `haltCause` and
`configGeneration`.

Read-only. Market definitions come from `markets.yaml`, the same file
the matching engine loads, mounted into both pods from one ConfigMap —
so a tick, fee or status change is a `terragrunt apply` and a restart,
not an API call. One file rather than a second copy behind a write
endpoint, because the engine is the component that must agree with
these numbers and a hand-synced copy is the drift the venue can least
afford.

Separate from the public endpoint rather than a query flag on it,
because the difference is who may see it: a client needs to know a
market is halted, not why. The causes name our own failure modes —
`produce_failure`, `integrity_violation`, `stale_balance_view` — and
publishing them tells the world when the venue is degraded and how.

Behind the Okta-gated internal ingress. `internal.anonymousPathsMatchers`
is a strict allowlist and Istio ALLOW rules union, so a broad
`/internal/*` entry there would defeat the JWT gate on these routes.


### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import kora_gateway_client
from kora_gateway_client.models.get_internal_markets200_response import GetInternalMarkets200Response
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
    api_instance = kora_gateway_client.InternalApi(api_client)

    try:
        # Market registry with operational detail.
        api_response = await api_instance.get_internal_markets()
        print("The response of InternalApi->get_internal_markets:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling InternalApi->get_internal_markets: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**GetInternalMarkets200Response**](GetInternalMarkets200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Markets with operational detail. |  -  |
**503** | Matching engine unreachable. Authoritative reads fail rather than serving stale state.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

