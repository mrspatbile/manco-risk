"""Service layer for stress test calculation and persistence.

Orchestrates stress test calculation engines with database persistence.
Manages CalculationRun lifecycle: RUNNING → COMPLETED/FAILED.
"""

from dataclasses import dataclass
from datetime import datetime

from manco_risk.database.models import (
    CalculationRun,
    CalculationStatusEnum,
    CalculationTypeEnum,
    RiskMethodology,
)
from manco_risk.database.repositories import (
    CalculationRunRepository,
    StressTestResultRepository,
)
from manco_risk.database.session import SessionFactory
from manco_risk.database.stress_mappers import (
    map_historical_stress_result_to_orm,
    map_reverse_stress_result_to_orm,
    map_stress_portfolio_result_to_orm,
)
from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.engines import (
    HistoricalEquityStressEngine,
    ReverseEquityStressEngine,
)
from manco_risk.risk.engines.equity_stress import EquityStressEngine
from manco_risk.risk.models import (
    HistoricalStressInput,
    ReverseStressInput,
    StressScenario,
    StressTestInput,
)


@dataclass
class StressTestCalculationResult:
    """Result of a stress test calculation run.

    Attributes
    ----------
    calculation_run_id : int
        Foreign key to CalculationRun.
    num_results_persisted : int
        Number of stress test results inserted.
    """

    calculation_run_id: int
    num_results_persisted: int


class StressTestCalculationService:
    """Service for executing stress test calculations with persistence.

    Coordinates:
    - CalculationRun lifecycle management
    - Risk engine invocation
    - Result mapping to ORM
    - Database persistence

    All methods follow a consistent workflow:
    1. Create CalculationRun (STRESS_TEST, RUNNING)
    2. Invoke risk engine
    3. Map result(s) to ORM
    4. Persist to database
    5. Mark CalculationRun COMPLETED
    6. On error: mark FAILED and re-raise
    """

    def __init__(self, session_factory: SessionFactory) -> None:
        """Initialize service with session factory.

        Parameters
        ----------
        session_factory : SessionFactory
            Session factory for database access.
        """
        self.session_factory = session_factory
        self.calc_run_repo = CalculationRunRepository(session_factory)
        self.stress_result_repo = StressTestResultRepository(session_factory)

    def calculate_and_persist_hypothetical_equity_stress(
        self,
        portfolio: RiskReadyPortfolio,
        scenarios: list[StressScenario],
        position_snapshot_id: int,
        nav_snapshot_id: int,
        risk_methodology: RiskMethodology,
        created_by: str,
    ) -> StressTestCalculationResult:
        """Calculate and persist hypothetical equity stress.

        Parameters
        ----------
        portfolio : RiskReadyPortfolio
            Risk-ready portfolio.
        scenarios : list[StressScenario]
            List of stress scenarios to apply.
        position_snapshot_id : int
            Position snapshot ID.
        nav_snapshot_id : int
            NAV snapshot ID.
        risk_methodology : RiskMethodology
            Risk methodology for this calculation.
        created_by : str
            User identifier for audit trail.

        Returns
        -------
        StressTestCalculationResult
            Calculation run ID and count of results persisted.

        Raises
        ------
        Exception
            If calculation or persistence fails; CalculationRun marked FAILED.
        """
        calculation_run = CalculationRun(
            fund_id=portfolio.fund_id,
            valuation_date=portfolio.valuation_date,
            calculation_type=CalculationTypeEnum.STRESS_TEST,
            created_timestamp=datetime.now(),
            methodology_version_id=risk_methodology.methodology_version_id,
            position_snapshot_id=position_snapshot_id,
            nav_snapshot_id=nav_snapshot_id,
            status=CalculationStatusEnum.RUNNING,
            created_by=created_by,
        )
        calculation_run = self.calc_run_repo.insert(calculation_run)

        try:
            engine = EquityStressEngine()
            stress_input = StressTestInput(portfolio=portfolio, scenarios=scenarios)
            stress_results = engine.stress(stress_input)

            orm_results = [
                map_stress_portfolio_result_to_orm(result, calculation_run.calculation_run_id)
                for result in stress_results
            ]

            result_ids = self.stress_result_repo.insert_many(orm_results)

            self.calc_run_repo.update_status(
                calculation_run.calculation_run_id, CalculationStatusEnum.COMPLETED
            )

            return StressTestCalculationResult(
                calculation_run_id=calculation_run.calculation_run_id,
                num_results_persisted=len(result_ids),
            )

        except Exception:
            self.calc_run_repo.update_status(
                calculation_run.calculation_run_id, CalculationStatusEnum.FAILED
            )
            raise

    def calculate_and_persist_reverse_equity_stress(
        self,
        portfolio: RiskReadyPortfolio,
        reverse_inputs: list[ReverseStressInput],
        position_snapshot_id: int,
        nav_snapshot_id: int,
        risk_methodology: RiskMethodology,
        created_by: str,
    ) -> StressTestCalculationResult:
        """Calculate and persist reverse equity stress.

        Parameters
        ----------
        portfolio : RiskReadyPortfolio
            Risk-ready portfolio.
        reverse_inputs : list[ReverseStressInput]
            List of reverse stress inputs (target loss percentages).
        position_snapshot_id : int
            Position snapshot ID.
        nav_snapshot_id : int
            NAV snapshot ID.
        risk_methodology : RiskMethodology
            Risk methodology for this calculation.
        created_by : str
            User identifier for audit trail.

        Returns
        -------
        StressTestCalculationResult
            Calculation run ID and count of results persisted.

        Raises
        ------
        Exception
            If calculation or persistence fails; CalculationRun marked FAILED.
        """
        calculation_run = CalculationRun(
            fund_id=portfolio.fund_id,
            valuation_date=portfolio.valuation_date,
            calculation_type=CalculationTypeEnum.STRESS_TEST,
            created_timestamp=datetime.now(),
            methodology_version_id=risk_methodology.methodology_version_id,
            position_snapshot_id=position_snapshot_id,
            nav_snapshot_id=nav_snapshot_id,
            status=CalculationStatusEnum.RUNNING,
            created_by=created_by,
        )
        calculation_run = self.calc_run_repo.insert(calculation_run)

        try:
            engine = ReverseEquityStressEngine()
            reverse_results = [engine.calculate(input) for input in reverse_inputs]

            orm_results = [
                map_reverse_stress_result_to_orm(result, calculation_run.calculation_run_id)
                for result in reverse_results
            ]

            result_ids = self.stress_result_repo.insert_many(orm_results)

            self.calc_run_repo.update_status(
                calculation_run.calculation_run_id, CalculationStatusEnum.COMPLETED
            )

            return StressTestCalculationResult(
                calculation_run_id=calculation_run.calculation_run_id,
                num_results_persisted=len(result_ids),
            )

        except Exception:
            self.calc_run_repo.update_status(
                calculation_run.calculation_run_id, CalculationStatusEnum.FAILED
            )
            raise

    def calculate_and_persist_historical_equity_stress(
        self,
        portfolio: RiskReadyPortfolio,
        historical_inputs: list[HistoricalStressInput],
        position_snapshot_id: int,
        nav_snapshot_id: int,
        risk_methodology: RiskMethodology,
        created_by: str,
    ) -> StressTestCalculationResult:
        """Calculate and persist historical equity stress.

        Parameters
        ----------
        portfolio : RiskReadyPortfolio
            Risk-ready portfolio.
        historical_inputs : list[HistoricalStressInput]
            List of historical stress inputs (windows and scenario P&Ls).
        position_snapshot_id : int
            Position snapshot ID.
        nav_snapshot_id : int
            NAV snapshot ID.
        risk_methodology : RiskMethodology
            Risk methodology for this calculation.
        created_by : str
            User identifier for audit trail.

        Returns
        -------
        StressTestCalculationResult
            Calculation run ID and count of results persisted.

        Raises
        ------
        Exception
            If calculation or persistence fails; CalculationRun marked FAILED.
        """
        calculation_run = CalculationRun(
            fund_id=portfolio.fund_id,
            valuation_date=portfolio.valuation_date,
            calculation_type=CalculationTypeEnum.STRESS_TEST,
            created_timestamp=datetime.now(),
            methodology_version_id=risk_methodology.methodology_version_id,
            position_snapshot_id=position_snapshot_id,
            nav_snapshot_id=nav_snapshot_id,
            status=CalculationStatusEnum.RUNNING,
            created_by=created_by,
        )
        calculation_run = self.calc_run_repo.insert(calculation_run)

        try:
            engine = HistoricalEquityStressEngine()
            historical_results = [engine.calculate(input) for input in historical_inputs]

            orm_results = [
                map_historical_stress_result_to_orm(result, calculation_run.calculation_run_id)
                for result in historical_results
            ]

            result_ids = self.stress_result_repo.insert_many(orm_results)

            self.calc_run_repo.update_status(
                calculation_run.calculation_run_id, CalculationStatusEnum.COMPLETED
            )

            return StressTestCalculationResult(
                calculation_run_id=calculation_run.calculation_run_id,
                num_results_persisted=len(result_ids),
            )

        except Exception:
            self.calc_run_repo.update_status(
                calculation_run.calculation_run_id, CalculationStatusEnum.FAILED
            )
            raise
