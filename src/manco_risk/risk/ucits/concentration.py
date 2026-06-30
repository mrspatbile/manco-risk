"""UCITS single-issuer concentration monitoring models.

Pure data models. No calculation or persistence logic.
"""

from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class UCITSConcentrationStatus(str, PyEnum):
    """Compliance status of issuer concentration vs. regulatory threshold.

    WITHIN_LIMIT: Issuer exposure <= threshold (compliant).
    BREACH: Issuer exposure > threshold (non-compliant).
    """

    WITHIN_LIMIT = "WITHIN_LIMIT"
    BREACH = "BREACH"


class UCITSConcentrationInput(BaseModel):
    """Input to UCITS single-issuer concentration monitoring engine.

    Minimal input containing pre-computed issuer exposure for a fund snapshot.

    The engine will calculate exposure_ratio internally from issuer_exposure_amount and nav.
    No duplication of derived state.

    Fields:
    - fund_id: Fund identifier (string, e.g., "UCITS_Balanced").
    - valuation_date: Snapshot date (ISO 8601).
    - nav: Net asset value at valuation date (positive Decimal, in base currency).
    - issuer_id: Issuer identifier (LEI, ticker, or internal code).
    - issuer_name: Issuer name for audit trail (optional, not used in calculation).
    - issuer_exposure_amount: Total exposure to issuer (non-negative, positive monetary amount).

    Note: This engine monitors only single-issuer concentration under the UCITS framework.
    It does not aggregate exposures from positions or derivatives.

    Invariants:
    - fund_id must be non-empty.
    - nav must be positive.
    - issuer_id must be non-empty.
    - issuer_exposure_amount must be non-negative.
    """

    fund_id: str
    valuation_date: date
    nav: Decimal
    issuer_id: str
    issuer_name: Optional[str] = None
    issuer_exposure_amount: Decimal

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

    @field_validator("issuer_id")
    @classmethod
    def validate_issuer_id(cls, v: str) -> str:
        """Issuer ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("issuer_id must be non-empty")
        return v.strip()

    @field_validator("issuer_exposure_amount")
    @classmethod
    def validate_issuer_exposure_amount(cls, v: Decimal) -> Decimal:
        """Issuer exposure amount must be non-negative."""
        v = Decimal(str(v)) if not isinstance(v, Decimal) else v
        if v < Decimal("0"):
            raise ValueError(f"issuer_exposure_amount must be non-negative, got {v}")
        return v


class UCITSConcentrationResult(BaseModel):
    """Result of UCITS single-issuer concentration monitoring.

    Compares single-issuer exposure observation against a regulatory threshold ratio.

    All derived values are populated by the engine and stored for reporting
    convenience. This model is a simple immutable DTO with minimal defensive
    validation.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Snapshot date.
    - nav: Net asset value.
    - issuer_id: Issuer identifier.
    - issuer_name: Issuer name (audit only).
    - issuer_exposure_amount: Total exposure to issuer.
    - exposure_ratio: Issuer exposure as fraction of NAV (calculated).
    - limit_ratio: Regulatory limit as fraction (0.10 = 10%).
    - limit_amount: Regulatory limit in base currency (calculated).
    - status: WITHIN_LIMIT or BREACH.
    - excess_amount: Amount by which exposure exceeds limit (calculated, >= 0).
    - excess_ratio: Ratio by which exposure exceeds limit (calculated, >= 0).
    """

    fund_id: str
    valuation_date: date
    nav: Decimal
    issuer_id: str
    issuer_name: Optional[str] = None
    issuer_exposure_amount: Decimal
    exposure_ratio: Decimal
    limit_ratio: Decimal
    limit_amount: Decimal
    status: UCITSConcentrationStatus
    excess_amount: Decimal
    excess_ratio: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("nav")
    @classmethod
    def validate_nav_positive(cls, v: Decimal) -> Decimal:
        """NAV must be positive (defensive check)."""
        if v <= Decimal("0"):
            raise ValueError(f"nav must be positive, got {v}")
        return v

    @field_validator("limit_ratio")
    @classmethod
    def validate_limit_ratio_positive(cls, v: Decimal) -> Decimal:
        """Limit ratio must be positive (defensive check)."""
        if v <= Decimal("0"):
            raise ValueError(f"limit_ratio must be positive, got {v}")
        return v

    @field_validator("issuer_exposure_amount", "excess_amount")
    @classmethod
    def validate_non_negative_amounts(cls, v: Decimal) -> Decimal:
        """Exposure and excess amounts must be non-negative (defensive check)."""
        if v < Decimal("0"):
            raise ValueError(f"Exposure and excess amounts must be non-negative, got {v}")
        return v

    @field_validator("exposure_ratio", "excess_ratio")
    @classmethod
    def validate_non_negative_ratios(cls, v: Decimal) -> Decimal:
        """Exposure and excess ratios must be non-negative (defensive check)."""
        if v < Decimal("0"):
            raise ValueError(f"Exposure and excess ratios must be non-negative, got {v}")
        return v
