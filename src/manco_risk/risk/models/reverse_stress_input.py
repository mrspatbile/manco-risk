"""Input model for reverse equity stress calculation.

Specifies a portfolio and a target NAV loss to be reached via reverse stress.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.etl.enriched_position import RiskReadyPortfolio


class ReverseStressInput(BaseModel):
    """Input to the reverse equity stress engine.

    Specifies a risk-ready portfolio and a target NAV loss percentage to reach
    via calculated parallel equity shock.

    Fields:
    - portfolio: Risk-ready portfolio (current fixed positions, enriched).
    - target_loss_pct: Target NAV loss as decimal ratio, e.g., 0.20 for 20% loss.
    - scenario_id: Unique scenario identifier, e.g., "REV_TARGET_20PCT".
    - scenario_name: Human-readable scenario name, e.g., "Reverse: 20% NAV loss".
    - scenario_type: Always "REVERSE" for reverse stress scenarios.
    - scenario_source: Source of the scenario, e.g., "MANAGER_DEFINED", "STRESS_TEST".
    - description: Documentation of the scenario, rationale, and assumptions.

    Constraints:
    - target_loss_pct must be >= 0 and < 1 (cannot lose 100% or more).
    - Decimal precision for target_loss_pct.
    - target_loss_pct = 0 is valid and feasible (zero shock needed).

    Immutability:
    - ReverseStressInput is frozen; caller creates once, engine reads repeatedly.
    """

    portfolio: RiskReadyPortfolio
    target_loss_pct: Decimal
    scenario_id: str
    scenario_name: str
    scenario_type: str
    scenario_source: str
    description: str

    model_config = ConfigDict(frozen=True)

    @field_validator(
        "scenario_id", "scenario_name", "scenario_type", "scenario_source", "description"
    )
    @classmethod
    def validate_non_empty_strings(cls, v: str, info) -> str:
        """All string fields must be non-empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must be non-empty")
        return v.strip()

    @field_validator("target_loss_pct", mode="before")
    @classmethod
    def validate_target_loss_pct(cls, v) -> Decimal:
        """Target loss percentage must be >= 0 and < 1."""
        if isinstance(v, Decimal):
            pct = v
        else:
            try:
                pct = Decimal(str(v))
            except Exception as e:
                raise ValueError(f"target_loss_pct must be convertible to Decimal, got {v}: {e}")

        if pct < Decimal("0"):
            raise ValueError(f"target_loss_pct must be >= 0, got {pct}")
        if pct >= Decimal("1"):
            raise ValueError(f"target_loss_pct must be < 1, got {pct}")

        return pct
