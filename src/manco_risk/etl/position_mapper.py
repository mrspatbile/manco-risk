"""Position input mapping and persistence for manco-risk.

Maps validated PositionInput records to database ORM entities and persists them.

Responsibilities:
- Resolve fund_name to Fund via repository
- Verify instrument ISIN exists via repository
- Create or reuse PositionSnapshot for fund/date
- Map PositionInput to Position ORM records
- Persist positions using repositories

Notes:
- Fund and Instrument must pre-exist; this layer does not create them.
- PositionSnapshot is reused if it already exists for the same fund/date.
- Positions are appended to existing snapshots.
"""

from datetime import datetime, timezone

from manco_risk.database import (
    FundRepository,
    InstrumentRepository,
    Position,
    PositionRepository,
    PositionSnapshot,
    PositionSnapshotRepository,
    SessionFactory,
)
from manco_risk.etl.exceptions import (
    FundNotFoundError,
    InstrumentNotFoundError,
    PositionIngestionError,
)
from manco_risk.etl.position_loader import PositionInput


class PositionMapper:
    """Map validated position inputs to database records."""

    def __init__(self, session_factory: SessionFactory) -> None:
        """Initialize mapper with database session factory.

        Parameters
        ----------
        session_factory : SessionFactory
            Factory for creating database sessions.
        """
        self.session_factory = session_factory
        self.fund_repo = FundRepository(session_factory)
        self.instrument_repo = InstrumentRepository(session_factory)
        self.position_snapshot_repo = PositionSnapshotRepository(session_factory)
        self.position_repo = PositionRepository(session_factory)

    def persist_positions(self, position_inputs: list[PositionInput]) -> None:
        """Persist position inputs to database.

        Parameters
        ----------
        position_inputs : list[PositionInput]
            Validated position input records.

        Raises
        ------
        FundNotFoundError
            If fund_name does not exist in database.
        InstrumentNotFoundError
            If ISIN does not exist in database.
        PositionIngestionError
            If persistence fails for another reason.

        Notes
        -----
        - All positions must be for the same fund and valuation_date in a single call.
        - PositionSnapshot is created for new fund/date combinations or reused if exists.
        - Positions are appended to the snapshot.
        """
        if not position_inputs:
            return

        # All inputs must be for the same fund and date (caller's responsibility)
        first_input = position_inputs[0]
        fund_name = first_input.fund_name
        valuation_date = first_input.valuation_date

        # Resolve fund
        fund = self.fund_repo.find_by_name(fund_name)
        if fund is None:
            raise FundNotFoundError(f"Fund '{fund_name}' not found in database")

        # Verify all ISINs exist
        for position_input in position_inputs:
            instrument = self.instrument_repo.find_by_isin(position_input.isin)
            if instrument is None:
                raise InstrumentNotFoundError(
                    f"Instrument with ISIN '{position_input.isin}' not found in database"
                )

        # Find or create PositionSnapshot
        position_snapshot = self.position_snapshot_repo.find_by_fund_and_date(
            fund.fund_id, valuation_date
        )

        if position_snapshot is None:
            # Create new snapshot
            position_snapshot = PositionSnapshot(
                fund_id=fund.fund_id,
                valuation_date=valuation_date,
                source_extract_date=valuation_date,
                load_timestamp=datetime.now(tz=timezone.utc),
                num_positions=len(position_inputs),
            )
            position_snapshot = self.position_snapshot_repo.insert(position_snapshot)
        else:
            # Reuse existing snapshot; update position count
            # Note: num_positions should reflect total positions in the snapshot after load
            # For now, count positions that will be linked to this snapshot
            position_snapshot.num_positions = len(position_inputs)

        # Map inputs to Position ORM records
        positions: list[Position] = []
        for position_input in position_inputs:
            position = Position(
                position_snapshot_id=position_snapshot.position_snapshot_id,
                fund_id=fund.fund_id,
                valuation_date=valuation_date,
                isin=position_input.isin,
                quantity=position_input.quantity,
                market_value=position_input.market_value,
                market_value_base_ccy_source=position_input.market_value_base_ccy_source,
                source_position_identifier=position_input.source_position_identifier,
            )
            positions.append(position)

        # Persist positions
        try:
            self.position_repo.insert_batch(positions)
        except Exception as e:
            raise PositionIngestionError(f"Failed to persist positions: {e}") from e
