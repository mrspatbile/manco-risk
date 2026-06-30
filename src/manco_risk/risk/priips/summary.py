"""PRIIPs Summary result models.

Pure data models. No calculation or persistence logic.

The summary assembles pre-computed PRIIPs result objects (SRI, scenarios, costs)
into one export-ready, immutable container for reporting and KID generation.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.risk.priips.costs import PRIIPSCostsResult
from manco_risk.risk.priips.performance_scenarios import PerformanceScenariosResult
from manco_risk.risk.priips.sri import SRIResult


class PRIIPSSummaryInput(BaseModel):
    """Input to PRIIPs Summary service.

    Contains pre-computed PRIIPs result objects for a product.

    The service validates consistency (product_id, valuation_date,
    methodology_version, RHP) and returns an immutable summary.

    Fields:
    - sri_result: SRI calculation result (MRM + CRM combined to SRI class).
    - performance_scenarios_result: Performance scenario values (stress, unfav, mod, fav).
    - costs_result: Cost breakdown (entry, exit, ongoing, transaction, incidental).

    Invariants:
    - All results must have matching product_id.
    - All results must have matching valuation_date.
    - All results must have matching methodology_version.
    - All results must have matching recommended_holding_period_years.
    """

    sri_result: SRIResult
    performance_scenarios_result: PerformanceScenariosResult
    costs_result: PRIIPSCostsResult

    model_config = ConfigDict(frozen=True)


class PRIIPSSummaryResult(BaseModel):
    """Result of PRIIPs Summary assembly.

    Contains pre-computed PRIIPs outputs organised into one export-ready container.

    This model is an immutable DTO that references existing result objects
    (not duplicating their fields) and adds summary-level metadata.

    Fields:
    - product_id: Product identifier (from results).
    - valuation_date: Snapshot date (from results).
    - methodology_version: PRIIPs RTS version (from results).
    - recommended_holding_period_years: RHP in years (from results).
    - sri_result: SRI calculation result (reference).
    - performance_scenarios_result: Performance scenario result (reference).
    - costs_result: Cost result (reference).
    - included_sections: List of included result sections (informational).

    Invariants (defensive checks):
    - product_id must be non-empty.
    - valuation_date must be valid.
    - methodology_version must be non-empty.
    - recommended_holding_period_years must be positive.
    - All referenced results must have matching identifiers.
    - included_sections must list the provided sections.
    """

    product_id: str
    valuation_date: date
    methodology_version: str
    recommended_holding_period_years: int
    sri_result: SRIResult
    performance_scenarios_result: PerformanceScenariosResult
    costs_result: PRIIPSCostsResult
    included_sections: list[str]

    model_config = ConfigDict(frozen=True)

    @field_validator("product_id")
    @classmethod
    def validate_product_id(cls, v: str) -> str:
        """Product ID must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("product_id must be non-empty")
        return v.strip()

    @field_validator("methodology_version")
    @classmethod
    def validate_methodology_version(cls, v: str) -> str:
        """Methodology version must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("methodology_version must be non-empty")
        return v.strip()

    @field_validator("recommended_holding_period_years")
    @classmethod
    def validate_recommended_holding_period_years(cls, v: int) -> int:
        """Recommended holding period must be positive (defensive check)."""
        if v <= 0:
            raise ValueError(f"recommended_holding_period_years must be positive, got {v}")
        return v

    @field_validator("included_sections")
    @classmethod
    def validate_included_sections(cls, v: list[str]) -> list[str]:
        """Included sections must be non-empty (defensive check)."""
        if not v or len(v) == 0:
            raise ValueError("included_sections must contain at least one section")
        return v
