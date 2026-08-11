# kora_gateway_client.MarketDataApi

All URIs are relative to *https://api.kora.so*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_candlesticks**](MarketDataApi.md#get_candlesticks) | **GET** /public/v1/exchange/candlesticks/{market} | OHLCV.
[**get_depth**](MarketDataApi.md#get_depth) | **GET** /public/v1/exchange/depth/{market} | Order book snapshot.
[**get_exchange_stats**](MarketDataApi.md#get_exchange_stats) | **GET** /public/v1/exchange/stats | Venue statistics over a time range.
[**get_exchange_stats_all_time**](MarketDataApi.md#get_exchange_stats_all_time) | **GET** /public/v1/exchange/stats/allTime | Cumulative venue statistics.
[**get_markets**](MarketDataApi.md#get_markets) | **GET** /public/v1/markets | Provisioned market registry.
[**get_ticker**](MarketDataApi.md#get_ticker) | **GET** /public/v1/exchange/ticker/{market} | 24h rollup plus best bid/ask.
[**get_tickers**](MarketDataApi.md#get_tickers) | **GET** /public/v1/exchange/tickers | Ticker for every market in one call.
[**get_trades**](MarketDataApi.md#get_trades) | **GET** /public/v1/exchange/trades/{market} | Recent public prints.


# **get_candlesticks**
> GetCandlesticks200Response get_candlesticks(market, interval, start_time=start_time, end_time=end_time)

OHLCV.

### Example


```python
import kora_gateway_client
from kora_gateway_client.models.candle_interval import CandleInterval
from kora_gateway_client.models.get_candlesticks200_response import GetCandlesticks200Response
from kora_gateway_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.kora.so
# See configuration.py for a list of all supported configuration parameters.
configuration = kora_gateway_client.Configuration(
    host = "https://api.kora.so"
)


# Enter a context with an instance of the API client
async with kora_gateway_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = kora_gateway_client.MarketDataApi(api_client)
    market = 'market_example' # str | Symbol as published by `/public/v1/markets`, e.g. `eXAU-USDCx`.
    interval = kora_gateway_client.CandleInterval() # CandleInterval | 
    start_time = '2013-10-20T19:20:30+01:00' # datetime |  (optional)
    end_time = '2013-10-20T19:20:30+01:00' # datetime |  (optional)

    try:
        # OHLCV.
        api_response = await api_instance.get_candlesticks(market, interval, start_time=start_time, end_time=end_time)
        print("The response of MarketDataApi->get_candlesticks:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MarketDataApi->get_candlesticks: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **market** | **str**| Symbol as published by &#x60;/public/v1/markets&#x60;, e.g. &#x60;eXAU-USDCx&#x60;. | 
 **interval** | [**CandleInterval**](.md)|  | 
 **start_time** | **datetime**|  | [optional] 
 **end_time** | **datetime**|  | [optional] 

### Return type

[**GetCandlesticks200Response**](GetCandlesticks200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Candles, oldest first. |  -  |
**400** | Malformed request. |  -  |
**404** | Not found. |  -  |
**503** | Matching engine unreachable. Authoritative reads fail rather than serving stale state.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_depth**
> GetDepth200Response get_depth(market, depth=depth)

Order book snapshot.

**v0: served by polling the matching engine, not from a diff stream.**
The gateway re-fetches the engine snapshot and holds it for about a
second, so a response is at most that stale and any request rate costs
the engine at most one call per market per second.

The consequence for clients is that `lastUpdateId` is **not a sync
anchor in v0**. Consecutive snapshots skip arbitrarily far because
nothing carries the updates in between, so the algorithm described on
that field cannot be run and the `diffDepth` stream it pairs with does
not exist yet. Poll this endpoint instead, and treat each response as a
whole replacement for the previous one.

A registered market with no resting orders returns `200` with empty
`bids` and `asks`. `503` means the engine could not be asked, which is
the only case in which the book is unknown.


### Example


```python
import kora_gateway_client
from kora_gateway_client.models.get_depth200_response import GetDepth200Response
from kora_gateway_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.kora.so
# See configuration.py for a list of all supported configuration parameters.
configuration = kora_gateway_client.Configuration(
    host = "https://api.kora.so"
)


# Enter a context with an instance of the API client
async with kora_gateway_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = kora_gateway_client.MarketDataApi(api_client)
    market = 'market_example' # str | Symbol as published by `/public/v1/markets`, e.g. `eXAU-USDCx`.
    depth = 50 # int |  (optional) (default to 50)

    try:
        # Order book snapshot.
        api_response = await api_instance.get_depth(market, depth=depth)
        print("The response of MarketDataApi->get_depth:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MarketDataApi->get_depth: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **market** | **str**| Symbol as published by &#x60;/public/v1/markets&#x60;, e.g. &#x60;eXAU-USDCx&#x60;. | 
 **depth** | **int**|  | [optional] [default to 50]

### Return type

[**GetDepth200Response**](GetDepth200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Depth-limited book. A client must not infer that an absent level is empty beyond the returned window.  |  -  |
**400** | Malformed request. |  -  |
**404** | Not found. |  -  |
**503** | The book for this market is not servable yet — bootstrapping, or resyncing after a sequence gap or an engine restart.  Distinct from 404, which means the market does not exist. A known market whose projection is not ready is a \&quot;ask again\&quot; answer, and the alternative — serving an empty book — reads as \&quot;no liquidity\&quot;, which a client will act on.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_exchange_stats**
> GetExchangeStats200Response get_exchange_stats(interval=interval, start_time=start_time, end_time=end_time, market=market)

Venue statistics over a time range.

**In scope for MVP, not implemented yet — answers `501` until its handler lands.** Committed to the contract ahead of the implementation so clients can generate against the final shape. Unlike the operations marked not-available-in-v0, this one has a source and is planned; track it before depending on it in a release.


### Example


```python
import kora_gateway_client
from kora_gateway_client.models.get_exchange_stats200_response import GetExchangeStats200Response
from kora_gateway_client.models.stats_interval import StatsInterval
from kora_gateway_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.kora.so
# See configuration.py for a list of all supported configuration parameters.
configuration = kora_gateway_client.Configuration(
    host = "https://api.kora.so"
)


# Enter a context with an instance of the API client
async with kora_gateway_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = kora_gateway_client.MarketDataApi(api_client)
    interval = '1d' # StatsInterval |  (optional) (default to '1d')
    start_time = '2013-10-20T19:20:30+01:00' # datetime |  (optional)
    end_time = '2013-10-20T19:20:30+01:00' # datetime |  (optional)
    market = 'market_example' # str | Restrict to one market. Omit for venue-wide. (optional)

    try:
        # Venue statistics over a time range.
        api_response = await api_instance.get_exchange_stats(interval=interval, start_time=start_time, end_time=end_time, market=market)
        print("The response of MarketDataApi->get_exchange_stats:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MarketDataApi->get_exchange_stats: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **interval** | [**StatsInterval**](.md)|  | [optional] [default to &#39;1d&#39;]
 **start_time** | **datetime**|  | [optional] 
 **end_time** | **datetime**|  | [optional] 
 **market** | **str**| Restrict to one market. Omit for venue-wide. | [optional] 

### Return type

[**GetExchangeStats200Response**](GetExchangeStats200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | One entry per interval bucket, oldest first. |  -  |
**400** | Malformed request. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_exchange_stats_all_time**
> ExchangeStatsAllTime get_exchange_stats_all_time()

Cumulative venue statistics.

**In scope for MVP, not implemented yet — answers `501` until its handler lands.** Committed to the contract ahead of the implementation so clients can generate against the final shape. Unlike the operations marked not-available-in-v0, this one has a source and is planned; track it before depending on it in a release.


### Example


```python
import kora_gateway_client
from kora_gateway_client.models.exchange_stats_all_time import ExchangeStatsAllTime
from kora_gateway_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.kora.so
# See configuration.py for a list of all supported configuration parameters.
configuration = kora_gateway_client.Configuration(
    host = "https://api.kora.so"
)


# Enter a context with an instance of the API client
async with kora_gateway_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = kora_gateway_client.MarketDataApi(api_client)

    try:
        # Cumulative venue statistics.
        api_response = await api_instance.get_exchange_stats_all_time()
        print("The response of MarketDataApi->get_exchange_stats_all_time:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MarketDataApi->get_exchange_stats_all_time: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**ExchangeStatsAllTime**](ExchangeStatsAllTime.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Cumulative totals since launch. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_markets**
> GetMarkets200Response get_markets()

Provisioned market registry.

The client-visible source of truth for symbols and trading rules.

### Example


```python
import kora_gateway_client
from kora_gateway_client.models.get_markets200_response import GetMarkets200Response
from kora_gateway_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.kora.so
# See configuration.py for a list of all supported configuration parameters.
configuration = kora_gateway_client.Configuration(
    host = "https://api.kora.so"
)


# Enter a context with an instance of the API client
async with kora_gateway_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = kora_gateway_client.MarketDataApi(api_client)

    try:
        # Provisioned market registry.
        api_response = await api_instance.get_markets()
        print("The response of MarketDataApi->get_markets:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MarketDataApi->get_markets: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**GetMarkets200Response**](GetMarkets200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Markets. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_ticker**
> Ticker get_ticker(market)

24h rollup plus best bid/ask.

### Example


```python
import kora_gateway_client
from kora_gateway_client.models.ticker import Ticker
from kora_gateway_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.kora.so
# See configuration.py for a list of all supported configuration parameters.
configuration = kora_gateway_client.Configuration(
    host = "https://api.kora.so"
)


# Enter a context with an instance of the API client
async with kora_gateway_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = kora_gateway_client.MarketDataApi(api_client)
    market = 'market_example' # str | Symbol as published by `/public/v1/markets`, e.g. `eXAU-USDCx`.

    try:
        # 24h rollup plus best bid/ask.
        api_response = await api_instance.get_ticker(market)
        print("The response of MarketDataApi->get_ticker:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MarketDataApi->get_ticker: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **market** | **str**| Symbol as published by &#x60;/public/v1/markets&#x60;, e.g. &#x60;eXAU-USDCx&#x60;. | 

### Return type

[**Ticker**](Ticker.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Ticker. |  -  |
**404** | Not found. |  -  |
**503** | Matching engine unreachable. Authoritative reads fail rather than serving stale state.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_tickers**
> GetTickers200Response get_tickers()

Ticker for every market in one call.

**In scope for MVP, not implemented yet — answers `501` until its handler lands.** Committed to the contract ahead of the implementation so clients can generate against the final shape. Unlike the operations marked not-available-in-v0, this one has a source and is planned; track it before depending on it in a release.

The polled endpoint. An MM watching N markets should call this once
rather than N times, which is why it exists separately from
`/ticker/{market}`.


### Example


```python
import kora_gateway_client
from kora_gateway_client.models.get_tickers200_response import GetTickers200Response
from kora_gateway_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.kora.so
# See configuration.py for a list of all supported configuration parameters.
configuration = kora_gateway_client.Configuration(
    host = "https://api.kora.so"
)


# Enter a context with an instance of the API client
async with kora_gateway_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = kora_gateway_client.MarketDataApi(api_client)

    try:
        # Ticker for every market in one call.
        api_response = await api_instance.get_tickers()
        print("The response of MarketDataApi->get_tickers:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MarketDataApi->get_tickers: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**GetTickers200Response**](GetTickers200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | One entry per provisioned market. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_trades**
> GetTrades200Response get_trades(market, limit=limit)

Recent public prints.

**Settled trades only.** A trade is written at match time and settles
~13-15s later, and settlement can fail — so this endpoint filters to
`settled`, and a trade that busted or was rejected never appears here or
in any published volume figure.

The live WS tape (`Recent_Trade`) does the opposite: it prints at match
for immediacy and carries `settlementState` so a client can see what is
still provisional. A print it already showed can be **retracted**: treat
any terminal state that is not `settled` as a removal. There are two
today, `busted` and `rejected`, and matching on `busted` alone leaves
phantom volume that disagrees with this endpoint permanently.


### Example


```python
import kora_gateway_client
from kora_gateway_client.models.get_trades200_response import GetTrades200Response
from kora_gateway_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.kora.so
# See configuration.py for a list of all supported configuration parameters.
configuration = kora_gateway_client.Configuration(
    host = "https://api.kora.so"
)


# Enter a context with an instance of the API client
async with kora_gateway_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = kora_gateway_client.MarketDataApi(api_client)
    market = 'market_example' # str | Symbol as published by `/public/v1/markets`, e.g. `eXAU-USDCx`.
    limit = 100 # int |  (optional) (default to 100)

    try:
        # Recent public prints.
        api_response = await api_instance.get_trades(market, limit=limit)
        print("The response of MarketDataApi->get_trades:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MarketDataApi->get_trades: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **market** | **str**| Symbol as published by &#x60;/public/v1/markets&#x60;, e.g. &#x60;eXAU-USDCx&#x60;. | 
 **limit** | **int**|  | [optional] [default to 100]

### Return type

[**GetTrades200Response**](GetTrades200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Trades, newest first. |  -  |
**400** | Malformed request. |  -  |
**404** | Not found. |  -  |
**503** | Matching engine unreachable. Authoritative reads fail rather than serving stale state.  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

