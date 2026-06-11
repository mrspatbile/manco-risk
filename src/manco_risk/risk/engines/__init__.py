"""Risk calculation engines.

Pure computation engines for risk metrics.
"""

from manco_risk.risk.engines.backtesting_tests import KupiecTest
from manco_risk.risk.engines.christoffersen_test import ChristoffersenTest
from manco_risk.risk.engines.duration_based_pricer import DurationBasedFixedIncomePricer
from manco_risk.risk.engines.equity_stress import EquityStressEngine
from manco_risk.risk.engines.fixed_income_pricer import FixedIncomeStressPricer
from manco_risk.risk.engines.fixed_income_stress import FixedIncomeStressEngine
from manco_risk.risk.engines.historical_equity_stress import HistoricalEquityStressEngine
from manco_risk.risk.engines.parametric_var import ParametricNormalVaR
from manco_risk.risk.engines.price_converter import PriceToReturnConverter
from manco_risk.risk.engines.reverse_equity_stress import ReverseEquityStressEngine
from manco_risk.risk.engines.var import HistoricalVaR
from manco_risk.risk.engines.var_backtesting import VaRBacktestingEngine

__all__ = [
    "ChristoffersenTest",
    "DurationBasedFixedIncomePricer",
    "EquityStressEngine",
    "FixedIncomeStressEngine",
    "FixedIncomeStressPricer",
    "HistoricalEquityStressEngine",
    "KupiecTest",
    "ParametricNormalVaR",
    "PriceToReturnConverter",
    "ReverseEquityStressEngine",
    "HistoricalVaR",
    "VaRBacktestingEngine",
]
