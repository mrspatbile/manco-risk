"""Mappers converting stress test results to ORM models.

Converts pure risk engine outputs (Pydantic models) to SQLAlchemy ORM entities
for database persistence. Each mapper enforces type consistency and nullability rules.
"""

from manco_risk.database.models import (
    StressTestAssetScopeEnum,
    StressTestResult,
    StressTestResultTypeEnum,
)
from manco_risk.risk.models import (
    HistoricalStressResult,
    ReverseStressResult,
    StressPortfolioResult,
)


def map_stress_portfolio_result_to_orm(
    result: StressPortfolioResult, calculation_run_id: int
) -> StressTestResult:
    """Map hypothetical stress result (StressPortfolioResult) to ORM.

    Parameters
    ----------
    result : StressPortfolioResult
        Hypothetical stress calculation result.
    calculation_run_id : int
        Foreign key to CalculationRun.

    Returns
    -------
    StressTestResult
        ORM entity ready for insertion.

    Notes
    - result_type set to HYPOTHETICAL.
    - asset_scope set to EQUITY_LIKE (Phase 1).
    - All fields populated (no nullable outcome fields in hypothetical).
    """
    return StressTestResult(
        calculation_run_id=calculation_run_id,
        fund_id=result.fund_id,
        scenario_id=result.scenario_id,
        scenario_name=result.scenario_name,
        scenario_type=result.scenario_type,
        scenario_source=result.scenario_source,
        result_type=StressTestResultTypeEnum.HYPOTHETICAL,
        asset_scope=StressTestAssetScopeEnum.EQUITY_LIKE,
        shock_type=result.shock_type,
        shock_rate=result.shock_rate,
        current_nav=result.current_nav,
        stressed_nav=result.stressed_nav,
        total_pnl=result.total_pnl,
        loss_pct_nav=result.loss_pct_nav,
        description=None,
    )


def map_reverse_stress_result_to_orm(
    result: ReverseStressResult, calculation_run_id: int
) -> StressTestResult:
    """Map reverse stress result to ORM.

    Parameters
    ----------
    result : ReverseStressResult
        Reverse stress calculation result.
    calculation_run_id : int
        Foreign key to CalculationRun.

    Returns
    -------
    StressTestResult
        ORM entity ready for insertion.

    Notes
    - result_type set to REVERSE.
    - asset_scope set to EQUITY_LIKE (Phase 1).
    - If infeasible: stressed_nav, total_pnl, loss_pct_nav are NULL.
    - If feasible: all fields populated from stress_result.
    - shock_type and shock_rate come from stress_result if feasible.
    """
    if result.is_feasible and result.stress_result is not None:
        shock_type = result.stress_result.shock_type
        shock_rate = result.stress_result.shock_rate
        stressed_nav = result.stressed_nav
        total_pnl = result.total_pnl
        loss_pct_nav = result.loss_pct_nav
    else:
        shock_type = None
        shock_rate = None
        stressed_nav = None
        total_pnl = None
        loss_pct_nav = None

    return StressTestResult(
        calculation_run_id=calculation_run_id,
        fund_id=result.fund_id,
        scenario_id=result.scenario_id,
        scenario_name=result.scenario_name,
        scenario_type=result.scenario_type,
        scenario_source=result.scenario_source,
        result_type=StressTestResultTypeEnum.REVERSE,
        asset_scope=StressTestAssetScopeEnum.EQUITY_LIKE,
        shock_type=shock_type,
        shock_rate=shock_rate,
        current_nav=result.current_nav,
        stressed_nav=stressed_nav,
        total_pnl=total_pnl,
        loss_pct_nav=loss_pct_nav,
        description=None,
    )


def map_historical_stress_result_to_orm(
    result: HistoricalStressResult, calculation_run_id: int
) -> StressTestResult:
    """Map historical stress result to ORM.

    Parameters
    ----------
    result : HistoricalStressResult
        Historical stress calculation result.
    calculation_run_id : int
        Foreign key to CalculationRun.

    Returns
    -------
    StressTestResult
        ORM entity ready for insertion.

    Notes
    - result_type set to HISTORICAL.
    - asset_scope set to EQUITY_LIKE (Phase 1).
    - All fields populated (historical stress always feasible).
    - shock_type and shock_rate are NULL (historical does not apply a shock).
    - scenario_type from result is "HISTORICAL".
    """
    return StressTestResult(
        calculation_run_id=calculation_run_id,
        fund_id=result.fund_id,
        scenario_id=result.scenario_id,
        scenario_name=result.scenario_name,
        scenario_type=result.scenario_type,
        scenario_source=result.scenario_source,
        result_type=StressTestResultTypeEnum.HISTORICAL,
        asset_scope=StressTestAssetScopeEnum.EQUITY_LIKE,
        shock_type=None,
        shock_rate=None,
        current_nav=result.current_nav,
        stressed_nav=result.stressed_nav,
        total_pnl=result.worst_scenario_pnl,
        loss_pct_nav=result.loss_pct_nav,
        description=result.description,
    )
