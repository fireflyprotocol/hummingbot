# kora_gateway_client.TradingApi

All URIs are relative to *https://api.kora.so*

Method | HTTP request | Description
------------- | ------------- | -------------
[**cancel_all_orders**](TradingApi.md#cancel_all_orders) | **DELETE** /api/v1/trade/orders | Mass cancel. Idempotent.
[**cancel_order**](TradingApi.md#cancel_order) | **DELETE** /api/v1/trade/orders/{orderId} | Cancel one order.
[**get_fills**](TradingApi.md#get_fills) | **GET** /api/v1/trade/fills | Fill history including settlement state.
[**get_open_orders**](TradingApi.md#get_open_orders) | **GET** /api/v1/trade/orders | Open orders, read-through to the matching engine.
[**get_order**](TradingApi.md#get_order) | **GET** /api/v1/trade/orders/{orderId} | One order, read-through to the matching engine.
[**place_order**](TradingApi.md#place_order) | **POST** /api/v1/trade/orders | Place an order.


# **cancel_all_orders**
> CancelAllOrders200Response cancel_all_orders(market=market)

Mass cancel. Idempotent.

**Not available in v0 — this operation answers `501`.** The v0 matching-engine contract (protobuf-messages #354) offers only PlaceOrder, GetOpenOrders and GetBook, so the gateway has no source for this. The route, shapes and auth stay in the contract so clients can generate against the final surface; turning it on is a handler change, not a contract change. Do not build a v0 flow that depends on it.


### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import kora_gateway_client
from kora_gateway_client.models.cancel_all_orders200_response import CancelAllOrders200Response
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
    api_instance = kora_gateway_client.TradingApi(api_client)
    market = 'market_example' # str | Restrict to one market. Omit to cancel everywhere. (optional)

    try:
        # Mass cancel. Idempotent.
        api_response = await api_instance.cancel_all_orders(market=market)
        print("The response of TradingApi->cancel_all_orders:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TradingApi->cancel_all_orders: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **market** | **str**| Restrict to one market. Omit to cancel everywhere. | [optional] 

### Return type

[**CancelAllOrders200Response**](CancelAllOrders200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Cancellation outcome per order. |  -  |
**400** | Unknown &#x60;market&#x60;.  A mass cancel is a kill switch, and a kill switch that no-ops on a typo is worse than one that errors: the caller reads &#x60;cancelled: []&#x60; as \&quot;nothing was open\&quot; and believes it is flat while its orders are still resting.  |  -  |
**401** | Missing, malformed or expired token. |  -  |
**503** | Matching engine unreachable. Authoritative reads fail rather than serving stale state.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **cancel_order**
> Order cancel_order(order_id)

Cancel one order.

**Not available in v0 — this operation answers `501`.** The v0 matching-engine contract (protobuf-messages #354) offers only PlaceOrder, GetOpenOrders and GetBook, so the gateway has no source for this. The route, shapes and auth stay in the contract so clients can generate against the final surface; turning it on is a handler change, not a contract change. Do not build a v0 flow that depends on it.


### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import kora_gateway_client
from kora_gateway_client.models.order import Order
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
    api_instance = kora_gateway_client.TradingApi(api_client)
    order_id = 'order_id_example' # str | 

    try:
        # Cancel one order.
        api_response = await api_instance.cancel_order(order_id)
        print("The response of TradingApi->cancel_order:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TradingApi->cancel_order: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **order_id** | **str**|  | 

### Return type

[**Order**](Order.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Cancelled, or already terminal — see &#x60;alreadyTerminal&#x60;. Reserved balance is released on engine ack.  Idempotent by design rather than as a convenience. Busts cancel orders asynchronously, so a client and the venue race *by design*: the client cancels an order the venue already cancelled on a &#x60;settlement_bust&#x60;. Under a 409 the client cannot tell \&quot;my cancel failed\&quot; from \&quot;someone got there first\&quot;, and the only safe reaction to an error is a retry — against an order that will never come back.  |  -  |
**401** | Missing, malformed or expired token. |  -  |
**404** | Not found. |  -  |
**503** | Matching engine unreachable. Authoritative reads fail rather than serving stale state.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_fills**
> GetFills200Response get_fills(market=market, order_id=order_id, settlement_state=settlement_state, start_time=start_time, end_time=end_time, cursor=cursor, limit=limit)

Fill history including settlement state.

Filter by `settlementState` to reconcile what actually traded without
replaying the event stream.

Cursor pagination on the full fill identity —
`(matchedAt, market, marketEpoch, fillId)`. `fillId` alone is unique
only within a market and engine epoch, so a shorter key can compare two
distinct fills as equal and skip one at a page boundary.

**Not `settledAt`** — that
field is null while a fill is `settling` and is written later, so it is
neither total nor stable over a result set that spans settlement
states. A row would move as it settles, and a client paginating
concurrently would see fills twice or not at all. `matchedAt` is
stamped by the engine at match and never changes.


### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import kora_gateway_client
from kora_gateway_client.models.get_fills200_response import GetFills200Response
from kora_gateway_client.models.settlement_state import SettlementState
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
    api_instance = kora_gateway_client.TradingApi(api_client)
    market = 'market_example' # str |  (optional)
    order_id = 'order_id_example' # str | All fills for one order — the Order Details screen, which breaks an order into its individual fills with maker/taker role, fee and time.  (optional)
    settlement_state = kora_gateway_client.SettlementState() # SettlementState |  (optional)
    start_time = '2013-10-20T19:20:30+01:00' # datetime |  (optional)
    end_time = '2013-10-20T19:20:30+01:00' # datetime |  (optional)
    cursor = 'cursor_example' # str |  (optional)
    limit = 100 # int |  (optional) (default to 100)

    try:
        # Fill history including settlement state.
        api_response = await api_instance.get_fills(market=market, order_id=order_id, settlement_state=settlement_state, start_time=start_time, end_time=end_time, cursor=cursor, limit=limit)
        print("The response of TradingApi->get_fills:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TradingApi->get_fills: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **market** | **str**|  | [optional] 
 **order_id** | **str**| All fills for one order — the Order Details screen, which breaks an order into its individual fills with maker/taker role, fee and time.  | [optional] 
 **settlement_state** | [**SettlementState**](.md)|  | [optional] 
 **start_time** | **datetime**|  | [optional] 
 **end_time** | **datetime**|  | [optional] 
 **cursor** | **str**|  | [optional] 
 **limit** | **int**|  | [optional] [default to 100]

### Return type

[**GetFills200Response**](GetFills200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Fills, newest first. |  -  |
**400** | Malformed request. |  -  |
**401** | Missing, malformed or expired token. |  -  |
**503** | The fill projection is unavailable — its store is unreachable or not yet provisioned. Distinct from a 500: the request was valid and will succeed later, and a client should retry rather than treat its trading history as lost.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_open_orders**
> GetOpenOrders200Response get_open_orders(market=market, settlement_state=settlement_state)

Open orders, read-through to the matching engine.

Read-through, never a projection: serving a stale open-order list
invites an MM to act on orders that no longer exist. Returns 503 rather
than stale data.


### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import kora_gateway_client
from kora_gateway_client.models.get_open_orders200_response import GetOpenOrders200Response
from kora_gateway_client.models.settlement_state import SettlementState
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
    api_instance = kora_gateway_client.TradingApi(api_client)
    market = 'market_example' # str |  (optional)
    settlement_state = kora_gateway_client.SettlementState() # SettlementState | Return only orders having at least one fill in this settlement state. Note this endpoint returns **open** orders, so filtering on `settled` or `busted` yields only partially-filled open orders — a fully filled order is no longer open. To reconcile completed trading, use `/api/v1/trade/fills`.  (optional)

    try:
        # Open orders, read-through to the matching engine.
        api_response = await api_instance.get_open_orders(market=market, settlement_state=settlement_state)
        print("The response of TradingApi->get_open_orders:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TradingApi->get_open_orders: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **market** | **str**|  | [optional] 
 **settlement_state** | [**SettlementState**](.md)| Return only orders having at least one fill in this settlement state. Note this endpoint returns **open** orders, so filtering on &#x60;settled&#x60; or &#x60;busted&#x60; yields only partially-filled open orders — a fully filled order is no longer open. To reconcile completed trading, use &#x60;/api/v1/trade/fills&#x60;.  | [optional] 

### Return type

[**GetOpenOrders200Response**](GetOpenOrders200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Open orders. |  -  |
**400** | Unknown &#x60;market&#x60;, or a filter this build cannot honour.  &#x60;settlementState&#x60; is accepted by the schema but returns &#x60;FIELD_NOT_SUPPORTED&#x60; until the engine&#39;s order record carries per-fill settlement state. Answering it by ignoring it would return every open order to a client that asked for a subset — silently wrong in the direction that matters, since the client would read orders it filtered out as matching the filter.  |  -  |
**401** | Missing, malformed or expired token. |  -  |
**503** | Matching engine unreachable. Authoritative reads fail rather than serving stale state.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_order**
> Order get_order(order_id)

One order, read-through to the matching engine.

**Not available in v0 — this operation answers `501`.** The v0 matching-engine contract (protobuf-messages #354) offers only PlaceOrder, GetOpenOrders and GetBook, so the gateway has no source for this. The route, shapes and auth stay in the contract so clients can generate against the final surface; turning it on is a handler change, not a contract change. Do not build a v0 flow that depends on it.


### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import kora_gateway_client
from kora_gateway_client.models.order import Order
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
    api_instance = kora_gateway_client.TradingApi(api_client)
    order_id = 'order_id_example' # str | 

    try:
        # One order, read-through to the matching engine.
        api_response = await api_instance.get_order(order_id)
        print("The response of TradingApi->get_order:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TradingApi->get_order: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **order_id** | **str**|  | 

### Return type

[**Order**](Order.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | The order. |  -  |
**401** | Missing, malformed or expired token. |  -  |
**404** | Not found. |  -  |
**503** | Matching engine unreachable. Authoritative reads fail rather than serving stale state.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **place_order**
> Order place_order(place_order_request)

Place an order.

Day-0 order types only. Anything outside the set below is rejected with
a typed code rather than silently coerced — `FOK` and `reduceOnly` both
exist in the perps enum and will arrive from ported clients.

Self-trade prevention groups by **namespace fingerprint**, not party id.
Party ids are unique, but one entity runs many: a party id is
`hint::1220<fingerprint>`, and every party allocated under one namespace
shares the fingerprint. Verified in prod — all 13 active Rivershore MM
parties carry `…26c34563051238db7b42` under one KMS key. Grouping at
party level would let that MM trade against itself across its own
parties.

So `stpGroupId` is the fingerprint, parsed from the party id. No lookup,
no table, and it applies uniformly to makers and takers.

It is never accepted from the client: a client-supplied grouping key
would let an MM declare itself ungrouped and self-trade freely, or
declare itself grouped with a competitor and cancel their orders.

**The engine treats it as opaque** and never interprets it. Deriving it
gateway-side is not because the engine *could not* parse a party id —
it could — but because the engine holds no Canton concepts, and the
grouping policy stays changeable without touching the hot path.


### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import kora_gateway_client
from kora_gateway_client.models.order import Order
from kora_gateway_client.models.place_order_request import PlaceOrderRequest
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
    api_instance = kora_gateway_client.TradingApi(api_client)
    place_order_request = kora_gateway_client.PlaceOrderRequest() # PlaceOrderRequest | 

    try:
        # Place an order.
        api_response = await api_instance.place_order(place_order_request)
        print("The response of TradingApi->place_order:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TradingApi->place_order: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **place_order_request** | [**PlaceOrderRequest**](PlaceOrderRequest.md)|  | 

### Return type

[**Order**](Order.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Order accepted by the matching engine. |  -  |
**400** | Malformed request. |  -  |
**401** | Missing, malformed or expired token. |  -  |
**409** | Duplicate &#x60;clientOrderId&#x60; for this party. |  -  |
**422** | Rejected on a rule rather than a malformed body — insufficient available balance, post-only would cross, below minimum quantity.  |  -  |
**429** | Rate limit exceeded. |  -  |
**503** | Matching engine unreachable. Authoritative reads fail rather than serving stale state.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

