"""Scenario P&L model for risk calculations.

Represents portfolio profit/loss under a single historical or hypothetical scenario.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class ScenarioPnL(BaseModel):
    """Portfolio P&L for a single scenario.

    A scenario is identified either by a date (historical) or a scenario ID (stress, parametric).

    Fields:
    - scenario_date: Date of the scenario (e.g., historical date). Optional.
    - scenario_id: Identifier for non-date scenarios (e.g., stress_001). Optional.
    - total_pnl: Portfolio P&L in base currency. Signed: negative = loss, positive = gain.

    Invariants:
    - At least one of scenario_date or scenario_id must be provided.
    - total_pnl can be any signed Decimal (no restrictions on sign or magnitude).
    """

    scenario_date: Optional[date] = None
    scenario_id: Optional[str] = None
    total_pnl: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("total_pnl", mode="before")
    @classmethod
    def validate_pnl_is_decimal(cls, v) -> Decimal:
        """Ensure total_pnl is a valid Decimal."""
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))

    @model_validator(mode="after")
    def validate_at_least_one_identifier(self) -> "ScenarioPnL":
        """At least one of scenario_date or scenario_id must be provided."""
        if self.scenario_date is None and self.scenario_id is None:
            raise ValueError("At least one of scenario_date or scenario_id must be provided")
        return self
