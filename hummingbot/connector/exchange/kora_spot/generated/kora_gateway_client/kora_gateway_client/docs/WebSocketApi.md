# kora_gateway_client.WebSocketApi

All URIs are relative to *https://api.kora.so*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_ws_ticket**](WebSocketApi.md#create_ws_ticket) | **POST** /api/v1/ws/ticket | Mint a short-lived single-use WebSocket ticket.


# **create_ws_ticket**
> CreateWsTicket200Response create_ws_ticket()

Mint a short-lived single-use WebSocket ticket.

Browsers cannot set headers on a WebSocket upgrade, and the gateway has
no JWKS client, so an in-band JWT would be an unverified bearer token.
Istio validates the JWT on THIS request; the ticket is redeemed on the
socket. Single-use, redeemed atomically.

Bots may skip this and connect to `/api/v1/ws` with a normal
Authorization header on the upgrade.


### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import kora_gateway_client
from kora_gateway_client.models.create_ws_ticket200_response import CreateWsTicket200Response
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
    api_instance = kora_gateway_client.WebSocketApi(api_client)

    try:
        # Mint a short-lived single-use WebSocket ticket.
        api_response = await api_instance.create_ws_ticket()
        print("The response of WebSocketApi->create_ws_ticket:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling WebSocketApi->create_ws_ticket: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**CreateWsTicket200Response**](CreateWsTicket200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Ticket minted. |  -  |
**401** | Missing, malformed or expired token. |  -  |
**503** | The ticket store is unavailable. The request was valid and will succeed later, so a client should retry rather than treat this as a rejection.  Bots are unaffected and should not implement a fallback for this: they connect to &#x60;/api/v1/ws&#x60; with an &#x60;Authorization&#x60; header on the upgrade and never mint a ticket. Only browsers reach this endpoint, because only they cannot set a header on an upgrade.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

