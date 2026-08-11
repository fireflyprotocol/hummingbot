# ExchangeStatsEntry


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**start_time** | **datetime** |  | 
**end_time** | **datetime** |  | 
**market** | **str** | Absent on a venue-wide query. | [optional] 
**quote_volume** | **str** | Traded volume in quote units, **settled fills only**. Matched-but-busted trades are excluded, so this never overstates what actually changed hands.  | 
**trade_count** | **int** |  | 

## Example

```python
from kora_gateway_client.models.exchange_stats_entry import ExchangeStatsEntry

# TODO update the JSON string below
json = "{}"
# create an instance of ExchangeStatsEntry from a JSON string
exchange_stats_entry_instance = ExchangeStatsEntry.from_json(json)
# print the JSON string representation of the object
print(ExchangeStatsEntry.to_json())

# convert the object into a dict
exchange_stats_entry_dict = exchange_stats_entry_instance.to_dict()
# create an instance of ExchangeStatsEntry from a dict
exchange_stats_entry_from_dict = ExchangeStatsEntry.from_dict(exchange_stats_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


