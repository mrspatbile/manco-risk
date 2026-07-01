"""Infrastructure analytics models.

Domain models for infrastructure asset analysis, including debt service coverage
and leverage metrics.

No forecasting, valuation, or duration calculations performed in this module.
Models are immutable Pydantic v2 with ConfigDict(frozen=True).
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = [
    "InfrastructureAssetInput",
    "InfrastructureAnalyticsResult",
]


class InfrastructureAssetInput(BaseModel):
    """Input model for infrastructure asset analysis.

    Provides point-in-time financial data for an infrastructure asset:
    cash available for debt service, debt service obligations, asset value,
    and outstanding debt.

    No calculations performed. Input validation only.

    Attributes:
        valuation_date: date, snapshot date for the asset financial metrics.
        cash_available_for_debt_service: Decimal, non-negative. Cash reserves or
            revenue available to service debt in the current period.
        debt_service_amount: Decimal, non-negative. Principal + interest due
            in the current period.
        asset_value: Decimal, non-negative. Current valuation of the asset.
        debt_outstanding: Decimal, non-negative. Total outstanding debt.
        asset_id: str, optional. Asset identifier for reference.
    """

    valuation_date: date
    cash_available_for_debt_service: Decimal
    debt_service_amount: Decimal
    asset_value: Decimal
    debt_outstanding: Decimal
    asset_id: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("cash_available_for_debt_service")
    @classmethod
    def validate_cash_available_for_debt_service(cls, v: Decimal) -> Decimal:
        """Cash available for debt service must be non-negative."""
        if v < 0:
            raise ValueError("cash_available_for_debt_service must be non-negative")
        return v

    @field_validator("debt_service_amount")
    @classmethod
    def validate_debt_service_amount(cls, v: Decimal) -> Decimal:
        """Debt service amount must be non-negative."""
        if v < 0:
            raise ValueError("debt_service_amount must be non-negative")
        return v

    @field_validator("asset_value")
    @classmethod
    def validate_asset_value(cls, v: Decimal) -> Decimal:
        """Asset value must be non-negative."""
        if v < 0:
            raise ValueError("asset_value must be non-negative")
        return v

    @field_validator("debt_outstanding")
    @classmethod
    def validate_debt_outstanding(cls, v: Decimal) -> Decimal:
        """Debt outstanding must be non-negative."""
        if v < 0:
            raise ValueError("debt_outstanding must be non-negative")
        return v


class InfrastructureAnalyticsResult(BaseModel):
    """Immutable result model for infrastructure asset metrics.

    Contains point-in-time debt service coverage ratio (DSCR) and
    loan-to-value (LTV) ratio.

    All ratios are stored as Decimal with positive values (e.g., 1.2 = 120%).

    Attributes:
        asset_id: str, optional. Asset identifier from input.
        valuation_date: date, snapshot date for metrics.
        dscr: Decimal, Debt Service Coverage Ratio. None if debt_service_amount is zero.
        ltv: Decimal, Loan-to-Value ratio. None if asset_value is zero.
        cash_available_for_debt_service: Decimal, from input.
        debt_service_amount: Decimal, from input.
        asset_value: Decimal, from input.
        debt_outstanding: Decimal, from input.
    """

    asset_id: Optional[str] = None
    valuation_date: date
    dscr: Optional[Decimal] = None
    ltv: Optional[Decimal] = None
    cash_available_for_debt_service: Decimal
    debt_service_amount: Decimal
    asset_value: Decimal
    debt_outstanding: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("dscr")
    @classmethod
    def validate_dscr(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """DSCR must be non-negative."""
        if v is not None and v < 0:
            raise ValueError("dscr must be non-negative")
        return v

    @field_validator("ltv")
    @classmethod
    def validate_ltv(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """LTV must be non-negative."""
        if v is not None and v < 0:
            raise ValueError("ltv must be non-negative")
        return v
