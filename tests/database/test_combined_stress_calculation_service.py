"""Tests for combined stress calculation service.

End-to-end: portfolio → CombinedStressEngine → mappers → ORM → database.

Row-count rules per scenario:
    equity + FI positions:  3 rows (EQUITY_LIKE + FIXED_INCOME + MULTI_ASSET)
    equity only:            2 rows (EQUITY_LIKE + MULTI_ASSET)
    FI only:                2 rows (FIXED_INCOME + MULTI_ASSET)
    all-cash portfolio:     1 row  (MULTI_ASSET only)
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
    StressTestResultTypeEnum,
)
from manco_risk.database.repositories import CalculationRunRepository, StressTestResultRepository
from manco_risk.database.session import SessionFactory, create_database_engine, initialize_database
from manco_risk.database.stress_calculation_service import StressTestCalculationService
from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.exceptions import UnsupportedAssetClassError
from manco_risk.risk.models.combined_stress_scenario import CombinedStressScenario
from manco_risk.risk.models.fixed_income_stress_scenario import FixedIncomeStressScenario
from manco_risk.risk.models.stress_scenario import StressScenario

# ---------------------------------------------------------------------------
# Infrastructure fixtures
# ---------------------------------------------------------------------------

BASE_CCY = "EUR"
VALUATION_DATE = "2026-06-10"
NAV = Decimal("10000000.00")


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = create_database_engine("sqlite:///:memory:")
    initialize_database(engine)
    return SessionFactory(engine)


@pytest.fixture
def test_fund(session_factory: SessionFactory) -> Fund:
    from manco_risk.database.repositories import FundRepository

    fund = Fund(
        fund_name="Combined Stress Test Fund",
        base_currency=BASE_CCY,
        domicile="Ireland",
        fund_regime="AIFM",
    )
    return FundRepository(session_factory).insert(fund)


@pytest.fixture
def test_methodology(session_factory: SessionFactory, test_fund: Fund) -> RiskMethodology:
    from manco_risk.database.repositories import RiskMethodologyRepository

    methodology = RiskMethodology(
        effective_date=date(2026, 1, 1),
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
        created_date=date(2026, 1, 1),
        created_by="test",
    )
    return RiskMethodologyRepository(session_factory).insert(methodology)


@pytest.fixture
def test_position_snapshot(session_factory: SessionFactory, test_fund: Fund) -> PositionSnapshot:
    from manco_risk.database.repositories import PositionSnapshotRepository

    snapshot = PositionSnapshot(
        fund_id=test_fund.fund_id,
        valuation_date=date(2026, 6, 10),
        source_extract_date=date(2026, 6, 10),
        source_extract_filename="positions.csv",
        load_timestamp=datetime.now(),
        num_positions=3,
    )
    return PositionSnapshotRepository(session_factory).insert(snapshot)


@pytest.fixture
def test_nav_snapshot(session_factory: SessionFactory, test_fund: Fund) -> NAVSnapshot:
    from manco_risk.database.repositories import NAVSnapshotRepository

    snapshot = NAVSnapshot(
        fund_id=test_fund.fund_id,
        nav_date=date(2026, 6, 10),
        nav_value=NAV,
        nav_source="test",
        nav_timestamp=datetime.now(),
    )
    return NAVSnapshotRepository(session_factory).insert(snapshot)


# ---------------------------------------------------------------------------
# Portfolio fixtures
# ---------------------------------------------------------------------------


def _make_equity_pos(fund_id: int, position_id: int = 1) -> EnrichedPosition:
    return EnrichedPosition(
        fund_id=fund_id,
        position_snapshot_id=1,
        position_id=position_id,
        isin="IE0031442068",
        valuation_date=VALUATION_DATE,
        quantity=Decimal("1000"),
        market_value=Decimal("2000000.00"),
        position_currency=BASE_CCY,
        asset_class="EQUITY",
        instrument_currency=BASE_CCY,
        market_value_base_ccy=Decimal("2000000.00"),
        fund_base_currency=BASE_CCY,
        weight=Decimal("0.20"),
    )


def _make_bond_pos(fund_id: int, position_id: int = 2) -> EnrichedPosition:
    return EnrichedPosition(
        fund_id=fund_id,
        position_snapshot_id=1,
        position_id=position_id,
        isin="US912828YK09",
        valuation_date=VALUATION_DATE,
        quantity=Decimal("1000"),
        market_value=Decimal("3000000.00"),
        position_currency=BASE_CCY,
        asset_class="BOND",
        instrument_currency=BASE_CCY,
        market_value_base_ccy=Decimal("3000000.00"),
        fund_base_currency=BASE_CCY,
        weight=Decimal("0.30"),
        modified_duration=Decimal("5.0"),
        spread_duration=Decimal("5.0"),
    )


def _make_cash_pos(fund_id: int, position_id: int = 3) -> EnrichedPosition:
    return EnrichedPosition(
        fund_id=fund_id,
        position_snapshot_id=1,
        position_id=position_id,
        isin="EUR_CASH",
        valuation_date=VALUATION_DATE,
        quantity=NAV,
        market_value=Decimal("5000000.00"),
        position_currency=BASE_CCY,
        asset_class="CASH",
        instrument_currency=BASE_CCY,
        market_value_base_ccy=Decimal("5000000.00"),
        fund_base_currency=BASE_CCY,
        weight=Decimal("0.50"),
    )


def _portfolio(fund_id: int, positions: list[EnrichedPosition]) -> RiskReadyPortfolio:
    return RiskReadyPortfolio(
        fund_id=fund_id,
        valuation_date=VALUATION_DATE,
        fund_base_currency=BASE_CCY,
        nav=NAV,
        positions=positions,
    )


# ---------------------------------------------------------------------------
# Scenario fixtures
# ---------------------------------------------------------------------------


def _equity_scenario() -> StressScenario:
    return StressScenario(
        scenario_id="EQ_DOWN_20",
        scenario_name="Equity down 20%",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="PARALLEL_EQUITY",
        shock_rate=Decimal("-0.20"),
        description="Parallel 20% equity shock.",
    )


def _fi_scenario() -> FixedIncomeStressScenario:
    return FixedIncomeStressScenario(
        scenario_id="FI_RATE_UP_100",
        scenario_name="Rates +100bps",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="RATE_SHOCK",
        rate_shock_bps=100,
        spread_shock_bps=0,
        description="Parallel rate shock +100bps.",
    )


def _combined_scenario(
    equity: StressScenario | None = None,
    fi: FixedIncomeStressScenario | None = None,
    scenario_id: str = "COMBINED_01",
) -> CombinedStressScenario:
    if equity is None and fi is None:
        equity = _equity_scenario()
    return CombinedStressScenario(
        scenario_id=scenario_id,
        scenario_name="Combined stress",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        description="Combined equity and FI stress.",
        equity_scenario=equity,
        fi_scenario=fi,
    )


# ---------------------------------------------------------------------------
# Happy path — equity + FI portfolio, combined scenario (3 rows per scenario)
# ---------------------------------------------------------------------------


def test_combined_stress_end_to_end(
    session_factory: SessionFactory,
    test_fund: Fund,
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """Full workflow: creates CalculationRun, persists 3 rows for 1 combined scenario."""
    portfolio = _portfolio(
        test_fund.fund_id,
        [
            _make_equity_pos(test_fund.fund_id),
            _make_bond_pos(test_fund.fund_id),
            _make_cash_pos(test_fund.fund_id),
        ],
    )
    service = StressTestCalculationService(session_factory)

    calc_result = service.calculate_and_persist_combined_stress(
        portfolio=portfolio,
        scenarios=[_combined_scenario(equity=_equity_scenario(), fi=_fi_scenario())],
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    assert calc_result.calculation_run_id > 0
    assert calc_result.num_results_persisted == 3


def test_combined_stress_three_rows_have_correct_scopes(
    session_factory: SessionFactory,
    test_fund: Fund,
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """Three rows: EQUITY_LIKE, FIXED_INCOME, MULTI_ASSET; all same calculation_run_id."""
    portfolio = _portfolio(
        test_fund.fund_id,
        [
            _make_equity_pos(test_fund.fund_id),
            _make_bond_pos(test_fund.fund_id),
            _make_cash_pos(test_fund.fund_id),
        ],
    )
    service = StressTestCalculationService(session_factory)
    stress_repo = StressTestResultRepository(session_factory)

    calc_result = service.calculate_and_persist_combined_stress(
        portfolio=portfolio,
        scenarios=[_combined_scenario(equity=_equity_scenario(), fi=_fi_scenario())],
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    rows = stress_repo.find_by_calculation_run(calc_result.calculation_run_id)
    assert len(rows) == 3

    scopes = {r.asset_scope for r in rows}
    assert scopes == {
        StressTestAssetScopeEnum.EQUITY_LIKE,
        StressTestAssetScopeEnum.FIXED_INCOME,
        StressTestAssetScopeEnum.MULTI_ASSET,
    }

    run_ids = {r.calculation_run_id for r in rows}
    assert run_ids == {calc_result.calculation_run_id}


def test_multi_asset_total_pnl_equals_equity_plus_fi(
    session_factory: SessionFactory,
    test_fund: Fund,
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """MULTI_ASSET.total_pnl = EQUITY_LIKE.total_pnl + FIXED_INCOME.total_pnl."""
    portfolio = _portfolio(
        test_fund.fund_id,
        [_make_equity_pos(test_fund.fund_id), _make_bond_pos(test_fund.fund_id)],
    )
    service = StressTestCalculationService(session_factory)
    stress_repo = StressTestResultRepository(session_factory)

    calc_result = service.calculate_and_persist_combined_stress(
        portfolio=portfolio,
        scenarios=[_combined_scenario(equity=_equity_scenario(), fi=_fi_scenario())],
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    rows = stress_repo.find_by_calculation_run(calc_result.calculation_run_id)
    eq_row = next(r for r in rows if r.asset_scope == StressTestAssetScopeEnum.EQUITY_LIKE)
    fi_row = next(r for r in rows if r.asset_scope == StressTestAssetScopeEnum.FIXED_INCOME)
    ma_row = next(r for r in rows if r.asset_scope == StressTestAssetScopeEnum.MULTI_ASSET)

    assert ma_row.total_pnl == pytest.approx(float(eq_row.total_pnl + fi_row.total_pnl), rel=1e-6)


def test_multi_asset_row_has_no_shock_rate(
    session_factory: SessionFactory,
    test_fund: Fund,
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """MULTI_ASSET row shock_rate and shock_type are None."""
    portfolio = _portfolio(
        test_fund.fund_id,
        [_make_equity_pos(test_fund.fund_id), _make_bond_pos(test_fund.fund_id)],
    )
    service = StressTestCalculationService(session_factory)
    stress_repo = StressTestResultRepository(session_factory)

    calc_result = service.calculate_and_persist_combined_stress(
        portfolio=portfolio,
        scenarios=[_combined_scenario(equity=_equity_scenario(), fi=_fi_scenario())],
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    rows = stress_repo.find_by_calculation_run(calc_result.calculation_run_id)
    ma_row = next(r for r in rows if r.asset_scope == StressTestAssetScopeEnum.MULTI_ASSET)

    assert ma_row.shock_rate is None
    assert ma_row.shock_type is None
    assert ma_row.rate_shock_bps is None
    assert ma_row.spread_shock_bps is None


def test_all_rows_result_type_hypothetical(
    session_factory: SessionFactory,
    test_fund: Fund,
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    portfolio = _portfolio(
        test_fund.fund_id,
        [_make_equity_pos(test_fund.fund_id), _make_bond_pos(test_fund.fund_id)],
    )
    service = StressTestCalculationService(session_factory)
    stress_repo = StressTestResultRepository(session_factory)

    calc_result = service.calculate_and_persist_combined_stress(
        portfolio=portfolio,
        scenarios=[_combined_scenario(equity=_equity_scenario(), fi=_fi_scenario())],
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    rows = stress_repo.find_by_calculation_run(calc_result.calculation_run_id)
    for row in rows:
        assert row.result_type == StressTestResultTypeEnum.HYPOTHETICAL


# ---------------------------------------------------------------------------
# Equity-only scenario (2 rows: EQUITY_LIKE + MULTI_ASSET)
# ---------------------------------------------------------------------------


def test_equity_only_scenario_persists_two_rows(
    session_factory: SessionFactory,
    test_fund: Fund,
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """Equity-only scenario: no FIXED_INCOME row, 2 rows total."""
    portfolio = _portfolio(
        test_fund.fund_id,
        [_make_equity_pos(test_fund.fund_id), _make_bond_pos(test_fund.fund_id)],
    )
    service = StressTestCalculationService(session_factory)
    stress_repo = StressTestResultRepository(session_factory)

    calc_result = service.calculate_and_persist_combined_stress(
        portfolio=portfolio,
        scenarios=[_combined_scenario(equity=_equity_scenario(), fi=None)],
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    rows = stress_repo.find_by_calculation_run(calc_result.calculation_run_id)
    assert len(rows) == 2
    scopes = {r.asset_scope for r in rows}
    assert scopes == {StressTestAssetScopeEnum.EQUITY_LIKE, StressTestAssetScopeEnum.MULTI_ASSET}
    assert calc_result.num_results_persisted == 2


# ---------------------------------------------------------------------------
# FI-only scenario (2 rows: FIXED_INCOME + MULTI_ASSET)
# ---------------------------------------------------------------------------


def test_fi_only_scenario_persists_two_rows(
    session_factory: SessionFactory,
    test_fund: Fund,
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """FI-only scenario: no EQUITY_LIKE row, 2 rows total."""
    portfolio = _portfolio(
        test_fund.fund_id,
        [_make_equity_pos(test_fund.fund_id), _make_bond_pos(test_fund.fund_id)],
    )
    service = StressTestCalculationService(session_factory)
    stress_repo = StressTestResultRepository(session_factory)

    calc_result = service.calculate_and_persist_combined_stress(
        portfolio=portfolio,
        scenarios=[_combined_scenario(equity=None, fi=_fi_scenario())],
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    rows = stress_repo.find_by_calculation_run(calc_result.calculation_run_id)
    assert len(rows) == 2
    scopes = {r.asset_scope for r in rows}
    assert scopes == {StressTestAssetScopeEnum.FIXED_INCOME, StressTestAssetScopeEnum.MULTI_ASSET}
    assert calc_result.num_results_persisted == 2


# ---------------------------------------------------------------------------
# All-cash portfolio (1 row: MULTI_ASSET only)
# ---------------------------------------------------------------------------


def test_all_cash_portfolio_persists_one_row(
    session_factory: SessionFactory,
    test_fund: Fund,
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """All-cash portfolio: only MULTI_ASSET row, total_pnl = 0."""
    portfolio = _portfolio(test_fund.fund_id, [_make_cash_pos(test_fund.fund_id)])
    service = StressTestCalculationService(session_factory)
    stress_repo = StressTestResultRepository(session_factory)

    calc_result = service.calculate_and_persist_combined_stress(
        portfolio=portfolio,
        scenarios=[_combined_scenario(equity=_equity_scenario(), fi=_fi_scenario())],
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    rows = stress_repo.find_by_calculation_run(calc_result.calculation_run_id)
    assert len(rows) == 1
    assert rows[0].asset_scope == StressTestAssetScopeEnum.MULTI_ASSET
    assert rows[0].total_pnl == Decimal("0")
    assert calc_result.num_results_persisted == 1


# ---------------------------------------------------------------------------
# Multiple scenarios — row count scales correctly
# ---------------------------------------------------------------------------


def test_multiple_scenarios_row_count(
    session_factory: SessionFactory,
    test_fund: Fund,
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """Two combined scenarios over equity+FI portfolio: 6 rows total (3 per scenario)."""
    portfolio = _portfolio(
        test_fund.fund_id,
        [_make_equity_pos(test_fund.fund_id), _make_bond_pos(test_fund.fund_id)],
    )
    service = StressTestCalculationService(session_factory)

    scenarios = [
        _combined_scenario(equity=_equity_scenario(), fi=_fi_scenario(), scenario_id="COMB_A"),
        _combined_scenario(equity=_equity_scenario(), fi=_fi_scenario(), scenario_id="COMB_B"),
    ]

    calc_result = service.calculate_and_persist_combined_stress(
        portfolio=portfolio,
        scenarios=scenarios,
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    assert calc_result.num_results_persisted == 6


# ---------------------------------------------------------------------------
# CalculationRun lifecycle
# ---------------------------------------------------------------------------


def test_calculation_run_completed_on_success(
    session_factory: SessionFactory,
    test_fund: Fund,
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    portfolio = _portfolio(test_fund.fund_id, [_make_equity_pos(test_fund.fund_id)])
    service = StressTestCalculationService(session_factory)
    calc_run_repo = CalculationRunRepository(session_factory)

    calc_result = service.calculate_and_persist_combined_stress(
        portfolio=portfolio,
        scenarios=[_combined_scenario(equity=_equity_scenario())],
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    run = calc_run_repo.find_by_id(calc_result.calculation_run_id)
    assert run is not None
    assert run.calculation_type == CalculationTypeEnum.STRESS_TEST
    assert run.status == CalculationStatusEnum.COMPLETED


def test_calculation_run_failed_on_engine_error(
    session_factory: SessionFactory,
    test_fund: Fund,
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """CalculationRun marked FAILED and exception re-raised on engine error."""
    from sqlalchemy import select

    from manco_risk.database.models import CalculationRun

    unsupported_pos = EnrichedPosition(
        fund_id=test_fund.fund_id,
        position_snapshot_id=1,
        position_id=99,
        isin="XX0000000000",
        valuation_date=VALUATION_DATE,
        quantity=Decimal("1"),
        market_value=Decimal("10000"),
        position_currency=BASE_CCY,
        asset_class="DERIVATIVE",
        instrument_currency=BASE_CCY,
        market_value_base_ccy=Decimal("10000"),
        fund_base_currency=BASE_CCY,
        weight=Decimal("1.0"),
    )
    portfolio = _portfolio(test_fund.fund_id, [unsupported_pos])
    service = StressTestCalculationService(session_factory)

    with pytest.raises(UnsupportedAssetClassError):
        service.calculate_and_persist_combined_stress(
            portfolio=portfolio,
            scenarios=[_combined_scenario(equity=_equity_scenario())],
            position_snapshot_id=test_position_snapshot.position_snapshot_id,
            nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
            risk_methodology=test_methodology,
            created_by="test_user",
        )

    with session_factory.create_session() as session:
        latest = list(
            session.execute(
                select(CalculationRun).order_by(CalculationRun.calculation_run_id.desc()).limit(1)
            ).scalars()
        )
    assert latest[0].status == CalculationStatusEnum.FAILED


# ---------------------------------------------------------------------------
# Results retrievable through StressTestResultRepository
# ---------------------------------------------------------------------------


def test_results_retrievable_through_repository(
    session_factory: SessionFactory,
    test_fund: Fund,
    test_position_snapshot: PositionSnapshot,
    test_nav_snapshot: NAVSnapshot,
    test_methodology: RiskMethodology,
) -> None:
    """StressTestResultRepository.find_by_calculation_run returns all persisted rows."""
    portfolio = _portfolio(
        test_fund.fund_id,
        [
            _make_equity_pos(test_fund.fund_id),
            _make_bond_pos(test_fund.fund_id),
            _make_cash_pos(test_fund.fund_id),
        ],
    )
    service = StressTestCalculationService(session_factory)
    stress_repo = StressTestResultRepository(session_factory)

    calc_result = service.calculate_and_persist_combined_stress(
        portfolio=portfolio,
        scenarios=[_combined_scenario(equity=_equity_scenario(), fi=_fi_scenario())],
        position_snapshot_id=test_position_snapshot.position_snapshot_id,
        nav_snapshot_id=test_nav_snapshot.nav_snapshot_id,
        risk_methodology=test_methodology,
        created_by="test_user",
    )

    rows = stress_repo.find_by_calculation_run(calc_result.calculation_run_id)
    assert len(rows) == 3
    for row in rows:
        assert row.calculation_run_id == calc_result.calculation_run_id
        assert row.fund_id == test_fund.fund_id
        assert row.current_nav == NAV
