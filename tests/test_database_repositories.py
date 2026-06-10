"""Tests for database repository layer."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from manco_risk.database import (
    Fund,
    FundRepository,
    Instrument,
    InstrumentRepository,
    MarketDataPoint,
    MarketDataPointRepository,
    MarketDataTypeEnum,
    NAVSnapshot,
    NAVSnapshotRepository,
    Position,
    PositionRepository,
    PositionSnapshot,
    PositionSnapshotRepository,
    RiskMethodology,
    RiskMethodologyRepository,
    SessionFactory,
    create_database_engine,
    initialize_database,
)

# Test data constants
BASELINE_DATE = date(2025, 1, 15)
NEXT_DATE = date(2025, 1, 16)
BASELINE_LOAD_TIMESTAMP = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
BASELINE_DATA_TIMESTAMP = datetime(2025, 1, 15, 16, 0, 0, tzinfo=timezone.utc)
NEXT_LOAD_TIMESTAMP = datetime(2025, 1, 16, 10, 0, 0, tzinfo=timezone.utc)
NEXT_DATA_TIMESTAMP = datetime(2025, 1, 16, 16, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    """Create in-memory SQLite engine for tests."""
    eng = create_database_engine("sqlite:///:memory:")
    initialize_database(eng)
    return eng


@pytest.fixture
def session_factory(engine):
    """Create session factory from engine."""
    return SessionFactory(engine)


@pytest.fixture
def fund_repository(session_factory):
    """Create FundRepository instance."""
    return FundRepository(session_factory)


class TestFundRepository:
    """Tests for FundRepository."""

    def test_find_by_id_not_found(self, fund_repository: FundRepository) -> None:
        """find_by_id returns None when fund not found."""
        result = fund_repository.find_by_id(999)
        assert result is None

    def test_find_all_empty(self, fund_repository: FundRepository) -> None:
        """find_all returns empty list when no funds exist."""
        result = fund_repository.find_all()
        assert result == []

    def test_insert_fund(self, fund_repository: FundRepository, fund_standard: Fund) -> None:
        """insert creates a new fund with fund_id."""
        result = fund_repository.insert(fund_standard)

        assert result is not None
        assert result.fund_id is not None
        assert result.fund_name == "Standard Fund"
        assert result.base_currency == "EUR"

    def test_find_by_id_after_insert(
        self, fund_repository: FundRepository, fund_standard: Fund
    ) -> None:
        """find_by_id returns the inserted fund."""
        inserted = fund_repository.insert(fund_standard)

        result = fund_repository.find_by_id(inserted.fund_id)

        assert result is not None
        assert result.fund_id == inserted.fund_id
        assert result.fund_name == "Standard Fund"

    def test_find_all_multiple_funds(self, fund_repository: FundRepository) -> None:
        """find_all returns all inserted funds."""
        fund1 = Fund(
            fund_name="Fund 1",
            base_currency="EUR",
            domicile="Luxembourg",
            fund_regime="AIFM",
        )
        fund2 = Fund(
            fund_name="Fund 2",
            base_currency="USD",
            domicile="New York",
            fund_regime="AIFM",
        )

        fund_repository.insert(fund1)
        fund_repository.insert(fund2)

        result = fund_repository.find_all()

        assert len(result) == 2
        assert any(f.fund_name == "Fund 1" for f in result)
        assert any(f.fund_name == "Fund 2" for f in result)

    def test_find_by_name_not_found(self, fund_repository: FundRepository) -> None:
        """find_by_name returns None when fund not found."""
        result = fund_repository.find_by_name("Nonexistent Fund")
        assert result is None

    def test_find_by_name_found(self, fund_repository: FundRepository) -> None:
        """find_by_name returns fund when found."""
        fund = Fund(
            fund_name="Alpha Fund",
            base_currency="EUR",
            domicile="Luxembourg",
            fund_regime="AIFM",
        )
        inserted = fund_repository.insert(fund)

        result = fund_repository.find_by_name("Alpha Fund")

        assert result is not None
        assert result.fund_id == inserted.fund_id

    def test_find_by_name_unique_per_name(self, fund_repository: FundRepository) -> None:
        """find_by_name returns first match if multiple funds with same name exist.

        Note: In practice, fund names should be unique. This tests behavior.
        """
        fund = Fund(
            fund_name="Shared Name",
            base_currency="EUR",
            domicile="Luxembourg",
            fund_regime="AIFM",
        )
        fund_repository.insert(fund)

        result = fund_repository.find_by_name("Shared Name")

        assert result is not None
        assert result.fund_name == "Shared Name"

    def test_insert_fund_with_optional_fields(self, fund_repository: FundRepository) -> None:
        """insert supports optional fields like aifm_id and inception_date."""
        from datetime import date

        fund = Fund(
            fund_name="Fund with Details",
            aifm_id="LEI123456",
            base_currency="EUR",
            domicile="Luxembourg",
            fund_regime="AIFM",
            inception_date=date(2020, 1, 15),
        )

        result = fund_repository.insert(fund)

        assert result.aifm_id == "LEI123456"
        assert result.inception_date == date(2020, 1, 15)

    def test_find_by_id_returns_detached_entity(
        self, fund_repository: FundRepository, session_factory: SessionFactory, fund_standard: Fund
    ) -> None:
        """find_by_id returns detached entity (not bound to session).

        This ensures the entity can be used outside the repository.
        """
        inserted = fund_repository.insert(fund_standard)

        result = fund_repository.find_by_id(inserted.fund_id)

        # Entity should be usable outside session context
        assert result.fund_name == "Standard Fund"
        assert result.base_currency == "EUR"

    def test_find_all_returns_detached_entities(self, fund_repository: FundRepository) -> None:
        """find_all returns detached entities (not bound to session)."""
        fund1 = Fund(
            fund_name="Fund A",
            base_currency="EUR",
            domicile="Luxembourg",
            fund_regime="AIFM",
        )
        fund2 = Fund(
            fund_name="Fund B",
            base_currency="USD",
            domicile="New York",
            fund_regime="AIFM",
        )

        fund_repository.insert(fund1)
        fund_repository.insert(fund2)

        result = fund_repository.find_all()

        # Entities should be usable outside session context
        assert len(result) == 2
        for fund in result:
            assert fund.fund_name is not None
            assert fund.base_currency is not None

    def test_multiple_sequential_inserts(self, fund_repository: FundRepository) -> None:
        """Multiple insert calls work correctly with auto-increment IDs."""
        funds = [
            Fund(
                fund_name=f"Fund {i}",
                base_currency="EUR",
                domicile="Luxembourg",
                fund_regime="AIFM",
            )
            for i in range(5)
        ]

        inserted_ids = [fund_repository.insert(f).fund_id for f in funds]

        # All IDs should be unique and sequential (or at least unique)
        assert len(set(inserted_ids)) == 5

        # All funds should be retrievable
        for fund_id in inserted_ids:
            result = fund_repository.find_by_id(fund_id)
            assert result is not None

    def test_insert_persists_across_sessions(
        self, fund_repository: FundRepository, session_factory: SessionFactory, fund_standard: Fund
    ) -> None:
        """Data inserted via repository persists across session boundaries."""
        inserted = fund_repository.insert(fund_standard)
        inserted_id = inserted.fund_id

        # Create new repository instance (simulating new session context)
        new_repository = FundRepository(session_factory)

        result = new_repository.find_by_id(inserted_id)

        assert result is not None
        assert result.fund_name == "Standard Fund"


@pytest.fixture
def instrument_repository(session_factory):
    """Create InstrumentRepository instance."""
    return InstrumentRepository(session_factory)


class TestInstrumentRepository:
    """Tests for InstrumentRepository."""

    def test_find_by_id_not_found(self, instrument_repository: InstrumentRepository) -> None:
        """find_by_id returns None when instrument not found."""
        result = instrument_repository.find_by_id(999)
        assert result is None

    def test_find_all_empty(self, instrument_repository: InstrumentRepository) -> None:
        """find_all returns empty list when no instruments exist."""
        result = instrument_repository.find_all()
        assert result == []

    def test_insert_instrument(
        self, instrument_repository: InstrumentRepository, instrument_equity: Instrument
    ) -> None:
        """insert creates a new instrument with instrument_id."""
        result = instrument_repository.insert(instrument_equity)

        assert result is not None
        assert result.instrument_id is not None
        assert result.isin == "IE00B4L5Y983"
        assert result.asset_class == "Equity"

    def test_find_by_id_after_insert(
        self, instrument_repository: InstrumentRepository, instrument_equity: Instrument
    ) -> None:
        """find_by_id returns the inserted instrument."""
        inserted = instrument_repository.insert(instrument_equity)

        result = instrument_repository.find_by_id(inserted.instrument_id)

        assert result is not None
        assert result.isin == "IE00B4L5Y983"

    def test_find_by_isin_not_found(self, instrument_repository: InstrumentRepository) -> None:
        """find_by_isin returns None when instrument not found."""
        result = instrument_repository.find_by_isin("INVALID")
        assert result is None

    def test_find_by_isin_found(
        self, instrument_repository: InstrumentRepository, instrument_equity: Instrument
    ) -> None:
        """find_by_isin returns instrument when found."""
        inserted = instrument_repository.insert(instrument_equity)

        result = instrument_repository.find_by_isin("IE00B4L5Y983")

        assert result is not None
        assert result.instrument_id == inserted.instrument_id

    def test_find_all_multiple_instruments(
        self,
        instrument_repository: InstrumentRepository,
        instrument_equity: Instrument,
        instrument_bond: Instrument,
    ) -> None:
        """find_all returns all inserted instruments."""
        instrument_repository.insert(instrument_equity)
        instrument_repository.insert(instrument_bond)

        result = instrument_repository.find_all()

        assert len(result) == 2
        assert any(i.asset_class == "Equity" for i in result)
        assert any(i.asset_class == "Bond" for i in result)


@pytest.fixture
def risk_methodology_repository(session_factory):
    """Create RiskMethodologyRepository instance."""
    return RiskMethodologyRepository(session_factory)


class TestRiskMethodologyRepository:
    """Tests for RiskMethodologyRepository."""

    def test_find_by_id_not_found(
        self, risk_methodology_repository: RiskMethodologyRepository
    ) -> None:
        """find_by_id returns None when methodology not found."""
        result = risk_methodology_repository.find_by_id(999)
        assert result is None

    def test_find_active_empty(
        self, risk_methodology_repository: RiskMethodologyRepository
    ) -> None:
        """find_active returns empty list when no active methodologies exist."""
        result = risk_methodology_repository.find_active()
        assert result == []

    def test_insert_methodology(
        self,
        risk_methodology_repository: RiskMethodologyRepository,
        methodology_standard: RiskMethodology,
    ) -> None:
        """insert creates a new methodology with methodology_version_id."""
        result = risk_methodology_repository.insert(methodology_standard)

        assert result is not None
        assert result.methodology_version_id is not None
        assert result.var_confidence_level == Decimal("0.99")
        assert result.is_active is True

    def test_find_by_id_after_insert(
        self,
        risk_methodology_repository: RiskMethodologyRepository,
        methodology_standard: RiskMethodology,
    ) -> None:
        """find_by_id returns the inserted methodology."""
        inserted = risk_methodology_repository.insert(methodology_standard)

        result = risk_methodology_repository.find_by_id(inserted.methodology_version_id)

        assert result is not None
        assert result.var_confidence_level == Decimal("0.99")

    def test_find_active_excludes_inactive(
        self,
        risk_methodology_repository: RiskMethodologyRepository,
        methodology_standard: RiskMethodology,
    ) -> None:
        """find_active only returns is_active=True methodologies."""
        inactive = RiskMethodology(
            effective_date=date(2024, 1, 1),
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
            created_by="system",
            is_active=False,
        )

        risk_methodology_repository.insert(methodology_standard)
        risk_methodology_repository.insert(inactive)

        result = risk_methodology_repository.find_active()

        assert len(result) == 1
        assert result[0].is_active is True

    def test_find_by_name_not_found(
        self, risk_methodology_repository: RiskMethodologyRepository
    ) -> None:
        """find_by_name returns None when active methodology with name not found."""
        result = risk_methodology_repository.find_by_name("Nonexistent")
        assert result is None

    def test_find_by_name_found(
        self, risk_methodology_repository: RiskMethodologyRepository
    ) -> None:
        """find_by_name returns active methodology with matching name."""
        methodology = RiskMethodology(
            effective_date=date(2025, 1, 1),
            var_confidence_level=Decimal("0.99"),
            var_lookback_days=250,
            var_horizon_days=1,
            es_method="historical",
            es_lookback_days=250,
            es_horizon_days=1,
            backtesting_window_days=250,
            fx_conversion_method="eod_spot",
            missing_data_handling="strict_fail",
            created_date=date(2025, 1, 1),
            created_by="system",
            notes="Phase 1 Standard",
            is_active=True,
        )
        inserted = risk_methodology_repository.insert(methodology)

        result = risk_methodology_repository.find_by_name("Phase 1 Standard")

        assert result is not None
        assert result.methodology_version_id == inserted.methodology_version_id

    def test_find_by_name_excludes_inactive(
        self, risk_methodology_repository: RiskMethodologyRepository
    ) -> None:
        """find_by_name only returns active methodologies."""
        inactive = RiskMethodology(
            effective_date=date(2024, 1, 1),
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
            created_by="system",
            notes="Old Config",
            is_active=False,
        )

        risk_methodology_repository.insert(inactive)

        result = risk_methodology_repository.find_by_name("Old Config")

        assert result is None


@pytest.fixture
def position_snapshot_repository(session_factory):
    """Create PositionSnapshotRepository instance."""
    return PositionSnapshotRepository(session_factory)


class TestPositionSnapshotRepository:
    """Tests for PositionSnapshotRepository."""

    def test_insert_and_find_by_id(
        self,
        position_snapshot_repository: PositionSnapshotRepository,
        position_snapshot_base: PositionSnapshot,
    ) -> None:
        """Insert and retrieve position snapshot by ID."""
        inserted = position_snapshot_repository.insert(position_snapshot_base)
        result = position_snapshot_repository.find_by_id(inserted.position_snapshot_id)

        assert result is not None
        assert result.fund_id == 1
        assert result.valuation_date == BASELINE_DATE

    def test_find_by_fund_and_date(
        self,
        position_snapshot_repository: PositionSnapshotRepository,
        position_snapshot_base: PositionSnapshot,
    ) -> None:
        """Find position snapshot by fund and date."""
        position_snapshot_repository.insert(position_snapshot_base)
        result = position_snapshot_repository.find_by_fund_and_date(1, BASELINE_DATE)

        assert result is not None
        assert result.num_positions == 5

    def test_find_by_fund(
        self,
        position_snapshot_repository: PositionSnapshotRepository,
        position_snapshot_base: PositionSnapshot,
    ) -> None:
        """Find all position snapshots for a fund."""
        snapshot2 = PositionSnapshot(
            fund_id=1,
            valuation_date=NEXT_DATE,
            source_extract_date=NEXT_DATE,
            load_timestamp=NEXT_LOAD_TIMESTAMP,
            num_positions=5,
        )

        position_snapshot_repository.insert(position_snapshot_base)
        position_snapshot_repository.insert(snapshot2)
        result = position_snapshot_repository.find_by_fund(1)

        assert len(result) == 2


@pytest.fixture
def position_repository(session_factory):
    """Create PositionRepository instance."""
    return PositionRepository(session_factory)


class TestPositionRepository:
    """Tests for PositionRepository."""

    def test_insert_and_find_by_id(
        self, position_repository: PositionRepository, position_base: Position
    ) -> None:
        """Insert and retrieve position by ID."""
        inserted = position_repository.insert(position_base)
        result = position_repository.find_by_id(inserted.position_id)

        assert result is not None
        assert result.isin == "IE00B4L5Y983"

    def test_find_by_snapshot(
        self, position_repository: PositionRepository, position_base: Position
    ) -> None:
        """Find positions in a snapshot."""
        position2 = Position(
            position_snapshot_id=1,
            fund_id=1,
            valuation_date=BASELINE_DATE,
            isin="US0378331005",
            quantity=Decimal("50"),
            market_value=Decimal("8000"),
        )

        position_repository.insert(position_base)
        position_repository.insert(position2)
        result = position_repository.find_by_snapshot(1)

        assert len(result) == 2

    def test_insert_batch(self, position_repository: PositionRepository) -> None:
        """Insert multiple positions at once."""
        positions = [
            Position(
                position_snapshot_id=1,
                fund_id=1,
                valuation_date=date(2025, 1, 15),
                isin=f"ISIN{i}",
                quantity=Decimal("100"),
                market_value=Decimal("10000"),
            )
            for i in range(5)
        ]

        result = position_repository.insert_batch(positions)

        assert len(result) == 5
        assert all(p.position_id is not None for p in result)


@pytest.fixture
def nav_snapshot_repository(session_factory):
    """Create NAVSnapshotRepository instance."""
    return NAVSnapshotRepository(session_factory)


class TestNAVSnapshotRepository:
    """Tests for NAVSnapshotRepository."""

    def test_insert_and_find_by_id(
        self, nav_snapshot_repository: NAVSnapshotRepository, nav_snapshot_base: NAVSnapshot
    ) -> None:
        """Insert and retrieve NAV snapshot by ID."""
        inserted = nav_snapshot_repository.insert(nav_snapshot_base)
        result = nav_snapshot_repository.find_by_id(inserted.nav_snapshot_id)

        assert result is not None
        assert result.nav_value == Decimal("50000000")

    def test_find_by_fund_and_date(
        self, nav_snapshot_repository: NAVSnapshotRepository, nav_snapshot_base: NAVSnapshot
    ) -> None:
        """Find NAV snapshot by fund and date."""
        nav_snapshot_repository.insert(nav_snapshot_base)
        result = nav_snapshot_repository.find_by_fund_and_date(1, BASELINE_DATE)

        assert result is not None
        assert result.nav_value == Decimal("50000000")

    def test_find_by_fund(
        self, nav_snapshot_repository: NAVSnapshotRepository, nav_snapshot_base: NAVSnapshot
    ) -> None:
        """Find all NAV snapshots for a fund."""
        nav2 = NAVSnapshot(
            fund_id=1,
            nav_date=NEXT_DATE,
            nav_value=Decimal("50100000"),
            nav_source="accounting_system",
            nav_timestamp=NEXT_LOAD_TIMESTAMP,
        )

        nav_snapshot_repository.insert(nav_snapshot_base)
        nav_snapshot_repository.insert(nav2)
        result = nav_snapshot_repository.find_by_fund(1)

        assert len(result) == 2


@pytest.fixture
def market_data_point_repository(session_factory):
    """Create MarketDataPointRepository instance."""
    return MarketDataPointRepository(session_factory)


# Baseline test data fixtures
@pytest.fixture
def fund_standard() -> Fund:
    """Create a standard EUR fund in Luxembourg."""
    return Fund(
        fund_name="Standard Fund",
        base_currency="EUR",
        domicile="Luxembourg",
        fund_regime="AIFM",
    )


@pytest.fixture
def instrument_equity() -> Instrument:
    """Create a standard equity instrument."""
    return Instrument(
        isin="IE00B4L5Y983",
        instrument_name="MSCI World ETF",
        asset_class="Equity",
        currency="EUR",
    )


@pytest.fixture
def instrument_bond() -> Instrument:
    """Create a standard bond instrument."""
    return Instrument(
        isin="XS2191065822",
        instrument_name="EU Green Bond",
        asset_class="Bond",
        currency="EUR",
    )


@pytest.fixture
def methodology_standard() -> RiskMethodology:
    """Create a standard active risk methodology."""
    return RiskMethodology(
        effective_date=date(2025, 1, 1),
        var_confidence_level=Decimal("0.99"),
        var_lookback_days=250,
        var_horizon_days=1,
        es_method="historical",
        es_lookback_days=250,
        es_horizon_days=1,
        backtesting_window_days=250,
        fx_conversion_method="eod_spot",
        missing_data_handling="strict_fail",
        created_date=date(2025, 1, 1),
        created_by="system",
        is_active=True,
    )


@pytest.fixture
def position_snapshot_base() -> PositionSnapshot:
    """Create a baseline position snapshot for Jan 15."""
    return PositionSnapshot(
        fund_id=1,
        valuation_date=BASELINE_DATE,
        source_extract_date=BASELINE_DATE,
        load_timestamp=BASELINE_LOAD_TIMESTAMP,
        num_positions=5,
    )


@pytest.fixture
def position_base() -> Position:
    """Create a baseline position."""
    return Position(
        position_snapshot_id=1,
        fund_id=1,
        valuation_date=BASELINE_DATE,
        isin="IE00B4L5Y983",
        quantity=Decimal("100"),
        market_value=Decimal("12500"),
    )


@pytest.fixture
def nav_snapshot_base() -> NAVSnapshot:
    """Create a baseline NAV snapshot for Jan 15."""
    return NAVSnapshot(
        fund_id=1,
        nav_date=BASELINE_DATE,
        nav_value=Decimal("50000000"),
        nav_source="accounting_system",
        nav_timestamp=BASELINE_LOAD_TIMESTAMP,
    )


@pytest.fixture
def market_data_point_base() -> MarketDataPoint:
    """Create a baseline market data point."""
    return MarketDataPoint(
        isin="IE00B4L5Y983",
        valuation_date=BASELINE_DATE,
        data_type=MarketDataTypeEnum.PRICE,
        data_value=Decimal("125.50"),
        source_provider="Bloomberg",
        data_timestamp=BASELINE_DATA_TIMESTAMP,
    )


class TestMarketDataPointRepository:
    """Tests for MarketDataPointRepository."""

    def test_insert_and_find_by_id(
        self,
        market_data_point_repository: MarketDataPointRepository,
        market_data_point_base: MarketDataPoint,
    ) -> None:
        """Insert and retrieve market data point by ID."""
        inserted = market_data_point_repository.insert(market_data_point_base)
        result = market_data_point_repository.find_by_id(inserted.market_data_point_id)

        assert result is not None
        assert result.data_value == Decimal("125.50")

    def test_find_by_instrument_and_date(
        self,
        market_data_point_repository: MarketDataPointRepository,
        market_data_point_base: MarketDataPoint,
    ) -> None:
        """Find market data points for instrument on date."""
        point2 = MarketDataPoint(
            isin="IE00B4L5Y983",
            valuation_date=BASELINE_DATE,
            data_type=MarketDataTypeEnum.YIELD,
            data_value=Decimal("0.025"),
            source_provider="Bloomberg",
            data_timestamp=BASELINE_DATA_TIMESTAMP,
        )

        market_data_point_repository.insert(market_data_point_base)
        market_data_point_repository.insert(point2)
        result = market_data_point_repository.find_by_instrument_and_date(
            "IE00B4L5Y983", BASELINE_DATE
        )

        assert len(result) == 2

    def test_find_by_type_and_date(
        self,
        market_data_point_repository: MarketDataPointRepository,
        market_data_point_base: MarketDataPoint,
    ) -> None:
        """Find market data points of type on date."""
        point2 = MarketDataPoint(
            isin="US0378331005",
            valuation_date=BASELINE_DATE,
            data_type=MarketDataTypeEnum.PRICE,
            data_value=Decimal("180.75"),
            source_provider="Bloomberg",
            data_timestamp=BASELINE_DATA_TIMESTAMP,
        )

        market_data_point_repository.insert(market_data_point_base)
        market_data_point_repository.insert(point2)
        result = market_data_point_repository.find_by_type_and_date(
            MarketDataTypeEnum.PRICE, BASELINE_DATE
        )

        assert len(result) == 2

    def test_insert_batch(self, market_data_point_repository: MarketDataPointRepository) -> None:
        """Insert multiple market data points at once."""
        points = [
            MarketDataPoint(
                isin=f"ISIN{i}",
                valuation_date=BASELINE_DATE,
                data_type=MarketDataTypeEnum.PRICE,
                data_value=Decimal("100.00") + Decimal(str(i)),
                source_provider="Bloomberg",
                data_timestamp=BASELINE_DATA_TIMESTAMP,
            )
            for i in range(5)
        ]

        result = market_data_point_repository.insert_batch(points)

        assert len(result) == 5
        assert all(p.market_data_point_id is not None for p in result)
