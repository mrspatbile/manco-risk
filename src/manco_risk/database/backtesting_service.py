"""VaR backtesting calculation and persistence orchestration services.

Coordinates the workflow: validate backtest inputs → run backtesting engine →
run statistical tests (Kupiec, Christoffersen) → persist results.
Manages calculation run lineage and status.

This module lives in the database layer because it:
- Imports and uses ORM models
- Calls repositories for persistence
- Is not part of the pure risk calculation layer
"""

from dataclasses import dataclass
from datetime import datetime

from manco_risk.database.backtest_mappers import map_backtest_result_to_orm
from manco_risk.database.models import (
    CalculationRun,
    CalculationStatusEnum,
    CalculationTypeEnum,
    RiskMethodology,
)
from manco_risk.database.repositories import (
    CalculationRunRepository,
    VaRBacktestingResultRepository,
)
from manco_risk.database.session import SessionFactory
from manco_risk.risk.engines.backtesting_tests import KupiecTest
from manco_risk.risk.engines.christoffersen_test import ChristoffersenTest
from manco_risk.risk.engines.var_backtesting import VaRBacktestingEngine
from manco_risk.risk.models.backtest_input import BacktestInput
from manco_risk.risk.models.backtest_result import BacktestResult
from manco_risk.risk.models.christoffersen_test import ChristoffersenTestResult
from manco_risk.risk.models.kupiec_test import KupiecTestResult


@dataclass(frozen=True)
class VaRBacktestingCalculationResult:
    """Result of VaR backtesting calculation and persistence workflow.

    Attributes
    ----------
    backtest_result : BacktestResult
        In-memory regulatory counting result. Includes alignment of VaR forecasts
        and realised P&Ls, breach detection, and statistical counts.
    kupiec_result : KupiecTestResult
        In-memory Kupiec unconditional coverage test result.
    christoffersen_result : ChristoffersenTestResult
        In-memory Christoffersen conditional coverage test result.
    calculation_run_id : int
        FK to CalculationRun for lineage and audit trail.
    """

    backtest_result: BacktestResult
    kupiec_result: KupiecTestResult
    christoffersen_result: ChristoffersenTestResult
    calculation_run_id: int


class VaRBacktestingCalculationService:
    """Orchestrate VaR backtesting calculation and persistence.

    Workflow:
    1. Validate inputs (fund_id, risk_methodology consistency)
    2. Create CalculationRun with status RUNNING
    3. Run VaRBacktestingEngine to align forecasts and realised P&Ls
    4. Run KupiecTest for unconditional coverage
    5. Run ChristoffersenTest for conditional coverage
    6. Map all three pure results to ORM
    7. Persist VaRBacktestingResult
    8. Mark CalculationRun COMPLETED
    9. On failure: mark FAILED and re-raise

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
        self.backtesting_engine = VaRBacktestingEngine()
        self.kupiec_test = KupiecTest()
        self.christoffersen_test = ChristoffersenTest()

    def calculate_and_persist_backtest(
        self,
        backtest_input: BacktestInput,
        fund_id: int,
        risk_methodology: RiskMethodology,
        position_snapshot_id: int,
        nav_snapshot_id: int,
        created_by: str,
    ) -> VaRBacktestingCalculationResult:
        """Calculate VaR backtesting and persist results.

        Manages the complete workflow from backtest input to persisted
        VaRBacktestingResult. Creates a CalculationRun for lineage and
        audit trail.

        Parameters
        ----------
        backtest_input : BacktestInput
            VaR forecasts and realised P&Ls, pre-validated.
        fund_id : int
            Fund identifier for lineage.
        risk_methodology : RiskMethodology
            Risk methodology version for lineage.
        position_snapshot_id : int
            FK to PositionSnapshot for lineage.
        nav_snapshot_id : int
            FK to NAVSnapshot for lineage.
        created_by : str
            User/system identifier for audit trail.

        Returns
        -------
        VaRBacktestingCalculationResult
            In-memory results (counting, Kupiec, Christoffersen) plus
            calculation_run_id. ORM result is persisted internally.

        Raises
        ------
        (ValidationError)
            If backtest_input is invalid (caught by Pydantic).
        (database errors)
            If persistence fails.

        Notes
        -----
        On calculation failure after CalculationRun creation: marks run as FAILED,
        does not insert VaRBacktestingResult, and re-raises the exception.
        """
        # Use first forecast date as valuation date for lineage
        valuation_date = backtest_input.var_forecasts[0].forecast_date

        # Create CalculationRun with status RUNNING
        calc_repo = CalculationRunRepository(self.session_factory)
        calculation_run = CalculationRun(
            fund_id=fund_id,
            valuation_date=valuation_date,
            calculation_type=CalculationTypeEnum.VAR_BACKTEST,
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
            # Run VaRBacktestingEngine
            backtest_result = self.backtesting_engine.calculate(backtest_input)

            # Run KupiecTest
            kupiec_result = self.kupiec_test.calculate(
                num_observations=backtest_result.num_valid_aligned,
                num_breaches=backtest_result.num_breaches,
                expected_breach_probability=backtest_result.expected_breach_probability,
            )

            # Run ChristoffersenTest
            christoffersen_result = self.christoffersen_test.calculate(backtest_result)

            # Map to ORM and persist
            orm_result = map_backtest_result_to_orm(
                backtest_result,
                kupiec_result,
                christoffersen_result,
                calculation_run_id=calculation_run_id,
                fund_id=fund_id,
            )
            backtest_repo = VaRBacktestingResultRepository(self.session_factory)
            backtest_repo.insert(orm_result)

            # Mark calculation run COMPLETED
            calc_repo.update_status(calculation_run_id, CalculationStatusEnum.COMPLETED)

            return VaRBacktestingCalculationResult(
                backtest_result=backtest_result,
                kupiec_result=kupiec_result,
                christoffersen_result=christoffersen_result,
                calculation_run_id=calculation_run_id,
            )

        except Exception:
            # Mark calculation run FAILED
            calc_repo.update_status(calculation_run_id, CalculationStatusEnum.FAILED)
            raise
