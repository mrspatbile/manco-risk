"""Tests for VaR backtesting calculation service.

Tests the end-to-end workflow from BacktestInput through persistence.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from manco_risk.database.backtesting_service import (
    VaRBacktestingCalculationResult,
    VaRBacktestingCalculationService,
)
from manco_risk.database.models import (
    CalculationStatusEnum,
    CalculationTypeEnum,
    Fund,
    NAVSnapshot,
    PositionSnapshot,
    RiskMethodology,
)
from manco_risk.database.repositories import CalculationRunRepository
from manco_risk.database.session import SessionFactory, create_database_engine, initialize_database
from manco_risk.risk.models.backtest_input import (
    BacktestInput,
    RealisedPnLObservation,
    VaRForecastObservation,
)
from manco_risk.risk.models.backtest_result import BacktestResult


@pytest.fixture
def session_factory() -> SessionFactory:
    """Create an in-memory SQLite session factory for testing."""
    engine = create_database_engine("sqlite:///:memory:")
    initialize_database(engine)
    return SessionFactory(engine)


@pytest.fixture
def test_fund(session_factory: SessionFactory) -> Fund:
    """Create a test fund."""
    from manco_risk.database.repositories import FundRepository

    fund = Fund(
        fund_name="Test Backtest Fund",
        base_currency="EUR",
        domicile="Ireland",
        fund_regime="AIFM",
    )
    repo = FundRepository(session_factory)
    return repo.insert(fund)


@pytest.fixture
def test_methodology(session_factory: SessionFactory, test_fund: Fund) -> RiskMethodology:
    """Create a test risk methodology."""
    from manco_risk.database.repositories import RiskMethodologyRepository

    methodology = RiskMethodology(
        effective_date=date(2024, 1, 1),
        fund_id=test_fund.fund_id,
        var_confidence_level=Decimal("0.95"),
        var_lookback_days=250,
        var_horizon_days=1,
        es_method="historical",
        es_lookback_days=250,
        es_horizon_days=1,
        backtesting_window_days=250,
        fx_conversion_method="eod_spot",
        missing_data_handling="strict_fail",
        created_date=date(2024, 1, 1),
        created_by="test",
    )
    repo = RiskMethodologyRepository(session_factory)
    return repo.insert(methodology)


@pytest.fixture
def test_position_snapshot(session_factory: SessionFactory, test_fund: Fund) -> PositionSnapshot:
    """Create a test position snapshot."""
    from manco_risk.database.repositories import PositionSnapshotRepository

    pos_snap = PositionSnapshot(
        fund_id=test_fund.fund_id,
        valuation_date=date(2024, 6, 1),
        source_extract_date=date(2024, 6, 1),
        load_timestamp=datetime.now(),
        num_positions=1,
    )
    repo = PositionSnapshotRepository(session_factory)
    return repo.insert(pos_snap)


@pytest.fixture
def test_nav_snapshot(session_factory: SessionFactory, test_fund: Fund) -> NAVSnapshot:
    """Create a test NAV snapshot."""
    from manco_risk.database.repositories import NAVSnapshotRepository

    nav_snap = NAVSnapshot(
        fund_id=test_fund.fund_id,
        nav_date=date(2024, 6, 1),
        nav_value=Decimal("1000000"),
        nav_source="test",
        nav_timestamp=datetime.now(),
    )
    repo = NAVSnapshotRepository(session_factory)
    return repo.insert(nav_snap)


def create_backtest_input(num_obs: int) -> BacktestInput:
    """Create a test BacktestInput with num_obs observations."""
    start_date = date(2024, 1, 1)

    var_forecasts = [
        VaRForecastObservation(
            forecast_date=start_date + timedelta(days=i),
            var_value=Decimal("0.025"),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        for i in range(num_obs)
    ]

    realised_pnls = [
        RealisedPnLObservation(
            pnl_date=start_date + timedelta(days=i),
            realised_pnl=Decimal("-0.030") if i % 5 == 0 else Decimal("-0.010"),
        )
        for i in range(num_obs)
    ]

    return BacktestInput(
        var_forecasts=var_forecasts,
        realised_pnls=realised_pnls,
        confidence_level=Decimal("0.95"),
        horizon_days=1,
    )


class TestVaRBacktestingCalculationService:
    """Tests for VaRBacktestingCalculationService."""

    def test_happy_path_persists_one_backtest_result(
        self,
        session_factory: SessionFactory,
        test_fund: Fund,
        test_methodology: RiskMethodology,
        test_position_snapshot: PositionSnapshot,
        test_nav_snapshot: NAVSnapshot,
    ) -> None:
        """Happy path: valid input produces persisted backtest result."""
        backtest_input = create_backtest_input(100)
        service = VaRBacktestingCalculationService(session_factory)

        result = service.calculate_and_persist_backtest(
            backtest_input=backtest_input,
            fund_id=test_fund.fund_id,
            risk_methodology=test_methodology,
            position_snapshot_id=test_position_snapshot.position_snapshot_id,
            nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
            created_by="test",
        )

        # Verify result structure
        assert isinstance(result, VaRBacktestingCalculationResult)
        assert isinstance(result.backtest_result, BacktestResult)
        assert result.backtest_result.num_valid_aligned == 100
        assert result.kupiec_result is not None
        assert result.christoffersen_result is not None
        assert result.calculation_run_id > 0

    def test_returned_service_result_includes_all_three_results(
        self,
        session_factory: SessionFactory,
        test_fund: Fund,
        test_methodology: RiskMethodology,
        test_position_snapshot: PositionSnapshot,
        test_nav_snapshot: NAVSnapshot,
    ) -> None:
        """Service result includes counting, Kupiec, and Christoffersen results."""
        backtest_input = create_backtest_input(50)
        service = VaRBacktestingCalculationService(session_factory)

        result = service.calculate_and_persist_backtest(
            backtest_input=backtest_input,
            fund_id=test_fund.fund_id,
            risk_methodology=test_methodology,
            position_snapshot_id=test_position_snapshot.position_snapshot_id,
            nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
            created_by="test",
        )

        # All three calculation results present
        assert result.backtest_result.num_breaches >= 0
        assert result.kupiec_result.lr_statistic >= 0
        assert result.christoffersen_result.uc_test_statistic >= 0

    def test_persisted_orm_row_matches_pure_results(
        self,
        session_factory: SessionFactory,
        test_fund: Fund,
        test_methodology: RiskMethodology,
        test_position_snapshot: PositionSnapshot,
        test_nav_snapshot: NAVSnapshot,
    ) -> None:
        """Persisted ORM row matches the pure calculation results."""
        backtest_input = create_backtest_input(80)
        service = VaRBacktestingCalculationService(session_factory)

        service_result = service.calculate_and_persist_backtest(
            backtest_input=backtest_input,
            fund_id=test_fund.fund_id,
            risk_methodology=test_methodology,
            position_snapshot_id=test_position_snapshot.position_snapshot_id,
            nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
            created_by="test",
        )

        # Retrieve persisted result
        from manco_risk.database.repositories import VaRBacktestingResultRepository

        repo = VaRBacktestingResultRepository(session_factory)
        persisted_results = repo.find_by_calculation_run(service_result.calculation_run_id)

        assert len(persisted_results) == 1
        orm_result = persisted_results[0]

        # Verify ORM fields match pure results
        assert orm_result.total_observations == service_result.backtest_result.num_valid_aligned
        assert orm_result.num_exceptions == service_result.backtest_result.num_breaches
        # Note: ORM uses NUMERIC(18, 8) precision, so test with approximate equality
        assert abs(
            orm_result.kupiec_test_statistic - service_result.kupiec_result.lr_statistic
        ) < Decimal("0.00001")
        assert abs(
            orm_result.christoffersen_cc_test_statistic
            - service_result.christoffersen_result.cc_test_statistic
        ) < Decimal("0.00001")

    def test_calculation_run_is_completed_on_success(
        self,
        session_factory: SessionFactory,
        test_fund: Fund,
        test_methodology: RiskMethodology,
        test_position_snapshot: PositionSnapshot,
        test_nav_snapshot: NAVSnapshot,
    ) -> None:
        """CalculationRun is marked COMPLETED on successful completion."""
        backtest_input = create_backtest_input(60)
        service = VaRBacktestingCalculationService(session_factory)

        result = service.calculate_and_persist_backtest(
            backtest_input=backtest_input,
            fund_id=test_fund.fund_id,
            risk_methodology=test_methodology,
            position_snapshot_id=test_position_snapshot.position_snapshot_id,
            nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
            created_by="test",
        )

        calc_repo = CalculationRunRepository(session_factory)
        calc_run = calc_repo.find_by_id(result.calculation_run_id)

        assert calc_run.status == CalculationStatusEnum.COMPLETED

    def test_calculation_run_marked_failed_on_error(
        self,
        session_factory: SessionFactory,
        test_fund: Fund,
        test_methodology: RiskMethodology,
        test_position_snapshot: PositionSnapshot,
        test_nav_snapshot: NAVSnapshot,
    ) -> None:
        """CalculationRun is marked FAILED if exception occurs after run creation."""
        # Create invalid input: more than 100% breach rate triggers engine error
        backtest_input = create_backtest_input(10)
        service = VaRBacktestingCalculationService(session_factory)

        # Inject a failure by monkeypatching the engine
        original_calculate = service.backtesting_engine.calculate

        def failing_calculate(inp: BacktestInput) -> BacktestResult:
            raise RuntimeError("Simulated engine failure")

        service.backtesting_engine.calculate = failing_calculate  # type: ignore

        with pytest.raises(RuntimeError, match="Simulated engine failure"):
            service.calculate_and_persist_backtest(
                backtest_input=backtest_input,
                fund_id=test_fund.fund_id,
                risk_methodology=test_methodology,
                position_snapshot_id=test_position_snapshot.position_snapshot_id,
                nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
                created_by="test",
            )

        # Restore original method
        service.backtesting_engine.calculate = original_calculate

        # Verify run was marked FAILED (get all runs for this fund)
        calc_repo = CalculationRunRepository(session_factory)
        from manco_risk.database.models import CalculationRun as CalcRunModel

        with calc_repo.session_factory.session_scope() as session:
            runs = (
                session.query(CalcRunModel)
                .filter(CalcRunModel.fund_id == test_fund.fund_id)
                .filter(CalcRunModel.calculation_type == CalculationTypeEnum.VAR_BACKTEST)
                .all()
            )
            session.expunge_all()

        # Should have one run marked FAILED
        assert len(runs) == 1
        assert runs[0].status == CalculationStatusEnum.FAILED

    def test_failure_inserts_no_backtest_result(
        self,
        session_factory: SessionFactory,
        test_fund: Fund,
        test_methodology: RiskMethodology,
        test_position_snapshot: PositionSnapshot,
        test_nav_snapshot: NAVSnapshot,
    ) -> None:
        """On failure after run creation, no VaRBacktestingResult is persisted."""
        backtest_input = create_backtest_input(10)
        service = VaRBacktestingCalculationService(session_factory)

        # Inject failure in engine
        original_calculate = service.backtesting_engine.calculate

        def failing_calculate(inp: BacktestInput) -> BacktestResult:
            raise RuntimeError("Simulated engine failure")

        service.backtesting_engine.calculate = failing_calculate  # type: ignore

        with pytest.raises(RuntimeError):
            service.calculate_and_persist_backtest(
                backtest_input=backtest_input,
                fund_id=test_fund.fund_id,
                risk_methodology=test_methodology,
                position_snapshot_id=test_position_snapshot.position_snapshot_id,
                nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
                created_by="test",
            )

        service.backtesting_engine.calculate = original_calculate

        # Verify no backtest result was persisted
        from manco_risk.database.repositories import VaRBacktestingResultRepository

        repo = VaRBacktestingResultRepository(session_factory)
        from manco_risk.database.models import VaRBacktestingResult

        with repo.session_factory.session_scope() as session:
            count = session.query(VaRBacktestingResult).count()
            session.expunge_all()

        assert count == 0

    def test_calculation_run_has_correct_metadata(
        self,
        session_factory: SessionFactory,
        test_fund: Fund,
        test_methodology: RiskMethodology,
        test_position_snapshot: PositionSnapshot,
        test_nav_snapshot: NAVSnapshot,
    ) -> None:
        """CalculationRun stores correct metadata (fund_id, methodology, snapshots)."""
        backtest_input = create_backtest_input(50)
        service = VaRBacktestingCalculationService(session_factory)

        result = service.calculate_and_persist_backtest(
            backtest_input=backtest_input,
            fund_id=test_fund.fund_id,
            risk_methodology=test_methodology,
            position_snapshot_id=test_position_snapshot.position_snapshot_id,
            nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
            created_by="service_test",
        )

        calc_repo = CalculationRunRepository(session_factory)
        calc_run = calc_repo.find_by_id(result.calculation_run_id)

        assert calc_run.fund_id == test_fund.fund_id
        assert calc_run.calculation_type == CalculationTypeEnum.VAR_BACKTEST
        assert calc_run.methodology_version_id == test_methodology.methodology_version_id
        assert calc_run.position_snapshot_id == test_position_snapshot.position_snapshot_id
        assert calc_run.nav_snapshot_id == test_nav_snapshot.nav_snapshot_id
        assert calc_run.created_by == "service_test"
