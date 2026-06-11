"""Mappers for VaR backtesting results to ORM models.

Converts pure backtesting calculation results to database ORM objects.
"""

from manco_risk.database.models import VaRBacktestingResult
from manco_risk.risk.models.backtest_result import BacktestResult
from manco_risk.risk.models.christoffersen_test import ChristoffersenTestResult
from manco_risk.risk.models.kupiec_test import KupiecTestResult


def map_backtest_result_to_orm(
    backtest_result: BacktestResult,
    kupiec_result: KupiecTestResult,
    christoffersen_result: ChristoffersenTestResult,
    calculation_run_id: int,
    fund_id: int,
) -> VaRBacktestingResult:
    """Map pure backtesting results to VaRBacktestingResult ORM.

    Combines counting results from BacktestResult with statistical test results
    from Kupiec and Christoffersen tests.

    Parameters
    ----------
    backtest_result : BacktestResult
        Pure backtesting counts and diagnostics.
    kupiec_result : KupiecTestResult
        Kupiec unconditional coverage test result.
    christoffersen_result : ChristoffersenTestResult
        Christoffersen conditional coverage test result.
    calculation_run_id : int
        FK to CalculationRun for lineage.
    fund_id : int
        FK to Fund for the fund owning this backtest.

    Returns
    -------
    VaRBacktestingResult
        ORM entity ready for insertion.
    """
    return VaRBacktestingResult(
        calculation_run_id=calculation_run_id,
        fund_id=fund_id,
        window_days=1,  # Phase 1: 1-day backtesting only
        total_observations=backtest_result.num_valid_aligned,
        num_exceptions=backtest_result.num_breaches,
        pof=backtest_result.breach_ratio if backtest_result.breach_ratio is not None else 0,
        kupiec_test_statistic=kupiec_result.lr_statistic,
        kupiec_p_value=kupiec_result.p_value,
        kupiec_reject=kupiec_result.reject_null,
        christoffersen_uc_test_statistic=christoffersen_result.uc_test_statistic,
        christoffersen_cc_test_statistic=christoffersen_result.cc_test_statistic,
        christoffersen_reject=christoffersen_result.reject_cc,
    )
