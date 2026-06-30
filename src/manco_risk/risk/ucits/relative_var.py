"""UCITS Relative VaR monitoring models.

Pure data models. No calculation or persistence logic.
"""

from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum

from pydantic import BaseModel, ConfigDict, field_validator


class UCITSRelativeVaRStatus(str, PyEnum):
    """Compliance status of relative VaR vs. regulatory threshold.

    WITHIN_LIMIT: Fund VaR <= 200% of reference portfolio VaR (compliant).
    BREACH: Fund VaR > 200% of reference portfolio VaR (non-compliant).
    """

    WITHIN_LIMIT = "WITHIN_LIMIT"
    BREACH = "BREACH"


class UCITSRelativeVaRInput(BaseModel):
    """Input to UCITS Relative VaR monitoring engine.

    Minimal input containing pre-computed fund and reference portfolio VaR observations.

    The engine will calculate relative_var_ratio internally from fund_var and reference_portfolio_var.
    No duplication of derived state.

    Fields:
    - fund_id: Fund identifier (string, e.g., "UCITS_Balanced").
    - valuation_date: Snapshot date (ISO 8601).
    - fund_var: VaR of the fund (non-negative, positive loss magnitude).
    - reference_portfolio_var: VaR of the reference portfolio/benchmark (positive, positive loss magnitude).
    - confidence_level: Confidence level of VaR (e.g., 0.99 for 99%).
    - holding_period_days: Holding period used for VaR (e.g., 10 days).

    Note: This engine monitors relative VaR under the UCITS framework.
    It does not calculate VaR or construct reference portfolios.

    Invariants:
    - fund_id must be non-empty.
    - fund_var must be non-negative.
    - reference_portfolio_var must be positive (cannot be zero).
    - confidence_level must be in (0, 1).
    - holding_period_days must be positive.
    """

    fund_id: str
    valuation_date: date
    fund_var: Decimal
    reference_portfolio_var: Decimal
    confidence_level: Decimal
    holding_period_days: int

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_id")
    @classmethod
    def validate_fund_id(cls, v: str) -> str:
        """Fund ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("fund_id must be non-empty")
        return v.strip()

    @field_validator("fund_var")
    @classmethod
    def validate_fund_var(cls, v: Decimal) -> Decimal:
        """Fund VaR must be non-negative (loss magnitude)."""
        v = Decimal(str(v)) if not isinstance(v, Decimal) else v
        if v < Decimal("0"):
            raise ValueError(f"fund_var must be non-negative, got {v}")
        return v

    @field_validator("reference_portfolio_var")
    @classmethod
    def validate_reference_portfolio_var(cls, v: Decimal) -> Decimal:
        """Reference portfolio VaR must be positive (cannot be zero)."""
        v = Decimal(str(v)) if not isinstance(v, Decimal) else v
        if v <= Decimal("0"):
            raise ValueError(f"reference_portfolio_var must be positive, got {v}")
        return v

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level(cls, v: Decimal) -> Decimal:
        """Confidence level must be in (0, 1)."""
        v = Decimal(str(v)) if not isinstance(v, Decimal) else v
        if v <= Decimal("0") or v >= Decimal("1"):
            raise ValueError(f"confidence_level must be in (0, 1), got {v}")
        return v

    @field_validator("holding_period_days")
    @classmethod
    def validate_holding_period_days(cls, v: int) -> int:
        """Holding period must be positive."""
        if v <= 0:
            raise ValueError(f"holding_period_days must be positive, got {v}")
        return v


class UCITSRelativeVaRResult(BaseModel):
    """Result of UCITS Relative VaR monitoring.

    Compares fund VaR observation against reference portfolio VaR (regulatory limit).

    All derived values are populated by the engine and stored for reporting
    convenience. This model is a simple immutable DTO with minimal defensive
    validation.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Snapshot date.
    - fund_var: Fund VaR amount.
    - reference_portfolio_var: Reference portfolio VaR amount.
    - relative_var_ratio: Fund VaR as ratio to reference portfolio VaR (calculated).
    - limit_ratio: Regulatory limit as ratio (2.0 = fund VaR must not exceed 2× reference).
    - status: WITHIN_LIMIT or BREACH.
    - excess_ratio: Ratio by which fund VaR exceeds reference VaR (calculated, >= 0).
    - confidence_level: Confidence level of VaR (audit).
    - holding_period_days: Holding period of VaR (audit).
    """

    fund_id: str
    valuation_date: date
    fund_var: Decimal
    reference_portfolio_var: Decimal
    relative_var_ratio: Decimal
    limit_ratio: Decimal
    status: UCITSRelativeVaRStatus
    excess_ratio: Decimal
    confidence_level: Decimal
    holding_period_days: int

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_var", "reference_portfolio_var")
    @classmethod
    def validate_non_negative_amounts(cls, v: Decimal) -> Decimal:
        """VaR amounts must be non-negative (defensive check)."""
        if v < Decimal("0"):
            raise ValueError(f"VaR amounts must be non-negative, got {v}")
        return v

    @field_validator("limit_ratio")
    @classmethod
    def validate_limit_ratio_positive(cls, v: Decimal) -> Decimal:
        """Limit ratio must be positive (defensive check)."""
        if v <= Decimal("0"):
            raise ValueError(f"limit_ratio must be positive, got {v}")
        return v

    @field_validator("relative_var_ratio", "excess_ratio")
    @classmethod
    def validate_non_negative_ratios(cls, v: Decimal) -> Decimal:
        """VaR ratios must be non-negative (defensive check)."""
        if v < Decimal("0"):
            raise ValueError(f"VaR ratios must be non-negative, got {v}")
        return v

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level(cls, v: Decimal) -> Decimal:
        """Confidence level must be in (0, 1) (defensive check)."""
        if v <= Decimal("0") or v >= Decimal("1"):
            raise ValueError(f"confidence_level must be in (0, 1), got {v}")
        return v

    @field_validator("holding_period_days")
    @classmethod
    def validate_holding_period_days(cls, v: int) -> int:
        """Holding period must be positive (defensive check)."""
        if v <= 0:
            raise ValueError(f"holding_period_days must be positive, got {v}")
        return v
