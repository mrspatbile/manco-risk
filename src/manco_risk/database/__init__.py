"""Database layer for manco-risk.

Provides:
- SQLAlchemy ORM models for Phase 1 entities
- Session management and database initialization
- Repository/query layer for data access
"""

from manco_risk.database.models import (
    Base,
    CalculationRun,
    CalculationStatusEnum,
    CalculationTypeEnum,
    ESMethodEnum,
    ExpectedShortfallResult,
    Fund,
    FXConversionMethodEnum,
    Instrument,
    MarketDataPoint,
    MarketDataTypeEnum,
    MissingDataHandlingEnum,
    NAVSnapshot,
    PnLSeries,
    Position,
    PositionSnapshot,
    RiskMethodology,
    VaRBacktestingResult,
    VaRResult,
)
from manco_risk.database.repositories import (
    BaseRepository,
    FundRepository,
    InstrumentRepository,
    MarketDataPointRepository,
    NAVSnapshotRepository,
    PositionRepository,
    PositionSnapshotRepository,
    RiskMethodologyRepository,
)
from manco_risk.database.session import (
    SessionFactory,
    create_database_engine,
    initialize_database,
)

__all__ = [
    # Models
    "Base",
    "Fund",
    "Instrument",
    "PositionSnapshot",
    "Position",
    "MarketDataPoint",
    "NAVSnapshot",
    "RiskMethodology",
    "CalculationRun",
    "PnLSeries",
    "VaRResult",
    "ExpectedShortfallResult",
    "VaRBacktestingResult",
    # Enums
    "CalculationTypeEnum",
    "CalculationStatusEnum",
    "MarketDataTypeEnum",
    "FXConversionMethodEnum",
    "MissingDataHandlingEnum",
    "ESMethodEnum",
    # Session management
    "create_database_engine",
    "initialize_database",
    "SessionFactory",
    # Repositories
    "BaseRepository",
    "FundRepository",
    "InstrumentRepository",
    "PositionSnapshotRepository",
    "PositionRepository",
    "NAVSnapshotRepository",
    "MarketDataPointRepository",
    "RiskMethodologyRepository",
]
