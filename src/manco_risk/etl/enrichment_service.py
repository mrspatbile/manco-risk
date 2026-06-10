"""Enrichment service for orchestrating portfolio enrichment.

Responsibilities:
- Load fund, positions, instruments, and NAV from database
- Coordinate with pure PositionEnricher
- Return risk-ready portfolio

Notes:
- All data sources are database repositories
- FX rates provided explicitly by caller
- No market data provider integration
- No persistence of enriched values
- Enriched positions remain in memory only
"""

from datetime import date
from decimal import Decimal

from manco_risk.database import (
    FundRepository,
    InstrumentRepository,
    NAVSnapshotRepository,
    PositionRepository,
    PositionSnapshotRepository,
    SessionFactory,
)
from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.etl.exceptions import FundNotFoundError, NAVSnapshotNotFoundError
from manco_risk.etl.position_enricher import PositionEnricher


class EnrichmentService:
    """Orchestrate enrichment of portfolio positions.

    Loads source data from repositories, coordinates with PositionEnricher,
    and returns risk-ready portfolio.

    No direct market data provider interaction. FX rates must be provided
    explicitly by caller.
    """

    def __init__(self, session_factory: SessionFactory) -> None:
        """Initialize enrichment service.

        Parameters
        ----------
        session_factory : SessionFactory
            Factory for creating database sessions.
        """
        self.session_factory = session_factory
        self.enricher = PositionEnricher()

    def enrich_portfolio_for_fund(
        self,
        fund_id: int,
        valuation_date: date,
        fx_rates: dict[tuple[str, str], Decimal],
    ) -> RiskReadyPortfolio:
        """Enrich positions for a fund on a valuation date.

        Loads fund, positions, instruments, and NAV from database repositories.
        FX rates must be provided explicitly by caller.

        If no position snapshot exists for the fund/date, returns an empty but
        valid RiskReadyPortfolio.

        Parameters
        ----------
        fund_id : int
            Fund identifier
        valuation_date : date
            Valuation date for the portfolio
        fx_rates : dict[tuple[str, str], Decimal]
            FX rates keyed by (from_currency, to_currency).
            Required for any position currency != fund base currency.
            Example: {('USD', 'EUR'): Decimal('0.92')}

        Returns
        -------
        RiskReadyPortfolio
            Enriched portfolio ready for risk calculation

        Raises
        ------
        FundNotFoundError
            If fund_id not found in database
        NAVSnapshotNotFoundError
            If NAV not found for fund on valuation_date
        InstrumentReferenceNotFoundError
            If a position references an ISIN not in database
        MissingFXRateError
            If a position requires currency conversion but FX rate not provided
        """
        # Load fund
        fund_repo = FundRepository(self.session_factory)
        fund = fund_repo.find_by_id(fund_id)
        if fund is None:
            raise FundNotFoundError(f"Fund with id {fund_id} not found")

        # Load NAV
        nav_repo = NAVSnapshotRepository(self.session_factory)
        nav_snapshot = nav_repo.find_by_fund_and_date(fund_id, valuation_date)
        if nav_snapshot is None:
            raise NAVSnapshotNotFoundError(fund_id, valuation_date)

        # Load position snapshot (may not exist)
        snapshot_repo = PositionSnapshotRepository(self.session_factory)
        position_snapshot = snapshot_repo.find_by_fund_and_date(fund_id, valuation_date)

        # Load positions
        if position_snapshot is not None:
            position_repo = PositionRepository(self.session_factory)
            positions = position_repo.find_by_snapshot(position_snapshot.position_snapshot_id)
        else:
            positions = []

        # Load all instruments
        instrument_repo = InstrumentRepository(self.session_factory)
        all_instruments = instrument_repo.find_all()
        instruments_by_isin = {inst.isin: inst for inst in all_instruments}

        # Enrich portfolio
        return self.enricher.enrich_portfolio(
            fund_id=fund.fund_id,
            fund_base_currency=fund.base_currency,
            valuation_date=valuation_date,
            nav=nav_snapshot.nav_value,
            positions=positions,
            instruments_by_isin=instruments_by_isin,
            fx_rates=fx_rates,
        )
