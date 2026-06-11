"""Mapper from risk-layer results to database-layer ORM models.

Converts VaR calculation results (Pydantic, from risk calculation engines)
to VaRResult (SQLAlchemy ORM, for database persistence).

This module lives in the database layer to keep the risk layer pure.
"""

from manco_risk.database.models import VaRResult
from manco_risk.risk.models.parametric_var_result import ParametricNormalVaRResult
from manco_risk.risk.models.var_result import HistoricalVaRResult


def map_historical_var_result_to_orm(
    historical_var_result: HistoricalVaRResult,
    calculation_run_id: int,
    lookback_days: int,
) -> VaRResult:
    """Convert HistoricalVaRResult to ORM VaRResult for database persistence.

    Maps risk-layer Pydantic model to database-layer ORM model.

    Parameters
    ----------
    historical_var_result : HistoricalVaRResult
        Result from HistoricalVaR calculation engine.
    calculation_run_id : int
        Foreign key to CalculationRun. Supplied by caller.
    lookback_days : int
        Historical lookback window (from RiskMethodology). Supplied by caller.

    Returns
    -------
    VaRResult
        ORM entity ready for database insertion.

    Notes
    -----
    - quantile_index is not persisted (derivable from num_scenarios and confidence_level)
    - valuation_date is available via CalculationRun, not repeated here
    - num_scenarios from Pydantic maps to num_observations_used in ORM
    """
    return VaRResult(
        calculation_run_id=calculation_run_id,
        fund_id=historical_var_result.fund_id,
        confidence_level=historical_var_result.confidence_level,
        horizon_days=historical_var_result.horizon_days,
        var_value_absolute=historical_var_result.var_value,
        var_pct_nav=historical_var_result.var_pct_nav,
        lookback_days=lookback_days,
        num_observations_used=historical_var_result.num_scenarios,
    )


def map_parametric_normal_var_result_to_orm(
    parametric_var_result: ParametricNormalVaRResult,
    calculation_run_id: int,
    lookback_days: int,
) -> VaRResult:
    """Convert ParametricNormalVaRResult to ORM VaRResult for database persistence.

    Maps risk-layer Pydantic model to database-layer ORM model.
    Uses same VaRResult table as historical VaR; method distinction via RiskMethodology.

    Parameters
    ----------
    parametric_var_result : ParametricNormalVaRResult
        Result from ParametricNormalVaR calculation engine.
    calculation_run_id : int
        Foreign key to CalculationRun. Supplied by caller.
    lookback_days : int
        Scenario generation lookback window (from RiskMethodology). Supplied by caller.

    Returns
    -------
    VaRResult
        ORM entity ready for database insertion.

    Notes
    -----
    - Distributional parameters (mean_return, std_dev, z_score) not persisted.
    - num_observations from Pydantic maps to num_observations_used in ORM.
    - valuation_date is available via CalculationRun, not repeated here.
    """
    return VaRResult(
        calculation_run_id=calculation_run_id,
        fund_id=parametric_var_result.fund_id,
        confidence_level=parametric_var_result.confidence_level,
        horizon_days=parametric_var_result.horizon_days,
        var_value_absolute=parametric_var_result.var_value,
        var_pct_nav=parametric_var_result.var_pct_nav,
        lookback_days=lookback_days,
        num_observations_used=parametric_var_result.num_observations,
    )
