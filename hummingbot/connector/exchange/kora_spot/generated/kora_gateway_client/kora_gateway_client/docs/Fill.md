# Fill


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fill_id** | **str** |  | 
**order_id** | **str** |  | 
**market** | **str** |  | 
**side** | [**Side**](Side.md) |  | 
**price** | **str** |  | 
**quantity** | **str** |  | 
**is_maker** | **bool** | Whether this party was the maker. Named to match &#x60;Trade.isMaker&#x60; on the perps API, which ported clients already parse.  Not decorative: &#x60;Market&#x60; carries &#x60;makerFeeBps&#x60; and &#x60;takerFeeBps&#x60; separately, so this is the field that says which of the two produced &#x60;fee&#x60;. Without it a client cannot reconcile a fee against the published schedule.  | 
**quote_qty** | **str** | &#x60;price × quantity&#x60;, denominated in the market&#39;s **quote asset** — the counterpart of &#x60;quantity&#x60;, which is in the base asset. Named after &#x60;Trade.quoteQuantityE9&#x60; on the perps API.  **This is not a USD value.** It coincides with one only where the quote asset is a dollar stablecoin, as in &#x60;eXAU-USDCx&#x60;. On a market quoted in anything else it is denominated in that asset, and rendering it with a currency symbol would be wrong. Converting to USD needs an oracle price for the quote asset, which this endpoint does not apply.  Returned rather than left to the client so every surface rounds identically.  | [optional] 
**fee** | **str** |  | [optional] 
**fee_asset** | **str** | **The asset this party received on this fill** — base for a BUY, quote for a SELL. Fees are deducted from proceeds rather than sourced separately, so a fee can never fail an otherwise-valid fill.  Stated because it is side-dependent, and a maker sizing an order needs it *before* placing: a bot budgeting the fee against the wrong asset either under-uses its balance or gets rejected. &#x60;isMaker&#x60; selects which of &#x60;Market.makerFeeBps&#x60; / &#x60;takerFeeBps&#x60; applied; this says which asset it came out of.  | [optional] 
**settlement_state** | [**SettlementState**](SettlementState.md) |  | 
**bust_reason** | **str** | Present when &#x60;settlementState&#x60; is &#x60;busted&#x60;.  **Deliberately not an enum, unlike &#x60;cancelReason&#x60;.** Cancels are venue-initiated, so that set is closed and we control it. Busts are classified from Canton failures, so the set is open — a new node version or token-standard change can produce a cause nobody has seen. Clients must render an unrecognised value rather than reject the message.  Known values at launch: &#x60;insufficient_funds&#x60; (the trader spent the assets between match and settle), &#x60;delegation_revoked&#x60;, &#x60;delegation_expired&#x60;, &#x60;contract_validation_failed&#x60; (an on-chain assert rejected the fill), &#x60;contention_retries_exhausted&#x60;.  | [optional] 
**matched_at** | **datetime** |  | 
**settled_at** | **datetime** | Absent until &#x60;settlementState&#x60; is &#x60;settled&#x60;. | [optional] 

## Example

```python
from kora_gateway_client.models.fill import Fill

# TODO update the JSON string below
json = "{}"
# create an instance of Fill from a JSON string
fill_instance = Fill.from_json(json)
# print the JSON string representation of the object
print(Fill.to_json())

# convert the object into a dict
fill_dict = fill_instance.to_dict()
# create an instance of Fill from a dict
fill_from_dict = Fill.from_dict(fill_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


