"""Risk calculation models.

Type definitions for risk engine inputs and outputs.
"""

from manco_risk.risk.models.backtest_input import (
    BacktestInput,
    RealisedPnLObservation,
    VaRForecastObservation,
)
from manco_risk.risk.models.backtest_result import BacktestObservation, BacktestResult
from manco_risk.risk.models.christoffersen_test import (
    ChristoffersenTestResult,
    TransitionMatrix,
)
from manco_risk.risk.models.expected_shortfall_input import HistoricalExpectedShortfallInput
from manco_risk.risk.models.expected_shortfall_result import HistoricalExpectedShortfallResult
from manco_risk.risk.models.fixed_income_stress_input import FixedIncomeStressInput
from manco_risk.risk.models.fixed_income_stress_portfolio_result import (
    FixedIncomeStressPortfolioResult,
)
from manco_risk.risk.models.fixed_income_stress_position_result import (
    FixedIncomeStressPositionResult,
)
from manco_risk.risk.models.fixed_income_stress_scenario import FixedIncomeStressScenario
from manco_risk.risk.models.historical_stress_input import HistoricalStressInput
from manco_risk.risk.models.historical_stress_result import HistoricalStressResult
from manco_risk.risk.models.kupiec_test import KupiecTestResult
from manco_risk.risk.models.parametric_var_input import ParametricNormalVaRInput
from manco_risk.risk.models.parametric_var_result import ParametricNormalVaRResult
from manco_risk.risk.models.price_return import (
    PricePoint,
    PriceToReturnInput,
    PriceToReturnResult,
)
from manco_risk.risk.models.reverse_stress_input import ReverseStressInput
from manco_risk.risk.models.reverse_stress_result import ReverseStressResult
from manco_risk.risk.models.scenario_pnl import ScenarioPnL
from manco_risk.risk.models.stress_portfolio_result import StressPortfolioResult
from manco_risk.risk.models.stress_position_result import StressPositionResult
from manco_risk.risk.models.stress_scenario import StressScenario
from manco_risk.risk.models.stress_test_input import StressTestInput
from manco_risk.risk.models.var_input import HistoricalVaRInput
from manco_risk.risk.models.var_result import HistoricalVaRResult

__all__ = [
    "BacktestInput",
    "FixedIncomeStressInput",
    "FixedIncomeStressPortfolioResult",
    "FixedIncomeStressPositionResult",
    "FixedIncomeStressScenario",
    "BacktestObservation",
    "BacktestResult",
    "ChristoffersenTestResult",
    "HistoricalExpectedShortfallInput",
    "HistoricalExpectedShortfallResult",
    "HistoricalStressInput",
    "HistoricalStressResult",
    "KupiecTestResult",
    "ParametricNormalVaRInput",
    "ParametricNormalVaRResult",
    "PricePoint",
    "PriceToReturnInput",
    "PriceToReturnResult",
    "RealisedPnLObservation",
    "ReverseStressInput",
    "ReverseStressResult",
    "ScenarioPnL",
    "StressPortfolioResult",
    "StressPositionResult",
    "StressScenario",
    "StressTestInput",
    "TransitionMatrix",
    "VaRForecastObservation",
    "HistoricalVaRInput",
    "HistoricalVaRResult",
]
