# kora_auth_client.DefaultApi

All URIs are relative to *https://auth.api.prod.kora.so*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_auth_jwks**](DefaultApi.md#get_auth_jwks) | **GET** /auth/jwks | JWKS public key endpoint
[**get_internal_service_token**](DefaultApi.md#get_internal_service_token) | **GET** /internal/service-token | Issue service JWT for Canton/Ledger calls
[**post_auth_token**](DefaultApi.md#post_auth_token) | **POST** /auth/token | Sign in with wallet signature
[**put_auth_token_refresh**](DefaultApi.md#put_auth_token_refresh) | **PUT** /auth/token/refresh | Refresh access token


# **get_auth_jwks**
> JwksResponse get_auth_jwks()

JWKS public key endpoint

Returns the RS256 public key used to sign all JWTs (user access tokens,
refresh tokens, and service tokens). Consumed by node-service, Validator
App, and Ledger API for JWT verification.


### Example


```python
import kora_auth_client
from kora_auth_client.models.jwks_response import JwksResponse
from kora_auth_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://auth.api.prod.kora.so
# See configuration.py for a list of all supported configuration parameters.
configuration = kora_auth_client.Configuration(
    host = "https://auth.api.prod.kora.so"
)


# Enter a context with an instance of the API client
async with kora_auth_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = kora_auth_client.DefaultApi(api_client)

    try:
        # JWKS public key endpoint
        api_response = await api_instance.get_auth_jwks()
        print("The response of DefaultApi->get_auth_jwks:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_auth_jwks: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**JwksResponse**](JwksResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | JWKS document |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_internal_service_token**
> ServiceTokenResponse get_internal_service_token(audience)

Issue service JWT for Canton/Ledger calls

Issues a cached RS256 service JWT for node-service to authenticate
against the Validator App or Ledger API. Not internet-facing — internal
network only.


### Example


```python
import kora_auth_client
from kora_auth_client.models.service_token_response import ServiceTokenResponse
from kora_auth_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://auth.api.prod.kora.so
# See configuration.py for a list of all supported configuration parameters.
configuration = kora_auth_client.Configuration(
    host = "https://auth.api.prod.kora.so"
)


# Enter a context with an instance of the API client
async with kora_auth_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = kora_auth_client.DefaultApi(api_client)
    audience = 'audience_example' # str | 

    try:
        # Issue service JWT for Canton/Ledger calls
        api_response = await api_instance.get_internal_service_token(audience)
        print("The response of DefaultApi->get_internal_service_token:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_internal_service_token: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **audience** | **str**|  | 

### Return type

[**ServiceTokenResponse**](ServiceTokenResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Service JWT |  -  |
**400** | Unknown audience |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_auth_token**
> LoginResponse post_auth_token(payload_signature, login_request, read_only=read_only)

Sign in with wallet signature

Verifies a signed login payload and issues a user JWT (access + refresh tokens).

The client must:
1. Build the JSON request body `{ accountAddress, signedAtMillis, audience }`
2. Compute `Blake2b-256(body)`
3. Sign the digest with an Ed25519 private key (e.g. via Privy SDK `signMessage`)
4. Encode the signature as `[0x00 | 64-byte sig | 32-byte pubkey]` → base64url
5. Pass the encoded signature in the `payloadSignature` query parameter

The server verifies the signature, recovers the wallet address from the public key,
checks the timestamp is within 5 minutes, and checks the audience matches.


### Example


```python
import kora_auth_client
from kora_auth_client.models.login_request import LoginRequest
from kora_auth_client.models.login_response import LoginResponse
from kora_auth_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://auth.api.prod.kora.so
# See configuration.py for a list of all supported configuration parameters.
configuration = kora_auth_client.Configuration(
    host = "https://auth.api.prod.kora.so"
)


# Enter a context with an instance of the API client
async with kora_auth_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = kora_auth_client.DefaultApi(api_client)
    payload_signature = 'payload_signature_example' # str | Base64url-encoded signature — `[sigType (1 byte) | signature (64 bytes) | publicKey (32 bytes)]`
    login_request = {"accountAddress":"0xabc123...","signedAtMillis":1740470400000,"audience":"kora-prod"} # LoginRequest | 
    read_only = False # bool |  (optional) (default to False)

    try:
        # Sign in with wallet signature
        api_response = await api_instance.post_auth_token(payload_signature, login_request, read_only=read_only)
        print("The response of DefaultApi->post_auth_token:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->post_auth_token: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **payload_signature** | **str**| Base64url-encoded signature — &#x60;[sigType (1 byte) | signature (64 bytes) | publicKey (32 bytes)]&#x60; | 
 **login_request** | [**LoginRequest**](LoginRequest.md)|  | 
 **read_only** | **bool**|  | [optional] [default to False]

### Return type

[**LoginResponse**](LoginResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | JWT issued successfully |  -  |
**401** | Signature verification failed or timestamp expired |  -  |
**400** | Malformed request body or invalid audience |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **put_auth_token_refresh**
> LoginResponse put_auth_token_refresh(refresh_request)

Refresh access token

Exchange a valid refresh token for a new access token.

### Example


```python
import kora_auth_client
from kora_auth_client.models.login_response import LoginResponse
from kora_auth_client.models.refresh_request import RefreshRequest
from kora_auth_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://auth.api.prod.kora.so
# See configuration.py for a list of all supported configuration parameters.
configuration = kora_auth_client.Configuration(
    host = "https://auth.api.prod.kora.so"
)


# Enter a context with an instance of the API client
async with kora_auth_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = kora_auth_client.DefaultApi(api_client)
    refresh_request = kora_auth_client.RefreshRequest() # RefreshRequest | 

    try:
        # Refresh access token
        api_response = await api_instance.put_auth_token_refresh(refresh_request)
        print("The response of DefaultApi->put_auth_token_refresh:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->put_auth_token_refresh: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **refresh_request** | [**RefreshRequest**](RefreshRequest.md)|  | 

### Return type

[**LoginResponse**](LoginResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | New access token issued |  -  |
**401** | Refresh token invalid or expired |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

