"""Leverage limit monitoring models and enums.

Pure models for limit definition, observation, and checking results.
No calculation, persistence, or reporting logic.

Limit monitoring is separate from leverage calculation.
Calculation engines (MRS-157 to MRS-165) produce metrics.
Limit monitoring (MRS-166) checks those metrics against limits.
"""

from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum

from pydantic import BaseModel, ConfigDict, field_validator


class LimitSource(str, PyEnum):
    """Origin of a leverage limit.

    REGULATORY: hard rule from law/regulation (e.g., AIFMD Article 25).
    REGULATOR_IMPOSED: fund/manager-specific restriction (CSSF/NCA).
    FUND_DOCUMENT: prospectus, LPA, fund rules, constitutional docs.
    INTERNAL: ManCo/risk policy, internal monitoring threshold.
    """

    REGULATORY = "REGULATORY"
    REGULATOR_IMPOSED = "REGULATOR_IMPOSED"
    FUND_DOCUMENT = "FUND_DOCUMENT"
    INTERNAL = "INTERNAL"


class LimitType(str, PyEnum):
    """Classification of limit enforcement strength.

    HARD_LIMIT: violation is breach (firm compliance requirement).
    WARNING_THRESHOLD: violation triggers warning (early alert).
    ESCALATION_THRESHOLD: violation triggers escalation (governance review).
    """

    HARD_LIMIT = "HARD_LIMIT"
    WARNING_THRESHOLD = "WARNING_THRESHOLD"
    ESCALATION_THRESHOLD = "ESCALATION_THRESHOLD"


class LimitMetric(str, PyEnum):
    """Metric that is subject to limit monitoring.

    AIFMD_GROSS_LEVERAGE: AIFMD gross leverage ratio.
    AIFMD_COMMITMENT_LEVERAGE: AIFMD commitment leverage ratio.
    LOAN_ORIGINATING_AIF_COMMITMENT_LEVERAGE: AIFMD commitment for loan-orig AIFs.
    UCITS_GLOBAL_EXPOSURE: UCITS global exposure (commitment approach).
    DIRECT_BORROWING: direct borrowing exposure (standalone).
    DERIVATIVE_EXPOSURE: derivative exposure (standalone).
    SFT_EXPOSURE: securities financing transaction exposure (standalone).
    """

    AIFMD_GROSS_LEVERAGE = "AIFMD_GROSS_LEVERAGE"
    AIFMD_COMMITMENT_LEVERAGE = "AIFMD_COMMITMENT_LEVERAGE"
    LOAN_ORIGINATING_AIF_COMMITMENT_LEVERAGE = "LOAN_ORIGINATING_AIF_COMMITMENT_LEVERAGE"
    UCITS_GLOBAL_EXPOSURE = "UCITS_GLOBAL_EXPOSURE"
    DIRECT_BORROWING = "DIRECT_BORROWING"
    DERIVATIVE_EXPOSURE = "DERIVATIVE_EXPOSURE"
    SFT_EXPOSURE = "SFT_EXPOSURE"


class LimitStatus(str, PyEnum):
    """Status of a metric relative to its limit.

    WITHIN_LIMIT: metric within acceptable range.
    WARNING: metric breaches warning threshold.
    BREACH: metric breaches hard limit.
    NOT_ASSESSED: cannot assess (no observation available).
    """

    WITHIN_LIMIT = "WITHIN_LIMIT"
    WARNING = "WARNING"
    BREACH = "BREACH"
    NOT_ASSESSED = "NOT_ASSESSED"


class LimitDirection(str, PyEnum):
    """Direction of limit constraint.

    MAXIMUM: metric must not exceed threshold (e.g., leverage <= 2.0).
    MINIMUM: metric must meet or exceed threshold (e.g., capital >= 0.08).
    """

    MAXIMUM = "MAXIMUM"
    MINIMUM = "MINIMUM"


class LimitDefinition(BaseModel):
    """Definition of a leverage limit.

    Fields:
    - limit_id: unique identifier (non-empty).
    - metric: which metric is subject to the limit.
    - source: where the limit originates (regulatory, regulator, fund doc, internal).
    - limit_type: HARD_LIMIT, WARNING_THRESHOLD, or ESCALATION_THRESHOLD.
    - direction: MAXIMUM (metric <= threshold) or MINIMUM (metric >= threshold).
    - threshold: limit value (non-negative Decimal).
    - description: optional explanation.
    - is_active: whether this limit is currently enforced.

    Invariants:
    - limit_id must be non-empty.
    - threshold must be non-negative.
    - description, if provided, must be non-empty.
    """

    limit_id: str
    metric: LimitMetric
    source: LimitSource
    limit_type: LimitType
    direction: LimitDirection
    threshold: Decimal
    description: str | None = None
    is_active: bool = True

    model_config = ConfigDict(frozen=True)

    @field_validator("limit_id")
    @classmethod
    def validate_limit_id(cls, v: str) -> str:
        """Limit ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("limit_id must be non-empty")
        return v

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, v: Decimal) -> Decimal:
        """Threshold must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"threshold must be non-negative, got {v}")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Description, if provided, must be non-empty."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("description must be non-empty if provided")
        return v


class MetricObservation(BaseModel):
    """Observed value of a metric at a point in time.

    Fields:
    - metric: which metric is being observed.
    - value: observed metric value (non-negative Decimal).
    - fund_id: fund identifier.
    - valuation_date: date of observation.
    - source_reference: optional reference to calculation source (e.g., calculation run ID).

    Invariants:
    - value must be non-negative.
    - source_reference, if provided, must be non-empty.
    """

    metric: LimitMetric
    value: Decimal
    fund_id: int
    valuation_date: date
    source_reference: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Decimal) -> Decimal:
        """Metric value must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"value must be non-negative, got {v}")
        return v

    @field_validator("source_reference")
    @classmethod
    def validate_source_reference(cls, v: str | None) -> str | None:
        """Source reference, if provided, must be non-empty."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("source_reference must be non-empty if provided")
        return v


class LimitCheckResult(BaseModel):
    """Result of checking an observation against a limit.

    Fields:
    - limit: the limit definition being checked.
    - observation: the metric observation (None if NOT_ASSESSED).
    - status: WITHIN_LIMIT, WARNING, BREACH, or NOT_ASSESSED.
    - excess_amount: how much metric exceeds (or falls short of) threshold (Decimal).
    - excess_ratio: excess_amount / threshold if threshold > 0, else None.
    - message: explanation of result (non-empty).

    Invariants:
    - excess_amount must be non-negative.
    - if status = NOT_ASSESSED, observation may be None.
    - if status != NOT_ASSESSED, observation should be present.
    - message must be non-empty.
    """

    limit: LimitDefinition
    observation: MetricObservation | None
    status: LimitStatus
    excess_amount: Decimal
    excess_ratio: Decimal | None
    message: str

    model_config = ConfigDict(frozen=True)

    @field_validator("excess_amount")
    @classmethod
    def validate_excess_amount(cls, v: Decimal) -> Decimal:
        """Excess amount must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"excess_amount must be non-negative, got {v}")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Message must be non-empty."""
        if not v or not v.strip():
            raise ValueError("message must be non-empty")
        return v


class LeverageLimitMonitoringResult(BaseModel):
    """Result of checking multiple limits.

    Fields:
    - fund_id: fund identifier.
    - valuation_date: valuation date of observations.
    - results: list of limit check results (may be empty if no active limits).
    - warnings: processing warnings.

    Invariants:
    - results may be empty only if no active limits were checked.
    """

    fund_id: int
    valuation_date: date
    results: list[LimitCheckResult]
    warnings: list[str] = []

    model_config = ConfigDict(frozen=True)
