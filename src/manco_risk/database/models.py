"""Phase 1 SQLAlchemy ORM models for manco-risk database.

This module defines the database schema for:
- Source data (Fund, Instrument, Position, MarketDataPoint, NAVSnapshot)
- Lineage (PositionSnapshot, CalculationRun)
- Methodology (RiskMethodology)
- Derived outputs (PnLSeries, VaRResult, ExpectedShortfallResult, VaRBacktestingResult)
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""

    pass


# ============================================================================
# Enumerations
# ============================================================================


class CalculationTypeEnum(str, PyEnum):
    """Type of risk calculation run."""

    VAR_ES_DAILY = "var_es_daily"
    VAR_BACKTEST = "var_backtest"
    STRESS_TEST = "stress_test"


class CalculationStatusEnum(str, PyEnum):
    """Status of calculation run execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MarketDataTypeEnum(str, PyEnum):
    """Type of market data point."""

    PRICE = "price"
    FX_RATE = "fx_rate"
    YIELD = "yield"
    SPREAD = "spread"
    DURATION = "duration"


class FXConversionMethodEnum(str, PyEnum):
    """FX rate conversion methodology."""

    EOD_SPOT = "eod_spot"
    TRANSACTION_RATE = "transaction_rate"
    AVERAGE_RATE = "average_rate"


class MissingDataHandlingEnum(str, PyEnum):
    """How to handle missing market data."""

    STRICT_FAIL = "strict_fail"
    FORWARD_FILL = "forward_fill"
    INTERPOLATE = "interpolate"


class ESMethodEnum(str, PyEnum):
    """Expected Shortfall calculation method."""

    HISTORICAL = "historical"
    PARAMETRIC = "parametric"


class StressTestResultTypeEnum(str, PyEnum):
    """Type of stress test result."""

    HYPOTHETICAL = "hypothetical"
    REVERSE = "reverse"
    HISTORICAL = "historical"


class StressTestAssetScopeEnum(str, PyEnum):
    """Asset scope of stress test (supports future multi-asset stress testing)."""

    EQUITY_LIKE = "equity_like"
    FIXED_INCOME = "fixed_income"
    FX = "fx"
    MULTI_ASSET = "multi_asset"


# ============================================================================
# Source Data Entities
# ============================================================================


class Fund(Base):
    """
    Fund master data.

    Simplified equivalent SQL:

    CREATE TABLE fund (
        fund_id SERIAL PRIMARY KEY,
        fund_name VARCHAR(255) NOT NULL,
        aifm_id VARCHAR(50),
        base_currency VARCHAR(3) NOT NULL,
        domicile VARCHAR(50) NOT NULL,
        fund_regime VARCHAR(50) NOT NULL,
        inception_date DATE,
        nav_reporting_frequency VARCHAR(20),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    Relationships:
    - 1:many to Position
    - 1:many to PositionSnapshot
    - 1:many to NAVSnapshot
    - 1:many to CalculationRun
    - 1:many to RiskMethodology (optional: fund-specific overrides)

    Notes:
    - Pure identity and structural reference data.
    - No methodology parameters stored here (moved to RiskMethodology).
    - Immutable after creation.
    """

    __tablename__ = "fund"

    fund_id: Mapped[int] = mapped_column(primary_key=True)
    fund_name: Mapped[str] = mapped_column(String(255), nullable=False)
    aifm_id: Mapped[Optional[str]] = mapped_column(String(50))
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    domicile: Mapped[str] = mapped_column(String(50), nullable=False)
    fund_regime: Mapped[str] = mapped_column(String(50), nullable=False)
    inception_date: Mapped[Optional[date]] = mapped_column(Date)
    nav_reporting_frequency: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    positions: Mapped[list["Position"]] = relationship("Position", back_populates="fund")
    position_snapshots: Mapped[list["PositionSnapshot"]] = relationship(
        "PositionSnapshot", back_populates="fund"
    )
    nav_snapshots: Mapped[list["NAVSnapshot"]] = relationship("NAVSnapshot", back_populates="fund")
    calculation_runs: Mapped[list["CalculationRun"]] = relationship(
        "CalculationRun", back_populates="fund"
    )
    risk_methodologies: Mapped[list["RiskMethodology"]] = relationship(
        "RiskMethodology", back_populates="fund"
    )


class Instrument(Base):
    """
    Reference data for traded securities.

    Simplified equivalent SQL:

    CREATE TABLE instrument (
        instrument_id SERIAL PRIMARY KEY,
        isin VARCHAR(12) UNIQUE NOT NULL,
        ticker VARCHAR(50),
        instrument_name VARCHAR(255) NOT NULL,
        asset_class VARCHAR(50) NOT NULL,
        currency VARCHAR(3) NOT NULL,
        instrument_type VARCHAR(50),
        is_traded_daily BOOLEAN DEFAULT FALSE,
        issuer_id VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    Relationships:
    - 1:many to Position
    - 1:many to MarketDataPoint

    Notes:
    - ISIN is the primary business identifier (unique constraint).
    - Immutable reference data.
    - is_traded_daily: indicates data availability; default false for illiquid assets.
    - Duration not stored here (date-sensitive, enrichment-dependent).
    """

    __tablename__ = "instrument"

    instrument_id: Mapped[int] = mapped_column(primary_key=True)
    isin: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    ticker: Mapped[Optional[str]] = mapped_column(String(50))
    instrument_name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    instrument_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_traded_daily: Mapped[bool] = mapped_column(default=False, nullable=False)
    issuer_id: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    positions: Mapped[list["Position"]] = relationship("Position", back_populates="instrument")
    market_data_points: Mapped[list["MarketDataPoint"]] = relationship(
        "MarketDataPoint", back_populates="instrument"
    )


class PositionSnapshot(Base):
    """
    Metadata for a batch load of positions from administrator extract.

    Simplified equivalent SQL:

    CREATE TABLE position_snapshot (
        position_snapshot_id SERIAL PRIMARY KEY,
        fund_id INTEGER NOT NULL REFERENCES fund,
        valuation_date DATE NOT NULL,
        source_extract_date DATE NOT NULL,
        source_extract_filename VARCHAR(255),
        load_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        num_positions INTEGER NOT NULL,
        file_hash VARCHAR(64),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (fund_id, valuation_date)
    );

    Relationships:
    - many:1 to Fund
    - 1:many to Position
    - 1:many to CalculationRun

    Notes:
    - Represents one position extract per fund per valuation date.
    - Links positions to their source file metadata.
    - file_hash enables reproducibility verification (optional).
    - Immutable; represents historical state of extracted positions.
    """

    __tablename__ = "position_snapshot"

    position_snapshot_id: Mapped[int] = mapped_column(primary_key=True)
    fund_id: Mapped[int] = mapped_column(
        ForeignKey("fund.fund_id", ondelete="RESTRICT"), nullable=False
    )
    valuation_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_extract_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_extract_filename: Mapped[Optional[str]] = mapped_column(String(255))
    load_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    num_positions: Mapped[int] = mapped_column(nullable=False)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("fund_id", "valuation_date", name="uq_position_snapshot_fund_date"),
    )

    fund: Mapped["Fund"] = relationship("Fund", back_populates="position_snapshots")
    positions: Mapped[list["Position"]] = relationship(
        "Position", back_populates="position_snapshot"
    )
    calculation_runs: Mapped[list["CalculationRun"]] = relationship(
        "CalculationRun", back_populates="position_snapshot"
    )


class Position(Base):
    """
    Source holdings snapshot; one row per security per valuation date.

    Simplified equivalent SQL:

    CREATE TABLE position (
        position_id SERIAL PRIMARY KEY,
        position_snapshot_id INTEGER NOT NULL REFERENCES position_snapshot,
        fund_id INTEGER NOT NULL REFERENCES fund,
        valuation_date DATE NOT NULL,
        isin VARCHAR(12) NOT NULL REFERENCES instrument(isin),
        quantity NUMERIC(16, 6) NOT NULL,
        market_value NUMERIC(18, 8) NOT NULL,
        market_value_base_ccy_source NUMERIC(18, 8),
        source_position_identifier VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (position_snapshot_id, isin)
    );

    Relationships:
    - many:1 to PositionSnapshot
    - many:1 to Fund
    - many:1 to Instrument

    Notes:
    - Minimal validation; validation framework is Phase 4.
    - market_value stored in instrument currency (source fidelity).
    - market_value_base_ccy_source optional (if admin provides base-currency value).
    - weight_pct not stored (derive from market_value / NAV on read).
    - No enrichment fields stored (enrichment computed per calculation run).
    """

    __tablename__ = "position"

    position_id: Mapped[int] = mapped_column(primary_key=True)
    position_snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("position_snapshot.position_snapshot_id", ondelete="RESTRICT"),
        nullable=False,
    )
    fund_id: Mapped[int] = mapped_column(
        ForeignKey("fund.fund_id", ondelete="RESTRICT"), nullable=False
    )
    valuation_date: Mapped[date] = mapped_column(Date, nullable=False)
    isin: Mapped[str] = mapped_column(
        ForeignKey("instrument.isin", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(16, 6), nullable=False)
    market_value: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    market_value_base_ccy_source: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8))
    source_position_identifier: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("position_snapshot_id", "isin", name="uq_position_snapshot_isin"),
    )

    position_snapshot: Mapped["PositionSnapshot"] = relationship(
        "PositionSnapshot", back_populates="positions"
    )
    fund: Mapped["Fund"] = relationship("Fund", back_populates="positions")
    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="positions")


class MarketDataPoint(Base):
    """
    One observed market datum: price, FX rate, yield, spread, or duration.

    Simplified equivalent SQL:

    CREATE TABLE market_data_point (
        market_data_point_id SERIAL PRIMARY KEY,
        isin VARCHAR(12) REFERENCES instrument(isin),
        valuation_date DATE NOT NULL,
        data_type VARCHAR(20) NOT NULL,
        data_value NUMERIC(18, 8) NOT NULL,
        source_provider VARCHAR(50) NOT NULL,
        data_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        data_source_timestamp TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (isin, valuation_date, data_type, source_provider)
    );

    Relationships:
    - many:1 to Instrument (nullable; FX rates have no ISIN)

    Notes:
    - isin nullable for FX rates, spreads (no instrument link).
    - data_type distinguishes price, fx_rate, yield, spread, duration.
    - One price per instrument per date per provider (typical assumption).
    - source_provider tracks data origin (Bloomberg, ECB, fund_admin, manual, etc).
    - Missing data: validation at CalculationRun level (not here).
    - Duration for bonds stored here if available; or computed on demand.
    """

    __tablename__ = "market_data_point"

    market_data_point_id: Mapped[int] = mapped_column(primary_key=True)
    isin: Mapped[Optional[str]] = mapped_column(ForeignKey("instrument.isin", ondelete="RESTRICT"))
    valuation_date: Mapped[date] = mapped_column(Date, nullable=False)
    data_type: Mapped[str] = mapped_column(
        Enum(MarketDataTypeEnum, native_enum=False), nullable=False
    )
    data_value: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    source_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    data_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_source_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "isin",
            "valuation_date",
            "data_type",
            "source_provider",
            name="uq_market_data_point_unique",
        ),
        Index("idx_market_data_isin_date", "isin", "valuation_date"),
        Index("idx_market_data_type_date", "data_type", "valuation_date"),
    )

    instrument: Mapped[Optional["Instrument"]] = relationship(
        "Instrument", back_populates="market_data_points"
    )


class NAVSnapshot(Base):
    """
    Fund net asset value as of date.

    Simplified equivalent SQL:

    CREATE TABLE nav_snapshot (
        nav_snapshot_id SERIAL PRIMARY KEY,
        fund_id INTEGER NOT NULL REFERENCES fund,
        nav_date DATE NOT NULL,
        nav_value NUMERIC(18, 8) NOT NULL,
        aum_value NUMERIC(18, 8),
        nav_source VARCHAR(50) NOT NULL,
        nav_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (fund_id, nav_date)
    );

    Relationships:
    - many:1 to Fund
    - 1:many to CalculationRun (each calc run links to NAV snapshot)

    Notes:
    - Denominator for VaR and ES as % of NAV.
    - One NAV per fund per date (no share class breakdown in Phase 1).
    - aum_value is optional alternative measure.
    - nav_source tracks provenance (accounting_system, admin_extract, calculated).
    - NAV frequency (daily, weekly, monthly) is external constraint; schema does not enforce.
    """

    __tablename__ = "nav_snapshot"

    nav_snapshot_id: Mapped[int] = mapped_column(primary_key=True)
    fund_id: Mapped[int] = mapped_column(
        ForeignKey("fund.fund_id", ondelete="RESTRICT"), nullable=False
    )
    nav_date: Mapped[date] = mapped_column(Date, nullable=False)
    nav_value: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    aum_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8))
    nav_source: Mapped[str] = mapped_column(String(50), nullable=False)
    nav_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("fund_id", "nav_date", name="uq_nav_snapshot_fund_date"),)

    fund: Mapped["Fund"] = relationship("Fund", back_populates="nav_snapshots")
    calculation_runs: Mapped[list["CalculationRun"]] = relationship(
        "CalculationRun", back_populates="nav_snapshot"
    )


# ============================================================================
# Methodology Entity
# ============================================================================


class RiskMethodology(Base):
    """
    Versioned configuration for all risk calculations.

    Simplified equivalent SQL:

    CREATE TABLE risk_methodology (
        methodology_version_id SERIAL PRIMARY KEY,
        effective_date DATE NOT NULL,
        fund_id INTEGER REFERENCES fund,
        var_confidence_level NUMERIC(6, 6) NOT NULL,
        var_lookback_days INTEGER NOT NULL,
        var_horizon_days INTEGER NOT NULL,
        es_method VARCHAR(20) NOT NULL,
        es_lookback_days INTEGER NOT NULL,
        es_horizon_days INTEGER NOT NULL,
        backtesting_window_days INTEGER NOT NULL,
        fx_conversion_method VARCHAR(30) NOT NULL,
        missing_data_handling VARCHAR(20) NOT NULL,
        created_date DATE NOT NULL,
        created_by VARCHAR(100) NOT NULL,
        notes TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    Relationships:
    - many:1 to Fund (optional; nullable = global default)
    - 1:many to CalculationRun

    Notes:
    - Versioning: new row for each change; is_active flag for filtering.
    - Fund-specific: if fund_id is not null, overrides global default for that fund.
    - All calculation engines consume a methodology version.
    - Phase 1: es_method = 'historical' only; parametric deferred.
    - Enforce via app logic: only one active version per fund (or global) per effective_date.
    """

    __tablename__ = "risk_methodology"

    methodology_version_id: Mapped[int] = mapped_column(primary_key=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    fund_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fund.fund_id", ondelete="RESTRICT"))
    var_confidence_level: Mapped[Decimal] = mapped_column(Numeric(6, 6), nullable=False)
    var_lookback_days: Mapped[int] = mapped_column(nullable=False)
    var_horizon_days: Mapped[int] = mapped_column(nullable=False)
    es_method: Mapped[str] = mapped_column(Enum(ESMethodEnum, native_enum=False), nullable=False)
    es_lookback_days: Mapped[int] = mapped_column(nullable=False)
    es_horizon_days: Mapped[int] = mapped_column(nullable=False)
    backtesting_window_days: Mapped[int] = mapped_column(nullable=False)
    fx_conversion_method: Mapped[str] = mapped_column(
        Enum(FXConversionMethodEnum, native_enum=False), nullable=False
    )
    missing_data_handling: Mapped[str] = mapped_column(
        Enum(MissingDataHandlingEnum, native_enum=False), nullable=False
    )
    created_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1000))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    fund: Mapped[Optional["Fund"]] = relationship("Fund", back_populates="risk_methodologies")
    calculation_runs: Mapped[list["CalculationRun"]] = relationship(
        "CalculationRun", back_populates="risk_methodology"
    )


# ============================================================================
# Lineage Entity (Hub)
# ============================================================================


class CalculationRun(Base):
    """
    Execution metadata tying inputs, methodology, and outputs.

    Simplified equivalent SQL:

    CREATE TABLE calculation_run (
        calculation_run_id UUID PRIMARY KEY,
        fund_id INTEGER NOT NULL REFERENCES fund,
        valuation_date DATE NOT NULL,
        calculation_type VARCHAR(30) NOT NULL,
        created_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        methodology_version_id INTEGER NOT NULL REFERENCES risk_methodology,
        position_snapshot_id INTEGER NOT NULL REFERENCES position_snapshot,
        nav_snapshot_id INTEGER NOT NULL REFERENCES nav_snapshot,
        status VARCHAR(20) NOT NULL,
        created_by VARCHAR(100) NOT NULL,
        notes TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    Relationships:
    - many:1 to Fund
    - many:1 to RiskMethodology
    - many:1 to PositionSnapshot
    - many:1 to NAVSnapshot
    - 1:many to PnLSeries (cascade on delete)
    - 1:many to VaRResult (cascade on delete)
    - 1:many to ExpectedShortfallResult (cascade on delete)
    - 1:many to VaRBacktestingResult (cascade on delete)
    - 1:many to StressTestResult (cascade on delete)

    Notes:
    - Central hub for reproducibility and lineage.
    - Links exact inputs (positions, prices, NAV, methodology) to each calculation.
    - Multiple runs per fund per date allowed (ad-hoc recalculations, compliance checks).
    - calculation_type drives which outputs are expected.
    - status tracks execution state.
    - Created only after pre-calculation validation (market data completeness, etc).
    """

    __tablename__ = "calculation_run"

    calculation_run_id: Mapped[int] = mapped_column(primary_key=True)
    fund_id: Mapped[int] = mapped_column(
        ForeignKey("fund.fund_id", ondelete="RESTRICT"), nullable=False
    )
    valuation_date: Mapped[date] = mapped_column(Date, nullable=False)
    calculation_type: Mapped[str] = mapped_column(
        Enum(CalculationTypeEnum, native_enum=False), nullable=False
    )
    created_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    methodology_version_id: Mapped[int] = mapped_column(
        ForeignKey("risk_methodology.methodology_version_id", ondelete="RESTRICT"),
        nullable=False,
    )
    position_snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("position_snapshot.position_snapshot_id", ondelete="RESTRICT"),
        nullable=False,
    )
    nav_snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("nav_snapshot.nav_snapshot_id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(CalculationStatusEnum, native_enum=False), nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1000))

    fund: Mapped["Fund"] = relationship("Fund", back_populates="calculation_runs")
    risk_methodology: Mapped["RiskMethodology"] = relationship(
        "RiskMethodology", back_populates="calculation_runs"
    )
    position_snapshot: Mapped["PositionSnapshot"] = relationship(
        "PositionSnapshot", back_populates="calculation_runs"
    )
    nav_snapshot: Mapped["NAVSnapshot"] = relationship(
        "NAVSnapshot", back_populates="calculation_runs"
    )
    pnl_series: Mapped[list["PnLSeries"]] = relationship(
        "PnLSeries", back_populates="calculation_run", cascade="all, delete-orphan"
    )
    var_results: Mapped[list["VaRResult"]] = relationship(
        "VaRResult", back_populates="calculation_run", cascade="all, delete-orphan"
    )
    es_results: Mapped[list["ExpectedShortfallResult"]] = relationship(
        "ExpectedShortfallResult", back_populates="calculation_run", cascade="all, delete-orphan"
    )
    backtest_results: Mapped[list["VaRBacktestingResult"]] = relationship(
        "VaRBacktestingResult", back_populates="calculation_run", cascade="all, delete-orphan"
    )
    stress_test_results: Mapped[list["StressTestResult"]] = relationship(
        "StressTestResult", back_populates="calculation_run", cascade="all, delete-orphan"
    )


# ============================================================================
# Derived Output Entities
# ============================================================================


class PnLSeries(Base):
    """
    Historical portfolio daily P&L time series.

    Simplified equivalent SQL:

    CREATE TABLE pnl_series (
        pnl_series_id SERIAL PRIMARY KEY,
        calculation_run_id INTEGER NOT NULL REFERENCES calculation_run,
        fund_id INTEGER NOT NULL REFERENCES fund,
        date DATE NOT NULL,
        pnl_absolute NUMERIC(18, 8) NOT NULL,
        pnl_pct NUMERIC(6, 6) NOT NULL,
        num_observations_to_date INTEGER NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (calculation_run_id, date)
    );

    Relationships:
    - many:1 to CalculationRun
    - many:1 to Fund

    Notes:
    - One row per observation date per calculation run.
    - Typically 250 rows for 250-day lookback window.
    - Materialized in database for performance and reproducibility.
    - pnl_absolute: daily portfolio P&L in base currency.
    - pnl_pct: daily P&L as % of NAV (stored for query performance).
    - Does not link directly to VaRResult; both reference same CalculationRun.
    - VaR and backtesting calculations consume this series.
    """

    __tablename__ = "pnl_series"

    pnl_series_id: Mapped[int] = mapped_column(primary_key=True)
    calculation_run_id: Mapped[int] = mapped_column(
        ForeignKey("calculation_run.calculation_run_id", ondelete="CASCADE"),
        nullable=False,
    )
    fund_id: Mapped[int] = mapped_column(
        ForeignKey("fund.fund_id", ondelete="RESTRICT"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    pnl_absolute: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    pnl_pct: Mapped[Decimal] = mapped_column(Numeric(6, 6), nullable=False)
    num_observations_to_date: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("calculation_run_id", "date", name="uq_pnl_series_calc_run_date"),
        Index("idx_pnl_series_fund_date", "fund_id", "date"),
    )

    calculation_run: Mapped["CalculationRun"] = relationship(
        "CalculationRun", back_populates="pnl_series"
    )
    fund: Mapped["Fund"] = relationship("Fund")


class VaRResult(Base):
    """
    Historical Value-at-Risk calculation result.

    Simplified equivalent SQL:

    CREATE TABLE var_result (
        var_result_id SERIAL PRIMARY KEY,
        calculation_run_id INTEGER NOT NULL REFERENCES calculation_run,
        fund_id INTEGER NOT NULL REFERENCES fund,
        confidence_level NUMERIC(6, 6) NOT NULL,
        horizon_days INTEGER NOT NULL,
        var_value_absolute NUMERIC(18, 8) NOT NULL,
        var_pct_nav NUMERIC(6, 6) NOT NULL,
        lookback_days INTEGER NOT NULL,
        num_observations_used INTEGER NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (calculation_run_id, confidence_level, horizon_days)
    );

    Relationships:
    - many:1 to CalculationRun
    - many:1 to Fund

    Notes:
    - One record per confidence level, horizon, and calculation run.
    - Calculated from PnLSeries via quantile (no direct FK).
    - Loss convention: VaR reported as positive.
    - Linked to RiskMethodology via CalculationRun.
    - Always >= ES at same confidence level.
    """

    __tablename__ = "var_result"

    var_result_id: Mapped[int] = mapped_column(primary_key=True)
    calculation_run_id: Mapped[int] = mapped_column(
        ForeignKey("calculation_run.calculation_run_id", ondelete="CASCADE"),
        nullable=False,
    )
    fund_id: Mapped[int] = mapped_column(
        ForeignKey("fund.fund_id", ondelete="RESTRICT"), nullable=False
    )
    confidence_level: Mapped[Decimal] = mapped_column(Numeric(6, 6), nullable=False)
    horizon_days: Mapped[int] = mapped_column(nullable=False)
    var_value_absolute: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    var_pct_nav: Mapped[Decimal] = mapped_column(Numeric(6, 6), nullable=False)
    lookback_days: Mapped[int] = mapped_column(nullable=False)
    num_observations_used: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "calculation_run_id",
            "confidence_level",
            "horizon_days",
            name="uq_var_result_calc_run_confidence_horizon",
        ),
    )

    calculation_run: Mapped["CalculationRun"] = relationship(
        "CalculationRun", back_populates="var_results"
    )
    fund: Mapped["Fund"] = relationship("Fund")


class ExpectedShortfallResult(Base):
    """
    Historical Expected Shortfall (CVaR) calculation result.

    Simplified equivalent SQL:

    CREATE TABLE expected_shortfall_result (
        es_result_id SERIAL PRIMARY KEY,
        calculation_run_id INTEGER NOT NULL REFERENCES calculation_run,
        fund_id INTEGER NOT NULL REFERENCES fund,
        confidence_level NUMERIC(6, 6) NOT NULL,
        horizon_days INTEGER NOT NULL,
        es_value_absolute NUMERIC(18, 8) NOT NULL,
        es_pct_nav NUMERIC(6, 6) NOT NULL,
        method VARCHAR(20) NOT NULL,
        num_breaches INTEGER NOT NULL,
        num_observations_used INTEGER NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (calculation_run_id, confidence_level, horizon_days)
    );

    Relationships:
    - many:1 to CalculationRun
    - many:1 to Fund

    Notes:
    - One record per confidence level, horizon, and calculation run.
    - Conditional mean of tail losses beyond VaR threshold.
    - method: 'historical' in Phase 1; 'parametric' deferred.
    - num_breaches: count of observations below VaR threshold; validates ES reliability.
    - Always >= VaR at same confidence level.
    """

    __tablename__ = "expected_shortfall_result"

    es_result_id: Mapped[int] = mapped_column(primary_key=True)
    calculation_run_id: Mapped[int] = mapped_column(
        ForeignKey("calculation_run.calculation_run_id", ondelete="CASCADE"),
        nullable=False,
    )
    fund_id: Mapped[int] = mapped_column(
        ForeignKey("fund.fund_id", ondelete="RESTRICT"), nullable=False
    )
    confidence_level: Mapped[Decimal] = mapped_column(Numeric(6, 6), nullable=False)
    horizon_days: Mapped[int] = mapped_column(nullable=False)
    es_value_absolute: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    es_pct_nav: Mapped[Decimal] = mapped_column(Numeric(6, 6), nullable=False)
    method: Mapped[str] = mapped_column(Enum(ESMethodEnum, native_enum=False), nullable=False)
    num_breaches: Mapped[int] = mapped_column(nullable=False)
    num_observations_used: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "calculation_run_id",
            "confidence_level",
            "horizon_days",
            name="uq_es_result_calc_run_confidence_horizon",
        ),
    )

    calculation_run: Mapped["CalculationRun"] = relationship(
        "CalculationRun", back_populates="es_results"
    )
    fund: Mapped["Fund"] = relationship("Fund")


class VaRBacktestingResult(Base):
    """
    1-day VaR backtesting metrics and statistical tests.

    Simplified equivalent SQL:

    CREATE TABLE var_backtesting_result (
        backtest_result_id SERIAL PRIMARY KEY,
        calculation_run_id INTEGER NOT NULL REFERENCES calculation_run,
        fund_id INTEGER NOT NULL REFERENCES fund,
        window_days INTEGER NOT NULL,
        total_observations INTEGER NOT NULL,
        num_exceptions INTEGER NOT NULL,
        pof NUMERIC(6, 6) NOT NULL,
        kupiec_test_statistic NUMERIC(18, 8) NOT NULL,
        kupiec_p_value NUMERIC(6, 6) NOT NULL,
        kupiec_reject BOOLEAN NOT NULL,
        christoffersen_uc_test_statistic NUMERIC(18, 8) NOT NULL,
        christoffersen_cc_test_statistic NUMERIC(18, 8) NOT NULL,
        christoffersen_reject BOOLEAN NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (calculation_run_id, window_days)
    );

    Relationships:
    - many:1 to CalculationRun
    - many:1 to Fund

    Notes:
    - 1-day backtesting only in Phase 1; multi-day deferred.
    - Kupiec POF test: binomial test for unconditional coverage.
    - Christoffersen test: UC + independence test (no clustering of exceptions).
    - exception_dates not stored; compute on demand from PnLSeries and VaRResult.
    - kupiec_reject/christoffersen_reject: bool flags indicate model under-conservative
      (too few exceptions) or over-conservative (too many).
    """

    __tablename__ = "var_backtesting_result"

    backtest_result_id: Mapped[int] = mapped_column(primary_key=True)
    calculation_run_id: Mapped[int] = mapped_column(
        ForeignKey("calculation_run.calculation_run_id", ondelete="CASCADE"),
        nullable=False,
    )
    fund_id: Mapped[int] = mapped_column(
        ForeignKey("fund.fund_id", ondelete="RESTRICT"), nullable=False
    )
    window_days: Mapped[int] = mapped_column(nullable=False)
    total_observations: Mapped[int] = mapped_column(nullable=False)
    num_exceptions: Mapped[int] = mapped_column(nullable=False)
    pof: Mapped[Decimal] = mapped_column(Numeric(6, 6), nullable=False)
    kupiec_test_statistic: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    kupiec_p_value: Mapped[Decimal] = mapped_column(Numeric(6, 6), nullable=False)
    kupiec_reject: Mapped[bool] = mapped_column(nullable=False)
    christoffersen_uc_test_statistic: Mapped[Decimal] = mapped_column(
        Numeric(18, 8), nullable=False
    )
    christoffersen_cc_test_statistic: Mapped[Decimal] = mapped_column(
        Numeric(18, 8), nullable=False
    )
    christoffersen_reject: Mapped[bool] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "calculation_run_id",
            "window_days",
            name="uq_backtest_result_calc_run_window",
        ),
    )

    calculation_run: Mapped["CalculationRun"] = relationship(
        "CalculationRun", back_populates="backtest_results"
    )
    fund: Mapped["Fund"] = relationship("Fund")


class StressTestResult(Base):
    """
    Stress test calculation result (hypothetical, reverse, or historical).

    Simplified equivalent SQL:

    CREATE TABLE stress_test_result (
        stress_test_result_id SERIAL PRIMARY KEY,
        calculation_run_id INTEGER NOT NULL REFERENCES calculation_run,
        fund_id INTEGER NOT NULL REFERENCES fund,
        scenario_id VARCHAR(100) NOT NULL,
        scenario_name VARCHAR(255) NOT NULL,
        scenario_type VARCHAR(50) NOT NULL,
        scenario_source VARCHAR(50) NOT NULL,
        result_type VARCHAR(20) NOT NULL,
        asset_scope VARCHAR(30) NOT NULL,
        shock_type VARCHAR(50),
        shock_rate NUMERIC(18, 8),
        current_nav NUMERIC(18, 8) NOT NULL,
        stressed_nav NUMERIC(18, 8),
        total_pnl NUMERIC(18, 8),
        loss_pct_nav NUMERIC(18, 8),
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    Relationships:
    - many:1 to CalculationRun
    - many:1 to Fund

    Notes:
    - Generic stress test result table supporting multiple methodologies.
    - result_type discriminator: HYPOTHETICAL, REVERSE, HISTORICAL.
    - asset_scope: EQUITY_LIKE, FIXED_INCOME, FX, MULTI_ASSET (supports future extensions).
    - Shock-based methodologies (HYPOTHETICAL, REVERSE) populate shock_type and shock_rate.
    - Historical stress does not use shock_type or shock_rate.
    - HYPOTHETICAL and REVERSE: all fields populated when feasible.
    - REVERSE infeasible: stressed_nav, total_pnl, loss_pct_nav are NULL.
    - HISTORICAL: always fully populated; validates stressed_nav = current_nav + worst_scenario_pnl.
    - Monetary fields (current_nav, stressed_nav, total_pnl) use base currency.
    - loss_pct_nav: percentage as decimal (0.05 = 5%); NULL for infeasible reverse stress.
    - All shock values (shock_rate, loss_pct_nav) use Numeric(18, 8) for precision.
    """

    __tablename__ = "stress_test_result"

    stress_test_result_id: Mapped[int] = mapped_column(primary_key=True)
    calculation_run_id: Mapped[int] = mapped_column(
        ForeignKey("calculation_run.calculation_run_id", ondelete="CASCADE"),
        nullable=False,
    )
    fund_id: Mapped[int] = mapped_column(
        ForeignKey("fund.fund_id", ondelete="RESTRICT"), nullable=False
    )
    scenario_id: Mapped[str] = mapped_column(String(100), nullable=False)
    scenario_name: Mapped[str] = mapped_column(String(255), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(50), nullable=False)
    scenario_source: Mapped[str] = mapped_column(String(50), nullable=False)
    result_type: Mapped[str] = mapped_column(
        Enum(StressTestResultTypeEnum, native_enum=False), nullable=False
    )
    asset_scope: Mapped[str] = mapped_column(
        Enum(StressTestAssetScopeEnum, native_enum=False), nullable=False
    )
    shock_type: Mapped[Optional[str]] = mapped_column(String(50))
    shock_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8))
    current_nav: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    stressed_nav: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8))
    total_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8))
    loss_pct_nav: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8))
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    __table_args__ = (Index("idx_stress_test_result_calc_run_id", "calculation_run_id"),)

    calculation_run: Mapped["CalculationRun"] = relationship(
        "CalculationRun", back_populates="stress_test_results"
    )
    fund: Mapped["Fund"] = relationship("Fund")
