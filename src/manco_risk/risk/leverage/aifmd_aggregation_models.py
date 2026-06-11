"""AIFMD leverage aggregation input and commitment reduction models.

Pure data models for AIFMD gross and commitment aggregation engines.
"""

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.leverage.cash_result import CashExposureResult
from manco_risk.risk.leverage.derivative_result import DerivativeExposureResult
from manco_risk.risk.leverage.direct_borrowing_result import DirectBorrowingExposureResult
from manco_risk.risk.leverage.physical_instrument_result import (
    PhysicalInstrumentExposureResult,
)
from manco_risk.risk.leverage.sft_result import SFTExposureResult


class CommitmentReductionType(str, Enum):
    """Type of commitment reduction.

    NETTING: Offset of opposite exposures with same underlying.
    HEDGING: Reduction from explicit hedging relationship.
    CURRENCY_HEDGING: FX hedge reducing currency exposure.
    OTHER: Other documented reduction type.
    """

    NETTING = "NETTING"
    HEDGING = "HEDGING"
    CURRENCY_HEDGING = "CURRENCY_HEDGING"
    OTHER = "OTHER"


class CommitmentReduction(BaseModel):
    """Explicit commitment reduction record.

    Used to apply netting, hedging, or other approved reductions to commitment
    method leverage exposure. Reductions are not inferred automatically;
    they must be explicitly provided and validated.

    Fields:
    - reduction_id: Unique identifier (non-empty).
    - reduction_type: Type of reduction.
    - source_position_id: Position identifier for source/protected position (optional).
    - source_derivative_id: Derivative identifier for source/protected derivative (optional).
    - target_position_id: Position identifier for target/hedged position (optional).
    - target_derivative_id: Derivative identifier for target/hedged derivative (optional).
    - underlying_identifier: Underlying asset identifier (ISIN, ticker, etc, optional).
    - asset_class: Asset class of reduction (optional).
    - reduction_amount: Amount to reduce exposure by (non-negative).
    - reason: Explanation of reduction (non-empty).
    - is_regulatory_eligible: Whether reduction is eligible under AIFMD rules.

    Invariants:
    - reduction_id must be non-empty.
    - reduction_amount must be non-negative.
    - reason must be non-empty.
    - At least one of source_position_id, source_derivative_id, target_position_id,
      target_derivative_id must be populated.
    """

    reduction_id: str
    reduction_type: CommitmentReductionType
    source_position_id: int | None = None
    source_derivative_id: str | None = None
    target_position_id: int | None = None
    target_derivative_id: str | None = None
    underlying_identifier: str | None = None
    asset_class: str | None = None
    reduction_amount: Decimal
    reason: str
    is_regulatory_eligible: bool

    model_config = ConfigDict(frozen=True)

    @field_validator("reduction_id")
    @classmethod
    def validate_reduction_id(cls, v: str) -> str:
        """Reduction ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("reduction_id must be non-empty")
        return v.strip()

    @field_validator("reduction_amount")
    @classmethod
    def validate_reduction_amount(cls, v: Decimal) -> Decimal:
        """Reduction amount must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"reduction_amount must be non-negative, got {v}")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """Reason must be non-empty."""
        if not v or not v.strip():
            raise ValueError("reason must be non-empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_source_or_target(self) -> "CommitmentReduction":
        """At least one source or target identifier must be populated."""
        has_source = self.source_position_id is not None or self.source_derivative_id is not None
        has_target = self.target_position_id is not None or self.target_derivative_id is not None

        if not (has_source or has_target):
            raise ValueError(
                "At least one of source_position_id, source_derivative_id, "
                "target_position_id, target_derivative_id must be populated"
            )

        return self


class AIFMDLeverageAggregationInput(BaseModel):
    """Input to AIFMD gross and commitment aggregation engines.

    Composes all source-layer results into aggregation inputs.

    Fields:
    - portfolio: Risk-ready portfolio with NAV for leverage ratio calculation.
    - physical_result: Physical instrument source result (optional).
    - cash_result: Cash and cash-equivalent source result (optional).
    - direct_borrowing_result: Direct borrowing source result (optional).
    - sft_result: Securities financing transaction source result (optional).
    - derivative_result: Derivative valuation and exposure result (optional).
    - commitment_reductions: Explicit commitment reductions to apply (default empty).

    Invariants:
    - portfolio.nav must be positive (inherited from RiskReadyPortfolio validation).
    - At least one source result should be provided (enforced in tests but not strictly required).
    """

    portfolio: RiskReadyPortfolio
    physical_result: PhysicalInstrumentExposureResult | None = None
    cash_result: CashExposureResult | None = None
    direct_borrowing_result: DirectBorrowingExposureResult | None = None
    sft_result: SFTExposureResult | None = None
    derivative_result: DerivativeExposureResult | None = None
    commitment_reductions: list[CommitmentReduction] = []

    model_config = ConfigDict(frozen=True)


class AIFMDCommitmentLeverageResult(BaseModel):
    """Result of AIFMD commitment aggregation with reduction audit trail.

    Wrapper around LeverageMethodResult to provide additional transparency
    for reductions applied and ignored.

    Fields:
    - method_result: Base leverage method result.
    - base_exposure_before_reductions: Total exposure before any reductions.
    - total_reductions: Sum of applied reductions.
    - final_exposure: Exposure after reductions (method_result.total_exposure).
    - applied_reductions: Reductions that were applied.
    - ignored_reductions: Reductions that were not applied (with reason).
    - warnings: Aggregation and reduction warnings.
    """

    method_result: "LeverageMethodResult"
    base_exposure_before_reductions: Decimal
    total_reductions: Decimal
    final_exposure: Decimal
    applied_reductions: list[CommitmentReduction]
    ignored_reductions: list[CommitmentReduction]
    warnings: list[str]

    model_config = ConfigDict(frozen=True)

    @field_validator("base_exposure_before_reductions")
    @classmethod
    def validate_base_exposure(cls, v: Decimal) -> Decimal:
        """Base exposure must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"base_exposure_before_reductions must be non-negative, got {v}")
        return v

    @field_validator("total_reductions")
    @classmethod
    def validate_total_reductions(cls, v: Decimal) -> Decimal:
        """Total reductions must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"total_reductions must be non-negative, got {v}")
        return v

    @field_validator("final_exposure")
    @classmethod
    def validate_final_exposure(cls, v: Decimal) -> Decimal:
        """Final exposure must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"final_exposure must be non-negative, got {v}")
        return v


# Import at end to avoid circular imports
from manco_risk.risk.leverage.models import LeverageMethodResult  # noqa: E402

AIFMDCommitmentLeverageResult.model_rebuild()
