"""SQLAlchemy session management for manco-risk database.

Provides:
- Engine creation (sqlite for Phase 1)
- Session factory
- Session context manager for safe transaction handling
- Database initialization via metadata.create_all()
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from manco_risk.database.models import Base


def create_database_engine(database_url: str) -> Engine:
    """
    Create a SQLAlchemy engine for the given database URL.

    Parameters
    ----------
    database_url : str
        Database URL. Examples:
        - "sqlite:///:memory:" for in-memory SQLite
        - "sqlite:///manco_risk.db" for file-based SQLite
        - "postgresql://user:pass@localhost/manco_risk" for PostgreSQL (Phase 2+)

    Returns
    -------
    Engine
        SQLAlchemy engine instance.

    Notes
    -----
    Phase 1 uses SQLite. PostgreSQL support deferred to Phase 2.
    """
    if database_url.startswith("sqlite"):
        return create_engine(database_url, connect_args={"check_same_thread": False})
    return create_engine(database_url)


def initialize_database(engine: Engine) -> None:
    """
    Create all tables in the database.

    Uses Base.metadata.create_all() to create tables based on ORM models.
    Safe to call multiple times; existing tables are not recreated.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine instance.

    Notes
    -----
    Phase 1 uses this for initialization. Phase 2+ will use Alembic migrations.
    """
    Base.metadata.create_all(engine)


class SessionFactory:
    """SQLAlchemy session factory for managing database connections."""

    def __init__(self, engine: Engine) -> None:
        """
        Initialize session factory.

        Parameters
        ----------
        engine : Engine
            SQLAlchemy engine instance.
        """
        self.engine = engine
        self._session_maker = sessionmaker(bind=engine, expire_on_commit=False)

    def create_session(self) -> Session:
        """Create a new database session."""
        return self._session_maker()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Context manager for safe session handling.

        Usage:
            factory = SessionFactory(engine)
            with factory.session_scope() as session:
                # perform operations
                # auto-commits on success, rolls back on exception

        Yields
        ------
        Session
            SQLAlchemy session instance.

        Notes
        -----
        - Commits transaction on successful exit
        - Rolls back on exception
        - Always closes session
        """
        session = self._session_maker()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
