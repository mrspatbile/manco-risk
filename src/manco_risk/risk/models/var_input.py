"""Input model for Historical VaR calculation.

Encapsulates a portfolio, confidence level, and scenario P&Ls for VaR computation.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.models.scenario_pnl import ScenarioPnL


class HistoricalVaRInput(BaseModel):
    """Input to the Historical VaR engine.

    Fields:
    - portfolio: Risk-ready portfolio (for reference, nav used for percentage conversion).
    - confidence_level: Confidence level for VaR, e.g., 0.95 for 95% VaR.
    - horizon_days: Horizon for VaR. Phase 1 supports 1-day only.
    - scenario_pnls: List of portfolio P&Ls, one per historical scenario.

    Invariants:
    - confidence_level must be in (0, 1) exclusive.
    - horizon_days must equal 1 for Phase 1.
    - scenario_pnls must be non-empty.
    """

    portfolio: RiskReadyPortfolio
    confidence_level: Decimal
    horizon_days: int
    scenario_pnls: list[ScenarioPnL]

    model_config = ConfigDict(frozen=True)

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level(cls, v: Decimal) -> Decimal:
        """Confidence level must be strictly between 0 and 1."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal <= Decimal("0") or v_decimal >= Decimal("1"):
            raise ValueError(f"Confidence level must be in (0, 1), got {v_decimal}")
        return v_decimal

    @field_validator("horizon_days")
    @classmethod
    def validate_horizon_days(cls, v: int) -> int:
        """Horizon days must be 1 for Phase 1."""
        if v != 1:
            raise ValueError(f"Phase 1 supports only horizon_days=1, got {v}")
        return v

    @field_validator("scenario_pnls")
    @classmethod
    def validate_scenario_pnls(cls, v: list[ScenarioPnL]) -> list[ScenarioPnL]:
        """Scenario P&Ls must not be empty."""
        if len(v) == 0:
            raise ValueError("At least one scenario P&L is required")
        return v
