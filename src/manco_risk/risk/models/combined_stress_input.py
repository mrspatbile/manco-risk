"""Input model for combined multi-asset stress testing.

Bundles a risk-ready portfolio with a list of combined stress scenarios.
"""

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.models.combined_stress_scenario import CombinedStressScenario


class CombinedStressInput(BaseModel):
    """Input for combined multi-asset stress testing.

    Fields:
    - portfolio: Risk-ready portfolio containing positions of any supported asset class.
    - scenarios: Non-empty list of combined stress scenarios to apply.

    Validation:
    - scenarios must be non-empty.

    Immutability:
    - Frozen; caller creates once, engine reads.
    """

    portfolio: RiskReadyPortfolio
    scenarios: list[CombinedStressScenario]

    model_config = ConfigDict(frozen=True)

    @field_validator("scenarios")
    @classmethod
    def validate_non_empty_scenarios(
        cls, v: list[CombinedStressScenario]
    ) -> list[CombinedStressScenario]:
        """Scenarios list must be non-empty."""
        if not v:
            raise ValueError("scenarios list must be non-empty")
        return v
