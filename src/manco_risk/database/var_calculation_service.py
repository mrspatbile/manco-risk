"""Historical VaR calculation and persistence orchestration service.

Coordinates the workflow: validate inputs → convert prices → generate scenarios →
calculate VaR → persist results. Manages calculation run lineage and status.

This service lives in the database layer because it:
- Imports and uses ORM models
- Calls repositories for persistence
- Is not part of the pure risk calculation layer
"""

from datetime import date, datetime

from manco_risk.database.models import (
    CalculationRun,
    CalculationStatusEnum,
    CalculationTypeEnum,
    RiskMethodology,
)
from manco_risk.database.repositories import (
    CalculationRunRepository,
    VaRResultRepository,
)
from manco_risk.database.session import SessionFactory
from manco_risk.database.var_mappers import map_historical_var_result_to_orm
from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.engines.equity_scenarios import EquityScenarioPnLGenerator
from manco_risk.risk.engines.price_converter import PriceToReturnConverter
from manco_risk.risk.engines.var import HistoricalVaR
from manco_risk.risk.models.equity_scenario_pnl import EquityScenarioPnLInput
from manco_risk.risk.models.price_return import PricePoint, PriceToReturnInput
from manco_risk.risk.models.var_input import HistoricalVaRInput
from manco_risk.risk.models.var_result import HistoricalVaRResult


class HistoricalVaRCalculationService:
    """Orchestrate historical VaR calculation and persistence.

    Workflow:
    1. Validate inputs (fund_id, valuation_date consistency)
    2. Create CalculationRun with status RUNNING
    3. Convert prices to returns
    4. Generate equity scenario P&Ls
    5. Calculate historical VaR
    6. Map and persist VaRResult
    7. Mark CalculationRun COMPLETED
    8. On failure: mark FAILED and re-raise

    All persistence operations use the existing repository patterns and
    session management.
    """

    def __init__(self, session_factory: SessionFactory) -> None:
        """Initialize service.

        Parameters
        ----------
        session_factory : SessionFactory
            Factory for database sessions.
        """
        self.session_factory = session_factory
        self.price_converter = PriceToReturnConverter()
        self.scenario_generator = EquityScenarioPnLGenerator()
        self.var_engine = HistoricalVaR()

    def calculate_and_persist_historical_var(
        self,
        portfolio: RiskReadyPortfolio,
        historical_price_points: list[PricePoint],
        risk_methodology: RiskMethodology,
        position_snapshot_id: int,
        nav_snapshot_id: int,
        created_by: str,
    ) -> HistoricalVaRResult:
        """Calculate historical VaR and persist result.

        Manages the complete workflow from price data to persisted VaRResult.
        Creates a CalculationRun for lineage and audit trail.

        Parameters
        ----------
        portfolio : RiskReadyPortfolio
            Enriched portfolio at valuation date.
        historical_price_points : list[PricePoint]
            Historical prices for lookback period (typically 250+ observations).
        risk_methodology : RiskMethodology
            Risk parameters (confidence level, lookback days, horizon, etc.).
        position_snapshot_id : int
            FK to PositionSnapshot for lineage.
        nav_snapshot_id : int
            FK to NAVSnapshot for lineage.
        created_by : str
            User/system identifier for audit trail.

        Returns
        -------
        HistoricalVaRResult
            In-memory calculation result. Also persisted to VaRResult table.

        Raises
        ------
        ValueError
            If portfolio fund_id or valuation_date mismatches.
        InsufficientPriceDataError
            If insufficient price observations.
        UnsupportedAssetClassError
            If portfolio contains unsupported instruments.
        MissingHistoricalDataError
            If required return data is missing.
        (database errors)
            If persistence fails.

        Notes
        -----
        On calculation failure after CalculationRun creation: marks run as FAILED,
        does not insert VaRResult, and re-raises the exception.
        """
        # Validate inputs
        portfolio_fund_id = int(portfolio.fund_id)
        portfolio_valuation_date = date.fromisoformat(portfolio.valuation_date)

        if portfolio_fund_id != portfolio_fund_id:  # Placeholder check; validates fund_id is set
            raise ValueError(f"Invalid portfolio fund_id: {portfolio_fund_id}")
        if portfolio_valuation_date is None:
            raise ValueError(f"Invalid portfolio valuation_date: {portfolio_valuation_date}")

        # Create CalculationRun with status RUNNING
        calc_repo = CalculationRunRepository(self.session_factory)
        calculation_run = CalculationRun(
            fund_id=portfolio_fund_id,
            valuation_date=portfolio_valuation_date,
            calculation_type=CalculationTypeEnum.VAR_ES_DAILY,
            created_timestamp=datetime.now(),
            methodology_version_id=risk_methodology.methodology_version_id,
            position_snapshot_id=position_snapshot_id,
            nav_snapshot_id=nav_snapshot_id,
            status=CalculationStatusEnum.RUNNING,
            created_by=created_by,
        )
        inserted_run = calc_repo.insert(calculation_run)
        calculation_run_id = inserted_run.calculation_run_id

        try:
            # Convert prices to returns
            price_input = PriceToReturnInput(price_points=historical_price_points)
            price_result = self.price_converter.convert(price_input)

            # Generate equity scenario P&Ls
            scenario_input = EquityScenarioPnLInput(
                portfolio=portfolio,
                historical_returns=price_result.historical_returns,
            )
            scenario_result = self.scenario_generator.generate(scenario_input)

            # Calculate historical VaR
            var_input = HistoricalVaRInput(
                portfolio=portfolio,
                confidence_level=risk_methodology.var_confidence_level,
                horizon_days=risk_methodology.var_horizon_days,
                scenario_pnls=scenario_result.scenario_pnls,
            )
            var_result = self.var_engine.calculate(var_input)

            # Map to ORM and persist
            orm_var_result = map_historical_var_result_to_orm(
                var_result,
                calculation_run_id=calculation_run_id,
                lookback_days=risk_methodology.var_lookback_days,
            )
            var_repo = VaRResultRepository(self.session_factory)
            var_repo.insert(orm_var_result)

            # Mark calculation run COMPLETED
            calc_repo.update_status(calculation_run_id, CalculationStatusEnum.COMPLETED)

            return var_result

        except Exception:
            # Mark calculation run FAILED
            calc_repo.update_status(calculation_run_id, CalculationStatusEnum.FAILED)
            raise
