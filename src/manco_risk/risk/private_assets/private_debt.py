"""Private debt analytics models.

Domain models for private debt loan monitoring and covenant tracking.

This slice packages already-computed monitoring metrics and calculates loan-to-value.
No covenant ratio calculation, borrower cash flow projection, or credit analysis performed.

Models are immutable Pydantic v2 with ConfigDict(frozen=True).
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = [
    "PrivateDebtLoanInput",
    "PrivateDebtLoanResult",
]


class PrivateDebtLoanInput(BaseModel):
    """Input model for private debt loan monitoring.

    Provides loan financial metrics and covenant status for a single loan.

    Attributes:
        valuation_date: date, snapshot date for loan metrics.
        outstanding_balance: Decimal, non-negative. Current loan balance owed.
        collateral_value: Decimal, optional, non-negative. Market value of collateral.
        interest_coverage_ratio: Decimal, optional, non-negative. EBITDA / interest expense.
        debt_service_coverage_ratio: Decimal, optional, non-negative. Cash flow / debt service.
        leverage_ratio: Decimal, optional, non-negative. Debt / EBITDA or similar.
        covenant_breached: bool, required. Whether any covenant is currently breached.
        loan_id: str, optional. Loan identifier for reference.
        covenant_name: str, optional, non-empty when supplied. Name of breached covenant.
        methodology_version: str, optional. Monitoring methodology version.
    """

    valuation_date: date
    outstanding_balance: Decimal
    covenant_breached: bool
    collateral_value: Optional[Decimal] = None
    interest_coverage_ratio: Optional[Decimal] = None
    debt_service_coverage_ratio: Optional[Decimal] = None
    leverage_ratio: Optional[Decimal] = None
    loan_id: Optional[str] = None
    covenant_name: Optional[str] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("outstanding_balance")
    @classmethod
    def validate_outstanding_balance(cls, v: Decimal) -> Decimal:
        """Outstanding balance must be non-negative."""
        if v < 0:
            raise ValueError("outstanding_balance must be non-negative")
        return v

    @field_validator("collateral_value")
    @classmethod
    def validate_collateral_value(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Collateral value must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("collateral_value must be non-negative")
        return v

    @field_validator("interest_coverage_ratio")
    @classmethod
    def validate_interest_coverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Interest coverage ratio must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("interest_coverage_ratio must be non-negative")
        return v

    @field_validator("debt_service_coverage_ratio")
    @classmethod
    def validate_debt_service_coverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Debt service coverage ratio must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("debt_service_coverage_ratio must be non-negative")
        return v

    @field_validator("leverage_ratio")
    @classmethod
    def validate_leverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Leverage ratio must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("leverage_ratio must be non-negative")
        return v

    @field_validator("covenant_name")
    @classmethod
    def validate_covenant_name(cls, v: Optional[str]) -> Optional[str]:
        """Covenant name must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("covenant_name must be non-empty")
        return v.strip() if v else None


class PrivateDebtLoanResult(BaseModel):
    """Immutable result model for private debt loan monitoring.

    Packages loan metrics and covenant status with calculated loan-to-value.

    Attributes:
        loan_id: str, optional. Loan identifier from input.
        valuation_date: date, snapshot date for metrics.
        outstanding_balance: Decimal, from input.
        collateral_value: Decimal, optional, from input.
        loan_to_value: Decimal | None, calculated from outstanding_balance / collateral_value.
            None if collateral_value is None or zero.
        interest_coverage_ratio: Decimal, optional, from input.
        debt_service_coverage_ratio: Decimal, optional, from input.
        leverage_ratio: Decimal, optional, from input.
        covenant_breached: bool, from input.
        covenant_name: str, optional, from input.
        methodology_version: str, optional, from input.
    """

    loan_id: Optional[str] = None
    valuation_date: date
    outstanding_balance: Decimal
    covenant_breached: bool
    collateral_value: Optional[Decimal] = None
    loan_to_value: Optional[Decimal] = None
    interest_coverage_ratio: Optional[Decimal] = None
    debt_service_coverage_ratio: Optional[Decimal] = None
    leverage_ratio: Optional[Decimal] = None
    covenant_name: Optional[str] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("outstanding_balance")
    @classmethod
    def validate_outstanding_balance(cls, v: Decimal) -> Decimal:
        """Outstanding balance must be non-negative."""
        if v < 0:
            raise ValueError("outstanding_balance must be non-negative")
        return v

    @field_validator("collateral_value")
    @classmethod
    def validate_collateral_value(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Collateral value must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("collateral_value must be non-negative")
        return v

    @field_validator("loan_to_value")
    @classmethod
    def validate_loan_to_value(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Loan-to-value must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("loan_to_value must be non-negative")
        return v

    @field_validator("interest_coverage_ratio")
    @classmethod
    def validate_interest_coverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Interest coverage ratio must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("interest_coverage_ratio must be non-negative")
        return v

    @field_validator("debt_service_coverage_ratio")
    @classmethod
    def validate_debt_service_coverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Debt service coverage ratio must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("debt_service_coverage_ratio must be non-negative")
        return v

    @field_validator("leverage_ratio")
    @classmethod
    def validate_leverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Leverage ratio must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("leverage_ratio must be non-negative")
        return v
