"""Input model for equity stress testing.

Encapsulates a portfolio and a list of stress scenarios to be applied.
"""

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.models.stress_scenario import StressScenario


class StressTestInput(BaseModel):
    """Input to the equity stress engine.

    Specifies a fixed risk-ready portfolio and a list of stress scenarios
    to be applied.

    Fields:
    - portfolio: Risk-ready portfolio (current fixed positions, enriched).
    - scenarios: List of stress scenarios to apply. Non-empty.

    Invariants:
    - scenarios must not be empty.

    Design:
    - Caller supplies StressScenario objects; engine does not hard-code scenarios.
    - Portfolio is fixed at valuation date; no rebalancing during stress.
    """

    portfolio: RiskReadyPortfolio
    scenarios: list[StressScenario]

    model_config = ConfigDict(frozen=True)

    @field_validator("scenarios")
    @classmethod
    def validate_scenarios_non_empty(cls, v: list[StressScenario]) -> list[StressScenario]:
        """At least one scenario must be provided."""
        if not v or len(v) == 0:
            raise ValueError("At least one stress scenario is required")
        return v
