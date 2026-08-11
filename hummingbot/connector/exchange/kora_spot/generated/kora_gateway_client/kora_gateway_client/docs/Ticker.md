# Ticker

The 24h rollup behind the trading-screen header. Windows are rolling 24h, not calendar-day, and cover **settled** trades only. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**market** | **str** |  | 
**last** | **str** |  | [optional] 
**bid** | **str** |  | [optional] 
**ask** | **str** |  | [optional] 
**high** | **str** |  | [optional] 
**low** | **str** |  | [optional] 
**price_change** | **str** | Absolute 24h change, signed. &#x60;last − price 24h ago&#x60;. | [optional] 
**price_change_percent** | **str** | Signed. The header renders this coloured. | [optional] 
**volume** | **str** | 24h volume in **base** units. | [optional] 
**quote_volume** | **str** | 24h volume in **quote** units. Named separately because \&quot;volume\&quot; alone is ambiguous and the two differ by roughly the price.  | [optional] 
**as_of** | **datetime** |  | 

## Example

```python
from kora_gateway_client.models.ticker import Ticker

# TODO update the JSON string below
json = "{}"
# create an instance of Ticker from a JSON string
ticker_instance = Ticker.from_json(json)
# print the JSON string representation of the object
print(Ticker.to_json())

# convert the object into a dict
ticker_dict = ticker_instance.to_dict()
# create an instance of Ticker from a dict
ticker_from_dict = Ticker.from_dict(ticker_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


