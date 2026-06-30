"""UCITS OTC counterparty exposure monitoring models.

Pure data models. No calculation or persistence logic.
"""

from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class UCITSCounterpartyCategory(str, PyEnum):
    """OTC counterparty category for UCITS limit determination.

    STANDARD: Standard OTC counterparty (5% NAV limit).
    ELIGIBLE_CREDIT_INSTITUTION: Eligible credit institution counterparty (10% NAV limit).
    """

    STANDARD = "STANDARD"
    ELIGIBLE_CREDIT_INSTITUTION = "ELIGIBLE_CREDIT_INSTITUTION"


class UCITSOTCCounterpartyStatus(str, PyEnum):
    """Compliance status of OTC counterparty exposure vs. regulatory threshold.

    WITHIN_LIMIT: Counterparty exposure <= threshold (compliant).
    BREACH: Counterparty exposure > threshold (non-compliant).
    """

    WITHIN_LIMIT = "WITHIN_LIMIT"
    BREACH = "BREACH"


class UCITSOTCCounterpartyInput(BaseModel):
    """Input to UCITS OTC counterparty monitoring engine.

    Minimal input containing pre-computed OTC counterparty exposure for a fund snapshot.

    The engine will calculate exposure_ratio internally from exposure_amount and nav.
    No duplication of derived state.

    Fields:
    - fund_id: Fund identifier (string, e.g., "UCITS_Balanced").
    - valuation_date: Snapshot date (ISO 8601).
    - counterparty_id: Counterparty identifier (LEI or code).
    - counterparty_name: Counterparty name for audit trail (optional, not used in calculation).
    - nav: Net asset value at valuation date (positive Decimal, in base currency).
    - exposure_amount: Total exposure to counterparty (non-negative, positive monetary amount).
    - counterparty_category: Counterparty category for limit determination.

    Note: This engine monitors only OTC counterparty exposure under the UCITS framework.
    It does not value derivatives or aggregate positions.

    Invariants:
    - fund_id must be non-empty.
    - counterparty_id must be non-empty.
    - nav must be positive.
    - exposure_amount must be non-negative.
    - counterparty_category must be valid.
    """

    fund_id: str
    valuation_date: date
    counterparty_id: str
    counterparty_name: Optional[str] = None
    nav: Decimal
    exposure_amount: Decimal
    counterparty_category: UCITSCounterpartyCategory

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_id")
    @classmethod
    def validate_fund_id(cls, v: str) -> str:
        """Fund ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("fund_id must be non-empty")
        return v.strip()

    @field_validator("counterparty_id")
    @classmethod
    def validate_counterparty_id(cls, v: str) -> str:
        """Counterparty ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("counterparty_id must be non-empty")
        return v.strip()

    @field_validator("nav")
    @classmethod
    def validate_nav(cls, v: Decimal) -> Decimal:
        """NAV must be positive."""
        v = Decimal(str(v)) if not isinstance(v, Decimal) else v
        if v <= Decimal("0"):
            raise ValueError(f"nav must be positive, got {v}")
        return v

    @field_validator("exposure_amount")
    @classmethod
    def validate_exposure_amount(cls, v: Decimal) -> Decimal:
        """Exposure amount must be non-negative."""
        v = Decimal(str(v)) if not isinstance(v, Decimal) else v
        if v < Decimal("0"):
            raise ValueError(f"exposure_amount must be non-negative, got {v}")
        return v


class UCITSOTCCounterpartyResult(BaseModel):
    """Result of UCITS OTC counterparty exposure monitoring.

    Compares OTC counterparty exposure observation against a regulatory threshold ratio.

    All derived values are populated by the engine and stored for reporting
    convenience. This model is a simple immutable DTO with minimal defensive
    validation.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Snapshot date.
    - counterparty_id: Counterparty identifier.
    - counterparty_name: Counterparty name (audit only).
    - nav: Net asset value.
    - exposure_amount: Total exposure to counterparty.
    - exposure_ratio: Counterparty exposure as fraction of NAV (calculated).
    - limit_ratio: Regulatory limit as fraction (0.05 or 0.10, calculated).
    - limit_amount: Regulatory limit in base currency (calculated).
    - status: WITHIN_LIMIT or BREACH.
    - excess_amount: Amount by which exposure exceeds limit (calculated, >= 0).
    - excess_ratio: Ratio by which exposure exceeds limit (calculated, >= 0).
    - counterparty_category: Counterparty category (preserved).
    """

    fund_id: str
    valuation_date: date
    counterparty_id: str
    counterparty_name: Optional[str] = None
    nav: Decimal
    exposure_amount: Decimal
    exposure_ratio: Decimal
    limit_ratio: Decimal
    limit_amount: Decimal
    status: UCITSOTCCounterpartyStatus
    excess_amount: Decimal
    excess_ratio: Decimal
    counterparty_category: UCITSCounterpartyCategory

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

    @field_validator("exposure_amount", "excess_amount")
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
