"""UCITS SRRI (Synthetic Risk and Reward Indicator) models.

Pure data models. No calculation or persistence logic.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class SRRIInput(BaseModel):
    """Input to SRRI calculation engine.

    Minimal input containing annualised volatility for a fund snapshot.

    The engine will map volatility to SRRI class (1-7) internally.
    No duplication of derived state.

    Fields:
    - fund_id: Fund identifier (string, e.g., "UCITS_Balanced").
    - valuation_date: Snapshot date (ISO 8601).
    - annualised_volatility: Annualised volatility as decimal (e.g., 0.15 = 15%).

    Invariants:
    - fund_id must be non-empty.
    - annualised_volatility must be non-negative.
    """

    fund_id: str
    valuation_date: date
    annualised_volatility: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_id")
    @classmethod
    def validate_fund_id(cls, v: str) -> str:
        """Fund ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("fund_id must be non-empty")
        return v.strip()

    @field_validator("annualised_volatility")
    @classmethod
    def validate_annualised_volatility(cls, v: Decimal) -> Decimal:
        """Annualised volatility must be non-negative."""
        v = Decimal(str(v)) if not isinstance(v, Decimal) else v
        if v < Decimal("0"):
            raise ValueError(f"annualised_volatility must be non-negative, got {v}")
        return v


class SRRIResult(BaseModel):
    """Result of SRRI calculation.

    Maps an annualised volatility observation to SRRI class (1-7).

    All fields are populated by the engine and stored for reporting convenience.
    This model is a simple immutable DTO with minimal defensive validation.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Snapshot date.
    - annualised_volatility: Annualised volatility as decimal.
    - srri_class: SRRI class 1-7 (calculated by engine).

    Invariants (defensive checks):
    - fund_id must be non-empty.
    - srri_class must be in [1, 7].
    """

    fund_id: str
    valuation_date: date
    annualised_volatility: Decimal
    srri_class: int

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_id")
    @classmethod
    def validate_fund_id(cls, v: str) -> str:
        """Fund ID must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("fund_id must be non-empty")
        return v.strip()

    @field_validator("annualised_volatility")
    @classmethod
    def validate_annualised_volatility(cls, v: Decimal) -> Decimal:
        """Annualised volatility must be non-negative (defensive check)."""
        if v < Decimal("0"):
            raise ValueError(f"annualised_volatility must be non-negative, got {v}")
        return v

    @field_validator("srri_class")
    @classmethod
    def validate_srri_class(cls, v: int) -> int:
        """SRRI class must be in [1, 7] (defensive check)."""
        if v < 1 or v > 7:
            raise ValueError(f"srri_class must be in [1, 7], got {v}")
        return v
