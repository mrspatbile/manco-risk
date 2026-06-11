"""Leverage taxonomy and exposure source models.

Pure data models for leverage calculation inputs and outputs.
No calculation engines, persistence, or reporting logic.

Conventions:
- Monetary values and ratios stored as Decimal
- Leverage exposure is a positive magnitude
- Leverage ratio = exposure / NAV
- Unsupported exposure must be explicit with reason
- Excluded exposure must have reason; non-excluded must not have reason
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.leverage.enums import ExposureTreatment, LeverageMethod, LeverageSource


class UnsupportedLeverageExposure(BaseModel):
    """Unsupported exposure record.

    Tracks exposures that exist but are not yet supported by the leverage engine.

    Fields:
    - position_id: Optional internal position identifier.
    - isin: Optional ISIN identifier.
    - asset_class: Asset class name (non-empty).
    - source: Leverage source if identifiable, None if unknown.
    - reason: Non-empty explanation of why exposure is unsupported.
    """

    position_id: int | None = None
    isin: str | None = None
    asset_class: str
    source: LeverageSource | None = None
    reason: str

    model_config = ConfigDict(frozen=True)

    @field_validator("asset_class")
    @classmethod
    def validate_asset_class(cls, v: str) -> str:
        """Asset class must be non-empty."""
        if not v or not v.strip():
            raise ValueError("asset_class must be non-empty")
        return v.strip()

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """Reason must be non-empty."""
        if not v or not v.strip():
            raise ValueError("reason must be non-empty")
        return v.strip()


class LeverageExposureSourceContribution(BaseModel):
    """Raw source-level exposure building block.

    Represents exposure from a single leverage source before method-specific aggregation.

    Fields:
    - source: Leverage source classification.
    - gross_exposure: Absolute exposure amount (non-negative).
    - commitment_exposure: Commitment-method exposure (optional, non-negative).
    - treatment: Inclusion status (INCLUDED, EXCLUDED, UNSUPPORTED, PENDING_METHOD_RULE).
    - exclusion_reason: Required if treatment=EXCLUDED, None otherwise.
    """

    source: LeverageSource
    gross_exposure: Decimal
    commitment_exposure: Decimal | None = None
    treatment: ExposureTreatment
    exclusion_reason: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("gross_exposure")
    @classmethod
    def validate_gross_exposure(cls, v: Decimal) -> Decimal:
        """Gross exposure must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"gross_exposure must be non-negative, got {v}")
        return v

    @field_validator("commitment_exposure")
    @classmethod
    def validate_commitment_exposure(cls, v: Decimal | None) -> Decimal | None:
        """Commitment exposure, if provided, must be non-negative."""
        if v is not None and v < Decimal("0"):
            raise ValueError(f"commitment_exposure must be non-negative, got {v}")
        return v

    @model_validator(mode="after")
    def validate_exclusion_reason(self) -> "LeverageExposureSourceContribution":
        """Exclusion reason required if treatment=EXCLUDED, None otherwise."""
        if self.treatment == ExposureTreatment.EXCLUDED:
            if not self.exclusion_reason or not self.exclusion_reason.strip():
                raise ValueError("exclusion_reason must be non-empty when treatment=EXCLUDED")
        else:
            if self.exclusion_reason is not None:
                raise ValueError(f"exclusion_reason must be None when treatment={self.treatment}")
        return self


class LeveragePositionContribution(BaseModel):
    """Position-level leverage contribution.

    Fields:
    - position_id: Internal position identifier.
    - isin: Optional ISIN identifier.
    - position_name: Optional position name.
    - asset_class: Asset class (non-empty).
    - source: Leverage source.
    - treatment: Inclusion status.
    - market_value_base_ccy: Position market value in base currency.
    - raw_exposure: Pre-adjustment exposure amount (non-negative).
    - gross_exposure: Gross-method exposure (optional, non-negative).
    - commitment_exposure: Commitment-method exposure (optional, non-negative).
    - exclusion_reason: Required if treatment=EXCLUDED, None otherwise.
    """

    position_id: int
    isin: str | None = None
    position_name: str | None = None
    asset_class: str
    source: LeverageSource
    treatment: ExposureTreatment
    market_value_base_ccy: Decimal
    raw_exposure: Decimal
    gross_exposure: Decimal | None = None
    commitment_exposure: Decimal | None = None
    exclusion_reason: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("asset_class")
    @classmethod
    def validate_asset_class(cls, v: str) -> str:
        """Asset class must be non-empty."""
        if not v or not v.strip():
            raise ValueError("asset_class must be non-empty")
        return v.strip()

    @field_validator("raw_exposure")
    @classmethod
    def validate_raw_exposure(cls, v: Decimal) -> Decimal:
        """Raw exposure must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"raw_exposure must be non-negative, got {v}")
        return v

    @field_validator("gross_exposure")
    @classmethod
    def validate_gross_exposure(cls, v: Decimal | None) -> Decimal | None:
        """Gross exposure, if provided, must be non-negative."""
        if v is not None and v < Decimal("0"):
            raise ValueError(f"gross_exposure must be non-negative, got {v}")
        return v

    @field_validator("commitment_exposure")
    @classmethod
    def validate_commitment_exposure(cls, v: Decimal | None) -> Decimal | None:
        """Commitment exposure, if provided, must be non-negative."""
        if v is not None and v < Decimal("0"):
            raise ValueError(f"commitment_exposure must be non-negative, got {v}")
        return v

    @model_validator(mode="after")
    def validate_exclusion_reason(self) -> "LeveragePositionContribution":
        """Exclusion reason required if treatment=EXCLUDED, None otherwise."""
        if self.treatment == ExposureTreatment.EXCLUDED:
            if not self.exclusion_reason or not self.exclusion_reason.strip():
                raise ValueError("exclusion_reason must be non-empty when treatment=EXCLUDED")
        else:
            if self.exclusion_reason is not None:
                raise ValueError(f"exclusion_reason must be None when treatment={self.treatment}")
        return self


class LeverageInput(BaseModel):
    """Input to leverage calculation.

    Fields:
    - portfolio: Risk-ready portfolio.
    - methods: List of leverage methods to calculate (non-empty, no duplicates).
    """

    portfolio: RiskReadyPortfolio
    methods: list[LeverageMethod]

    model_config = ConfigDict(frozen=True)

    @field_validator("methods")
    @classmethod
    def validate_methods(cls, v: list[LeverageMethod]) -> list[LeverageMethod]:
        """Methods list must be non-empty with no duplicates."""
        if len(v) == 0:
            raise ValueError("methods list must be non-empty")
        if len(v) != len(set(v)):
            raise ValueError("methods list must not contain duplicates")
        return v


class LeverageMethodResult(BaseModel):
    """Leverage calculation result for a single method.

    Fields:
    - method: Leverage method.
    - nav: Net asset value (positive).
    - total_exposure: Total exposure for this method (non-negative).
    - leverage_ratio: Exposure / NAV (non-negative).
    - position_contributions: Exposure breakdown by position.
    - source_contributions: Exposure breakdown by source.
    - unsupported_exposures: Unsupported exposures found.
    - warnings: Processing warnings.
    """

    method: LeverageMethod
    nav: Decimal
    total_exposure: Decimal
    leverage_ratio: Decimal
    position_contributions: list[LeveragePositionContribution]
    source_contributions: list[LeverageExposureSourceContribution]
    unsupported_exposures: list[UnsupportedLeverageExposure]
    warnings: list[str]

    model_config = ConfigDict(frozen=True)

    @field_validator("nav")
    @classmethod
    def validate_nav(cls, v: Decimal) -> Decimal:
        """NAV must be positive."""
        if v <= Decimal("0"):
            raise ValueError(f"nav must be positive, got {v}")
        return v

    @field_validator("total_exposure")
    @classmethod
    def validate_total_exposure(cls, v: Decimal) -> Decimal:
        """Total exposure must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"total_exposure must be non-negative, got {v}")
        return v

    @field_validator("leverage_ratio")
    @classmethod
    def validate_leverage_ratio(cls, v: Decimal) -> Decimal:
        """Leverage ratio must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"leverage_ratio must be non-negative, got {v}")
        return v


class LeverageResult(BaseModel):
    """Overall leverage calculation result.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Date of valuation.
    - method_results: Results for each leverage method (non-empty, no duplicate methods).
    """

    fund_id: int
    valuation_date: date
    method_results: list[LeverageMethodResult]

    model_config = ConfigDict(frozen=True)

    @field_validator("method_results")
    @classmethod
    def validate_method_results(cls, v: list[LeverageMethodResult]) -> list[LeverageMethodResult]:
        """Method results list must be non-empty with no duplicate methods."""
        if len(v) == 0:
            raise ValueError("method_results list must be non-empty")
        methods = [mr.method for mr in v]
        if len(methods) != len(set(methods)):
            raise ValueError("method_results must not contain duplicate methods")
        return v
