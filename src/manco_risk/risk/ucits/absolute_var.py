"""UCITS Absolute VaR monitoring models.

Pure data models. No calculation or persistence logic.
"""

from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum

from pydantic import BaseModel, ConfigDict, field_validator


class UCITSAbsoluteVaRStatus(str, PyEnum):
    """Compliance status of VaR vs. regulatory threshold.

    WITHIN_LIMIT: VaR <= threshold (compliant).
    BREACH: VaR > threshold (non-compliant).
    """

    WITHIN_LIMIT = "WITHIN_LIMIT"
    BREACH = "BREACH"


class UCITSAbsoluteVaRInput(BaseModel):
    """Input to UCITS Absolute VaR monitoring engine.

    Minimal, VaR-methodology-agnostic input.
    Represents a single VaR observation for a fund at a point in time.

    The engine will calculate var_ratio internally from var_amount and nav.
    No duplication of derived state.

    Fields:
    - fund_id: Fund identifier (string, e.g., "UCITS_Balanced").
    - valuation_date: Snapshot date (ISO 8601).
    - nav: Net asset value at valuation date (positive Decimal, in base currency).
    - var_amount: VaR in base currency (non-negative, positive loss magnitude).
    - confidence_level: Confidence level of VaR (e.g., 0.99 for 99%).
    - holding_period_days: Holding period used for VaR (e.g., 10 days).

    Invariants:
    - nav must be positive.
    - var_amount must be non-negative.
    - confidence_level must be in (0, 1).
    - holding_period_days must be positive.
    """

    fund_id: str
    valuation_date: date
    nav: Decimal
    var_amount: Decimal
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

    @field_validator("nav")
    @classmethod
    def validate_nav(cls, v: Decimal) -> Decimal:
        """NAV must be positive."""
        v = Decimal(str(v)) if not isinstance(v, Decimal) else v
        if v <= Decimal("0"):
            raise ValueError(f"nav must be positive, got {v}")
        return v

    @field_validator("var_amount")
    @classmethod
    def validate_var_amount(cls, v: Decimal) -> Decimal:
        """VaR amount must be non-negative (loss magnitude)."""
        v = Decimal(str(v)) if not isinstance(v, Decimal) else v
        if v < Decimal("0"):
            raise ValueError(f"var_amount must be non-negative, got {v}")
        return v

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level(cls, v: Decimal) -> Decimal:
        """Confidence level must be strictly between 0 and 1."""
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


class UCITSAbsoluteVaRResult(BaseModel):
    """Result of UCITS Absolute VaR monitoring.

    Compares a VaR observation against a regulatory threshold ratio.

    All derived values are populated by the monitoring engine and stored
    for reporting convenience. This model is a simple immutable DTO with
    minimal defensive validation.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Snapshot date.
    - nav: Net asset value.
    - var_amount: Portfolio VaR (currency).
    - var_ratio: Portfolio VaR as fraction of NAV.
    - threshold_ratio: Regulatory limit as fraction (e.g., 0.20).
    - threshold_amount: Regulatory limit in currency.
    - status: WITHIN_LIMIT or BREACH.
    - excess_amount: Amount by which VaR exceeds threshold (>= 0).
    - excess_ratio: Ratio by which VaR exceeds threshold (>= 0).
    - confidence_level: Confidence level of underlying VaR (audit trail).
    - holding_period_days: Holding period of underlying VaR (audit trail).
    """

    fund_id: str
    valuation_date: date
    nav: Decimal
    var_amount: Decimal
    var_ratio: Decimal
    threshold_ratio: Decimal
    threshold_amount: Decimal
    status: UCITSAbsoluteVaRStatus
    excess_amount: Decimal
    excess_ratio: Decimal
    confidence_level: Decimal
    holding_period_days: int

    model_config = ConfigDict(frozen=True)

    @field_validator("nav")
    @classmethod
    def validate_nav_positive(cls, v: Decimal) -> Decimal:
        """NAV must be positive (defensive check)."""
        if v <= Decimal("0"):
            raise ValueError(f"nav must be positive, got {v}")
        return v

    @field_validator("threshold_ratio")
    @classmethod
    def validate_threshold_ratio_positive(cls, v: Decimal) -> Decimal:
        """Threshold ratio must be positive (defensive check)."""
        if v <= Decimal("0"):
            raise ValueError(f"threshold_ratio must be positive, got {v}")
        return v

    @field_validator("excess_amount", "excess_ratio")
    @classmethod
    def validate_excess_non_negative(cls, v: Decimal) -> Decimal:
        """Excess values must be non-negative (defensive check)."""
        if v < Decimal("0"):
            raise ValueError(f"Excess values must be non-negative, got {v}")
        return v

    @field_validator("var_ratio")
    @classmethod
    def validate_var_ratio_non_negative(cls, v: Decimal) -> Decimal:
        """VaR ratio must be non-negative (defensive check)."""
        if v < Decimal("0"):
            raise ValueError(f"var_ratio must be non-negative, got {v}")
        return v
