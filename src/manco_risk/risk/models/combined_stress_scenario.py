"""Combined stress scenario for multi-asset stress testing.

Wraps an optional equity shock and an optional fixed-income shock under a single
combined scenario identity. At least one sub-scenario must be provided; either or
both may be None, allowing equity-only, FI-only, or combined runs.

The combined orchestrator dispatches each sub-scenario to the relevant engine.
Neither sub-scenario is passed to the wrong engine.
"""

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from manco_risk.risk.models.fixed_income_stress_scenario import FixedIncomeStressScenario
from manco_risk.risk.models.stress_scenario import StressScenario


class CombinedStressScenario(BaseModel):
    """A scenario for combined multi-asset stress testing.

    Combines an optional equity shock and an optional fixed-income shock under
    a shared scenario identity. At least one of equity_scenario or fi_scenario
    must be provided.

    Fields:
    - scenario_id: Unique combined scenario identifier.
    - scenario_name: Human-readable combined scenario name.
    - scenario_type: Type of combined scenario, e.g. "HYPOTHETICAL".
    - scenario_source: Source of the combined scenario, e.g. "MANAGER_DEFINED".
    - description: Methodology documentation for the combined scenario.
    - equity_scenario: Equity-like shock to apply; None if no equity shock in this scenario.
    - fi_scenario: Fixed-income shock to apply; None if no FI shock in this scenario.

    Validation:
    - At least one of equity_scenario or fi_scenario must be non-None.
    - All string fields must be non-empty.

    Immutability:
    - Frozen; caller creates once, engine reads.
    """

    scenario_id: str
    scenario_name: str
    scenario_type: str
    scenario_source: str
    description: str
    equity_scenario: StressScenario | None = None
    fi_scenario: FixedIncomeStressScenario | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator(
        "scenario_id",
        "scenario_name",
        "scenario_type",
        "scenario_source",
        "description",
    )
    @classmethod
    def validate_non_empty_strings(cls, v: str, info) -> str:
        """All string fields must be non-empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must be non-empty")
        return v.strip()

    @model_validator(mode="after")
    def at_least_one_sub_scenario(self) -> "CombinedStressScenario":
        """At least one sub-scenario must be provided."""
        if self.equity_scenario is None and self.fi_scenario is None:
            raise ValueError("at least one of equity_scenario or fi_scenario must be provided")
        return self
