# ExchangeStatsAllTime

Pro's equivalent carries TVL. Spot has none to report — it is non-custodial, so the venue holds no user assets and there is no locked value. Anything resembling TVL here would be a sum of balances the venue does not control. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**since** | **datetime** |  | 
**quote_volume** | **str** |  | 
**trade_count** | **int** |  | 
**market_count** | **int** |  | 

## Example

```python
from kora_gateway_client.models.exchange_stats_all_time import ExchangeStatsAllTime

# TODO update the JSON string below
json = "{}"
# create an instance of ExchangeStatsAllTime from a JSON string
exchange_stats_all_time_instance = ExchangeStatsAllTime.from_json(json)
# print the JSON string representation of the object
print(ExchangeStatsAllTime.to_json())

# convert the object into a dict
exchange_stats_all_time_dict = exchange_stats_all_time_instance.to_dict()
# create an instance of ExchangeStatsAllTime from a dict
exchange_stats_all_time_from_dict = ExchangeStatsAllTime.from_dict(exchange_stats_all_time_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


