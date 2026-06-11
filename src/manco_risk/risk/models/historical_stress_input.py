"""Input model for historical equity stress calculation.

Specifies a portfolio and precomputed scenario P&Ls from a historical window.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.models.scenario_pnl import ScenarioPnL


class HistoricalStressInput(BaseModel):
    """Input to the historical equity stress engine.

    Specifies a risk-ready portfolio and precomputed portfolio-level P&Ls from
    a historical time window. The engine selects the worst scenario.

    Fields:
    - portfolio: Risk-ready portfolio (current fixed positions).
    - scenario_pnls: Precomputed portfolio P&Ls for each date in the window.
                     Must be non-empty.
    - scenario_id: Unique scenario identifier, e.g., "HIST_GFC".
    - scenario_name: Human-readable name, e.g., "Global financial crisis".
    - scenario_type: Always "HISTORICAL" for historical stress.
    - scenario_source: Source of the scenario, e.g., "HISTORICAL_WINDOW".
    - shock_type: Type of shock, e.g., "HISTORICAL_EQUITY".
    - window_start_date: Start of historical window (inclusive).
    - window_end_date: End of historical window (inclusive).
    - description: Documentation of the window, time period, and methodology.

    Constraints:
    - scenario_pnls must be non-empty.
    - window_start_date <= window_end_date.
    - All string fields must be non-empty.

    Note:
    - Scenario P&Ls are precomputed (not calculated here).
    - Historical stress selects the worst scenario; it does not apply a shock rate.
    - Current portfolio is fixed; no historical revaluation.

    Immutability:
    - HistoricalStressInput is frozen; caller creates once, engine reads repeatedly.
    """

    portfolio: RiskReadyPortfolio
    scenario_pnls: list[ScenarioPnL]
    scenario_id: str
    scenario_name: str
    scenario_type: str
    scenario_source: str
    shock_type: str
    window_start_date: date
    window_end_date: date
    description: str

    model_config = ConfigDict(frozen=True)

    @field_validator(
        "scenario_id",
        "scenario_name",
        "scenario_type",
        "scenario_source",
        "shock_type",
        "description",
    )
    @classmethod
    def validate_non_empty_strings(cls, v: str, info) -> str:
        """All string fields must be non-empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must be non-empty")
        return v.strip()

    @field_validator("scenario_pnls")
    @classmethod
    def validate_scenario_pnls_non_empty(cls, v: list[ScenarioPnL]) -> list[ScenarioPnL]:
        """Scenario P&Ls must not be empty."""
        if not v or len(v) == 0:
            raise ValueError("scenario_pnls must be non-empty")
        return v

    @field_validator("window_end_date")
    @classmethod
    def validate_window_dates(cls, v: date, info) -> date:
        """Window end date must be >= start date."""
        start_date = info.data.get("window_start_date")
        if start_date and v < start_date:
            raise ValueError(f"window_end_date ({v}) must be >= window_start_date ({start_date})")
        return v
