"""UCITS borrowing limit monitoring models.

Pure data models. No calculation or persistence logic.
"""

from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum

from pydantic import BaseModel, ConfigDict, field_validator


class UCITSBorrowingStatus(str, PyEnum):
    """Compliance status of direct borrowing vs. regulatory threshold.

    WITHIN_LIMIT: Borrowing <= threshold (compliant).
    BREACH: Borrowing > threshold (non-compliant).
    """

    WITHIN_LIMIT = "WITHIN_LIMIT"
    BREACH = "BREACH"


class UCITSBorrowingInput(BaseModel):
    """Input to UCITS borrowing limit monitoring engine.

    Minimal input containing direct borrowing observation for a fund snapshot.

    The engine will calculate borrowing_ratio internally from direct_borrowing_amount and nav.
    No duplication of derived state.

    Fields:
    - fund_id: Fund identifier (string, e.g., "UCITS_Balanced").
    - valuation_date: Snapshot date (ISO 8601).
    - nav: Net asset value at valuation date (positive Decimal, in base currency).
    - direct_borrowing_amount: Total direct borrowings (non-negative, positive monetary amount).

    Note: This engine monitors only direct borrowings under the UCITS framework.
    It does not infer borrowing from positions or derivative exposures.

    Invariants:
    - fund_id must be non-empty.
    - nav must be positive.
    - direct_borrowing_amount must be non-negative.
    """

    fund_id: str
    valuation_date: date
    nav: Decimal
    direct_borrowing_amount: Decimal

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

    @field_validator("direct_borrowing_amount")
    @classmethod
    def validate_direct_borrowing_amount(cls, v: Decimal) -> Decimal:
        """Direct borrowing amount must be non-negative."""
        v = Decimal(str(v)) if not isinstance(v, Decimal) else v
        if v < Decimal("0"):
            raise ValueError(f"direct_borrowing_amount must be non-negative, got {v}")
        return v


class UCITSBorrowingResult(BaseModel):
    """Result of UCITS borrowing limit monitoring.

    Compares direct borrowing observation against a regulatory threshold ratio.

    All derived values are populated by the engine and stored for reporting
    convenience. This model is a simple immutable DTO with minimal defensive
    validation.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Snapshot date.
    - nav: Net asset value.
    - direct_borrowing_amount: Total direct borrowings.
    - borrowing_ratio: Direct borrowing as fraction of NAV (calculated).
    - limit_ratio: Regulatory limit as fraction (0.10 = 10%).
    - limit_amount: Regulatory limit in base currency (calculated).
    - status: WITHIN_LIMIT or BREACH.
    - excess_amount: Amount by which borrowing exceeds limit (calculated, >= 0).
    - excess_ratio: Ratio by which borrowing exceeds limit (calculated, >= 0).
    """

    fund_id: str
    valuation_date: date
    nav: Decimal
    direct_borrowing_amount: Decimal
    borrowing_ratio: Decimal
    limit_ratio: Decimal
    limit_amount: Decimal
    status: UCITSBorrowingStatus
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

    @field_validator("direct_borrowing_amount", "excess_amount")
    @classmethod
    def validate_non_negative_amounts(cls, v: Decimal) -> Decimal:
        """Borrowing and excess amounts must be non-negative (defensive check)."""
        if v < Decimal("0"):
            raise ValueError(f"Borrowing and excess amounts must be non-negative, got {v}")
        return v

    @field_validator("borrowing_ratio", "excess_ratio")
    @classmethod
    def validate_non_negative_ratios(cls, v: Decimal) -> Decimal:
        """Borrowing and excess ratios must be non-negative (defensive check)."""
        if v < Decimal("0"):
            raise ValueError(f"Borrowing and excess ratios must be non-negative, got {v}")
        return v
