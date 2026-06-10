"""Output model for Historical VaR calculation.

Result of VaR computation: loss thresholds and metadata.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class HistoricalVaRResult(BaseModel):
    """Result of Historical VaR calculation.

    Represents the Value-at-Risk: the loss threshold at a given confidence level
    for a fixed portfolio under historical scenarios.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Date of the portfolio snapshot.
    - confidence_level: Confidence level, e.g., 0.95.
    - horizon_days: Horizon in days. Must be 1 for Phase 1.
    - var_value: VaR loss threshold in base currency (positive, signed as loss magnitude).
    - var_pct_nav: VaR as percentage of NAV (positive, decimal ratio).
    - num_scenarios: Number of scenarios used.
    - quantile_index: Index of selected quantile scenario (0-indexed).

    Sign convention:
    - var_value and var_pct_nav are always non-negative (loss magnitudes).
    - A 2.5% loss is represented as var_pct_nav = 0.025.
    """

    fund_id: int
    valuation_date: date
    confidence_level: Decimal
    horizon_days: int
    var_value: Decimal
    var_pct_nav: Decimal
    num_scenarios: int
    quantile_index: int

    model_config = ConfigDict(frozen=True)

    @field_validator("var_value")
    @classmethod
    def validate_var_value(cls, v: Decimal) -> Decimal:
        """VaR value must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"VaR value must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("var_pct_nav")
    @classmethod
    def validate_var_pct_nav(cls, v: Decimal) -> Decimal:
        """VaR as % of NAV must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"VaR % NAV must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("horizon_days")
    @classmethod
    def validate_horizon_days(cls, v: int) -> int:
        """Horizon days must be 1 for Phase 1."""
        if v != 1:
            raise ValueError(f"Phase 1 supports only horizon_days=1, got {v}")
        return v

    @field_validator("num_scenarios")
    @classmethod
    def validate_num_scenarios(cls, v: int) -> int:
        """Number of scenarios must be positive."""
        if v <= 0:
            raise ValueError(f"Number of scenarios must be positive, got {v}")
        return v

    @field_validator("quantile_index")
    @classmethod
    def validate_quantile_index(cls, v: int) -> int:
        """Quantile index must be non-negative."""
        if v < 0:
            raise ValueError(f"Quantile index must be non-negative, got {v}")
        return v
