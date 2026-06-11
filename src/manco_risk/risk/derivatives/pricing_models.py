"""Derivative pricing models and interfaces.

Pure models for derivative pricing inputs and results.
Defines the contract for pricing implementations (QuantLib, manual, mock, etc.)

Scope (Phase 1):
- Input and result models for fair value and Greeks
- Interface definition
- Manual/mock pricer for testing

Does NOT include:
- QuantLib dependency
- Actual pricing calculations
- Market data loading
- Curve bootstrapping
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class DerivativePricingInput(BaseModel):
    """Input to a derivative pricing calculation.

    Fields:
    - derivative_id: unique identifier (non-empty).
    - pricing_date: date for which to price.
    - fair_value_base_ccy: fair value / NPV if available (optional, may be None initially).
    - delta: delta Greek if available (optional, may be positive/negative/zero).
    - gamma: gamma Greek if available (optional, may be positive/negative/zero).
    - vega: vega Greek if available (optional, may be positive/negative/zero).
    - dv01: DV01 (dollar value of 1 bps) if available (optional).
    - theta: theta Greek if available (optional, may be positive/negative/zero).
    - rho: rho Greek if available (optional, may be positive/negative/zero).
    - pricing_model: model name if available (optional, non-empty if provided).
    - warnings: processing warnings (optional, empty list default).

    Invariants:
    - derivative_id must be non-empty.
    - pricing_model, if provided, must be non-empty.
    - Greeks may be positive, zero, or negative (no constraint).
    - fair_value may be positive, zero, or negative (no constraint).
    """

    derivative_id: str
    pricing_date: date
    fair_value_base_ccy: Decimal | None = None
    delta: Decimal | None = None
    gamma: Decimal | None = None
    vega: Decimal | None = None
    dv01: Decimal | None = None
    theta: Decimal | None = None
    rho: Decimal | None = None
    pricing_model: str | None = None
    warnings: list[str] = []

    model_config = ConfigDict(frozen=True)

    @field_validator("derivative_id")
    @classmethod
    def validate_derivative_id(cls, v: str) -> str:
        """Derivative ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("derivative_id must be non-empty")
        return v

    @field_validator("pricing_model")
    @classmethod
    def validate_pricing_model(cls, v: str | None) -> str | None:
        """Pricing model, if provided, must be non-empty."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("pricing_model must be non-empty if provided")
        return v


class DerivativePricingResult(BaseModel):
    """Result of a derivative pricing calculation.

    Fields:
    - derivative_id: unique identifier (non-empty).
    - pricing_date: date used for pricing.
    - fair_value_base_ccy: fair value / NPV (required).
    - delta: delta Greek (optional, may be None if not applicable).
    - gamma: gamma Greek (optional, may be None if not applicable).
    - vega: vega Greek (optional, may be None if not applicable).
    - dv01: DV01 (optional, may be None if not applicable).
    - theta: theta Greek (optional, may be None if not applicable).
    - rho: rho Greek (optional, may be None if not applicable).
    - pricing_model: model used (non-empty).
    - warnings: processing warnings (optional, empty list default).

    Invariants:
    - derivative_id must be non-empty.
    - pricing_model must be non-empty.
    - fair_value_base_ccy is required and may be positive/zero/negative.
    - Greeks are optional (may be None) and may be positive/zero/negative when present.
    """

    derivative_id: str
    pricing_date: date
    fair_value_base_ccy: Decimal
    delta: Decimal | None = None
    gamma: Decimal | None = None
    vega: Decimal | None = None
    dv01: Decimal | None = None
    theta: Decimal | None = None
    rho: Decimal | None = None
    pricing_model: str
    warnings: list[str] = []

    model_config = ConfigDict(frozen=True)

    @field_validator("derivative_id")
    @classmethod
    def validate_derivative_id(cls, v: str) -> str:
        """Derivative ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("derivative_id must be non-empty")
        return v

    @field_validator("pricing_model")
    @classmethod
    def validate_pricing_model(cls, v: str) -> str:
        """Pricing model must be non-empty."""
        if not v or not v.strip():
            raise ValueError("pricing_model must be non-empty")
        return v
