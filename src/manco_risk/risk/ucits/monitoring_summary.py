"""UCITS monitoring summary models.

Orchestration layer for consolidated monitoring results.
No calculation logic. Pure data models.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.risk.ucits.absolute_var import UCITSAbsoluteVaRResult
from manco_risk.risk.ucits.borrowing import UCITSBorrowingResult
from manco_risk.risk.ucits.concentration import UCITSConcentrationResult
from manco_risk.risk.ucits.otc_counterparty import UCITSOTCCounterpartyResult
from manco_risk.risk.ucits.relative_var import UCITSRelativeVaRResult
from manco_risk.risk.ucits.srri import SRRIResult


class UCITSMonitoringSummary(BaseModel):
    """Consolidated UCITS monitoring summary.

    Immutable orchestration of all monitoring engine results.

    This model is a pure container for existing monitoring results.
    It performs no calculations or aggregations.

    Fields:
    - fund_id: Fund identifier (copied from input results for convenience).
    - valuation_date: Snapshot date (copied for convenience).
    - overall_compliance: True if all monitoring engines report WITHIN_LIMIT.
    - breach_count: Number of monitoring engines in BREACH status.
    - breached_checks: List of monitoring check names that are in BREACH.
    - absolute_var_result: Absolute VaR monitoring result.
    - relative_var_result: Relative VaR monitoring result.
    - srri_result: SRRI calculation result.
    - borrowing_result: Direct borrowing limit result.
    - concentration_result: Single-issuer concentration result.
    - otc_counterparty_result: OTC counterparty exposure result.
    """

    fund_id: str
    valuation_date: date
    overall_compliance: bool
    breach_count: int
    breached_checks: list[str]
    absolute_var_result: UCITSAbsoluteVaRResult
    relative_var_result: UCITSRelativeVaRResult
    srri_result: SRRIResult
    borrowing_result: UCITSBorrowingResult
    concentration_result: UCITSConcentrationResult
    otc_counterparty_result: UCITSOTCCounterpartyResult

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_id")
    @classmethod
    def validate_fund_id(cls, v: str) -> str:
        """Fund ID must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("fund_id must be non-empty")
        return v.strip()

    @field_validator("breach_count")
    @classmethod
    def validate_breach_count_non_negative(cls, v: int) -> int:
        """Breach count must be non-negative (defensive check)."""
        if v < 0:
            raise ValueError(f"breach_count must be non-negative, got {v}")
        return v

    @field_validator("breach_count")
    @classmethod
    def validate_breach_count_range(cls, v: int) -> int:
        """Breach count must be at most 6 (one per monitoring engine)."""
        if v > 6:
            raise ValueError(f"breach_count must be at most 6, got {v}")
        return v

    @field_validator("breached_checks")
    @classmethod
    def validate_breached_checks_non_empty_items(cls, v: list[str]) -> list[str]:
        """Breached check names must not be empty (defensive check)."""
        for item in v:
            if not item or not item.strip():
                raise ValueError("breached_checks items must be non-empty")
        return v

    @field_validator("breached_checks")
    @classmethod
    def validate_breached_checks_count_matches_breach_count(cls, v: list[str], info) -> list[str]:
        """Breached checks count must match breach_count (consistency check)."""
        if "breach_count" in info.data:
            if len(v) != info.data["breach_count"]:
                raise ValueError(
                    f"breached_checks length {len(v)} must match breach_count {info.data['breach_count']}"
                )
        return v
