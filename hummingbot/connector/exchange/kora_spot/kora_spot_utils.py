from decimal import Decimal

from pydantic import ConfigDict, Field, SecretStr

from hummingbot.client.config.config_data_types import BaseConnectorConfigMap
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

# Kora's spot venue is a Canton-based CLOB, not a wallet-to-wallet DEX, but there is no
# hummingbot-managed account/API-key pair the way a CEX has — trading is authorized by an
# Ed25519 wallet signature (same as an on-chain venue). CENTRALIZED = False follows PR #1's
# (bluefin_perpetual) precedent for this signing model, not a claim about custody.
CENTRALIZED = False

EXAMPLE_PAIR = "eXAU-USDCx"

# Static fallback only. Real per-market maker/taker bps come from Market.makerFeeBps/takerFeeBps
# at runtime (see kora_spot_exchange.py._get_fee) — this schema is what hummingbot's framework
# needs before any market has been fetched.
DEFAULT_FEES = TradeFeeSchema(
    maker_percent_fee_decimal=Decimal("0.0002"),
    taker_percent_fee_decimal=Decimal("0.0005"),
)


class KoraSpotConfigMap(BaseConnectorConfigMap):
    connector: str = "kora_spot"

    kora_spot_ed25519_private_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Kora Ed25519 private key (32-byte seed, hex-encoded)",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )

    # DEFAULT_ORDER_EXPIRY_SECONDS is a plain constant in kora_spot_constants.py, not a ConfigMap
    # field: CONTRACT.md's "Shared symbols" section has other files import
    # CONSTANTS.DEFAULT_ORDER_EXPIRY_SECONDS directly, and KoraDataSource.__init__ already takes
    # order_expiry_seconds as a constructor override point — a second, ConfigMap-sourced override
    # would be a third place this one number could come from. Add a ConfigMap field later if a
    # strategy actually needs to tune it without code, wiring it through kora_spot_exchange.py
    # into that same constructor argument.

    model_config = ConfigDict(title="kora_spot")


KEYS = KoraSpotConfigMap.model_construct()
