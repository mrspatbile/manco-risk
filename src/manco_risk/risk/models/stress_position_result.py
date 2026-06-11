"""Result model for a single position under a stress scenario.

Represents the stressed value and P&L of a single position.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class StressPositionResult(BaseModel):
    """Stressed outcome for a single position under one scenario.

    Represents:
    - current market value before stress
    - stressed market value after stress
    - position-level P&L (signed)
    - position and shock metadata for audit and debugging

    Fields:
    - position_id: Position identifier (from enriched position).
    - isin: Instrument ISIN.
    - position_name: Optional human-readable position name for audit.
    - asset_class: Asset classification (e.g., "EQUITY", "CASH").
    - shock_type: Type of shock applied (e.g., "PARALLEL_EQUITY"). For audit and future multi-asset support.
    - shock_rate: Shock rate applied (decimal, e.g., -0.20).
    - current_market_value_base_ccy: Current value in base currency before stress.
    - stressed_market_value_base_ccy: Stressed value in base currency.
    - position_pnl: Position P&L (signed: negative = loss, positive = gain).

    Design:
    - shock_type is stored at position level for audit trail and to support
      future multi-asset stress workflows (bonds, derivatives, etc.).
    - Generic models allow extensibility without redesign.

    Sign convention:
    - position_pnl is signed: negative = loss, positive = gain.

    Monetary values:
    - All monetary values use Decimal for precision.
    - All values in base currency.

    Immutability:
    - Frozen; result is immutable after construction.
    """

    position_id: int
    isin: str
    position_name: Optional[str] = None
    asset_class: str
    shock_type: str
    shock_rate: Decimal
    current_market_value_base_ccy: Decimal
    stressed_market_value_base_ccy: Decimal
    position_pnl: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("shock_type")
    @classmethod
    def validate_shock_type_non_empty(cls, v: str) -> str:
        """Shock type must be non-empty."""
        if not v or not v.strip():
            raise ValueError("shock_type must be non-empty")
        return v.strip()

    @field_validator("current_market_value_base_ccy", "stressed_market_value_base_ccy")
    @classmethod
    def validate_non_negative_values(cls, v: Decimal) -> Decimal:
        """Market values must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"Market value must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("shock_rate", "position_pnl", mode="before")
    @classmethod
    def validate_decimal_conversion(cls, v) -> Decimal:
        """Ensure decimal fields are valid Decimals."""
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except Exception as e:
            raise ValueError(f"Value must be convertible to Decimal, got {v}: {e}")
