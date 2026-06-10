"""Output model for parametric normal VaR calculation.

Result of parametric normal VaR computation: loss threshold and distributional metadata.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class ParametricNormalVaRResult(BaseModel):
    """Result of parametric normal VaR calculation.

    Represents the Value-at-Risk under a normal distribution assumption,
    for a fixed portfolio using historical scenario P&L distribution.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Date of the portfolio snapshot.
    - confidence_level: Confidence level, e.g., 0.95.
    - horizon_days: Horizon in days. Must be 1 for Phase 1.
    - var_value: VaR loss threshold in base currency (positive, signed as loss magnitude).
    - var_pct_nav: VaR as percentage of NAV (positive, decimal ratio).
    - mean_return: Arithmetic mean of portfolio returns (signed).
    - std_dev: Sample standard deviation of returns (positive).
    - num_observations: Number of returns used in calculation (>= 2).
    - z_score: Standard normal quantile applied (e.g., -1.645 for 95% VaR, negative for left tail).

    Sign convention:
    - var_value and var_pct_nav are always non-negative (loss magnitudes).
    - mean_return is signed (positive = gain, negative = loss).
    - std_dev is always non-negative.
    - z_score is negative for left-tail quantiles.
    - A 2.5% loss is represented as var_pct_nav = 0.025.

    Formula:
    - portfolio_return = mean_return + z_score * std_dev
    - var_pct_nav = abs(portfolio_return) if portfolio_return < 0 else 0
    - var_value = var_pct_nav * NAV
    """

    fund_id: int
    valuation_date: date
    confidence_level: Decimal
    horizon_days: int
    var_value: Decimal
    var_pct_nav: Decimal
    mean_return: Decimal
    std_dev: Decimal
    num_observations: int
    z_score: Decimal

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

    @field_validator("std_dev")
    @classmethod
    def validate_std_dev(cls, v: Decimal) -> Decimal:
        """Standard deviation must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"Standard deviation must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("horizon_days")
    @classmethod
    def validate_horizon_days(cls, v: int) -> int:
        """Horizon days must be 1 for Phase 1."""
        if v != 1:
            raise ValueError(f"Phase 1 supports only horizon_days=1, got {v}")
        return v

    @field_validator("num_observations")
    @classmethod
    def validate_num_observations(cls, v: int) -> int:
        """Number of observations must be at least 2."""
        if v < 2:
            raise ValueError(f"Number of observations must be >= 2, got {v}")
        return v
