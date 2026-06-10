"""Mapper from risk-layer results to database-layer ORM models.

Converts HistoricalVaRResult (Pydantic, from risk calculation engine)
to VaRResult (SQLAlchemy ORM, for database persistence).

This module lives in the database layer to keep the risk layer pure.
"""

from manco_risk.database.models import VaRResult
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
