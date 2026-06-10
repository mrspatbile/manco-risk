"""Fixtures for database tests.

Provides in-memory SQLite database for testing.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from manco_risk.database.models import (
    Fund,
    Instrument,
    NAVSnapshot,
    PositionSnapshot,
    RiskMethodology,
)
from manco_risk.database.session import SessionFactory, create_database_engine, initialize_database


@pytest.fixture
def session_factory() -> SessionFactory:
    """Create an in-memory SQLite database for testing."""
    engine = create_database_engine("sqlite:///:memory:")
    initialize_database(engine)
    return SessionFactory(engine)


@pytest.fixture
def sample_fund(session_factory: SessionFactory) -> Fund:
    """Create a sample fund in the test database."""
    from manco_risk.database.repositories import FundRepository

    fund = Fund(
        fund_name="Test Fund",
        aifm_id="TEST_AIFM",
        base_currency="EUR",
        domicile="LU",
        fund_regime="AIFM",
        inception_date=date(2020, 1, 1),
    )
    repo = FundRepository(session_factory)
    return repo.insert(fund)


@pytest.fixture
def sample_instrument(session_factory: SessionFactory) -> Instrument:
    """Create a sample instrument in the test database."""
    from manco_risk.database.repositories import InstrumentRepository

    instrument = Instrument(
        isin="US0378331005",
        ticker="AAPL",
        instrument_name="Apple Inc.",
        asset_class="EQUITY",
        currency="EUR",
        instrument_type="STOCK",
        is_traded_daily=True,
    )
    repo = InstrumentRepository(session_factory)
    return repo.insert(instrument)


@pytest.fixture
def sample_position_snapshot(
    session_factory: SessionFactory, sample_fund: Fund
) -> PositionSnapshot:
    """Create a sample position snapshot in the test database."""
    from manco_risk.database.repositories import PositionSnapshotRepository

    snapshot = PositionSnapshot(
        fund_id=sample_fund.fund_id,
        valuation_date=date(2024, 1, 1),
        source_extract_date=date(2024, 1, 1),
        source_extract_filename="test_extract.csv",
        load_timestamp=datetime(2024, 1, 1, 12, 0, 0),
        num_positions=1,
    )
    repo = PositionSnapshotRepository(session_factory)
    return repo.insert(snapshot)


@pytest.fixture
def sample_nav_snapshot(session_factory: SessionFactory, sample_fund: Fund) -> NAVSnapshot:
    """Create a sample NAV snapshot in the test database."""
    from manco_risk.database.repositories import NAVSnapshotRepository

    nav = NAVSnapshot(
        fund_id=sample_fund.fund_id,
        nav_date=date(2024, 1, 1),
        nav_value=Decimal("100000.00"),
        nav_source="test",
        nav_timestamp=datetime(2024, 1, 1, 12, 0, 0),
    )
    repo = NAVSnapshotRepository(session_factory)
    return repo.insert(nav)


@pytest.fixture
def sample_risk_methodology(session_factory: SessionFactory, sample_fund: Fund) -> RiskMethodology:
    """Create a sample risk methodology in the test database."""
    from manco_risk.database.repositories import RiskMethodologyRepository

    methodology = RiskMethodology(
        effective_date=date(2024, 1, 1),
        fund_id=sample_fund.fund_id,
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
