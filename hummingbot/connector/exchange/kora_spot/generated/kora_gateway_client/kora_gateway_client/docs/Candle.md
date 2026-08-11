# Candle


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**open_time** | **datetime** |  | 
**o** | **str** |  | 
**h** | **str** |  | 
**l** | **str** |  | 
**c** | **str** |  | 
**v** | **str** |  | 
**closed** | **bool** | The bucket&#39;s time window has ended. **Not the same as final.**  A trade settles 13-15s after it matches, and only settled trades count, so a bucket can still gain or lose trades after it closes — the aggregate is recomputed when that happens. &#x60;closed&#x60; says the window has passed and nothing more.  A candle is safe to treat as immutable once it is closed **and** the venue&#39;s recompute horizon for that interval has passed:  | interval | horizon | |----------|---------| | &#x60;1m&#x60;, &#x60;5m&#x60; | 1 hour | | &#x60;15m&#x60; | 2 hours | | &#x60;1h&#x60; | 6 hours | | &#x60;4h&#x60; | 1 day | | &#x60;1d&#x60; | 3 days | | &#x60;1w&#x60; | 3 weeks |  In practice a bucket stops changing within a minute of closing, because that is when its last trade settles. The horizons above are the outer bound the venue guarantees, not the expected wait — cache against them rather than against &#x60;closed&#x60; alone.  | 

## Example

```python
from kora_gateway_client.models.candle import Candle

# TODO update the JSON string below
json = "{}"
# create an instance of Candle from a JSON string
candle_instance = Candle.from_json(json)
# print the JSON string representation of the object
print(Candle.to_json())

# convert the object into a dict
candle_dict = candle_instance.to_dict()
# create an instance of Candle from a dict
candle_from_dict = Candle.from_dict(candle_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


