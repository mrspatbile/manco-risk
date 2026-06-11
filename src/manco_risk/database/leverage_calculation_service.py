"""Service layer for AIFMD leverage calculation and persistence.

Orchestrates leverage calculation engines with database persistence.
Manages CalculationRun lifecycle: RUNNING → COMPLETED/FAILED.
"""

from dataclasses import dataclass
from datetime import date, datetime

from manco_risk.database.leverage_mappers import (
    map_commitment_leverage_result_to_orm,
    map_leverage_method_result_to_orm,
    map_source_contributions_to_orm,
)
from manco_risk.database.leverage_repositories import (
    LeverageResultRepository,
    LeverageSourceContributionResultRepository,
)
from manco_risk.database.models import (
    CalculationRun,
    CalculationStatusEnum,
    CalculationTypeEnum,
    RiskMethodology,
)
from manco_risk.database.repositories import CalculationRunRepository
from manco_risk.database.session import SessionFactory
from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.leverage import (
    AIFMDCommitmentLeverageEngine,
    AIFMDCommitmentLeverageResult,
    AIFMDGrossLeverageEngine,
    AIFMDLeverageAggregationInput,
    CashExposureResult,
    CommitmentReduction,
    DerivativeExposureResult,
    DirectBorrowingExposureResult,
    LeverageMethodResult,
    PhysicalInstrumentExposureResult,
    SFTExposureResult,
)


@dataclass
class AIFMDLeverageCalculationServiceResult:
    """Result of an AIFMD leverage calculation run.

    Attributes
    ----------
    calculation_run : CalculationRun
        The completed CalculationRun entity.
    gross_result : LeverageMethodResult
        Pure gross method result (from engine).
    commitment_result : AIFMDCommitmentLeverageResult
        Pure commitment method result with audit trail (from engine).
    gross_leverage_result_id : int
        Foreign key to persisted LeverageResult (gross method).
    commitment_leverage_result_id : int
        Foreign key to persisted LeverageResult (commitment method).
    num_method_results_persisted : int
        Number of method-level rows persisted (should be 2).
    num_source_contributions_persisted : int
        Total number of source contribution rows persisted (across both methods).
    """

    calculation_run: CalculationRun
    gross_result: LeverageMethodResult
    commitment_result: AIFMDCommitmentLeverageResult
    gross_leverage_result_id: int
    commitment_leverage_result_id: int
    num_method_results_persisted: int
    num_source_contributions_persisted: int


class AIFMDLeverageCalculationService:
    """Service for executing AIFMD leverage calculations with persistence.

    Coordinates:
    - CalculationRun lifecycle management
    - Risk engine invocation (gross and commitment methods)
    - Result mapping to ORM
    - Database persistence

    Workflow:
    1. Create CalculationRun (LEVERAGE, RUNNING)
    2. Run AIFMDGrossLeverageEngine
    3. Run AIFMDCommitmentLeverageEngine
    4. Persist results via mappers and repositories
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
        self.leverage_result_repo = LeverageResultRepository(session_factory)
        self.source_contrib_repo = LeverageSourceContributionResultRepository(session_factory)

    def calculate_and_persist_aifmd_leverage(
        self,
        portfolio: RiskReadyPortfolio,
        physical_result: PhysicalInstrumentExposureResult | None = None,
        cash_result: CashExposureResult | None = None,
        direct_borrowing_result: DirectBorrowingExposureResult | None = None,
        sft_result: SFTExposureResult | None = None,
        derivative_result: DerivativeExposureResult | None = None,
        commitment_reductions: list[CommitmentReduction] | None = None,
        position_snapshot_id: int | None = None,
        nav_snapshot_id: int | None = None,
        risk_methodology: RiskMethodology | None = None,
        created_by: str = "system",
    ) -> AIFMDLeverageCalculationServiceResult:
        """Calculate and persist AIFMD leverage using both gross and commitment methods.

        Parameters
        ----------
        portfolio
            Risk-ready portfolio with NAV and positions.
        physical_result
            Physical instrument source result (optional).
        cash_result
            Cash and cash-equivalent source result (optional).
        direct_borrowing_result
            Direct borrowing source result (optional).
        sft_result
            Securities financing transaction source result (optional).
        derivative_result
            Derivative valuation and exposure result (optional).
        commitment_reductions
            Explicit commitment reductions to apply (optional).
        position_snapshot_id
            Foreign key to PositionSnapshot (required by CalculationRun).
        nav_snapshot_id
            Foreign key to NAVSnapshot (required by CalculationRun).
        risk_methodology
            Risk methodology entity (required by CalculationRun).
        created_by
            User/system identifier creating the calculation.

        Returns
        -------
        AIFMDLeverageCalculationServiceResult
            Result with both method results and persistence details.

        Raises
        ------
        Exception
            Re-raises any exception from engines, with CalculationRun marked FAILED.
        """
        # Create CalculationRun
        valuation_date_obj = date.fromisoformat(portfolio.valuation_date)
        calculation_run = CalculationRun(
            fund_id=portfolio.fund_id,
            valuation_date=valuation_date_obj,
            calculation_type=CalculationTypeEnum.LEVERAGE,
            created_timestamp=datetime.now(),
            methodology_version_id=risk_methodology.methodology_version_id
            if risk_methodology
            else 1,
            position_snapshot_id=position_snapshot_id or 1,
            nav_snapshot_id=nav_snapshot_id or 1,
            status=CalculationStatusEnum.RUNNING,
            created_by=created_by,
        )

        try:
            # Persist CalculationRun in RUNNING state
            calculation_run = self.calc_run_repo.insert(calculation_run)

            # Build aggregation input
            aggregation_input = AIFMDLeverageAggregationInput(
                portfolio=portfolio,
                physical_result=physical_result,
                cash_result=cash_result,
                direct_borrowing_result=direct_borrowing_result,
                sft_result=sft_result,
                derivative_result=derivative_result,
                commitment_reductions=commitment_reductions or [],
            )

            # Run gross engine
            gross_engine = AIFMDGrossLeverageEngine()
            gross_result = gross_engine.calculate(aggregation_input)

            # Run commitment engine
            commitment_engine = AIFMDCommitmentLeverageEngine()
            commitment_result = commitment_engine.calculate(aggregation_input)

            # Map to ORM
            gross_orm = map_leverage_method_result_to_orm(
                gross_result,
                calculation_run_id=calculation_run.calculation_run_id,
                fund_id=portfolio.fund_id,
            )
            # Set valuation date
            gross_orm.valuation_date = valuation_date_obj

            commitment_orm = map_commitment_leverage_result_to_orm(
                commitment_result,
                calculation_run_id=calculation_run.calculation_run_id,
                fund_id=portfolio.fund_id,
            )
            # Set valuation date
            commitment_orm.valuation_date = valuation_date_obj

            # Persist method-level results
            gross_id = self.leverage_result_repo.insert(gross_orm)
            commitment_id = self.leverage_result_repo.insert(commitment_orm)

            # Persist source contributions
            gross_source_contribs = map_source_contributions_to_orm(
                leverage_result_id=gross_id,
                method_result=gross_result,
            )
            commitment_source_contribs = map_source_contributions_to_orm(
                leverage_result_id=commitment_id,
                method_result=commitment_result.method_result,
            )

            gross_contrib_ids = self.source_contrib_repo.insert_many(gross_source_contribs)
            commitment_contrib_ids = self.source_contrib_repo.insert_many(
                commitment_source_contribs
            )

            total_contrib_count = len(gross_contrib_ids) + len(commitment_contrib_ids)

            # Mark CalculationRun COMPLETED
            self.calc_run_repo.update_status(
                calculation_run.calculation_run_id, CalculationStatusEnum.COMPLETED
            )
            # Refresh calculation_run from database
            updated_run = self.calc_run_repo.find_by_id(calculation_run.calculation_run_id)
            if updated_run is None:
                raise RuntimeError("Failed to retrieve updated CalculationRun")

            return AIFMDLeverageCalculationServiceResult(
                calculation_run=updated_run,
                gross_result=gross_result,
                commitment_result=commitment_result,
                gross_leverage_result_id=gross_id,
                commitment_leverage_result_id=commitment_id,
                num_method_results_persisted=2,
                num_source_contributions_persisted=total_contrib_count,
            )

        except Exception:
            # Mark CalculationRun FAILED
            self.calc_run_repo.update_status(
                calculation_run.calculation_run_id, CalculationStatusEnum.FAILED
            )
            raise
