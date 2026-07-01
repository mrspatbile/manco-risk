"""Real estate stress analytics models.

Domain models for real estate property stress calculations under market shocks.

This slice calculates single-period stress outcomes only.
No multi-period forecasting, cap-rate modelling, or valuation performed.

Models are immutable Pydantic v2 with ConfigDict(frozen=True).
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = [
    "RealEstateStressInput",
    "RealEstateStressResult",
]


class RealEstateStressInput(BaseModel):
    """Input model for real estate stress analysis.

    Provides property financial data and stress shocks for single-period
    stress calculation.

    Attributes:
        valuation_date: date, snapshot date for stress calculation.
        property_value: Decimal, non-negative. Current property valuation.
        debt_outstanding: Decimal, non-negative. Mortgage or other debt.
        rental_income: Decimal, non-negative. Annual rental or operating income.
        operating_expenses: Decimal, non-negative. Annual operating expenses.
        value_shock: Decimal. Property value shock. Example: -0.20 = -20%.
        rental_income_shock: Decimal. Rental income shock. Example: -0.15 = -15%.
        expense_shock: Decimal, optional. Operating expense shock. Default 0.
            Example: 0.10 = +10% expenses.
        property_id: str, optional. Property identifier for reference.
        methodology_version: str, optional. Stress methodology version.
    """

    valuation_date: date
    property_value: Decimal
    debt_outstanding: Decimal
    rental_income: Decimal
    operating_expenses: Decimal
    value_shock: Decimal
    rental_income_shock: Decimal
    expense_shock: Decimal = Decimal("0")
    property_id: Optional[str] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("property_value")
    @classmethod
    def validate_property_value(cls, v: Decimal) -> Decimal:
        """Property value must be non-negative."""
        if v < 0:
            raise ValueError("property_value must be non-negative")
        return v

    @field_validator("debt_outstanding")
    @classmethod
    def validate_debt_outstanding(cls, v: Decimal) -> Decimal:
        """Debt outstanding must be non-negative."""
        if v < 0:
            raise ValueError("debt_outstanding must be non-negative")
        return v

    @field_validator("rental_income")
    @classmethod
    def validate_rental_income(cls, v: Decimal) -> Decimal:
        """Rental income must be non-negative."""
        if v < 0:
            raise ValueError("rental_income must be non-negative")
        return v

    @field_validator("operating_expenses")
    @classmethod
    def validate_operating_expenses(cls, v: Decimal) -> Decimal:
        """Operating expenses must be non-negative."""
        if v < 0:
            raise ValueError("operating_expenses must be non-negative")
        return v


class RealEstateStressResult(BaseModel):
    """Immutable result model for real estate stress analysis.

    Contains stressed property value, NOI, and LTV under market shocks.

    Attributes:
        property_id: str, optional. Property identifier from input.
        valuation_date: date, snapshot date for stress calculation.
        stressed_property_value: Decimal, property value after shock.
        stressed_rental_income: Decimal, rental income after shock.
        stressed_operating_expenses: Decimal, operating expenses after shock.
        stressed_noi: Decimal, Net Operating Income after shocks.
        stressed_ltv: Decimal | None, Loan-to-Value after shock. None if
            stressed_property_value is zero.
        debt_outstanding: Decimal, from input.
        methodology_version: str, optional. Methodology version.
    """

    property_id: Optional[str] = None
    valuation_date: date
    stressed_property_value: Decimal
    stressed_rental_income: Decimal
    stressed_operating_expenses: Decimal
    stressed_noi: Decimal
    stressed_ltv: Optional[Decimal] = None
    debt_outstanding: Decimal
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("stressed_property_value")
    @classmethod
    def validate_stressed_property_value(cls, v: Decimal) -> Decimal:
        """Stressed property value must be non-negative."""
        if v < 0:
            raise ValueError("stressed_property_value must be non-negative")
        return v

    @field_validator("stressed_rental_income")
    @classmethod
    def validate_stressed_rental_income(cls, v: Decimal) -> Decimal:
        """Stressed rental income must be non-negative."""
        if v < 0:
            raise ValueError("stressed_rental_income must be non-negative")
        return v

    @field_validator("stressed_operating_expenses")
    @classmethod
    def validate_stressed_operating_expenses(cls, v: Decimal) -> Decimal:
        """Stressed operating expenses must be non-negative."""
        if v < 0:
            raise ValueError("stressed_operating_expenses must be non-negative")
        return v

    @field_validator("debt_outstanding")
    @classmethod
    def validate_debt_outstanding(cls, v: Decimal) -> Decimal:
        """Debt outstanding must be non-negative."""
        if v < 0:
            raise ValueError("debt_outstanding must be non-negative")
        return v

    @field_validator("stressed_ltv")
    @classmethod
    def validate_stressed_ltv(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Stressed LTV must be non-negative."""
        if v is not None and v < 0:
            raise ValueError("stressed_ltv must be non-negative")
        return v
