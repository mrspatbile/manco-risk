"""Input model for fixed-income stress testing.

Wraps a risk-ready portfolio and a list of fixed-income stress scenarios.
"""

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.models.fixed_income_stress_scenario import FixedIncomeStressScenario


class FixedIncomeStressInput(BaseModel):
    """Input for fixed-income stress test calculation.

    Fields:
    - portfolio: Risk-ready portfolio of enriched positions.
    - scenarios: Non-empty list of fixed-income stress scenarios to apply.

    Immutability:
    - Frozen; constructed once and consumed by the stress engine.
    """

    portfolio: RiskReadyPortfolio
    scenarios: list[FixedIncomeStressScenario]

    model_config = ConfigDict(frozen=True)

    @field_validator("scenarios")
    @classmethod
    def validate_scenarios_non_empty(
        cls, v: list[FixedIncomeStressScenario]
    ) -> list[FixedIncomeStressScenario]:
        """Scenario list must contain at least one scenario."""
        if not v:
            raise ValueError("scenarios list must not be empty")
        return v
