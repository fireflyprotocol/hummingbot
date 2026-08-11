import time
from typing import Optional

import hummingbot.connector.exchange.kora_spot.kora_spot_constants as CONSTANTS
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory


def build_api_factory(
        throttler: Optional[AsyncThrottler] = None,
        auth: Optional[AuthBase] = None) -> WebAssistantsFactory:
    """
    Build hummingbot's WebAssistantsFactory. Same trade-off bluefin_perpetual_web_utils.py
    documents for its own SDK: the generated kora_gateway_client/kora_auth_client OpenAPI
    clients (used by data_sources/kora_data_source.py) issue the actual HTTP calls and do their
    own connection handling underneath, bypassing this factory and its throttler/logging entirely.
    This function exists only so kora_spot fulfils the framework surface hummingbot expects of
    every connector — do not delete it as "unused dead code"; nothing calls through it today by
    design, not by omission.
    """
    throttler = throttler or create_throttler()
    return WebAssistantsFactory(throttler=throttler, auth=auth)


def create_throttler() -> AsyncThrottler:
    return AsyncThrottler(CONSTANTS.RATE_LIMITS)


async def get_current_server_time(throttler: Optional[AsyncThrottler] = None, domain: str = CONSTANTS.DOMAIN) -> float:
    """
    Returns local time, matching bluefin_perpetual_web_utils.py's own choice for this hook.
    gateway-service does expose GET /public/v1/time, but nothing in this connector needs
    server-skew correction badly enough to justify routing it through the generated client here
    (see kora_data_source.py for the real REST calls) — revisit if clock drift ever bites.
    """
    return time.time()
