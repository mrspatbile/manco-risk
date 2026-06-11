"""Derivative valuation and exposure input models and enums.

Pure data models for derivative leverage source.
Separates fair value (NAV basis) from exposure (leverage basis).
No pricing, Greeks, or valuation methodology included.
"""

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class DerivativeType(str, Enum):
    """Type of derivative instrument.

    FUTURE: Futures contract.
    FORWARD: Forward contract.
    OPTION: Option (call or put).
    SWAP: Swap (interest rate, currency, etc).
    FX_FORWARD: FX forward contract.
    CFD: Contract for difference.
    WARRANT: Warrant.
    OTHER: Other derivative type.
    """

    FUTURE = "FUTURE"
    FORWARD = "FORWARD"
    OPTION = "OPTION"
    SWAP = "SWAP"
    FX_FORWARD = "FX_FORWARD"
    CFD = "CFD"
    WARRANT = "WARRANT"
    OTHER = "OTHER"


class DerivativePayoffType(str, Enum):
    """Payoff characteristic of derivative.

    LINEAR: Linear payoff (futures, forwards, swaps).
    NON_LINEAR: Non-linear payoff (options, warrants).
    OTHER: Other payoff structure.
    """

    LINEAR = "LINEAR"
    NON_LINEAR = "NON_LINEAR"
    OTHER = "OTHER"


class DerivativeValuationSource(str, Enum):
    """Source of derivative valuation (fair value).

    PROVIDED_MARKET_VALUE: Market-quoted value.
    PROVIDED_MODEL_VALUE: Model-computed value.
    FUTURE_PRICER: To be computed by future pricing engine (QuantLib, etc).
    UNKNOWN: Source unknown.
    """

    PROVIDED_MARKET_VALUE = "PROVIDED_MARKET_VALUE"
    PROVIDED_MODEL_VALUE = "PROVIDED_MODEL_VALUE"
    FUTURE_PRICER = "FUTURE_PRICER"
    UNKNOWN = "UNKNOWN"


class DerivativeExposureSource(str, Enum):
    """Source of derivative exposure (leverage basis).

    PROVIDED_NOTIONAL: Notional amount provided.
    PROVIDED_EQUIVALENT_UNDERLYING: Equivalent underlying exposure provided.
    PROVIDED_DELTA_ADJUSTED: Delta-adjusted (or equivalent) exposure provided.
    FUTURE_CONVERTER: To be computed by future converter (QuantLib Greeks, etc).
    UNKNOWN: Source unknown.
    """

    PROVIDED_NOTIONAL = "PROVIDED_NOTIONAL"
    PROVIDED_EQUIVALENT_UNDERLYING = "PROVIDED_EQUIVALENT_UNDERLYING"
    PROVIDED_DELTA_ADJUSTED = "PROVIDED_DELTA_ADJUSTED"
    FUTURE_CONVERTER = "FUTURE_CONVERTER"
    UNKNOWN = "UNKNOWN"


class DerivativeValuation(BaseModel):
    """Fair value and valuation context for derivative.

    Used for NAV basis, not for leverage exposure.

    Fields:
    - fair_value_base_ccy: Market or model value in base currency.
      Can be positive, zero, or negative.
    - valuation_source: Source of valuation.
    - pricing_model: Name of pricing model if applicable (non-empty if provided).
    - valuation_date: Date of valuation snapshot (optional).
    """

    fair_value_base_ccy: Decimal
    valuation_source: DerivativeValuationSource
    pricing_model: str | None = None
    valuation_date: date | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("pricing_model")
    @classmethod
    def validate_pricing_model(cls, v: str | None) -> str | None:
        """Pricing model, if provided, must be non-empty."""
        if v is not None and not v.strip():
            raise ValueError("pricing_model must be non-empty if provided")
        return v.strip() if v else None


class DerivativeExposure(BaseModel):
    """Exposure representation for derivative (leverage basis).

    Provides multiple ways to express exposure; engine selects in priority order.
    Fair value is NOT used as exposure.

    Fields:
    - notional_base_ccy: Notional amount in base currency (optional, non-negative).
    - equivalent_underlying_exposure_base_ccy: Underlying exposure equivalence (optional, non-negative).
    - delta_adjusted_exposure_base_ccy: Delta-adjusted or equivalent exposure (optional, non-negative).
    - exposure_source: Source of exposure representation.

    Invariants:
    - Any provided exposure must be non-negative.
    - At least one exposure field should be provided unless exposure_source is UNKNOWN.
    - If exposure_source is UNKNOWN, no exposure fields need to be provided.
    """

    notional_base_ccy: Decimal | None = None
    equivalent_underlying_exposure_base_ccy: Decimal | None = None
    delta_adjusted_exposure_base_ccy: Decimal | None = None
    exposure_source: DerivativeExposureSource

    model_config = ConfigDict(frozen=True)

    @field_validator("notional_base_ccy")
    @classmethod
    def validate_notional(cls, v: Decimal | None) -> Decimal | None:
        """Notional, if provided, must be non-negative."""
        if v is not None and v < Decimal("0"):
            raise ValueError(f"notional_base_ccy must be non-negative, got {v}")
        return v

    @field_validator("equivalent_underlying_exposure_base_ccy")
    @classmethod
    def validate_equivalent_underlying(cls, v: Decimal | None) -> Decimal | None:
        """Equivalent underlying exposure, if provided, must be non-negative."""
        if v is not None and v < Decimal("0"):
            raise ValueError(
                f"equivalent_underlying_exposure_base_ccy must be non-negative, got {v}"
            )
        return v

    @field_validator("delta_adjusted_exposure_base_ccy")
    @classmethod
    def validate_delta_adjusted(cls, v: Decimal | None) -> Decimal | None:
        """Delta-adjusted exposure, if provided, must be non-negative."""
        if v is not None and v < Decimal("0"):
            raise ValueError(f"delta_adjusted_exposure_base_ccy must be non-negative, got {v}")
        return v

    @model_validator(mode="after")
    def validate_exposure_provided(self) -> "DerivativeExposure":
        """Validate that at least one exposure field is provided unless source is UNKNOWN."""
        has_exposure = (
            self.notional_base_ccy is not None
            or self.equivalent_underlying_exposure_base_ccy is not None
            or self.delta_adjusted_exposure_base_ccy is not None
        )

        if (
            self.exposure_source != DerivativeExposureSource.UNKNOWN
            and self.exposure_source != DerivativeExposureSource.FUTURE_CONVERTER
            and not has_exposure
        ):
            raise ValueError(
                f"At least one exposure field must be provided "
                f"when exposure_source is {self.exposure_source}"
            )

        return self


class DerivativeRecord(BaseModel):
    """Derivative record for leverage source identification.

    Position-independent record of a derivative holding or position.
    Contains both valuation (for NAV) and exposure (for leverage).

    Fields:
    - derivative_id: Unique derivative identifier (non-empty).
    - derivative_type: Type of derivative.
    - payoff_type: Payoff characteristic.
    - underlying_identifier: Reference to underlying (ISIN, ticker, etc, optional).
    - currency: Derivative currency (non-empty).
    - valuation: Fair value and valuation context.
    - exposure: Exposure representation.
    - description: Optional text description.
    """

    derivative_id: str
    derivative_type: DerivativeType
    payoff_type: DerivativePayoffType
    underlying_identifier: str | None
    currency: str
    valuation: DerivativeValuation
    exposure: DerivativeExposure
    description: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("derivative_id")
    @classmethod
    def validate_derivative_id(cls, v: str) -> str:
        """Derivative ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("derivative_id must be non-empty")
        return v.strip()

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
