"""Database repository layer for manco-risk.

Provides type-safe data access patterns for ORM entities.

Philosophy:
- Start minimal: only implement what a real domain query needs
- No broad CRUD abstractions
- Base repository handles session scope + common patterns only
- Domain-specific repositories add domain queries as needed
"""

from datetime import date
from typing import Generic, TypeVar

from manco_risk.database.models import (
    CalculationRun,
    CalculationStatusEnum,
    ExpectedShortfallResult,
    Fund,
    Instrument,
    MarketDataPoint,
    MarketDataTypeEnum,
    NAVSnapshot,
    Position,
    PositionSnapshot,
    RiskMethodology,
    StressTestResult,
    VaRBacktestingResult,
    VaRResult,
)
from manco_risk.database.session import SessionFactory

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Minimal base repository for shared session handling.

    Provides:
    - Session factory injection
    - Context manager for safe session handling
    - No generic CRUD methods (add only what real queries need)
    """

    def __init__(self, session_factory: SessionFactory) -> None:
        """Initialize repository with session factory.

        Parameters
        ----------
        session_factory : SessionFactory
            Session factory for creating database sessions.
        """
        self.session_factory = session_factory


class FundRepository(BaseRepository):
    """Repository for Fund entity.

    Implements domain queries for Fund:
    - find_by_id: get fund by primary key
    - find_all: list all funds
    - find_by_name: get fund by name
    - insert: persist new fund
    """

    def find_by_id(self, fund_id: int) -> Fund | None:
        """Find a fund by primary key.

        Parameters
        ----------
        fund_id : int
            Fund ID.

        Returns
        -------
        Fund | None
            Fund if found, None otherwise.
        """
        with self.session_factory.session_scope() as session:
            fund = session.query(Fund).filter(Fund.fund_id == fund_id).first()
            if fund:
                session.expunge(fund)
            return fund

    def find_all(self) -> list[Fund]:
        """Find all funds.

        Returns
        -------
        list[Fund]
            List of all funds. Empty list if none exist.
        """
        with self.session_factory.session_scope() as session:
            funds = session.query(Fund).all()
            for fund in funds:
                session.expunge(fund)
            return funds

    def find_by_name(self, name: str) -> Fund | None:
        """Find a fund by name.

        Parameters
        ----------
        name : str
            Fund name.

        Returns
        -------
        Fund | None
            Fund if found, None otherwise.
        """
        with self.session_factory.session_scope() as session:
            fund = session.query(Fund).filter(Fund.fund_name == name).first()
            if fund:
                session.expunge(fund)
            return fund

    def insert(self, fund: Fund) -> Fund:
        """Insert a new fund.

        Parameters
        ----------
        fund : Fund
            Fund entity to insert. Should not have fund_id set.

        Returns
        -------
        Fund
            Inserted fund with fund_id populated.
        """
        with self.session_factory.session_scope() as session:
            session.add(fund)
            session.flush()
            inserted_fund = fund
            session.expunge(inserted_fund)
            return inserted_fund


class InstrumentRepository(BaseRepository):
    """Repository for Instrument entity.

    Implements domain queries for Instrument:
    - find_by_id: get instrument by primary key
    - find_by_isin: get instrument by ISIN (business key)
    - find_all: list all instruments
    - insert: persist new instrument
    """

    def find_by_id(self, instrument_id: int) -> Instrument | None:
        """Find an instrument by primary key.

        Parameters
        ----------
        instrument_id : int
            Instrument ID.

        Returns
        -------
        Instrument | None
            Instrument if found, None otherwise.
        """
        with self.session_factory.session_scope() as session:
            instrument = (
                session.query(Instrument).filter(Instrument.instrument_id == instrument_id).first()
            )
            if instrument:
                session.expunge(instrument)
            return instrument

    def find_by_isin(self, isin: str) -> Instrument | None:
        """Find an instrument by ISIN.

        Parameters
        ----------
        isin : str
            ISIN (business key).

        Returns
        -------
        Instrument | None
            Instrument if found, None otherwise.
        """
        with self.session_factory.session_scope() as session:
            instrument = session.query(Instrument).filter(Instrument.isin == isin).first()
            if instrument:
                session.expunge(instrument)
            return instrument

    def find_all(self) -> list[Instrument]:
        """Find all instruments.

        Returns
        -------
        list[Instrument]
            List of all instruments. Empty list if none exist.
        """
        with self.session_factory.session_scope() as session:
            instruments = session.query(Instrument).all()
            for instrument in instruments:
                session.expunge(instrument)
            return instruments

    def insert(self, instrument: Instrument) -> Instrument:
        """Insert a new instrument.

        Parameters
        ----------
        instrument : Instrument
            Instrument entity to insert. Should not have instrument_id set.

        Returns
        -------
        Instrument
            Inserted instrument with instrument_id populated.
        """
        with self.session_factory.session_scope() as session:
            session.add(instrument)
            session.flush()
            inserted_instrument = instrument
            session.expunge(inserted_instrument)
            return inserted_instrument


class RiskMethodologyRepository(BaseRepository):
    """Repository for RiskMethodology entity.

    Implements domain queries for RiskMethodology:
    - find_by_id: get methodology by primary key
    - find_by_name: get active methodology by name (domain query)
    - find_active: list active methodology versions
    - insert: persist new methodology version
    """

    def find_by_id(self, methodology_id: int) -> RiskMethodology | None:
        """Find a methodology by primary key.

        Parameters
        ----------
        methodology_id : int
            Methodology version ID.

        Returns
        -------
        RiskMethodology | None
            Methodology if found, None otherwise.
        """
        with self.session_factory.session_scope() as session:
            methodology = (
                session.query(RiskMethodology)
                .filter(RiskMethodology.methodology_version_id == methodology_id)
                .first()
            )
            if methodology:
                session.expunge(methodology)
            return methodology

    def find_by_name(self, name: str) -> RiskMethodology | None:
        """Find an active methodology by name.

        Domain query: returns the first active methodology with matching name.
        Used for methodology lookup by business name.

        Parameters
        ----------
        name : str
            Methodology descriptive name (notes field).

        Returns
        -------
        RiskMethodology | None
            Active methodology if found, None otherwise.
        """
        with self.session_factory.session_scope() as session:
            methodology = (
                session.query(RiskMethodology)
                .filter(
                    RiskMethodology.notes == name,
                    RiskMethodology.is_active,
                )
                .first()
            )
            if methodology:
                session.expunge(methodology)
            return methodology

    def find_active(self) -> list[RiskMethodology]:
        """Find all active methodology versions.

        Domain query: returns only is_active=True versions.
        Used for retrieving current methodology choices.

        Returns
        -------
        list[RiskMethodology]
            List of active methodologies. Empty list if none exist.
        """
        with self.session_factory.session_scope() as session:
            methodologies = session.query(RiskMethodology).filter(RiskMethodology.is_active).all()
            for methodology in methodologies:
                session.expunge(methodology)
            return methodologies

    def insert(self, methodology: RiskMethodology) -> RiskMethodology:
        """Insert a new methodology version.

        Parameters
        ----------
        methodology : RiskMethodology
            RiskMethodology entity to insert. Should not have methodology_version_id set.

        Returns
        -------
        RiskMethodology
            Inserted methodology with methodology_version_id populated.
        """
        with self.session_factory.session_scope() as session:
            session.add(methodology)
            session.flush()
            inserted_methodology = methodology
            session.expunge(inserted_methodology)
            return inserted_methodology


class PositionSnapshotRepository(BaseRepository):
    """Repository for PositionSnapshot entity.

    Implements domain queries for PositionSnapshot:
    - find_by_id: get snapshot by primary key
    - find_by_fund_and_date: get snapshot for fund on specific date
    - find_by_fund: list all snapshots for a fund
    - insert: persist new snapshot
    """

    def find_by_id(self, snapshot_id: int) -> PositionSnapshot | None:
        """Find a position snapshot by primary key."""
        with self.session_factory.session_scope() as session:
            snapshot = (
                session.query(PositionSnapshot)
                .filter(PositionSnapshot.position_snapshot_id == snapshot_id)
                .first()
            )
            if snapshot:
                session.expunge(snapshot)
            return snapshot

    def find_by_fund_and_date(self, fund_id: int, snapshot_date: date) -> PositionSnapshot | None:
        """Find a position snapshot for a fund on a specific date."""
        with self.session_factory.session_scope() as session:
            snapshot = (
                session.query(PositionSnapshot)
                .filter(
                    PositionSnapshot.fund_id == fund_id,
                    PositionSnapshot.valuation_date == snapshot_date,
                )
                .first()
            )
            if snapshot:
                session.expunge(snapshot)
            return snapshot

    def find_by_fund(self, fund_id: int) -> list[PositionSnapshot]:
        """Find all position snapshots for a fund."""
        with self.session_factory.session_scope() as session:
            snapshots = (
                session.query(PositionSnapshot).filter(PositionSnapshot.fund_id == fund_id).all()
            )
            for snapshot in snapshots:
                session.expunge(snapshot)
            return snapshots

    def insert(self, snapshot: PositionSnapshot) -> PositionSnapshot:
        """Insert a new position snapshot."""
        with self.session_factory.session_scope() as session:
            session.add(snapshot)
            session.flush()
            inserted_snapshot = snapshot
            session.expunge(inserted_snapshot)
            return inserted_snapshot


class PositionRepository(BaseRepository):
    """Repository for Position entity.

    Implements domain queries for Position:
    - find_by_id: get position by primary key
    - find_by_snapshot: get positions in a snapshot
    - insert: persist single position
    - insert_batch: persist multiple positions
    """

    def find_by_id(self, position_id: int) -> Position | None:
        """Find a position by primary key."""
        with self.session_factory.session_scope() as session:
            position = session.query(Position).filter(Position.position_id == position_id).first()
            if position:
                session.expunge(position)
            return position

    def find_by_snapshot(self, snapshot_id: int) -> list[Position]:
        """Find all positions in a snapshot."""
        with self.session_factory.session_scope() as session:
            positions = (
                session.query(Position).filter(Position.position_snapshot_id == snapshot_id).all()
            )
            for position in positions:
                session.expunge(position)
            return positions

    def insert(self, position: Position) -> Position:
        """Insert a single position."""
        with self.session_factory.session_scope() as session:
            session.add(position)
            session.flush()
            inserted_position = position
            session.expunge(inserted_position)
            return inserted_position

    def insert_batch(self, positions: list[Position]) -> list[Position]:
        """Insert multiple positions in a single transaction."""
        with self.session_factory.session_scope() as session:
            session.add_all(positions)
            session.flush()
            for position in positions:
                session.expunge(position)
            return positions


class NAVSnapshotRepository(BaseRepository):
    """Repository for NAVSnapshot entity.

    Implements domain queries for NAVSnapshot:
    - find_by_id: get NAV snapshot by primary key
    - find_by_fund_and_date: get NAV for fund on specific date
    - find_by_fund: list all NAV snapshots for a fund
    - insert: persist new NAV snapshot
    """

    def find_by_id(self, nav_snapshot_id: int) -> NAVSnapshot | None:
        """Find a NAV snapshot by primary key."""
        with self.session_factory.session_scope() as session:
            snapshot = (
                session.query(NAVSnapshot)
                .filter(NAVSnapshot.nav_snapshot_id == nav_snapshot_id)
                .first()
            )
            if snapshot:
                session.expunge(snapshot)
            return snapshot

    def find_by_fund_and_date(self, fund_id: int, nav_date: date) -> NAVSnapshot | None:
        """Find a NAV snapshot for a fund on a specific date."""
        with self.session_factory.session_scope() as session:
            snapshot = (
                session.query(NAVSnapshot)
                .filter(
                    NAVSnapshot.fund_id == fund_id,
                    NAVSnapshot.nav_date == nav_date,
                )
                .first()
            )
            if snapshot:
                session.expunge(snapshot)
            return snapshot

    def find_by_fund(self, fund_id: int) -> list[NAVSnapshot]:
        """Find all NAV snapshots for a fund."""
        with self.session_factory.session_scope() as session:
            snapshots = session.query(NAVSnapshot).filter(NAVSnapshot.fund_id == fund_id).all()
            for snapshot in snapshots:
                session.expunge(snapshot)
            return snapshots

    def insert(self, nav_snapshot: NAVSnapshot) -> NAVSnapshot:
        """Insert a new NAV snapshot."""
        with self.session_factory.session_scope() as session:
            session.add(nav_snapshot)
            session.flush()
            inserted_snapshot = nav_snapshot
            session.expunge(inserted_snapshot)
            return inserted_snapshot


class MarketDataPointRepository(BaseRepository):
    """Repository for MarketDataPoint entity.

    Implements domain queries for MarketDataPoint:
    - find_by_id: get market data point by primary key
    - find_by_instrument_and_date: get prices for instrument on date
    - find_by_type_and_date: get all market data of type on date
    - insert: persist single market data point
    - insert_batch: persist multiple market data points
    """

    def find_by_id(self, market_data_point_id: int) -> MarketDataPoint | None:
        """Find a market data point by primary key."""
        with self.session_factory.session_scope() as session:
            point = (
                session.query(MarketDataPoint)
                .filter(MarketDataPoint.market_data_point_id == market_data_point_id)
                .first()
            )
            if point:
                session.expunge(point)
            return point

    def find_by_instrument_and_date(self, isin: str, market_date: date) -> list[MarketDataPoint]:
        """Find all market data for an instrument on a specific date."""
        with self.session_factory.session_scope() as session:
            points = (
                session.query(MarketDataPoint)
                .filter(
                    MarketDataPoint.isin == isin,
                    MarketDataPoint.valuation_date == market_date,
                )
                .all()
            )
            for point in points:
                session.expunge(point)
            return points

    def find_by_type_and_date(
        self, data_type: MarketDataTypeEnum, market_date: date
    ) -> list[MarketDataPoint]:
        """Find all market data of a specific type on a date."""
        with self.session_factory.session_scope() as session:
            points = (
                session.query(MarketDataPoint)
                .filter(
                    MarketDataPoint.data_type == data_type,
                    MarketDataPoint.valuation_date == market_date,
                )
                .all()
            )
            for point in points:
                session.expunge(point)
            return points

    def insert(self, market_data_point: MarketDataPoint) -> MarketDataPoint:
        """Insert a single market data point."""
        with self.session_factory.session_scope() as session:
            session.add(market_data_point)
            session.flush()
            inserted_point = market_data_point
            session.expunge(inserted_point)
            return inserted_point

    def insert_batch(self, points: list[MarketDataPoint]) -> list[MarketDataPoint]:
        """Insert multiple market data points in a single transaction."""
        with self.session_factory.session_scope() as session:
            session.add_all(points)
            session.flush()
            for point in points:
                session.expunge(point)
            return points


class CalculationRunRepository(BaseRepository):
    """Repository for CalculationRun entity.

    Implements domain queries for CalculationRun:
    - insert: create new calculation run
    - find_by_id: get calculation run by primary key
    - find_by_fund_and_date: find all calculation runs for a fund on a date
    """

    def insert(self, calculation_run: CalculationRun) -> CalculationRun:
        """Insert a new calculation run.

        Parameters
        ----------
        calculation_run : CalculationRun
            CalculationRun entity to insert. Should not have calculation_run_id set.

        Returns
        -------
        CalculationRun
            Inserted calculation run with calculation_run_id populated.
        """
        with self.session_factory.session_scope() as session:
            session.add(calculation_run)
            session.flush()
            inserted_run = calculation_run
            session.expunge(inserted_run)
            return inserted_run

    def find_by_id(self, calculation_run_id: int) -> CalculationRun | None:
        """Find a calculation run by primary key.

        Parameters
        ----------
        calculation_run_id : int
            Calculation run ID.

        Returns
        -------
        CalculationRun | None
            Calculation run if found, None otherwise.
        """
        with self.session_factory.session_scope() as session:
            run = (
                session.query(CalculationRun)
                .filter(CalculationRun.calculation_run_id == calculation_run_id)
                .first()
            )
            if run:
                session.expunge(run)
            return run

    def find_by_fund_and_date(self, fund_id: int, valuation_date: date) -> list[CalculationRun]:
        """Find all calculation runs for a fund on a specific valuation date.

        Parameters
        ----------
        fund_id : int
            Fund ID.
        valuation_date : date
            Valuation date.

        Returns
        -------
        list[CalculationRun]
            List of calculation runs. Empty list if none exist.
        """
        with self.session_factory.session_scope() as session:
            runs = (
                session.query(CalculationRun)
                .filter(
                    CalculationRun.fund_id == fund_id,
                    CalculationRun.valuation_date == valuation_date,
                )
                .all()
            )
            for run in runs:
                session.expunge(run)
            return runs

    def update_status(self, calculation_run_id: int, status: CalculationStatusEnum) -> None:
        """Update status of a calculation run.

        Parameters
        ----------
        calculation_run_id : int
            Calculation run ID.
        status : CalculationStatusEnum
            New status (PENDING, RUNNING, COMPLETED, FAILED).
        """
        with self.session_factory.session_scope() as session:
            run = (
                session.query(CalculationRun)
                .filter(CalculationRun.calculation_run_id == calculation_run_id)
                .first()
            )
            if run:
                run.status = status
                session.flush()


class VaRResultRepository(BaseRepository):
    """Repository for VaRResult entity.

    Implements domain queries for VaRResult:
    - insert: create new VaR result
    - find_by_calculation_run: get all VaR results for a calculation run
    - find_by_fund_and_date: get all VaR results for a fund on a date
    """

    def insert(self, var_result: VaRResult) -> VaRResult:
        """Insert a new VaR result.

        Parameters
        ----------
        var_result : VaRResult
            VaRResult entity to insert. Should not have var_result_id set.

        Returns
        -------
        VaRResult
            Inserted VaR result with var_result_id populated.
        """
        with self.session_factory.session_scope() as session:
            session.add(var_result)
            session.flush()
            inserted_result = var_result
            session.expunge(inserted_result)
            return inserted_result

    def find_by_calculation_run(self, calculation_run_id: int) -> list[VaRResult]:
        """Find all VaR results for a calculation run.

        Parameters
        ----------
        calculation_run_id : int
            Calculation run ID.

        Returns
        -------
        list[VaRResult]
            List of VaR results. Empty list if none exist.
        """
        with self.session_factory.session_scope() as session:
            results = (
                session.query(VaRResult)
                .filter(VaRResult.calculation_run_id == calculation_run_id)
                .all()
            )
            for result in results:
                session.expunge(result)
            return results

    def find_by_fund_and_date(self, fund_id: int, valuation_date: date) -> list[VaRResult]:
        """Find all VaR results for a fund on a specific valuation date.

        Parameters
        ----------
        fund_id : int
            Fund ID.
        valuation_date : date
            Valuation date.

        Returns
        -------
        list[VaRResult]
            List of VaR results. Empty list if none exist.
        """
        with self.session_factory.session_scope() as session:
            results = (
                session.query(VaRResult)
                .join(CalculationRun)
                .filter(
                    VaRResult.fund_id == fund_id,
                    CalculationRun.valuation_date == valuation_date,
                )
                .all()
            )
            for result in results:
                session.expunge(result)
            return results


class ExpectedShortfallResultRepository(BaseRepository):
    """Repository for ExpectedShortfallResult entity.

    Implements domain queries for ExpectedShortfallResult:
    - insert: create new ES result
    - find_by_calculation_run: get all ES results for a calculation run
    - find_by_fund_and_date: get all ES results for a fund on a date
    """

    def insert(self, es_result: ExpectedShortfallResult) -> ExpectedShortfallResult:
        """Insert a new ES result.

        Parameters
        ----------
        es_result : ExpectedShortfallResult
            ExpectedShortfallResult entity to insert. Should not have es_result_id set.

        Returns
        -------
        ExpectedShortfallResult
            Inserted ES result with es_result_id populated.
        """
        with self.session_factory.session_scope() as session:
            session.add(es_result)
            session.flush()
            inserted_result = es_result
            session.expunge(inserted_result)
            return inserted_result

    def find_by_calculation_run(self, calculation_run_id: int) -> list[ExpectedShortfallResult]:
        """Find all ES results for a calculation run.

        Parameters
        ----------
        calculation_run_id : int
            Calculation run ID.

        Returns
        -------
        list[ExpectedShortfallResult]
            List of ES results. Empty list if none exist.
        """
        with self.session_factory.session_scope() as session:
            results = (
                session.query(ExpectedShortfallResult)
                .filter(ExpectedShortfallResult.calculation_run_id == calculation_run_id)
                .all()
            )
            for result in results:
                session.expunge(result)
            return results

    def find_by_fund_and_date(
        self, fund_id: int, valuation_date: date
    ) -> list[ExpectedShortfallResult]:
        """Find all ES results for a fund on a specific valuation date.

        Parameters
        ----------
        fund_id : int
            Fund ID.
        valuation_date : date
            Valuation date.

        Returns
        -------
        list[ExpectedShortfallResult]
            List of ES results. Empty list if none exist.
        """
        with self.session_factory.session_scope() as session:
            results = (
                session.query(ExpectedShortfallResult)
                .join(CalculationRun)
                .filter(
                    ExpectedShortfallResult.fund_id == fund_id,
                    CalculationRun.valuation_date == valuation_date,
                )
                .all()
            )
            for result in results:
                session.expunge(result)
            return results


class VaRBacktestingResultRepository(BaseRepository):
    """Repository for VaRBacktestingResult entity.

    Implements domain queries for VaRBacktestingResult:
    - insert: create new backtest result
    - find_by_calculation_run: get all backtest results for a calculation run
    """

    def insert(self, backtest_result: VaRBacktestingResult) -> VaRBacktestingResult:
        """Insert a new VaR backtesting result.

        Parameters
        ----------
        backtest_result : VaRBacktestingResult
            VaRBacktestingResult entity to insert.
            Should not have backtest_result_id set.

        Returns
        -------
        VaRBacktestingResult
            Inserted backtest result with backtest_result_id populated.
        """
        with self.session_factory.session_scope() as session:
            session.add(backtest_result)
            session.flush()
            inserted_result = backtest_result
            session.expunge(inserted_result)
            return inserted_result

    def find_by_calculation_run(self, calculation_run_id: int) -> list[VaRBacktestingResult]:
        """Find all backtest results for a calculation run.

        Parameters
        ----------
        calculation_run_id : int
            Calculation run ID.

        Returns
        -------
        list[VaRBacktestingResult]
            List of backtest results. Empty list if none exist.
        """
        with self.session_factory.session_scope() as session:
            results = (
                session.query(VaRBacktestingResult)
                .filter(VaRBacktestingResult.calculation_run_id == calculation_run_id)
                .all()
            )
            for result in results:
                session.expunge(result)
            return results


class StressTestResultRepository(BaseRepository):
    """Repository for StressTestResult entity.

    Implements domain queries for StressTestResult:
    - insert: create new stress test result
    - insert_many: create multiple stress test results in a single transaction
    - find_by_calculation_run: get all stress test results for a calculation run
    """

    def insert(self, stress_result: StressTestResult) -> int:
        """Insert a new stress test result.

        Parameters
        ----------
        stress_result : StressTestResult
            StressTestResult entity to insert.
            Should not have stress_test_result_id set.

        Returns
        -------
        int
            Inserted stress test result ID (stress_test_result_id).
        """
        with self.session_factory.session_scope() as session:
            session.add(stress_result)
            session.flush()
            result_id = stress_result.stress_test_result_id
            session.expunge(stress_result)
            return result_id

    def insert_many(self, stress_results: list[StressTestResult]) -> list[int]:
        """Insert multiple stress test results in a single transaction.

        Parameters
        ----------
        stress_results : list[StressTestResult]
            List of StressTestResult entities to insert.
            Should not have stress_test_result_id set.

        Returns
        -------
        list[int]
            List of inserted stress test result IDs.
        """
        with self.session_factory.session_scope() as session:
            session.add_all(stress_results)
            session.flush()
            result_ids = [result.stress_test_result_id for result in stress_results]
            for result in stress_results:
                session.expunge(result)
            return result_ids

    def find_by_calculation_run(self, calculation_run_id: int) -> list[StressTestResult]:
        """Find all stress test results for a calculation run.

        Parameters
        ----------
        calculation_run_id : int
            Calculation run ID.

        Returns
        -------
        list[StressTestResult]
            List of stress test results. Empty list if none exist.
        """
        with self.session_factory.session_scope() as session:
            results = (
                session.query(StressTestResult)
                .filter(StressTestResult.calculation_run_id == calculation_run_id)
                .all()
            )
            for result in results:
                session.expunge(result)
            return results
