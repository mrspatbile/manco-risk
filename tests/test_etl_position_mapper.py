"""Tests for ETL position mapping and persistence."""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.database import (
    Fund,
    FundRepository,
    Instrument,
    InstrumentRepository,
    PositionRepository,
    PositionSnapshotRepository,
    SessionFactory,
    create_database_engine,
    initialize_database,
)
from manco_risk.etl import PositionInput, PositionMapper
from manco_risk.etl.exceptions import (
    FundNotFoundError,
    InstrumentNotFoundError,
)


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
def mapper(session_factory):
    """Create PositionMapper instance."""
    return PositionMapper(session_factory)


@pytest.fixture
def fund_repository(session_factory):
    """Create FundRepository instance."""
    return FundRepository(session_factory)


@pytest.fixture
def instrument_repository(session_factory):
    """Create InstrumentRepository instance."""
    return InstrumentRepository(session_factory)


@pytest.fixture
def position_repository(session_factory):
    """Create PositionRepository instance."""
    return PositionRepository(session_factory)


@pytest.fixture
def position_snapshot_repository(session_factory):
    """Create PositionSnapshotRepository instance."""
    return PositionSnapshotRepository(session_factory)


class TestPositionMapperPersistence:
    """Tests for position mapping and persistence."""

    def test_persist_positions_single_position(
        self,
        mapper: PositionMapper,
        fund_repository: FundRepository,
        instrument_repository: InstrumentRepository,
        position_repository: PositionRepository,
        position_snapshot_repository: PositionSnapshotRepository,
    ) -> None:
        """Persist a single position successfully."""
        # Setup: create fund and instrument
        fund = Fund(
            fund_name="Test Fund",
            base_currency="EUR",
            domicile="Luxembourg",
            fund_regime="AIFM",
        )
        fund = fund_repository.insert(fund)

        instrument = Instrument(
            isin="IE00B4L5Y983",
            instrument_name="MSCI World ETF",
            asset_class="Equity",
            currency="EUR",
        )
        instrument = instrument_repository.insert(instrument)

        # Input
        position_input = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="EUR",
        )

        # Persist
        mapper.persist_positions([position_input])

        # Verify snapshot was created
        snapshot = position_snapshot_repository.find_by_fund_and_date(
            fund.fund_id, date(2025, 1, 15)
        )
        assert snapshot is not None
        assert snapshot.fund_id == fund.fund_id
        assert snapshot.num_positions == 1

        # Verify position was created
        positions = position_repository.find_by_snapshot(snapshot.position_snapshot_id)
        assert len(positions) == 1
        assert positions[0].fund_id == fund.fund_id
        assert positions[0].isin == "IE00B4L5Y983"
        assert positions[0].quantity == Decimal("100")
        assert positions[0].market_value == Decimal("12500")

    def test_persist_positions_multiple_positions(
        self,
        mapper: PositionMapper,
        fund_repository: FundRepository,
        instrument_repository: InstrumentRepository,
        position_repository: PositionRepository,
        position_snapshot_repository: PositionSnapshotRepository,
    ) -> None:
        """Persist multiple positions in one batch."""
        # Setup
        fund = Fund(
            fund_name="Test Fund",
            base_currency="EUR",
            domicile="Luxembourg",
            fund_regime="AIFM",
        )
        fund = fund_repository.insert(fund)

        for isin in ["IE00B4L5Y983", "US0378331005"]:
            instrument = Instrument(
                isin=isin,
                instrument_name=f"Test {isin}",
                asset_class="Equity",
                currency="EUR",
            )
            instrument_repository.insert(instrument)

        # Inputs
        position_inputs = [
            PositionInput(
                fund_name="Test Fund",
                valuation_date=date(2025, 1, 15),
                isin="IE00B4L5Y983",
                quantity=Decimal("100"),
                market_value=Decimal("12500"),
                currency="EUR",
            ),
            PositionInput(
                fund_name="Test Fund",
                valuation_date=date(2025, 1, 15),
                isin="US0378331005",
                quantity=Decimal("50"),
                market_value=Decimal("8000"),
                currency="USD",
            ),
        ]

        # Persist
        mapper.persist_positions(position_inputs)

        # Verify
        snapshot = position_snapshot_repository.find_by_fund_and_date(
            fund.fund_id, date(2025, 1, 15)
        )
        assert snapshot.num_positions == 2

        positions = position_repository.find_by_snapshot(snapshot.position_snapshot_id)
        assert len(positions) == 2

    def test_persist_positions_with_optional_fields(
        self,
        mapper: PositionMapper,
        fund_repository: FundRepository,
        instrument_repository: InstrumentRepository,
        position_repository: PositionRepository,
        position_snapshot_repository: PositionSnapshotRepository,
    ) -> None:
        """Persist positions with optional fields (source_id, base_ccy_value)."""
        # Setup
        fund = Fund(
            fund_name="Test Fund",
            base_currency="EUR",
            domicile="Luxembourg",
            fund_regime="AIFM",
        )
        fund = fund_repository.insert(fund)

        instrument = Instrument(
            isin="IE00B4L5Y983",
            instrument_name="MSCI World ETF",
            asset_class="Equity",
            currency="EUR",
        )
        instrument_repository.insert(instrument)

        # Input with optional fields
        position_input = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="EUR",
            source_position_identifier="POS-001",
            market_value_base_ccy_source=Decimal("13500"),
        )

        # Persist
        mapper.persist_positions([position_input])

        # Verify
        snapshot = position_snapshot_repository.find_by_fund_and_date(
            fund.fund_id, date(2025, 1, 15)
        )
        assert snapshot is not None
        positions = position_repository.find_by_snapshot(snapshot.position_snapshot_id)
        assert positions[0].source_position_identifier == "POS-001"
        assert positions[0].market_value_base_ccy_source == Decimal("13500")

    def test_persist_positions_reuses_existing_snapshot(
        self,
        mapper: PositionMapper,
        fund_repository: FundRepository,
        instrument_repository: InstrumentRepository,
        position_snapshot_repository: PositionSnapshotRepository,
        position_repository: PositionRepository,
    ) -> None:
        """Reuse existing PositionSnapshot for same fund/date."""
        # Setup
        fund = Fund(
            fund_name="Test Fund",
            base_currency="EUR",
            domicile="Luxembourg",
            fund_regime="AIFM",
        )
        fund = fund_repository.insert(fund)

        for i, isin in enumerate(["IE00B4L5Y983", "US0378331005", "DE0005933931"]):
            instrument = Instrument(
                isin=isin,
                instrument_name=f"Test {isin}",
                asset_class="Equity",
                currency="EUR",
            )
            instrument_repository.insert(instrument)

        # First batch: 2 positions
        first_batch = [
            PositionInput(
                fund_name="Test Fund",
                valuation_date=date(2025, 1, 15),
                isin="IE00B4L5Y983",
                quantity=Decimal("100"),
                market_value=Decimal("12500"),
                currency="EUR",
            ),
            PositionInput(
                fund_name="Test Fund",
                valuation_date=date(2025, 1, 15),
                isin="US0378331005",
                quantity=Decimal("50"),
                market_value=Decimal("8000"),
                currency="USD",
            ),
        ]

        mapper.persist_positions(first_batch)

        # Verify snapshot created
        snapshot1 = position_snapshot_repository.find_by_fund_and_date(
            fund.fund_id, date(2025, 1, 15)
        )
        assert snapshot1 is not None
        snapshot1_id = snapshot1.position_snapshot_id

        # Second batch: 1 more position (should reuse snapshot)
        second_batch = [
            PositionInput(
                fund_name="Test Fund",
                valuation_date=date(2025, 1, 15),
                isin="DE0005933931",
                quantity=Decimal("30"),
                market_value=Decimal("3000"),
                currency="EUR",
            ),
        ]

        mapper.persist_positions(second_batch)

        # Verify snapshot was reused (same ID)
        snapshot2 = position_snapshot_repository.find_by_fund_and_date(
            fund.fund_id, date(2025, 1, 15)
        )
        assert snapshot2 is not None
        assert snapshot2.position_snapshot_id == snapshot1_id

        # Verify all 3 positions exist
        positions = position_repository.find_by_snapshot(snapshot1_id)
        assert len(positions) == 3


class TestPositionMapperErrors:
    """Tests for error handling in position mapping."""

    def test_persist_positions_fund_not_found(
        self,
        mapper: PositionMapper,
        instrument_repository: InstrumentRepository,
    ) -> None:
        """Raise FundNotFoundError for unknown fund."""
        # Setup: create instrument but not fund
        instrument = Instrument(
            isin="IE00B4L5Y983",
            instrument_name="MSCI World ETF",
            asset_class="Equity",
            currency="EUR",
        )
        instrument_repository.insert(instrument)

        # Input with non-existent fund
        position_input = PositionInput(
            fund_name="Unknown Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="EUR",
        )

        # Should raise FundNotFoundError
        with pytest.raises(FundNotFoundError, match="Unknown Fund"):
            mapper.persist_positions([position_input])

    def test_persist_positions_instrument_not_found(
        self,
        mapper: PositionMapper,
        fund_repository: FundRepository,
    ) -> None:
        """Raise InstrumentNotFoundError for unknown ISIN."""
        # Setup: create fund but not instrument
        fund = Fund(
            fund_name="Test Fund",
            base_currency="EUR",
            domicile="Luxembourg",
            fund_regime="AIFM",
        )
        fund_repository.insert(fund)

        # Input with non-existent ISIN
        position_input = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="INVALID_ISIN",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="EUR",
        )

        # Should raise InstrumentNotFoundError
        with pytest.raises(InstrumentNotFoundError, match="INVALID_ISIN"):
            mapper.persist_positions([position_input])

    def test_persist_positions_empty_list(self, mapper: PositionMapper) -> None:
        """Handle empty position list gracefully."""
        # Should not raise, just return
        mapper.persist_positions([])


class TestPositionMapperIntegration:
    """Integration tests for position loader + mapper."""

    def test_end_to_end_csv_to_database(
        self,
        mapper: PositionMapper,
        fund_repository: FundRepository,
        instrument_repository: InstrumentRepository,
        position_repository: PositionRepository,
        position_snapshot_repository: PositionSnapshotRepository,
        tmp_path,
    ) -> None:
        """End-to-end: CSV load → position inputs → database persistence."""
        import csv

        # Setup: create fund and instruments
        fund = Fund(
            fund_name="Integration Test Fund",
            base_currency="EUR",
            domicile="Luxembourg",
            fund_regime="AIFM",
        )
        fund = fund_repository.insert(fund)

        for isin in ["IE00B4L5Y983", "US0378331005"]:
            instrument = Instrument(
                isin=isin,
                instrument_name=f"Test {isin}",
                asset_class="Equity",
                currency="EUR",
            )
            instrument_repository.insert(instrument)

        # Create CSV file
        csv_file = tmp_path / "positions.csv"
        with open(csv_file, "w") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "fund_name",
                    "valuation_date",
                    "isin",
                    "quantity",
                    "market_value",
                    "currency",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "fund_name": "Integration Test Fund",
                    "valuation_date": "2025-01-15",
                    "isin": "IE00B4L5Y983",
                    "quantity": "100",
                    "market_value": "12500",
                    "currency": "EUR",
                }
            )
            writer.writerow(
                {
                    "fund_name": "Integration Test Fund",
                    "valuation_date": "2025-01-15",
                    "isin": "US0378331005",
                    "quantity": "50",
                    "market_value": "8000",
                    "currency": "USD",
                }
            )

        # Load and persist
        from manco_risk.etl import PositionLoader

        position_inputs = PositionLoader.load_csv(csv_file)
        mapper.persist_positions(position_inputs)

        # Verify
        snapshot = position_snapshot_repository.find_by_fund_and_date(
            fund.fund_id, date(2025, 1, 15)
        )
        assert snapshot is not None
        assert snapshot.num_positions == 2

        positions = position_repository.find_by_snapshot(snapshot.position_snapshot_id)
        assert len(positions) == 2
        assert positions[0].isin == "IE00B4L5Y983"
        assert positions[1].isin == "US0378331005"
