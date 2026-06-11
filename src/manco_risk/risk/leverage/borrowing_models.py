"""Direct borrowing input models and enums.

Pure data models for direct borrowing leverage source.
Separates unreinvested and reinvested borrowing for leverage exposure calculation.
"""

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class BorrowingPurpose(str, Enum):
    """Purpose or context for borrowing.

    LIQUIDITY_MANAGEMENT: Cash management, short-term liquidity needs.
    INVESTMENT_LEVERAGE: Borrowed cash invested to increase exposure.
    SETTLEMENT: Settlement of trades or redemptions.
    REDEMPTION_FINANCING: Financing redemptions or withdrawals.
    OTHER: Other purposes (explicit fallback).
    """

    LIQUIDITY_MANAGEMENT = "LIQUIDITY_MANAGEMENT"
    INVESTMENT_LEVERAGE = "INVESTMENT_LEVERAGE"
    SETTLEMENT = "SETTLEMENT"
    REDEMPTION_FINANCING = "REDEMPTION_FINANCING"
    OTHER = "OTHER"


class BorrowingTreatment(str, Enum):
    """Treatment status of borrowed amounts.

    UNREINVESTED: Borrowed amount remains as cash, not invested.
    REINVESTED: Entire borrowed amount has been invested.
    PARTIALLY_REINVESTED: Part of borrowed amount is invested, part is cash.
    """

    UNREINVESTED = "UNREINVESTED"
    REINVESTED = "REINVESTED"
    PARTIALLY_REINVESTED = "PARTIALLY_REINVESTED"


class BorrowingRecord(BaseModel):
    """Direct borrowing record for leverage source identification.

    Tracks borrowed amounts and how they are deployed.
    Separates unreinvested borrowing (cash) from reinvested borrowing (exposure).

    Fields:
    - borrowing_id: Unique borrowing identifier (non-empty).
    - currency: Borrowing currency (non-empty).
    - amount_base_ccy: Total borrowed amount in base currency (non-negative).
    - purpose: Borrowing purpose classification.
    - treatment: Whether borrowing is reinvested, unreinvested, or partially reinvested.
    - is_temporary: Whether this is temporary borrowing (e.g., overnight repo).
    - is_secured: Whether borrowing is collateralized.
    - reinvested_amount_base_ccy: Amount of borrowing that has been invested (non-negative).
    - description: Optional text description or reference.

    Invariants:
    - reinvested_amount_base_ccy <= amount_base_ccy
    - if treatment=UNREINVESTED, reinvested_amount_base_ccy must be 0
    - if treatment=REINVESTED, reinvested_amount_base_ccy must equal amount_base_ccy
    - if treatment=PARTIALLY_REINVESTED, 0 < reinvested_amount_base_ccy < amount_base_ccy
    """

    borrowing_id: str
    currency: str
    amount_base_ccy: Decimal
    purpose: BorrowingPurpose
    treatment: BorrowingTreatment
    is_temporary: bool
    is_secured: bool
    reinvested_amount_base_ccy: Decimal
    description: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("borrowing_id")
    @classmethod
    def validate_borrowing_id(cls, v: str) -> str:
        """Borrowing ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("borrowing_id must be non-empty")
        return v.strip()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Currency must be non-empty."""
        if not v or not v.strip():
            raise ValueError("currency must be non-empty")
        return v.strip()

    @field_validator("amount_base_ccy")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Amount must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"amount_base_ccy must be non-negative, got {v}")
        return v

    @field_validator("reinvested_amount_base_ccy")
    @classmethod
    def validate_reinvested_amount(cls, v: Decimal) -> Decimal:
        """Reinvested amount must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"reinvested_amount_base_ccy must be non-negative, got {v}")
        return v

    @model_validator(mode="after")
    def validate_reinvested_not_greater_than_amount(self) -> "BorrowingRecord":
        """Reinvested amount cannot exceed total amount."""
        if self.reinvested_amount_base_ccy > self.amount_base_ccy:
            raise ValueError(
                f"reinvested_amount_base_ccy ({self.reinvested_amount_base_ccy}) "
                f"cannot exceed amount_base_ccy ({self.amount_base_ccy})"
            )
        return self

    @model_validator(mode="after")
    def validate_treatment_consistency(self) -> "BorrowingRecord":
        """Validate treatment matches reinvested amount."""
        if self.treatment == BorrowingTreatment.UNREINVESTED:
            if self.reinvested_amount_base_ccy != Decimal("0"):
                raise ValueError(
                    f"UNREINVESTED treatment requires reinvested_amount_base_ccy=0, "
                    f"got {self.reinvested_amount_base_ccy}"
                )
        elif self.treatment == BorrowingTreatment.REINVESTED:
            if self.reinvested_amount_base_ccy != self.amount_base_ccy:
                raise ValueError(
                    f"REINVESTED treatment requires reinvested_amount_base_ccy={self.amount_base_ccy}, "
                    f"got {self.reinvested_amount_base_ccy}"
                )
        elif self.treatment == BorrowingTreatment.PARTIALLY_REINVESTED:
            if not (Decimal("0") < self.reinvested_amount_base_ccy < self.amount_base_ccy):
                raise ValueError(
                    f"PARTIALLY_REINVESTED treatment requires 0 < reinvested_amount_base_ccy < amount_base_ccy, "
                    f"got {self.reinvested_amount_base_ccy} / {self.amount_base_ccy}"
                )
        return self
