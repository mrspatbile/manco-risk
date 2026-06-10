"""Tests for database session management and initialization."""

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import Engine, inspect, text

from manco_risk.database import (
    Fund,
    Instrument,
    Position,
    PositionSnapshot,
    SessionFactory,
    create_database_engine,
    initialize_database,
)


class TestDatabaseEngine:
    """Tests for engine creation."""

    def test_create_sqlite_memory_engine(self) -> None:
        """Create in-memory SQLite engine."""
        engine = create_database_engine("sqlite:///:memory:")
        assert isinstance(engine, Engine)
        assert engine.url.drivername == "sqlite"

    def test_create_sqlite_file_engine(self, tmp_path) -> None:
        """Create file-based SQLite engine."""
        db_path = tmp_path / "test.db"
        engine = create_database_engine(f"sqlite:///{db_path}")
        assert isinstance(engine, Engine)
        assert engine.url.drivername == "sqlite"


class TestInitializeDatabase:
    """Tests for database initialization."""

    def test_create_all_creates_tables(self) -> None:
        """create_all() creates all ORM model tables."""
        engine = create_database_engine("sqlite:///:memory:")
        initialize_database(engine)

        # Verify tables exist by inspecting schema
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = {
            "fund",
            "instrument",
            "position_snapshot",
            "position",
            "market_data_point",
            "nav_snapshot",
            "risk_methodology",
            "calculation_run",
            "pnl_series",
            "var_result",
            "expected_shortfall_result",
            "var_backtesting_result",
        }
        assert expected_tables.issubset(set(tables))

    def test_initialize_database_idempotent(self) -> None:
        """initialize_database() can be called multiple times safely."""
        engine = create_database_engine("sqlite:///:memory:")
        initialize_database(engine)
        initialize_database(engine)  # Should not raise

        # Verify tables still exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "fund" in tables

    def test_fund_table_schema(self) -> None:
        """Fund table has correct columns and constraints."""
        engine = create_database_engine("sqlite:///:memory:")
        initialize_database(engine)

        inspector = inspect(engine)
        columns = {col["name"]: col for col in inspector.get_columns("fund")}

        assert "fund_id" in columns
        assert "fund_name" in columns
        assert "base_currency" in columns
        assert "domicile" in columns
        assert "fund_regime" in columns
        # Verify fund_name is not nullable
        assert columns["fund_name"]["nullable"] is False

    def test_instrument_table_isin_unique(self) -> None:
        """Instrument.isin has unique constraint."""
        engine = create_database_engine("sqlite:///:memory:")
        initialize_database(engine)

        inspector = inspect(engine)
        constraints = inspector.get_unique_constraints("instrument")
        constraint_cols = [col for constraint in constraints for col in constraint["column_names"]]
        assert "isin" in constraint_cols

    def test_position_snapshot_unique_fund_date(self) -> None:
        """PositionSnapshot has unique constraint on (fund_id, valuation_date)."""
        engine = create_database_engine("sqlite:///:memory:")
        initialize_database(engine)

        inspector = inspect(engine)
        constraints = inspector.get_unique_constraints("position_snapshot")
        assert len(constraints) > 0


class TestSessionFactory:
    """Tests for session factory and context manager."""

    @pytest.fixture
    def engine(self) -> Engine:
        """Create in-memory SQLite engine for tests."""
        eng = create_database_engine("sqlite:///:memory:")
        initialize_database(eng)
        return eng

    def test_session_factory_creation(self, engine: Engine) -> None:
        """SessionFactory initializes correctly."""
        factory = SessionFactory(engine)
        assert factory.engine is engine

    def test_create_session(self, engine: Engine) -> None:
        """create_session() returns a session instance."""
        factory = SessionFactory(engine)
        session = factory.create_session()
        assert session is not None
        session.close()

    def test_session_scope_context_manager(self, engine: Engine) -> None:
        """session_scope context manager yields a session."""
        factory = SessionFactory(engine)
        with factory.session_scope() as session:
            assert session is not None
            # Session should be usable
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_session_scope_commits_on_success(self, engine: Engine) -> None:
        """session_scope commits transaction on success."""
        factory = SessionFactory(engine)

        with factory.session_scope() as session:
            fund = Fund(
                fund_name="Test Fund",
                base_currency="EUR",
                domicile="Luxembourg",
                fund_regime="AIFM",
            )
            session.add(fund)

        # Verify data persisted by querying in new session
        with factory.session_scope() as session:
            count = session.query(Fund).filter_by(fund_name="Test Fund").count()
            assert count == 1

    def test_session_scope_rollback_on_exception(self, engine: Engine) -> None:
        """session_scope rolls back on exception."""
        factory = SessionFactory(engine)

        try:
            with factory.session_scope() as session:
                fund = Fund(
                    fund_name="Failed Fund",
                    base_currency="EUR",
                    domicile="Luxembourg",
                    fund_regime="AIFM",
                )
                session.add(fund)
                raise ValueError("Intentional error")
        except ValueError:
            pass

        # Verify data was rolled back
        with factory.session_scope() as session:
            count = session.query(Fund).filter_by(fund_name="Failed Fund").count()
            assert count == 0

    def test_session_scope_closes_session(self, engine: Engine) -> None:
        """session_scope closes session even on exception."""
        factory = SessionFactory(engine)

        try:
            with factory.session_scope() as session:
                raise ValueError("Intentional error")
        except ValueError:
            pass

        # If session is closed, opening a new one should work fine
        with factory.session_scope() as session:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1


class TestDatabaseIntegration:
    """Integration tests for full database workflow."""

    def test_insert_and_query_fund(self) -> None:
        """Insert and query Fund via session factory."""
        engine = create_database_engine("sqlite:///:memory:")
        initialize_database(engine)
        factory = SessionFactory(engine)

        # Insert
        with factory.session_scope() as session:
            fund = Fund(
                fund_name="Integration Test Fund",
                base_currency="EUR",
                domicile="Luxembourg",
                fund_regime="AIFM",
            )
            session.add(fund)

        # Query
        with factory.session_scope() as session:
            funds = session.query(Fund).filter_by(fund_name="Integration Test Fund").all()
            assert len(funds) == 1
            assert funds[0].base_currency == "EUR"

    def test_insert_instrument_and_position_relationship(self) -> None:
        """Insert and query related Instrument and Position entities."""
        from decimal import Decimal

        engine = create_database_engine("sqlite:///:memory:")
        initialize_database(engine)
        factory = SessionFactory(engine)

        # Insert Instrument
        with factory.session_scope() as session:
            instrument = Instrument(
                isin="IE00B4L5Y983",
                instrument_name="Test ETF",
                asset_class="Equity",
                currency="EUR",
            )
            session.add(instrument)

        # Insert Fund and PositionSnapshot
        with factory.session_scope() as session:
            fund = Fund(
                fund_name="Test Fund",
                base_currency="EUR",
                domicile="Luxembourg",
                fund_regime="AIFM",
            )
            session.add(fund)

        # Insert Position (requires fund and instrument)
        val_date = date(2025, 1, 15)
        load_ts = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        with factory.session_scope() as session:
            position_snapshot = PositionSnapshot(
                fund_id=1,
                valuation_date=val_date,
                source_extract_date=val_date,
                load_timestamp=load_ts,
                num_positions=1,
            )
            session.add(position_snapshot)

        with factory.session_scope() as session:
            position = Position(
                position_snapshot_id=1,
                fund_id=1,
                valuation_date=val_date,
                isin="IE00B4L5Y983",
                quantity=Decimal("100"),
                market_value=Decimal("12500"),
            )
            session.add(position)

        # Query and verify relationships
        with factory.session_scope() as session:
            positions = session.query(Position).all()
            assert len(positions) == 1
            assert positions[0].isin == "IE00B4L5Y983"
            assert positions[0].quantity == Decimal("100")
