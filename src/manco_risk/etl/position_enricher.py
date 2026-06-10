"""Position enrichment engine for manco-risk.

Responsibilities:
- Convert source Position records to EnrichedPosition objects
- Resolve currency conversions using provided FX rates
- Calculate portfolio weights
- Assemble RiskReadyPortfolio

Notes:
- No database access; all inputs provided explicitly
- No market data provider integration
- No historical price data fetching
- Enriched positions are in-memory; not persisted
- FX rates must be provided for any currency != fund base currency
"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.etl.exceptions import (
    InstrumentReferenceNotFoundError,
    MissingFXRateError,
    PositionEnrichmentError,
)

if TYPE_CHECKING:
    from manco_risk.database import Instrument, Position


class PositionEnricher:
    """Enrich source positions into risk-ready portfolio objects.

    Converts source Position and Instrument records into EnrichedPosition
    objects ready for risk calculation. Handles currency conversion and
    portfolio weight calculation.

    No database access, market data provider calls, or historical price
    fetching. All required data provided explicitly as inputs.
    """

    def enrich_portfolio(
        self,
        fund_id: int,
        fund_base_currency: str,
        valuation_date: date,
        nav: Decimal,
        positions: list["Position"],
        instruments_by_isin: dict[str, "Instrument"],
        fx_rates: dict[tuple[str, str], Decimal],
    ) -> RiskReadyPortfolio:
        """Enrich positions into a risk-ready portfolio.

        Parameters
        ----------
        fund_id : int
            Fund identifier
        fund_base_currency : str
            Fund base currency (uppercase, e.g., 'EUR', 'USD')
        valuation_date : date
            Valuation date for all positions
        nav : Decimal
            Fund net asset value on valuation date (strictly positive)
        positions : list[Position]
            Source position records from database
        instruments_by_isin : dict[str, Instrument]
            Map of ISIN -> Instrument for reference data lookup
        fx_rates : dict[tuple[str, str], Decimal]
            FX rates keyed by (from_currency, to_currency) tuple.
            Example: {('USD', 'EUR'): Decimal('0.92')}
            If from_currency == to_currency, rate must be Decimal('1').

        Returns
        -------
        RiskReadyPortfolio
            Enriched portfolio ready for risk calculation

        Raises
        ------
        PositionEnrichmentError
            If nav is invalid (<=0)
        InstrumentReferenceNotFoundError
            If a position references an ISIN not in instruments_by_isin
        MissingFXRateError
            If a position requires currency conversion but the needed
            FX rate is not provided in fx_rates
        """
        # Validate NAV (complementary to RiskReadyPortfolio validation)
        if nav <= Decimal("0"):
            raise PositionEnrichmentError(f"NAV must be strictly positive, got {nav}")

        enriched_positions: list[EnrichedPosition] = []

        for position in positions:
            # Look up instrument
            instrument = instruments_by_isin.get(position.isin)
            if instrument is None:
                raise InstrumentReferenceNotFoundError(
                    isin=position.isin, position_id=position.position_id
                )

            # Determine position native currency from instrument
            position_currency = instrument.currency

            # Resolve FX rate
            if position_currency == fund_base_currency:
                # Same currency; no conversion needed
                fx_rate = Decimal("1")
            else:
                # Different currency; look up FX rate
                rate_key = (position_currency, fund_base_currency)
                rate = fx_rates.get(rate_key)
                if rate is None:
                    raise MissingFXRateError(
                        from_currency=position_currency,
                        to_currency=fund_base_currency,
                        position_id=position.position_id,
                    )
                fx_rate = rate

            # Calculate base-currency market value
            market_value_base_ccy = position.market_value * fx_rate

            # Calculate weight
            weight = market_value_base_ccy / nav

            # Build enriched position
            # Note: modified_duration not available in Phase 1 Instrument model
            enriched = EnrichedPosition(
                fund_id=fund_id,
                position_snapshot_id=position.position_snapshot_id,
                position_id=position.position_id,
                isin=position.isin,
                valuation_date=valuation_date.isoformat(),
                quantity=position.quantity,
                market_value=position.market_value,
                position_currency=position_currency,
                asset_class=instrument.asset_class,
                instrument_currency=instrument.currency,
                market_value_base_ccy=market_value_base_ccy,
                fund_base_currency=fund_base_currency,
                weight=weight,
                modified_duration=None,
            )
            enriched_positions.append(enriched)

        # Assemble portfolio
        return RiskReadyPortfolio(
            fund_id=fund_id,
            valuation_date=valuation_date.isoformat(),
            fund_base_currency=fund_base_currency,
            nav=nav,
            positions=enriched_positions,
        )
