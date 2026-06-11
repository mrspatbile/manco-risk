"""Risk calculation models.

Type definitions for risk engine inputs and outputs.
"""

from manco_risk.risk.models.backtest_input import (
    BacktestInput,
    RealisedPnLObservation,
    VaRForecastObservation,
)
from manco_risk.risk.models.backtest_result import BacktestObservation, BacktestResult
from manco_risk.risk.models.expected_shortfall_input import HistoricalExpectedShortfallInput
from manco_risk.risk.models.expected_shortfall_result import HistoricalExpectedShortfallResult
from manco_risk.risk.models.kupiec_test import KupiecTestResult
from manco_risk.risk.models.parametric_var_input import ParametricNormalVaRInput
from manco_risk.risk.models.parametric_var_result import ParametricNormalVaRResult
from manco_risk.risk.models.price_return import (
    PricePoint,
    PriceToReturnInput,
    PriceToReturnResult,
)
from manco_risk.risk.models.scenario_pnl import ScenarioPnL
from manco_risk.risk.models.var_input import HistoricalVaRInput
from manco_risk.risk.models.var_result import HistoricalVaRResult

__all__ = [
    "BacktestInput",
    "BacktestObservation",
    "BacktestResult",
    "HistoricalExpectedShortfallInput",
    "HistoricalExpectedShortfallResult",
    "KupiecTestResult",
    "ParametricNormalVaRInput",
    "ParametricNormalVaRResult",
    "PricePoint",
    "PriceToReturnInput",
    "PriceToReturnResult",
    "RealisedPnLObservation",
    "ScenarioPnL",
    "VaRForecastObservation",
    "HistoricalVaRInput",
    "HistoricalVaRResult",
]
