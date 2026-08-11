# GetDepth200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**market** | **str** |  | 
**mkt_epoch** | **int** | Engine session. &#x60;lastUpdateId&#x60; restarts at 0 when this changes, so a diff-stream consumer must treat an epoch change as a full resynchronisation, not a gap.  | 
**last_update_id** | **int** | Anchor for the local-orderbook sync algorithm, **not usable as one in v0** — see this operation&#39;s description. The engine publishes no book deltas yet, so consecutive snapshots skip and there is nothing to splice them into. It is still the engine value and still advances, so it is safe to use for ordering two snapshots against each other, and nothing more.  When deltas land the algorithm is: call this snapshot&#39;s value &#x60;S&#x60;, buffer diff frames, fetch the snapshot, discard every frame whose &#x60;lastUpdateId &lt;&#x3D; S&#x60;, and apply the first frame satisfying &#x60;firstUpdateId &lt;&#x3D; S + 1 &lt;&#x3D; lastUpdateId&#x60;. Thereafter each frame&#39;s &#x60;firstUpdateId&#x60; must equal the previous frame&#39;s &#x60;lastUpdateId + 1&#x60;.  The &#x60;S + 1&#x60; matters: a frame spans a *range*, because the engine coalesces repeated updates to a level within a flush tick. Requiring &#x60;firstUpdateId &lt;&#x3D; S&#x60; would reject the ordinary next frame &#x60;[S+1, S+1]&#x60; and leave a client resynchronising in a loop.  **Not yet implementable end to end.** The algorithm is correct and final, but the producer does not publish the id space it runs on: the engine&#39;s book snapshot carries no &#x60;last_update_id&#x60;, so &#x60;S&#x60; has no value, and the delta ids are documented against the venue-wide engine counter rather than a per-&#x60;(market, epoch)&#x60; one. A client that builds this loop today and sees it never converge has not made a mistake. Tracked on the engine contract; this field is served from the gateway&#39;s own projection meanwhile.  | 
**best_bid_price** | **str** |  | 
**best_bid_qty** | **str** |  | 
**best_ask_price** | **str** |  | 
**best_ask_qty** | **str** |  | 
**bids** | **List[List[str]]** | &#x60;[price, quantity]&#x60; pairs, both decimal strings, best first. | 
**asks** | **List[List[str]]** | &#x60;[price, quantity]&#x60; pairs, both decimal strings, best first. | 
**as_of** | **datetime** | When this book last **advanced** — the snapshot or delta that most recently changed a level — not when the response was built. A book that has been stalled for minutes therefore reports the age of its last real update rather than looking freshly observed.  **Not a liveness signal, and it cannot be used as one.** A quiet market whose levels genuinely have not moved is indistinguishable here from a market whose feed has died: both age at the same rate. Treating a stale &#x60;asOf&#x60; as \&quot;do not trust this book\&quot; discards good data on quiet markets; treating it as fine trusts a dead feed. Neither reading is available from this field, so do not infer feed health from it — the venue monitors that on its own side.  | 

## Example

```python
from kora_gateway_client.models.get_depth200_response import GetDepth200Response

# TODO update the JSON string below
json = "{}"
# create an instance of GetDepth200Response from a JSON string
get_depth200_response_instance = GetDepth200Response.from_json(json)
# print the JSON string representation of the object
print(GetDepth200Response.to_json())

# convert the object into a dict
get_depth200_response_dict = get_depth200_response_instance.to_dict()
# create an instance of GetDepth200Response from a dict
get_depth200_response_from_dict = GetDepth200Response.from_dict(get_depth200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


