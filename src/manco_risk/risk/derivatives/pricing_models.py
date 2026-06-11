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
from enum import Enum as PyEnum

from pydantic import BaseModel, ConfigDict, field_validator


class OptionType(str, PyEnum):
    """Option type: call or put.

    CALL: call option (right to buy).
    PUT: put option (right to sell).
    """

    CALL = "CALL"
    PUT = "PUT"


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


class EuropeanEquityOptionPricingInput(BaseModel):
    """Input for European equity option pricing via Black-Scholes-Merton.

    Fields:
    - derivative_id: unique identifier (non-empty).
    - pricing_date: date for which to price.
    - option_type: CALL or PUT.
    - spot: current underlying spot price (must be > 0).
    - strike: option strike price (must be > 0).
    - risk_free_rate: risk-free rate as decimal (e.g., 0.05 = 5%).
    - dividend_yield: dividend yield as decimal (default 0, may be negative).
    - volatility: annualized volatility as decimal (must be > 0, e.g., 0.20 = 20%).
    - maturity_date: option maturity/expiry date (must be > pricing_date).
    - quantity: number of contracts (default 1, must be non-zero).
    - currency: optional currency code (non-empty if provided).

    Invariants:
    - derivative_id must be non-empty.
    - spot must be positive.
    - strike must be positive.
    - volatility must be positive.
    - maturity_date must be after pricing_date.
    - quantity must be non-zero.
    - currency, if provided, must be non-empty.
    """

    derivative_id: str
    pricing_date: date
    option_type: OptionType
    spot: Decimal
    strike: Decimal
    risk_free_rate: Decimal
    dividend_yield: Decimal = Decimal("0")
    volatility: Decimal
    maturity_date: date
    quantity: Decimal = Decimal("1")
    currency: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("derivative_id")
    @classmethod
    def validate_derivative_id(cls, v: str) -> str:
        """Derivative ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("derivative_id must be non-empty")
        return v

    @field_validator("spot")
    @classmethod
    def validate_spot(cls, v: Decimal) -> Decimal:
        """Spot price must be positive."""
        if v <= Decimal("0"):
            raise ValueError(f"spot must be positive, got {v}")
        return v

    @field_validator("strike")
    @classmethod
    def validate_strike(cls, v: Decimal) -> Decimal:
        """Strike price must be positive."""
        if v <= Decimal("0"):
            raise ValueError(f"strike must be positive, got {v}")
        return v

    @field_validator("volatility")
    @classmethod
    def validate_volatility(cls, v: Decimal) -> Decimal:
        """Volatility must be positive."""
        if v <= Decimal("0"):
            raise ValueError(f"volatility must be positive, got {v}")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: Decimal) -> Decimal:
        """Quantity must be non-zero."""
        if v == Decimal("0"):
            raise ValueError("quantity must be non-zero")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Currency, if provided, must be non-empty."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("currency must be non-empty if provided")
        return v

    @field_validator("maturity_date")
    @classmethod
    def validate_maturity_date(cls, v: date, info) -> date:
        """Maturity date must be after pricing date."""
        pricing_date = info.data.get("pricing_date")
        if pricing_date and v <= pricing_date:
            raise ValueError(f"maturity_date {v} must be after pricing_date {pricing_date}")
        return v
