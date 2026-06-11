"""Input model for Historical Expected Shortfall calculation.

Encapsulates a portfolio, scenario P&Ls, and a matched HistoricalVaR result
for ES computation relative to the VaR threshold.
"""

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.models.scenario_pnl import ScenarioPnL
from manco_risk.risk.models.var_result import HistoricalVaRResult


class HistoricalExpectedShortfallInput(BaseModel):
    """Input to the Historical ES engine.

    Requires a matched HistoricalVaRResult to ensure ES is calculated
    relative to the same quantile threshold and methodology as VaR.

    Fields:
    - portfolio: Risk-ready portfolio (for reference, nav for percentage conversion).
    - scenario_pnls: List of portfolio P&Ls, one per historical scenario.
    - var_result: Historical VaR result (matched to portfolio and scenarios).

    Invariants:
    - scenario_pnls must contain at least 2 observations.
    - var_result.num_scenarios must equal len(scenario_pnls).
    - portfolio.fund_id must match var_result.fund_id.
    - portfolio.valuation_date must match var_result.valuation_date.
    """

    portfolio: RiskReadyPortfolio
    scenario_pnls: list[ScenarioPnL]
    var_result: HistoricalVaRResult

    model_config = ConfigDict(frozen=True)

    @field_validator("scenario_pnls")
    @classmethod
    def validate_scenario_pnls(cls, v: list[ScenarioPnL]) -> list[ScenarioPnL]:
        """Scenario P&Ls must contain at least 2 observations."""
        if len(v) < 2:
            raise ValueError(f"At least 2 scenario P&Ls required, got {len(v)}")
        return v

    @field_validator("var_result")
    @classmethod
    def validate_var_result_matches_scenarios(
        cls, v: HistoricalVaRResult, info
    ) -> HistoricalVaRResult:
        """VaR result num_scenarios must match scenario count."""
        if "scenario_pnls" in info.data:
            scenario_count = len(info.data["scenario_pnls"])
            if v.num_scenarios != scenario_count:
                raise ValueError(
                    f"VaR result num_scenarios {v.num_scenarios} does not match "
                    f"scenario_pnls count {scenario_count}"
                )
        return v

    @field_validator("var_result")
    @classmethod
    def validate_var_result_matches_portfolio(
        cls, v: HistoricalVaRResult, info
    ) -> HistoricalVaRResult:
        """VaR result fund_id and valuation_date must match portfolio."""
        if "portfolio" in info.data:
            portfolio = info.data["portfolio"]
            if v.fund_id != int(portfolio.fund_id):
                raise ValueError(
                    f"VaR result fund_id {v.fund_id} does not match "
                    f"portfolio fund_id {portfolio.fund_id}"
                )
            if v.valuation_date.isoformat() != portfolio.valuation_date:
                raise ValueError(
                    f"VaR result valuation_date {v.valuation_date} does not match "
                    f"portfolio valuation_date {portfolio.valuation_date}"
                )
        return v
