"""Derivative pricing to exposure conversion models.

Pure models for converting pricing results (fair value, Greeks) into
leverage exposure records.

Scope:
- Input and result models for option exposure conversion
- Delta-adjusted exposure computation

Does NOT include:
- QuantLib dependency
- Pricing calculations
- Database access
- Persistence
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.risk.derivatives.pricing_models import DerivativePricingResult
from manco_risk.risk.leverage.derivative_models import (
    DerivativeRecord,
)


class OptionExposureConversionInput(BaseModel):
    """Input for converting option pricing result to exposure.

    Fields:
    - derivative_id: unique derivative identifier (non-empty).
    - pricing_result: pricing result with fair value and Greeks.
    - underlying_identifier: reference to underlying (ISIN, ticker, optional).
    - underlying_spot: current underlying spot price (must be > 0).
    - quantity: number of contracts / units (must be non-zero).
    - contract_multiplier: multiplier for contract size (default 1, must be > 0).
    - currency: derivative currency (non-empty).
    - description: optional text description.

    Invariants:
    - derivative_id must be non-empty.
    - underlying_spot must be positive.
    - quantity must be non-zero (can be negative for short positions).
    - contract_multiplier must be positive.
    - currency must be non-empty.
    - pricing_result.delta must be provided (conversion fails if None).
    """

    derivative_id: str
    pricing_result: DerivativePricingResult
    underlying_identifier: str | None = None
    underlying_spot: Decimal
    quantity: Decimal
    contract_multiplier: Decimal = Decimal("1")
    currency: str
    description: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("derivative_id")
    @classmethod
    def validate_derivative_id(cls, v: str) -> str:
        """Derivative ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("derivative_id must be non-empty")
        return v.strip()

    @field_validator("underlying_spot")
    @classmethod
    def validate_underlying_spot(cls, v: Decimal) -> Decimal:
        """Underlying spot must be positive."""
        if v <= Decimal("0"):
            raise ValueError(f"underlying_spot must be positive, got {v}")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: Decimal) -> Decimal:
        """Quantity must be non-zero."""
        if v == Decimal("0"):
            raise ValueError("quantity must be non-zero")
        return v

    @field_validator("contract_multiplier")
    @classmethod
    def validate_contract_multiplier(cls, v: Decimal) -> Decimal:
        """Contract multiplier must be positive."""
        if v <= Decimal("0"):
            raise ValueError(f"contract_multiplier must be positive, got {v}")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Currency must be non-empty."""
        if not v or not v.strip():
            raise ValueError("currency must be non-empty")
        return v.strip()

    @field_validator("underlying_identifier")
    @classmethod
    def validate_underlying_identifier(cls, v: str | None) -> str | None:
        """Underlying identifier, if provided, must be non-empty."""
        if v is not None and not v.strip():
            raise ValueError("underlying_identifier must be non-empty if provided")
        return v.strip() if v else None


class OptionExposureConversionResult(BaseModel):
    """Result of option exposure conversion.

    Fields:
    - derivative_record: complete derivative record for leverage engine.
    - delta_adjusted_exposure_base_ccy: computed delta-adjusted exposure.
    - fair_value_base_ccy: fair value from pricing result.
    - warnings: processing or data quality warnings.
    """

    derivative_record: DerivativeRecord
    delta_adjusted_exposure_base_ccy: Decimal
    fair_value_base_ccy: Decimal
    warnings: list[str] = []

    model_config = ConfigDict(frozen=True)

    @field_validator("delta_adjusted_exposure_base_ccy")
    @classmethod
    def validate_delta_adjusted_exposure(cls, v: Decimal) -> Decimal:
        """Delta-adjusted exposure must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"delta_adjusted_exposure_base_ccy must be non-negative, got {v}")
        return v

    @field_validator("fair_value_base_ccy")
    @classmethod
    def validate_fair_value(cls, v: Decimal) -> Decimal:
        """Fair value can be any decimal (positive, negative, zero)."""
        return v
