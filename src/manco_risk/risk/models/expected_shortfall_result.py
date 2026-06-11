"""Output model for Historical Expected Shortfall calculation.

Result of ES computation: loss threshold, tail metrics, and VaR linkage.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class HistoricalExpectedShortfallResult(BaseModel):
    """Result of Historical ES calculation.

    Conditional mean of losses at or beyond the VaR threshold.
    Links back to the matched HistoricalVaR result for consistency.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Date of the portfolio snapshot.
    - confidence_level: Confidence level (copied from var_result).
    - horizon_days: Horizon in days. Must be 1 for Phase 1 (from var_result).
    - es_value: ES loss threshold in base currency (positive, signed as loss magnitude).
    - es_pct_nav: ES as percentage of NAV (positive, decimal ratio).
    - num_tail_observations: Count of scenario P&Ls in the tail (at or beyond VaR threshold).
    - num_observations: Total number of observations used.
    - quantile_index: Index of the VaR quantile (copied from var_result, for reference).
    - linked_var_value: VaR loss threshold in base currency (copied from var_result).
    - linked_var_pct_nav: VaR as percentage of NAV (copied from var_result).

    Sign convention:
    - es_value and es_pct_nav are always non-negative (loss magnitudes).
    - ES >= VaR at same confidence level (general mathematical invariant).
    - A 4.0% loss is represented as es_pct_nav = 0.040.

    Invariant (all methods):

    Expected Shortfall must be greater than or equal to the matching VaR result
    when both are calculated on the same portfolio, horizon, confidence level,
    distribution, and sign convention. This holds for all ES methods:

    - Historical ES >= Historical VaR (this implementation)
    - Parametric normal ES >= Parametric normal VaR (future)
    - Parametric Student-t ES >= Parametric Student-t VaR (future, if implemented)
    - Variance-covariance ES >= Variance-covariance VaR (future, if implemented)

    When implementing new ES methods, include a consistency test against
    the matching VaR method to validate this invariant.
    """

    fund_id: int
    valuation_date: date
    confidence_level: Decimal
    horizon_days: int
    es_value: Decimal
    es_pct_nav: Decimal
    num_tail_observations: int
    num_observations: int
    quantile_index: int
    linked_var_value: Decimal
    linked_var_pct_nav: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("es_value")
    @classmethod
    def validate_es_value(cls, v: Decimal) -> Decimal:
        """ES value must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"ES value must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("es_pct_nav")
    @classmethod
    def validate_es_pct_nav(cls, v: Decimal) -> Decimal:
        """ES as % of NAV must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"ES % NAV must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("horizon_days")
    @classmethod
    def validate_horizon_days(cls, v: int) -> int:
        """Horizon days must be 1 for Phase 1."""
        if v != 1:
            raise ValueError(f"Phase 1 supports only horizon_days=1, got {v}")
        return v

    @field_validator("num_tail_observations")
    @classmethod
    def validate_num_tail_observations(cls, v: int) -> int:
        """Number of tail observations must be positive."""
        if v <= 0:
            raise ValueError(f"Number of tail observations must be positive, got {v}")
        return v

    @field_validator("num_observations")
    @classmethod
    def validate_num_observations(cls, v: int) -> int:
        """Number of observations must be positive."""
        if v <= 0:
            raise ValueError(f"Number of observations must be positive, got {v}")
        return v

    @field_validator("quantile_index")
    @classmethod
    def validate_quantile_index(cls, v: int) -> int:
        """Quantile index must be non-negative."""
        if v < 0:
            raise ValueError(f"Quantile index must be non-negative, got {v}")
        return v

    @field_validator("linked_var_value")
    @classmethod
    def validate_linked_var_value(cls, v: Decimal) -> Decimal:
        """Linked VaR value must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"Linked VaR value must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("linked_var_pct_nav")
    @classmethod
    def validate_linked_var_pct_nav(cls, v: Decimal) -> Decimal:
        """Linked VaR as % of NAV must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"Linked VaR % NAV must be non-negative, got {v_decimal}")
        return v_decimal
