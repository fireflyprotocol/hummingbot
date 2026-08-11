# CreateWsTicket200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ticket** | **str** |  | 
**expires_at** | **datetime** |  | 
**auth_expires_at** | **datetime** | Underlying JWT expiry, **not** the ticket&#39;s — the two are minutes apart and mean different things. The ticket stops being redeemable at &#x60;expiresAt&#x60;; the session it opens stops being private at this time, dropping its private subscriptions and downgrading to anonymous while the socket stays open. Re-authenticate with a fresh ticket and resubscribe to restore them. A client that watches only &#x60;expiresAt&#x60; will be surprised when its private channels go quiet.  | 

## Example

```python
from kora_gateway_client.models.create_ws_ticket200_response import CreateWsTicket200Response

# TODO update the JSON string below
json = "{}"
# create an instance of CreateWsTicket200Response from a JSON string
create_ws_ticket200_response_instance = CreateWsTicket200Response.from_json(json)
# print the JSON string representation of the object
print(CreateWsTicket200Response.to_json())

# convert the object into a dict
create_ws_ticket200_response_dict = create_ws_ticket200_response_instance.to_dict()
# create an instance of CreateWsTicket200Response from a dict
create_ws_ticket200_response_from_dict = CreateWsTicket200Response.from_dict(create_ws_ticket200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


