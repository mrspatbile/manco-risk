"""Result model for a single fixed-income position under a stress scenario.

Carries decomposed P&L (rate component and credit component) alongside the
stressed dirty value. The decomposition supports attribution and audit.

Dirty value convention (Phase 1):
    current_dirty_value_base_ccy equals market_value_base_ccy from the
    EnrichedPosition. Fund administrator files report dirty values
    (full price + accrued interest). No accrued interest computation is
    performed in Phase 1.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class FixedIncomeStressPositionResult(BaseModel):
    """Stressed outcome for a single fixed-income position under one scenario.

    Fields:
    - position_id: Position identifier (from EnrichedPosition).
    - isin: Instrument ISIN.
    - position_name: Optional human-readable name for audit.
    - asset_class: Asset classification (e.g., "BOND", "CASH").
    - shock_type: Audit label (e.g., "RATE_SHOCK", "SPREAD_SHOCK", "COMBINED").
    - rate_shock_bps: Yield shock applied in integer basis points.
    - spread_shock_bps: Spread shock applied in integer basis points.
    - modified_duration: Modified duration used (years); None if not required.
    - spread_duration: Spread duration used (years); None if not required.
    - current_dirty_value_base_ccy: Dirty market value before stress (base ccy).
      Equals market_value_base_ccy from EnrichedPosition (Phase 1 proxy).
    - stressed_dirty_value_base_ccy: Dirty market value after stress (base ccy).
    - rate_pnl: Rate-shock component of P&L (signed). Negative = loss.
    - credit_pnl: Spread-shock component of P&L (signed). Negative = loss.
    - total_pnl: Sum of rate_pnl and credit_pnl (signed). Negative = loss.

    Sign conventions:
    - P&L is signed: negative = loss, positive = gain.
    - rate_pnl < 0 when yield rises (positive rate_shock_bps).
    - credit_pnl < 0 when spread widens (positive spread_shock_bps).

    Immutability:
    - Frozen; result is immutable after construction.
    """

    position_id: int
    isin: str
    position_name: Optional[str] = None
    asset_class: str
    shock_type: str
    rate_shock_bps: int
    spread_shock_bps: int
    modified_duration: Optional[Decimal] = None
    spread_duration: Optional[Decimal] = None
    current_dirty_value_base_ccy: Decimal
    stressed_dirty_value_base_ccy: Decimal
    rate_pnl: Decimal
    credit_pnl: Decimal
    total_pnl: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("shock_type")
    @classmethod
    def validate_shock_type_non_empty(cls, v: str) -> str:
        """Shock type must be non-empty."""
        if not v or not v.strip():
            raise ValueError("shock_type must be non-empty")
        return v.strip()

    @field_validator("current_dirty_value_base_ccy", "stressed_dirty_value_base_ccy")
    @classmethod
    def validate_non_negative_values(cls, v: Decimal) -> Decimal:
        """Dirty market values must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"Dirty market value must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("rate_pnl", "credit_pnl", "total_pnl", mode="before")
    @classmethod
    def validate_decimal_conversion(cls, v) -> Decimal:
        """Ensure P&L fields are valid Decimals."""
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except Exception as e:
            raise ValueError(f"Value must be convertible to Decimal, got {v}: {e}")

    @field_validator("modified_duration", "spread_duration", mode="before")
    @classmethod
    def validate_optional_duration(cls, v) -> Optional[Decimal]:
        """Duration fields must be non-negative Decimals when present."""
        if v is None:
            return None
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"Duration must be non-negative, got {v_decimal}")
        return v_decimal
