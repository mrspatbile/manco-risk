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
from manco_risk.risk.models.combined_stress_portfolio_result import (
    CombinedStressPortfolioResult,
)
from manco_risk.risk.models.fixed_income_stress_portfolio_result import (
    FixedIncomeStressPortfolioResult,
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


def map_fixed_income_stress_portfolio_result_to_orm(
    result: FixedIncomeStressPortfolioResult, calculation_run_id: int
) -> StressTestResult:
    """Map fixed-income stress result (portfolio-level) to ORM.

    Parameters
    ----------
    result : FixedIncomeStressPortfolioResult
        Fixed-income stress calculation output.
    calculation_run_id : int
        Foreign key to CalculationRun.

    Returns
    -------
    StressTestResult
        ORM entity ready for insertion.

    Mapping
    -------
    - result_type: HYPOTHETICAL (Phase 1)
    - asset_scope: FIXED_INCOME
    - shock_type: result.shock_type (audit label: RATE_SHOCK, SPREAD_SHOCK, COMBINED)
    - rate_shock_bps: result.rate_shock_bps (integer basis points)
    - spread_shock_bps: result.spread_shock_bps (integer basis points)
    - shock_rate: None (not applicable to FI; shocks are bps-based and multi-dimensional)
    - current_nav: result.current_nav
    - stressed_nav: result.stressed_nav
    - total_pnl: result.total_pnl (signed)
    - loss_pct_nav: result.loss_pct_nav (non-negative)
    - total_rate_pnl: result.total_rate_pnl (signed; FI-specific decomposition)
    - total_credit_pnl: result.total_credit_pnl (signed; FI-specific decomposition)
    - num_positions_stressed: result.num_bond_positions
    - num_cash_positions: result.num_cash_positions

    Notes
    -----
    Invariant: total_rate_pnl + total_credit_pnl = total_pnl (or within rounding tolerance).
    """
    return StressTestResult(
        calculation_run_id=calculation_run_id,
        fund_id=result.fund_id,
        scenario_id=result.scenario_id,
        scenario_name=result.scenario_name,
        scenario_type=result.scenario_type,
        scenario_source=result.scenario_source,
        result_type=StressTestResultTypeEnum.HYPOTHETICAL,
        asset_scope=StressTestAssetScopeEnum.FIXED_INCOME,
        shock_type=result.shock_type,
        shock_rate=None,
        current_nav=result.current_nav,
        stressed_nav=result.stressed_nav,
        total_pnl=result.total_pnl,
        loss_pct_nav=result.loss_pct_nav,
        rate_shock_bps=result.rate_shock_bps,
        spread_shock_bps=result.spread_shock_bps,
        total_rate_pnl=result.total_rate_pnl,
        total_credit_pnl=result.total_credit_pnl,
        num_positions_stressed=result.num_bond_positions,
        num_cash_positions=result.num_cash_positions,
        description=None,
    )


def map_combined_stress_portfolio_result_to_orm(
    result: CombinedStressPortfolioResult, calculation_run_id: int
) -> StressTestResult:
    """Map combined multi-asset stress result (portfolio-level) to ORM.

    Parameters
    ----------
    result : CombinedStressPortfolioResult
        Combined stress calculation output.
    calculation_run_id : int
        Foreign key to CalculationRun.

    Returns
    -------
    StressTestResult
        ORM entity ready for insertion.

    Mapping
    -------
    - result_type: HYPOTHETICAL
    - asset_scope: MULTI_ASSET
    - shock_type: None (sub-scope rows carry per-asset shock details)
    - shock_rate: None (not applicable to combined multi-asset result)
    - rate_shock_bps: None (sub-scope only)
    - spread_shock_bps: None (sub-scope only)
    - total_rate_pnl: fi_result.total_rate_pnl if fi_result present, else None
    - total_credit_pnl: fi_result.total_credit_pnl if fi_result present, else None
    - num_cash_positions: result.num_cash_positions (base-currency cash positions)
    - num_positions_stressed: None (not meaningful at combined scope)

    Notes
    -----
    The MULTI_ASSET row is the combined aggregate view. Sub-scope rows (EQUITY_LIKE,
    FIXED_INCOME) carry the detailed shock parameters for each asset class.
    total_pnl = equity_pnl + fi_pnl (cash contributes zero).
    """
    fi = result.fi_result
    return StressTestResult(
        calculation_run_id=calculation_run_id,
        fund_id=result.fund_id,
        scenario_id=result.scenario_id,
        scenario_name=result.scenario_name,
        scenario_type=result.scenario_type,
        scenario_source=result.scenario_source,
        result_type=StressTestResultTypeEnum.HYPOTHETICAL,
        asset_scope=StressTestAssetScopeEnum.MULTI_ASSET,
        shock_type=None,
        shock_rate=None,
        current_nav=result.current_nav,
        stressed_nav=result.stressed_nav,
        total_pnl=result.total_pnl,
        loss_pct_nav=result.loss_pct_nav,
        rate_shock_bps=None,
        spread_shock_bps=None,
        total_rate_pnl=fi.total_rate_pnl if fi is not None else None,
        total_credit_pnl=fi.total_credit_pnl if fi is not None else None,
        num_positions_stressed=None,
        num_cash_positions=result.num_cash_positions,
        description=None,
    )
