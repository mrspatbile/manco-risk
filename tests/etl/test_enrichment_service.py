"""Integration tests for enrichment service."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

from manco_risk.database import Base, SessionFactory
from manco_risk.database.models import (
    Fund,
    Instrument,
    NAVSnapshot,
    Position,
    PositionSnapshot,
)
from manco_risk.etl import (
    EnrichmentService,
    InstrumentReferenceNotFoundError,
    MissingFXRateError,
    NAVSnapshotNotFoundError,
)
from manco_risk.etl.exceptions import FundNotFoundError


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = SessionFactory(engine)
    return session_factory


@pytest.fixture
def sample_fund(in_memory_db):
    """Create a sample fund in the database."""
    session_factory = in_memory_db

    with session_factory.session_scope() as session:
        fund = Fund(
            fund_name="Test Fund",
            base_currency="EUR",
            domicile="LU",
            fund_regime="AIF",
        )
        session.add(fund)
        session.flush()
        fund_id = fund.fund_id
        session.expunge(fund)

    return session_factory, fund_id


@pytest.fixture
def sample_instruments(in_memory_db):
    """Create sample instruments in the database."""
    session_factory = in_memory_db

    with session_factory.session_scope() as session:
        instruments = [
            Instrument(
                isin="IE00B4L5Y983",
                instrument_name="iShares MSCI World ETF",
                asset_class="EQUITY",
                currency="USD",
            ),
            Instrument(
                isin="DE0001102309",
                instrument_name="German Bund",
                asset_class="BOND",
                currency="EUR",
            ),
            Instrument(
                isin="US0378331005",
                instrument_name="Apple Inc",
                asset_class="EQUITY",
                currency="USD",
            ),
        ]
        session.add_all(instruments)
        session.flush()
        isins = [inst.isin for inst in instruments]
        session.expunge_all()

    return session_factory, isins


class TestEnrichmentService:
    """Test EnrichmentService enrichment coordination."""

    def test_happy_path_same_currency(self, sample_fund, sample_instruments) -> None:
        """Enrich portfolio with all positions in fund base currency."""
        session_factory, fund_id = sample_fund
        _, isins = sample_instruments
        valuation_date = date(2026, 6, 10)

        # Create position snapshot and positions
        with session_factory.session_scope() as session:
            snapshot = PositionSnapshot(
                fund_id=fund_id,
                valuation_date=valuation_date,
                source_extract_date=valuation_date,
                load_timestamp=date.today(),
                num_positions=1,
            )
            session.add(snapshot)
            session.flush()
            snapshot_id = snapshot.position_snapshot_id

            position = Position(
                position_snapshot_id=snapshot_id,
                fund_id=fund_id,
                valuation_date=valuation_date,
                isin=isins[1],  # EUR bond
                quantity=Decimal("500"),
                market_value=Decimal("100000.00"),
            )
            session.add(position)

            nav_snapshot = NAVSnapshot(
                fund_id=fund_id,
                nav_date=valuation_date,
                nav_value=Decimal("1000000.00"),
                nav_source="test",
                nav_timestamp=datetime.now(tz=timezone.utc),
            )
            session.add(nav_snapshot)
            session.flush()
            session.expunge_all()

        # Enrich
        service = EnrichmentService(session_factory)
        portfolio = service.enrich_portfolio_for_fund(
            fund_id=fund_id,
            valuation_date=valuation_date,
            fx_rates={},  # No FX rates needed
        )

        assert portfolio.fund_id == fund_id
        assert len(portfolio.positions) == 1
        assert portfolio.nav == Decimal("1000000.00")
        assert portfolio.fund_base_currency == "EUR"

        enriched = portfolio.positions[0]
        assert enriched.isin == isins[1]
        assert enriched.market_value_base_ccy == Decimal("100000.00")
        assert enriched.weight == Decimal("100000.00") / Decimal("1000000.00")

    def test_mixed_currency_portfolio(self, sample_fund, sample_instruments) -> None:
        """Enrich portfolio with multiple currencies using FX rates."""
        session_factory, fund_id = sample_fund
        _, isins = sample_instruments
        valuation_date = date(2026, 6, 10)

        # Create positions in multiple currencies
        with session_factory.session_scope() as session:
            snapshot = PositionSnapshot(
                fund_id=fund_id,
                valuation_date=valuation_date,
                source_extract_date=valuation_date,
                load_timestamp=date.today(),
                num_positions=2,
            )
            session.add(snapshot)
            session.flush()
            snapshot_id = snapshot.position_snapshot_id

            # EUR position
            position1 = Position(
                position_snapshot_id=snapshot_id,
                fund_id=fund_id,
                valuation_date=valuation_date,
                isin=isins[1],  # EUR bond
                quantity=Decimal("500"),
                market_value=Decimal("100000.00"),
            )

            # USD position
            position2 = Position(
                position_snapshot_id=snapshot_id,
                fund_id=fund_id,
                valuation_date=valuation_date,
                isin=isins[0],  # USD equity
                quantity=Decimal("1000"),
                market_value=Decimal("100000.00"),
            )
            session.add_all([position1, position2])

            nav_snapshot = NAVSnapshot(
                fund_id=fund_id,
                nav_date=valuation_date,
                nav_value=Decimal("1000000.00"),
                nav_source="test",
                nav_timestamp=datetime.now(tz=timezone.utc),
            )
            session.add(nav_snapshot)
            session.flush()
            session.expunge_all()

        # Enrich with FX rate
        service = EnrichmentService(session_factory)
        portfolio = service.enrich_portfolio_for_fund(
            fund_id=fund_id,
            valuation_date=valuation_date,
            fx_rates={
                ("USD", "EUR"): Decimal("0.92"),
            },
        )

        assert len(portfolio.positions) == 2

        # EUR position: no conversion
        eur_pos = next(p for p in portfolio.positions if p.isin == isins[1])
        assert eur_pos.market_value_base_ccy == Decimal("100000.00")

        # USD position: converted
        usd_pos = next(p for p in portfolio.positions if p.isin == isins[0])
        expected_base_ccy = Decimal("100000.00") * Decimal("0.92")
        assert usd_pos.market_value_base_ccy == expected_base_ccy

        # Total weight should be correct
        total_weight = (Decimal("100000.00") + expected_base_ccy) / Decimal("1000000.00")
        assert portfolio.total_weight == total_weight

    def test_fund_not_found(self, in_memory_db) -> None:
        """Missing fund raises FundNotFoundError."""
        session_factory = in_memory_db

        service = EnrichmentService(session_factory)

        with pytest.raises(FundNotFoundError):
            service.enrich_portfolio_for_fund(
                fund_id=99,  # Non-existent
                valuation_date=date(2026, 6, 10),
                fx_rates={},
            )

    def test_nav_not_found(self, sample_fund, sample_instruments) -> None:
        """Missing NAV raises NAVSnapshotNotFoundError."""
        session_factory, fund_id = sample_fund
        _, _ = sample_instruments
        valuation_date = date(2026, 6, 10)

        # Create position snapshot but no NAV
        with session_factory.session_scope() as session:
            snapshot = PositionSnapshot(
                fund_id=fund_id,
                valuation_date=valuation_date,
                source_extract_date=valuation_date,
                load_timestamp=date.today(),
                num_positions=0,
            )
            session.add(snapshot)
            session.flush()
            session.expunge_all()

        service = EnrichmentService(session_factory)

        with pytest.raises(NAVSnapshotNotFoundError) as exc_info:
            service.enrich_portfolio_for_fund(
                fund_id=fund_id,
                valuation_date=valuation_date,
                fx_rates={},
            )

        error = exc_info.value
        assert error.fund_id == fund_id
        assert error.valuation_date == valuation_date

    def test_empty_portfolio_no_position_snapshot(self, sample_fund, sample_instruments) -> None:
        """No position snapshot returns empty but valid portfolio."""
        session_factory, fund_id = sample_fund
        _, _ = sample_instruments
        valuation_date = date(2026, 6, 10)

        # Create NAV but no position snapshot
        with session_factory.session_scope() as session:
            nav_snapshot = NAVSnapshot(
                fund_id=fund_id,
                nav_date=valuation_date,
                nav_value=Decimal("1000000.00"),
                nav_source="test",
                nav_timestamp=datetime.now(tz=timezone.utc),
            )
            session.add(nav_snapshot)
            session.flush()
            session.expunge_all()

        service = EnrichmentService(session_factory)
        portfolio = service.enrich_portfolio_for_fund(
            fund_id=fund_id,
            valuation_date=valuation_date,
            fx_rates={},
        )

        assert portfolio.fund_id == fund_id
        assert len(portfolio.positions) == 0
        assert portfolio.total_weight == Decimal("0")
        assert portfolio.nav == Decimal("1000000.00")

    def test_missing_fx_rate_propagates(self, sample_fund, sample_instruments) -> None:
        """Missing FX rate propagates MissingFXRateError from enricher."""
        session_factory, fund_id = sample_fund
        _, isins = sample_instruments
        valuation_date = date(2026, 6, 10)

        # Create position in USD (different currency)
        with session_factory.session_scope() as session:
            snapshot = PositionSnapshot(
                fund_id=fund_id,
                valuation_date=valuation_date,
                source_extract_date=valuation_date,
                load_timestamp=date.today(),
                num_positions=1,
            )
            session.add(snapshot)
            session.flush()
            snapshot_id = snapshot.position_snapshot_id

            position = Position(
                position_snapshot_id=snapshot_id,
                fund_id=fund_id,
                valuation_date=valuation_date,
                isin=isins[0],  # USD equity
                quantity=Decimal("1000"),
                market_value=Decimal("100000.00"),
            )
            session.add(position)

            nav_snapshot = NAVSnapshot(
                fund_id=fund_id,
                nav_date=valuation_date,
                nav_value=Decimal("1000000.00"),
                nav_source="test",
                nav_timestamp=datetime.now(tz=timezone.utc),
            )
            session.add(nav_snapshot)
            session.flush()
            session.expunge_all()

        service = EnrichmentService(session_factory)

        with pytest.raises(MissingFXRateError) as exc_info:
            service.enrich_portfolio_for_fund(
                fund_id=fund_id,
                valuation_date=valuation_date,
                fx_rates={},  # No FX rate provided
            )

        error = exc_info.value
        assert error.from_currency == "USD"
        assert error.to_currency == "EUR"

    def test_missing_instrument_propagates(self, sample_fund, in_memory_db) -> None:
        """Missing instrument propagates InstrumentReferenceNotFoundError."""
        session_factory, fund_id = sample_fund
        valuation_date = date(2026, 6, 10)

        # Create position but don't create corresponding instrument
        with session_factory.session_scope() as session:
            snapshot = PositionSnapshot(
                fund_id=fund_id,
                valuation_date=valuation_date,
                source_extract_date=valuation_date,
                load_timestamp=date.today(),
                num_positions=1,
            )
            session.add(snapshot)
            session.flush()
            snapshot_id = snapshot.position_snapshot_id

            position = Position(
                position_snapshot_id=snapshot_id,
                fund_id=fund_id,
                valuation_date=valuation_date,
                isin="UNKNOWN_ISIN",  # Not in instruments
                quantity=Decimal("1000"),
                market_value=Decimal("100000.00"),
            )
            session.add(position)

            nav_snapshot = NAVSnapshot(
                fund_id=fund_id,
                nav_date=valuation_date,
                nav_value=Decimal("1000000.00"),
                nav_source="test",
                nav_timestamp=datetime.now(tz=timezone.utc),
            )
            session.add(nav_snapshot)
            session.flush()
            session.expunge_all()

        service = EnrichmentService(session_factory)

        with pytest.raises(InstrumentReferenceNotFoundError) as exc_info:
            service.enrich_portfolio_for_fund(
                fund_id=fund_id,
                valuation_date=valuation_date,
                fx_rates={},
            )

        error = exc_info.value
        assert error.isin == "UNKNOWN_ISIN"

    def test_decimal_precision_preserved(self, sample_fund, sample_instruments) -> None:
        """Decimal precision preserved through enrichment."""
        session_factory, fund_id = sample_fund
        _, isins = sample_instruments
        valuation_date = date(2026, 6, 10)

        with session_factory.session_scope() as session:
            snapshot = PositionSnapshot(
                fund_id=fund_id,
                valuation_date=valuation_date,
                source_extract_date=valuation_date,
                load_timestamp=date.today(),
                num_positions=1,
            )
            session.add(snapshot)
            session.flush()
            snapshot_id = snapshot.position_snapshot_id

            position = Position(
                position_snapshot_id=snapshot_id,
                fund_id=fund_id,
                valuation_date=valuation_date,
                isin=isins[0],  # USD
                quantity=Decimal("123.456789"),
                market_value=Decimal("12345.6789123"),
            )
            session.add(position)

            nav_snapshot = NAVSnapshot(
                fund_id=fund_id,
                nav_date=valuation_date,
                nav_value=Decimal("1000000"),
                nav_source="test",
                nav_timestamp=datetime.now(tz=timezone.utc),
            )
            session.add(nav_snapshot)
            session.flush()
            session.expunge_all()

        service = EnrichmentService(session_factory)
        portfolio = service.enrich_portfolio_for_fund(
            fund_id=fund_id,
            valuation_date=valuation_date,
            fx_rates={
                ("USD", "EUR"): Decimal("0.9234567890"),
            },
        )

        enriched = portfolio.positions[0]
        assert enriched.quantity == Decimal("123.456789")
        assert enriched.market_value == Decimal("12345.6789123")

        # Weight should preserve precision
        expected_weight = (Decimal("12345.6789123") * Decimal("0.9234567890")) / Decimal("1000000")
        assert enriched.weight == expected_weight

    def test_multiple_positions_correct_totals(self, sample_fund, sample_instruments) -> None:
        """Multiple positions sum to correct total weight."""
        session_factory, fund_id = sample_fund
        _, isins = sample_instruments
        valuation_date = date(2026, 6, 10)

        with session_factory.session_scope() as session:
            snapshot = PositionSnapshot(
                fund_id=fund_id,
                valuation_date=valuation_date,
                source_extract_date=valuation_date,
                load_timestamp=date.today(),
                num_positions=3,
            )
            session.add(snapshot)
            session.flush()
            snapshot_id = snapshot.position_snapshot_id

            positions_to_add = [
                Position(
                    position_snapshot_id=snapshot_id,
                    fund_id=fund_id,
                    valuation_date=valuation_date,
                    isin=isins[1],  # EUR
                    quantity=Decimal("250"),
                    market_value=Decimal("250000.00"),
                ),
                Position(
                    position_snapshot_id=snapshot_id,
                    fund_id=fund_id,
                    valuation_date=valuation_date,
                    isin=isins[0],  # USD
                    quantity=Decimal("250"),
                    market_value=Decimal("250000.00"),
                ),
                Position(
                    position_snapshot_id=snapshot_id,
                    fund_id=fund_id,
                    valuation_date=valuation_date,
                    isin=isins[2],  # USD
                    quantity=Decimal("500"),
                    market_value=Decimal("500000.00"),
                ),
            ]
            session.add_all(positions_to_add)

            nav_snapshot = NAVSnapshot(
                fund_id=fund_id,
                nav_date=valuation_date,
                nav_value=Decimal("1000000.00"),
                nav_source="test",
                nav_timestamp=datetime.now(tz=timezone.utc),
            )
            session.add(nav_snapshot)
            session.flush()
            session.expunge_all()

        service = EnrichmentService(session_factory)
        portfolio = service.enrich_portfolio_for_fund(
            fund_id=fund_id,
            valuation_date=valuation_date,
            fx_rates={
                ("USD", "EUR"): Decimal("1.0"),  # 1:1 for simplicity
            },
        )

        assert len(portfolio.positions) == 3
        # Total weight should be exactly 1.0 (fully invested)
        assert portfolio.total_weight == Decimal("1")
