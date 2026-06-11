"""Tests for VaR backtesting result repository.

Tests persistence of backtesting calculations to the database.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from manco_risk.database.backtest_mappers import map_backtest_result_to_orm
from manco_risk.database.models import (
    CalculationRun,
    CalculationStatusEnum,
    CalculationTypeEnum,
    Fund,
)
from manco_risk.database.repositories import VaRBacktestingResultRepository
from manco_risk.database.session import SessionFactory, create_database_engine, initialize_database
from manco_risk.risk.models.backtest_result import BacktestObservation, BacktestResult
from manco_risk.risk.models.christoffersen_test import ChristoffersenTestResult, TransitionMatrix
from manco_risk.risk.models.kupiec_test import KupiecTestResult


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
        fund_name="Test Fund",
        base_currency="EUR",
        domicile="Ireland",
        fund_regime="AIFM",
    )
    repo = FundRepository(session_factory)
    return repo.insert(fund)


@pytest.fixture
def test_calculation_run(session_factory: SessionFactory, test_fund: Fund) -> CalculationRun:
    """Create a test calculation run."""
    from datetime import datetime

    from manco_risk.database.models import NAVSnapshot, PositionSnapshot, RiskMethodology
    from manco_risk.database.repositories import (
        CalculationRunRepository,
        NAVSnapshotRepository,
        PositionSnapshotRepository,
        RiskMethodologyRepository,
    )

    # Create position snapshot
    pos_snap = PositionSnapshot(
        fund_id=test_fund.fund_id,
        valuation_date=date(2024, 6, 1),
        source_extract_date=date(2024, 6, 1),
        load_timestamp=datetime.now(),
        num_positions=1,
    )
    pos_repo = PositionSnapshotRepository(session_factory)
    pos_snap = pos_repo.insert(pos_snap)

    # Create NAV snapshot
    nav_snap = NAVSnapshot(
        fund_id=test_fund.fund_id,
        nav_date=date(2024, 6, 1),
        nav_value=Decimal("1000000"),
        nav_source="test",
        nav_timestamp=datetime.now(),
    )
    nav_repo = NAVSnapshotRepository(session_factory)
    nav_snap = nav_repo.insert(nav_snap)

    # Create methodology
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
    method_repo = RiskMethodologyRepository(session_factory)
    methodology = method_repo.insert(methodology)

    # Create calculation run
    calc_run = CalculationRun(
        fund_id=test_fund.fund_id,
        valuation_date=date(2024, 6, 1),
        calculation_type=CalculationTypeEnum.VAR_BACKTEST,
        created_timestamp=datetime.now(),
        methodology_version_id=methodology.methodology_version_id,
        position_snapshot_id=pos_snap.position_snapshot_id,
        nav_snapshot_id=nav_snap.nav_snapshot_id,
        status=CalculationStatusEnum.RUNNING,
        created_by="test",
    )
    calc_repo = CalculationRunRepository(session_factory)
    return calc_repo.insert(calc_run)


def create_backtest_result(num_obs: int) -> BacktestResult:
    """Create a minimal test BacktestResult."""
    start_date = date(2024, 1, 1)
    aligned_obs = [
        BacktestObservation(
            observation_date=start_date + timedelta(days=i),
            var_value=Decimal("0.025"),
            realised_pnl=Decimal("-0.030") if i % 5 == 0 else Decimal("-0.010"),
            is_breach=i % 5 == 0,
        )
        for i in range(num_obs)
    ]

    num_breaches = sum(1 for obs in aligned_obs if obs.is_breach)
    return BacktestResult(
        num_var_forecasts=num_obs,
        num_pnl_observations=num_obs,
        num_valid_aligned=num_obs,
        num_breaches=num_breaches,
        num_non_breaches=num_obs - num_breaches,
        expected_breach_probability=Decimal("0.05"),
        expected_breach_count=Decimal(num_obs) * Decimal("0.05"),
        breach_ratio=Decimal(num_breaches) / Decimal(num_obs) if num_obs > 0 else None,
        backtest_start_date=start_date,
        backtest_end_date=start_date + timedelta(days=num_obs - 1),
        breach_dates=[
            aligned_obs[i].observation_date for i, obs in enumerate(aligned_obs) if obs.is_breach
        ],
        missing_var_dates=[],
        missing_pnl_dates=[],
        aligned_observations=aligned_obs,
    )


class TestVaRBacktestingResultRepository:
    """Tests for VaRBacktestingResultRepository."""

    def test_insert_and_retrieve(
        self, session_factory: SessionFactory, test_calculation_run: CalculationRun, test_fund: Fund
    ) -> None:
        """Insert and retrieve a backtest result."""
        backtest_result = create_backtest_result(100)
        kupiec_result = KupiecTestResult(
            num_observations=100,
            num_breaches=5,
            expected_breach_probability=Decimal("0.05"),
            observed_breach_probability=Decimal("0.05"),
            lr_statistic=Decimal("0.0"),
            p_value=Decimal("1.0"),
            alpha=Decimal("0.05"),
            reject_null=False,
        )
        christoffersen_result = ChristoffersenTestResult(
            num_observations=100,
            num_breaches=5,
            expected_breach_probability=Decimal("0.05"),
            transition_matrix=TransitionMatrix(n00=95, n01=5, n10=0, n11=0),
            uc_test_statistic=Decimal("0.0"),
            uc_p_value=Decimal("1.0"),
            ind_test_statistic=Decimal("0.0"),
            ind_p_value=Decimal("1.0"),
            cc_test_statistic=Decimal("0.0"),
            cc_p_value=Decimal("1.0"),
            alpha=Decimal("0.05"),
            reject_uc=False,
            reject_ind=False,
            reject_cc=False,
        )

        orm_result = map_backtest_result_to_orm(
            backtest_result,
            kupiec_result,
            christoffersen_result,
            test_calculation_run.calculation_run_id,
            test_fund.fund_id,
        )

        repo = VaRBacktestingResultRepository(session_factory)
        inserted = repo.insert(orm_result)

        assert inserted.backtest_result_id is not None
        assert inserted.calculation_run_id == test_calculation_run.calculation_run_id
        assert inserted.fund_id == test_fund.fund_id
        assert inserted.total_observations == 100
        assert inserted.num_exceptions == 20  # 20% of 100

    def test_find_by_calculation_run_empty(
        self, session_factory: SessionFactory, test_calculation_run: CalculationRun
    ) -> None:
        """Find returns empty list when no results exist."""
        repo = VaRBacktestingResultRepository(session_factory)
        results = repo.find_by_calculation_run(test_calculation_run.calculation_run_id)
        assert results == []

    def test_find_by_calculation_run_with_results(
        self, session_factory: SessionFactory, test_calculation_run: CalculationRun, test_fund: Fund
    ) -> None:
        """Find returns all results for a calculation run."""
        backtest_result = create_backtest_result(50)
        kupiec_result = KupiecTestResult(
            num_observations=50,
            num_breaches=3,
            expected_breach_probability=Decimal("0.05"),
            observed_breach_probability=Decimal("0.06"),
            lr_statistic=Decimal("0.1"),
            p_value=Decimal("0.75"),
            alpha=Decimal("0.05"),
            reject_null=False,
        )
        christoffersen_result = ChristoffersenTestResult(
            num_observations=50,
            num_breaches=3,
            expected_breach_probability=Decimal("0.05"),
            transition_matrix=TransitionMatrix(n00=45, n01=5, n10=0, n11=0),
            uc_test_statistic=Decimal("0.1"),
            uc_p_value=Decimal("0.75"),
            ind_test_statistic=Decimal("0.0"),
            ind_p_value=Decimal("1.0"),
            cc_test_statistic=Decimal("0.1"),
            cc_p_value=Decimal("0.95"),
            alpha=Decimal("0.05"),
            reject_uc=False,
            reject_ind=False,
            reject_cc=False,
        )

        orm_result = map_backtest_result_to_orm(
            backtest_result,
            kupiec_result,
            christoffersen_result,
            test_calculation_run.calculation_run_id,
            test_fund.fund_id,
        )

        repo = VaRBacktestingResultRepository(session_factory)
        repo.insert(orm_result)

        results = repo.find_by_calculation_run(test_calculation_run.calculation_run_id)
        assert len(results) == 1
        assert results[0].total_observations == 50

    def test_cascade_delete_on_calculation_run_delete(
        self, session_factory: SessionFactory, test_calculation_run: CalculationRun, test_fund: Fund
    ) -> None:
        """Backtest result is deleted when calculation run is deleted (CASCADE)."""
        backtest_result = create_backtest_result(50)
        kupiec_result = KupiecTestResult(
            num_observations=50,
            num_breaches=3,
            expected_breach_probability=Decimal("0.05"),
            observed_breach_probability=Decimal("0.06"),
            lr_statistic=Decimal("0.1"),
            p_value=Decimal("0.75"),
            alpha=Decimal("0.05"),
            reject_null=False,
        )
        christoffersen_result = ChristoffersenTestResult(
            num_observations=50,
            num_breaches=3,
            expected_breach_probability=Decimal("0.05"),
            transition_matrix=TransitionMatrix(n00=45, n01=5, n10=0, n11=0),
            uc_test_statistic=Decimal("0.1"),
            uc_p_value=Decimal("0.75"),
            ind_test_statistic=Decimal("0.0"),
            ind_p_value=Decimal("1.0"),
            cc_test_statistic=Decimal("0.1"),
            cc_p_value=Decimal("0.95"),
            alpha=Decimal("0.05"),
            reject_uc=False,
            reject_ind=False,
            reject_cc=False,
        )

        orm_result = map_backtest_result_to_orm(
            backtest_result,
            kupiec_result,
            christoffersen_result,
            test_calculation_run.calculation_run_id,
            test_fund.fund_id,
        )

        repo = VaRBacktestingResultRepository(session_factory)
        inserted = repo.insert(orm_result)

        assert inserted.backtest_result_id is not None
        assert len(repo.find_by_calculation_run(test_calculation_run.calculation_run_id)) == 1
