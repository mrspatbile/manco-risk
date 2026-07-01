"""Infrastructure sensitivity analytics models.

Domain models for infrastructure asset duration and inflation sensitivity.

This slice consumes already-computed sensitivity measures from external sources.
No duration derivation, inflation estimation, or cash flow projection performed.

Models are immutable Pydantic v2 with ConfigDict(frozen=True).
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = [
    "InfrastructureSensitivityInput",
    "InfrastructureSensitivityResult",
]


class InfrastructureSensitivityInput(BaseModel):
    """Input model for infrastructure asset sensitivity analysis.

    Provides point-in-time duration and inflation/interest-rate sensitivity measures
    for an infrastructure asset.

    Duration and sensitivity measures are supplied from external analysis.
    No derivation or estimation performed in this module.

    Attributes:
        valuation_date: date, snapshot date for sensitivity metrics.
        duration_years: Decimal, non-negative. Effective duration in years.
            Represents weighted average time to cash flow receipt/obligation.
        inflation_sensitivity: Decimal. Sensitivity to inflation changes.
            Example: 0.75 = asset value changes 0.75% per 1% inflation increase.
        asset_id: str, optional. Asset identifier for reference.
        interest_rate_sensitivity: Decimal, optional. Sensitivity to interest rate changes.
            Example: -2.5 = asset value changes -2.5% per 1% interest rate increase.
        methodology_version: str, optional. Version identifier for sensitivity methodology.
    """

    valuation_date: date
    duration_years: Decimal
    inflation_sensitivity: Decimal
    asset_id: Optional[str] = None
    interest_rate_sensitivity: Optional[Decimal] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("duration_years")
    @classmethod
    def validate_duration_years(cls, v: Decimal) -> Decimal:
        """Duration must be non-negative."""
        if v < 0:
            raise ValueError("duration_years must be non-negative")
        return v

    @field_validator("interest_rate_sensitivity")
    @classmethod
    def validate_interest_rate_sensitivity(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Interest rate sensitivity must be valid Decimal when supplied."""
        if v is not None and not isinstance(v, Decimal):
            raise ValueError("interest_rate_sensitivity must be a Decimal")
        return v


class InfrastructureSensitivityResult(BaseModel):
    """Immutable result model for infrastructure asset sensitivity metrics.

    Packages duration and inflation/interest-rate sensitivity from supplied measures.
    No calculations performed; input data is validated and returned.

    Attributes:
        asset_id: str, optional. Asset identifier from input.
        valuation_date: date, snapshot date for metrics.
        duration_years: Decimal, non-negative. Effective duration in years.
        inflation_sensitivity: Decimal. Sensitivity to inflation.
        interest_rate_sensitivity: Decimal, optional. Sensitivity to interest rates.
        methodology_version: str, optional. Sensitivity methodology version.
    """

    asset_id: Optional[str] = None
    valuation_date: date
    duration_years: Decimal
    inflation_sensitivity: Decimal
    interest_rate_sensitivity: Optional[Decimal] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("duration_years")
    @classmethod
    def validate_duration_years(cls, v: Decimal) -> Decimal:
        """Duration must be non-negative."""
        if v < 0:
            raise ValueError("duration_years must be non-negative")
        return v

    @field_validator("interest_rate_sensitivity")
    @classmethod
    def validate_interest_rate_sensitivity(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Interest rate sensitivity must be valid when supplied."""
        if v is not None and not isinstance(v, Decimal):
            raise ValueError("interest_rate_sensitivity must be a Decimal")
        return v
