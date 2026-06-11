"""Tests for fixed-income stress calculation service.

End-to-end: portfolio → engine → mapper → ORM → database.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from manco_risk.database.models import (
    CalculationStatusEnum,
    CalculationTypeEnum,
    Fund,
    NAVSnapshot,
    PositionSnapshot,
    RiskMethodology,
    StressTestAssetScopeEnum,
)
from manco_risk.database.repositories import CalculationRunRepository, StressTestResultRepository
from manco_risk.database.session import SessionFactory, create_database_engine, initialize_database
from manco_risk.database.stress_calculation_service import (
    StressTestCalculationService,
)
from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.exceptions import UnsupportedAssetClassError
from manco_risk.risk.models.fixed_income_stress_scenario import FixedIncomeStressScenario


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
        fund_name="Test FI Stress Fund",
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

    snapshot = PositionSnapshot(
        fund_id=test_fund.fund_id,
        valuation_date=date(2024, 1, 15),
        source_extract_date=date(2024, 1, 15),
        source_extract_filename="positions.csv",
        load_timestamp=datetime.now(),
        num_positions=3,
    )
    repo = PositionSnapshotRepository(session_factory)
    return repo.insert(snapshot)


@pytest.fixture
def test_nav_snapshot(session_factory: SessionFactory, test_fund: Fund) -> NAVSnapshot:
    """Create a test NAV snapshot."""
    from manco_risk.database.repositories import NAVSnapshotRepository

    snapshot = NAVSnapshot(
        fund_id=test_fund.fund_id,
        nav_date=date(2024, 1, 15),
        nav_value=Decimal("10000000.00"),
        nav_source="test",
        nav_timestamp=datetime.now(),
    )
    repo = NAVSnapshotRepository(session_factory)
    return repo.insert(snapshot)


@pytest.fixture
def test_portfolio() -> RiskReadyPortfolio:
    """Create a test risk-ready portfolio with fixed-income positions."""
    from manco_risk.etl.enriched_position import EnrichedPosition

    positions = [
        EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="XS0000000001",
            valuation_date="2024-01-15",
            quantity=Decimal("100"),
            market_value=Decimal("102000.00"),
            position_currency="EUR",
            asset_class="BOND",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("102000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.0102"),
            modified_duration=Decimal("5.2"),
            spread_duration=Decimal("4.8"),
        ),
        EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=2,
            isin="XS0000000002",
            valuation_date="2024-01-15",
            quantity=Decimal("50"),
            market_value=Decimal("51000.00"),
            position_currency="EUR",
            asset_class="BOND",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("51000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.0051"),
            modified_duration=Decimal("3.0"),
            spread_duration=Decimal("2.8"),
        ),
        EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=3,
            isin="EUR_CASH",
            valuation_date="2024-01-15",
            quantity=Decimal("9847000"),
            market_value=Decimal("9847000.00"),
            position_currency="EUR",
            asset_class="CASH",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("9847000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.9847"),
            modified_duration=None,
            spread_duration=None,
        ),
    ]

    return RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-01-15",
        positions=positions,
        fund_base_currency="EUR",
        nav=Decimal("10000000.00"),
    )


@pytest.fixture
def test_scenarios() -> list[FixedIncomeStressScenario]:
    """Create test fixed-income stress scenarios."""
    return [
        FixedIncomeStressScenario(
            scenario_id="FI_RATE_UP_100",
            scenario_name="Rates +100bps",
            scenario_type="HYPOTHETICAL",
            scenario_source="MANAGER_DEFINED",
            shock_type="RATE_SHOCK",
            rate_shock_bps=100,
            spread_shock_bps=0,
            description="Parallel yield shift up 100bps",
        ),
        FixedIncomeStressScenario(
            scenario_id="FI_SPREAD_UP_50",
            scenario_name="Spreads +50bps",
            scenario_type="HYPOTHETICAL",
            scenario_source="MANAGER_DEFINED",
            shock_type="SPREAD_SHOCK",
            rate_shock_bps=0,
            spread_shock_bps=50,
            description="Credit spread widening 50bps",
        ),
    ]


def test_calculate_and_persist_fixed_income_stress_end_to_end(
    session_factory: SessionFactory,
    test_portfolio: RiskReadyPortfolio,
    test_scenarios: list[FixedIncomeStressScenario],
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """Full workflow: create CalculationRun, invoke engine, persist results."""
    service = StressTestCalculationService(session_factory)

    result = service.calculate_and_persist_fixed_income_stress(
        portfolio=test_portfolio,
        scenarios=test_scenarios,
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    assert result.calculation_run_id > 0
    assert result.num_results_persisted == 2


def test_fixed_income_stress_calculation_run_created(
    session_factory: SessionFactory,
    test_portfolio: RiskReadyPortfolio,
    test_scenarios: list[FixedIncomeStressScenario],
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """CalculationRun created with STRESS_TEST type and marked COMPLETED."""
    service = StressTestCalculationService(session_factory)
    calc_run_repo = CalculationRunRepository(session_factory)

    result = service.calculate_and_persist_fixed_income_stress(
        portfolio=test_portfolio,
        scenarios=test_scenarios,
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    calc_run = calc_run_repo.find_by_id(result.calculation_run_id)
    assert calc_run is not None
    assert calc_run.calculation_type == CalculationTypeEnum.STRESS_TEST
    assert calc_run.status == CalculationStatusEnum.COMPLETED


def test_fixed_income_stress_results_persisted_correctly(
    session_factory: SessionFactory,
    test_portfolio: RiskReadyPortfolio,
    test_scenarios: list[FixedIncomeStressScenario],
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """One StressTestResult per scenario with correct FI-specific fields."""
    service = StressTestCalculationService(session_factory)
    stress_result_repo = StressTestResultRepository(session_factory)

    result = service.calculate_and_persist_fixed_income_stress(
        portfolio=test_portfolio,
        scenarios=test_scenarios,
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    results = stress_result_repo.find_by_calculation_run(result.calculation_run_id)
    assert len(results) == 2

    # Check first scenario (rate shock)
    result_1 = next(r for r in results if r.scenario_id == "FI_RATE_UP_100")
    assert result_1.asset_scope == StressTestAssetScopeEnum.FIXED_INCOME
    assert result_1.rate_shock_bps == 100
    assert result_1.spread_shock_bps == 0
    assert result_1.shock_rate is None
    assert result_1.shock_type == "RATE_SHOCK"
    assert result_1.total_rate_pnl is not None
    assert result_1.total_credit_pnl is not None
    assert result_1.num_positions_stressed == 2
    assert result_1.num_cash_positions == 1

    # Check second scenario (spread shock)
    result_2 = next(r for r in results if r.scenario_id == "FI_SPREAD_UP_50")
    assert result_2.asset_scope == StressTestAssetScopeEnum.FIXED_INCOME
    assert result_2.rate_shock_bps == 0
    assert result_2.spread_shock_bps == 50
    assert result_2.shock_rate is None
    assert result_2.shock_type == "SPREAD_SHOCK"
    assert result_2.total_rate_pnl is not None
    assert result_2.total_credit_pnl is not None


def test_fixed_income_stress_pnl_decomposition_sums(
    session_factory: SessionFactory,
    test_portfolio: RiskReadyPortfolio,
    test_scenarios: list[FixedIncomeStressScenario],
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """Verify total_rate_pnl + total_credit_pnl = total_pnl."""
    service = StressTestCalculationService(session_factory)
    stress_result_repo = StressTestResultRepository(session_factory)

    result = service.calculate_and_persist_fixed_income_stress(
        portfolio=test_portfolio,
        scenarios=test_scenarios,
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    results = stress_result_repo.find_by_calculation_run(result.calculation_run_id)

    for orm_result in results:
        expected_total = orm_result.total_rate_pnl + orm_result.total_credit_pnl
        assert expected_total == orm_result.total_pnl


def test_fixed_income_stress_calculation_marks_failed_on_unsupported_asset(
    session_factory: SessionFactory,
    test_fund: Fund,
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """CalculationRun marked FAILED if engine raises UnsupportedAssetClassError."""
    from sqlalchemy import select

    from manco_risk.database.models import CalculationRun
    from manco_risk.etl.enriched_position import EnrichedPosition

    # Portfolio with unsupported EQUITY asset class
    positions = [
        EnrichedPosition(
            fund_id=test_fund.fund_id,
            position_snapshot_id=test_position_snapshot.position_snapshot_id,
            position_id=1,
            isin="US0000000001",
            valuation_date="2024-01-15",
            quantity=Decimal("100"),
            market_value=Decimal("10000.00"),
            position_currency="USD",
            asset_class="EQUITY",
            instrument_currency="USD",
            market_value_base_ccy=Decimal("10000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
            modified_duration=None,
            spread_duration=None,
        ),
    ]

    portfolio = RiskReadyPortfolio(
        fund_id=test_fund.fund_id,
        valuation_date="2024-01-15",
        positions=positions,
        fund_base_currency="EUR",
        nav=Decimal("10000.00"),
    )

    scenarios = [
        FixedIncomeStressScenario(
            scenario_id="FI_TEST",
            scenario_name="Test",
            scenario_type="HYPOTHETICAL",
            scenario_source="MANAGER_DEFINED",
            shock_type="RATE_SHOCK",
            rate_shock_bps=100,
            spread_shock_bps=0,
            description="Test",
        ),
    ]

    service = StressTestCalculationService(session_factory)

    with pytest.raises(UnsupportedAssetClassError):
        service.calculate_and_persist_fixed_income_stress(
            portfolio=portfolio,
            scenarios=scenarios,
            position_snapshot_id=test_position_snapshot.position_snapshot_id,
            nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
            risk_methodology=test_methodology,
            created_by="test_user",
        )

    # Verify CalculationRun was marked FAILED
    # Note: we query for the most recent run since we don't have access to the ID
    with session_factory.create_session() as session:
        calc_runs = session.execute(
            select(CalculationRun).order_by(CalculationRun.calculation_run_id.desc()).limit(1)
        ).scalars()
        latest_run = list(calc_runs)[0] if calc_runs else None

    assert latest_run is not None
    assert latest_run.status == CalculationStatusEnum.FAILED


def test_fixed_income_stress_shock_rate_is_null_for_all_results(
    session_factory: SessionFactory,
    test_portfolio: RiskReadyPortfolio,
    test_scenarios: list[FixedIncomeStressScenario],
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """shock_rate field is None for all FI results (not applicable to FI)."""
    service = StressTestCalculationService(session_factory)
    stress_result_repo = StressTestResultRepository(session_factory)

    result = service.calculate_and_persist_fixed_income_stress(
        portfolio=test_portfolio,
        scenarios=test_scenarios,
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    results = stress_result_repo.find_by_calculation_run(result.calculation_run_id)

    for orm_result in results:
        assert orm_result.shock_rate is None


def test_fixed_income_stress_position_counts_populated(
    session_factory: SessionFactory,
    test_portfolio: RiskReadyPortfolio,
    test_scenarios: list[FixedIncomeStressScenario],
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """num_positions_stressed and num_cash_positions stored for audit."""
    service = StressTestCalculationService(session_factory)
    stress_result_repo = StressTestResultRepository(session_factory)

    result = service.calculate_and_persist_fixed_income_stress(
        portfolio=test_portfolio,
        scenarios=test_scenarios,
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    results = stress_result_repo.find_by_calculation_run(result.calculation_run_id)

    for orm_result in results:
        assert orm_result.num_positions_stressed == 2
        assert orm_result.num_cash_positions == 1
