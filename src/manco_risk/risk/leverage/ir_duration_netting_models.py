"""Interest-rate derivative duration netting models.

Pure models for linear interest-rate derivative records and duration-netting results.
Implements AIFMD Article 11 duration netting for Phase 1.

Scope (Phase 1):
- Linear interest-rate derivatives (swaps, FRAs, futures, forwards)
- Explicit maturity bucket assignment
- Duration-based netting grouping
- Auditable netting results

Does NOT include:
- Non-linear derivatives (swaptions, caps, floors, options)
- QuantLib pricing
- Greeks or delta calculations
- Automatic commitment reductions
"""

from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum

from pydantic import BaseModel, ConfigDict, field_validator


class InterestRateDerivativeDirection(str, PyEnum):
    """Direction of interest-rate derivative exposure.

    PAY_FIXED: pay fixed rate (exposed to falling rates, short rate exposure).
    RECEIVE_FIXED: receive fixed rate (exposed to rising rates, long rate exposure).
    LONG_RATE_EXPOSURE: directional long exposure to rate increases.
    SHORT_RATE_EXPOSURE: directional short exposure to rate decreases.
    """

    PAY_FIXED = "PAY_FIXED"
    RECEIVE_FIXED = "RECEIVE_FIXED"
    LONG_RATE_EXPOSURE = "LONG_RATE_EXPOSURE"
    SHORT_RATE_EXPOSURE = "SHORT_RATE_EXPOSURE"


class InterestRateMaturityBucket(str, PyEnum):
    """Maturity bucket for interest-rate derivatives.

    UP_TO_2Y: remaining maturity <= 2 years.
    TWO_TO_7Y: remaining maturity > 2 years and <= 7 years.
    OVER_7Y: remaining maturity > 7 years.

    Bucket assignment uses simple day-count: remaining_days / 365.
    """

    UP_TO_2Y = "UP_TO_2Y"
    TWO_TO_7Y = "TWO_TO_7Y"
    OVER_7Y = "OVER_7Y"


class LinearInterestRateDerivativeRecord(BaseModel):
    """Record of a linear interest-rate derivative.

    Fields:
    - derivative_id: unique identifier (non-empty).
    - currency: base currency (non-empty).
    - underlying_curve: interest rate curve name (non-empty).
    - maturity_date: derivative maturity/expiry date.
    - direction: rate exposure direction.
    - notional_base_ccy: notional amount in base currency (non-negative).
    - duration_equivalent_exposure_base_ccy: equivalent duration-adjusted exposure (non-negative).
    - description: optional human-readable description.

    Invariants:
    - derivative_id must be non-empty.
    - currency must be non-empty.
    - underlying_curve must be non-empty.
    - notional_base_ccy must be non-negative.
    - duration_equivalent_exposure_base_ccy must be non-negative.
    """

    derivative_id: str
    currency: str
    underlying_curve: str
    maturity_date: date
    direction: InterestRateDerivativeDirection
    notional_base_ccy: Decimal
    duration_equivalent_exposure_base_ccy: Decimal
    description: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("derivative_id")
    @classmethod
    def validate_derivative_id(cls, v: str) -> str:
        """Derivative ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("derivative_id must be non-empty")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Currency must be non-empty."""
        if not v or not v.strip():
            raise ValueError("currency must be non-empty")
        return v

    @field_validator("underlying_curve")
    @classmethod
    def validate_underlying_curve(cls, v: str) -> str:
        """Underlying curve must be non-empty."""
        if not v or not v.strip():
            raise ValueError("underlying_curve must be non-empty")
        return v

    @field_validator("notional_base_ccy")
    @classmethod
    def validate_notional(cls, v: Decimal) -> Decimal:
        """Notional must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"notional_base_ccy must be non-negative, got {v}")
        return v

    @field_validator("duration_equivalent_exposure_base_ccy")
    @classmethod
    def validate_duration_exposure(cls, v: Decimal) -> Decimal:
        """Duration exposure must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"duration_equivalent_exposure_base_ccy must be non-negative, got {v}")
        return v


class InterestRateDurationNettingInput(BaseModel):
    """Input to duration-netting calculation.

    Fields:
    - valuation_date: date for remaining maturity calculation.
    - records: list of IR derivative records to net (must be non-empty).

    Invariants:
    - records list must be non-empty.
    """

    valuation_date: date
    records: list[LinearInterestRateDerivativeRecord]

    model_config = ConfigDict(frozen=True)

    @field_validator("records")
    @classmethod
    def validate_records(cls, v: list[LinearInterestRateDerivativeRecord]) -> list:
        """Records list must be non-empty."""
        if not v:
            raise ValueError("records list must be non-empty")
        return v


class InterestRateNettingBucketResult(BaseModel):
    """Result of netting within a single maturity bucket.

    Fields:
    - currency: base currency.
    - underlying_curve: interest rate curve.
    - maturity_bucket: bucket classification.
    - long_exposure: total long exposure (RECEIVE_FIXED, LONG_RATE_EXPOSURE).
    - short_exposure: total short exposure (PAY_FIXED, SHORT_RATE_EXPOSURE).
    - net_exposure: |long - short| after netting.
    - reduction_amount: amount of exposure eliminated by netting.
    - record_ids: list of derivative IDs in this bucket (must be non-empty).

    Invariants:
    - exposures and reduction_amount must be non-negative.
    - record_ids must be non-empty.
    - net_exposure = |long_exposure - short_exposure|.
    - reduction_amount = min(long_exposure, short_exposure) * 2 or gross - net.
    """

    currency: str
    underlying_curve: str
    maturity_bucket: InterestRateMaturityBucket
    long_exposure: Decimal
    short_exposure: Decimal
    net_exposure: Decimal
    reduction_amount: Decimal
    record_ids: list[str]

    model_config = ConfigDict(frozen=True)

    @field_validator("long_exposure")
    @classmethod
    def validate_long_exposure(cls, v: Decimal) -> Decimal:
        """Long exposure must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"long_exposure must be non-negative, got {v}")
        return v

    @field_validator("short_exposure")
    @classmethod
    def validate_short_exposure(cls, v: Decimal) -> Decimal:
        """Short exposure must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"short_exposure must be non-negative, got {v}")
        return v

    @field_validator("net_exposure")
    @classmethod
    def validate_net_exposure(cls, v: Decimal) -> Decimal:
        """Net exposure must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"net_exposure must be non-negative, got {v}")
        return v

    @field_validator("reduction_amount")
    @classmethod
    def validate_reduction_amount(cls, v: Decimal) -> Decimal:
        """Reduction amount must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"reduction_amount must be non-negative, got {v}")
        return v

    @field_validator("record_ids")
    @classmethod
    def validate_record_ids(cls, v: list[str]) -> list[str]:
        """Record IDs must be non-empty."""
        if not v:
            raise ValueError("record_ids must be non-empty")
        return v


class InterestRateDurationNettingResult(BaseModel):
    """Result of interest-rate derivative duration netting.

    Fields:
    - valuation_date: date used for bucket assignment.
    - bucket_results: list of per-bucket netting results.
    - total_gross_exposure: sum of all long + short exposures.
    - total_net_exposure: sum of all net exposures after netting.
    - total_reduction_amount: sum of all reduction amounts.
    - non_nettable_records: derivatives excluded from netting with reasons.
    - warnings: processing warnings.

    Invariants:
    - all totals must be non-negative.
    - total_reduction_amount = total_gross_exposure - total_net_exposure.
    """

    valuation_date: date
    bucket_results: list[InterestRateNettingBucketResult]
    total_gross_exposure: Decimal
    total_net_exposure: Decimal
    total_reduction_amount: Decimal
    non_nettable_records: list[LinearInterestRateDerivativeRecord] = []
    warnings: list[str] = []

    model_config = ConfigDict(frozen=True)

    @field_validator("total_gross_exposure")
    @classmethod
    def validate_total_gross(cls, v: Decimal) -> Decimal:
        """Total gross exposure must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"total_gross_exposure must be non-negative, got {v}")
        return v

    @field_validator("total_net_exposure")
    @classmethod
    def validate_total_net(cls, v: Decimal) -> Decimal:
        """Total net exposure must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"total_net_exposure must be non-negative, got {v}")
        return v

    @field_validator("total_reduction_amount")
    @classmethod
    def validate_total_reduction(cls, v: Decimal) -> Decimal:
        """Total reduction amount must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"total_reduction_amount must be non-negative, got {v}")
        return v
