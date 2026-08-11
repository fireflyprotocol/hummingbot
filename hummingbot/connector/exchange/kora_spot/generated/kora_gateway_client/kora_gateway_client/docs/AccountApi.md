# kora_gateway_client.AccountApi

All URIs are relative to *https://api.kora.so*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_account_events**](AccountApi.md#get_account_events) | **GET** /api/v1/account/events | Private state-transition catch-up after a disconnect.


# **get_account_events**
> GetAccountEvents200Response get_account_events(since_seq, to_seq=to_seq, limit=limit)

Private state-transition catch-up after a disconnect.

**In scope for MVP, not implemented yet — answers `501` until its handler lands.** Committed to the contract ahead of the implementation so clients can generate against the final shape. Unlike the operations marked not-available-in-v0, this one has a source and is planned; track it before depending on it in a release.

**Use case:** a market maker whose WebSocket drops for 30s needs to know
what happened to its orders while it was away. Polling `/orders` gives
current state but not the transitions, so a fill that settled and an
order the venue cancelled with `balance_shortfall` are indistinguishable
from "gone". This endpoint replays those transitions from the last
`accountSeq` the client saw, so it can reconcile without a full resync.

Matters more here than on a CEX because two of the transitions are
venue-initiated and unprompted — `settlement_bust` and
`balance_shortfall`.

`accountSeq` is allocated from a counter shared across all parties, so a
client sees only its own subsequence and values SKIP. It is a range
bound for this query and nothing else — never gap-detect on it.


### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import kora_gateway_client
from kora_gateway_client.models.get_account_events200_response import GetAccountEvents200Response
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
    api_instance = kora_gateway_client.AccountApi(api_client)
    since_seq = 56 # int | 
    to_seq = 56 # int |  (optional)
    limit = 500 # int |  (optional) (default to 500)

    try:
        # Private state-transition catch-up after a disconnect.
        api_response = await api_instance.get_account_events(since_seq, to_seq=to_seq, limit=limit)
        print("The response of AccountApi->get_account_events:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AccountApi->get_account_events: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **since_seq** | **int**|  | 
 **to_seq** | **int**|  | [optional] 
 **limit** | **int**|  | [optional] [default to 500]

### Return type

[**GetAccountEvents200Response**](GetAccountEvents200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Events in ascending &#x60;accountSeq&#x60;. |  -  |
**400** | Malformed request. |  -  |
**401** | Missing, malformed or expired token. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

