"""UCITS global exposure models.

Pure data models for UCITS global exposure measurement.
No calculation, persistence, or reporting logic.

UCITS global exposure is separate from AIFMD leverage.
Focus: derivative-based market exposure under commitment approach.
Limit: 100% of NAV (first pass, commitment method only).
"""

from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.leverage import CommitmentReduction, DerivativeExposureResult


class UCITSGlobalExposureMethod(str, PyEnum):
    """UCITS global exposure measurement method.

    COMMITMENT: Commitment approach (converts derivatives to equivalent positions).
    ABSOLUTE_VAR: Absolute VaR approach (future).
    RELATIVE_VAR: Relative VaR approach (future).
    """

    COMMITMENT = "COMMITMENT"
    ABSOLUTE_VAR = "ABSOLUTE_VAR"
    RELATIVE_VAR = "RELATIVE_VAR"


class UCITSGlobalExposureStatus(str, PyEnum):
    """UCITS global exposure status relative to limit.

    WITHIN_LIMIT: Global exposure ratio <= 1.0 (within 100% NAV limit).
    BREACH: Global exposure ratio > 1.0 (exceeds 100% NAV limit).
    NOT_ASSESSED: Result cannot be assessed (insufficient data).
    """

    WITHIN_LIMIT = "WITHIN_LIMIT"
    BREACH = "BREACH"
    NOT_ASSESSED = "NOT_ASSESSED"


class UCITSGlobalExposureInput(BaseModel):
    """Input to UCITS global exposure calculation.

    Fields:
    - portfolio: Fund portfolio with NAV reference.
    - derivative_result: Derivative exposure source result (optional, Phase 1).
    - eligible_reductions: Explicit commitment reductions to apply (optional, Phase 1).

    Invariants:
    - portfolio.nav must be positive (inherited from RiskReadyPortfolio).
    - derivative_result may be None in Phase 1 (returns zero global exposure).
    """

    portfolio: RiskReadyPortfolio
    derivative_result: DerivativeExposureResult | None = None
    eligible_reductions: list[CommitmentReduction] = []

    model_config = ConfigDict(frozen=True)


class UCITSGlobalExposureResult(BaseModel):
    """Result of UCITS global exposure measurement.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Valuation date for this snapshot.
    - method: UCITS global exposure method (COMMITMENT, ABSOLUTE_VAR, RELATIVE_VAR).
    - nav: Net asset value at valuation date.
    - global_exposure: Absolute global exposure amount.
    - global_exposure_ratio: Global exposure / NAV (as decimal, e.g., 0.85 = 85%).
    - limit_ratio: Regulatory limit ratio (1.0 = 100% for commitment approach).
    - status: WITHIN_LIMIT, BREACH, or NOT_ASSESSED.
    - source_contributions: Breakdown by leverage source (for audit).
    - unsupported_exposures: Derivatives without usable exposure data.
    - warnings: Processing warnings (e.g., missing data, calculation issues).

    Invariants:
    - nav must be positive.
    - global_exposure must be non-negative.
    - global_exposure_ratio must be non-negative.
    - limit_ratio must be positive.
    - status derived from global_exposure_ratio vs limit_ratio.
    """

    fund_id: int
    valuation_date: date
    method: UCITSGlobalExposureMethod
    nav: Decimal
    global_exposure: Decimal
    global_exposure_ratio: Decimal
    limit_ratio: Decimal
    status: UCITSGlobalExposureStatus
    source_contributions: list = []  # list[LeverageExposureSourceContribution] for audit
    unsupported_exposures: list = []  # list[UnsupportedLeverageExposure] for audit
    warnings: list[str] = []

    model_config = ConfigDict(frozen=True)

    @field_validator("nav")
    @classmethod
    def validate_nav(cls, v: Decimal) -> Decimal:
        """NAV must be positive."""
        if v <= Decimal("0"):
            raise ValueError(f"nav must be positive, got {v}")
        return v

    @field_validator("global_exposure")
    @classmethod
    def validate_global_exposure(cls, v: Decimal) -> Decimal:
        """Global exposure must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"global_exposure must be non-negative, got {v}")
        return v

    @field_validator("global_exposure_ratio")
    @classmethod
    def validate_global_exposure_ratio(cls, v: Decimal) -> Decimal:
        """Global exposure ratio must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"global_exposure_ratio must be non-negative, got {v}")
        return v

    @field_validator("limit_ratio")
    @classmethod
    def validate_limit_ratio(cls, v: Decimal) -> Decimal:
        """Limit ratio must be positive."""
        if v <= Decimal("0"):
            raise ValueError(f"limit_ratio must be positive, got {v}")
        return v
