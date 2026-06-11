"""Physical instrument leverage exposure calculation engine.

Calculates raw leverage exposure from physical portfolio instruments:
- Equities, bonds, ETFs, listed funds, indices
- Uses market value in base currency as raw exposure
- Source = PHYSICAL_INSTRUMENT
- Treatment = INCLUDED for all physical instruments

Does NOT include:
- Cash (MRS-159)
- Derivatives (MRS-162)
- Borrowing or SFTs
- Leverage calculation or limit monitoring
"""

from decimal import Decimal

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.leverage.enums import ExposureTreatment, LeverageSource
from manco_risk.risk.leverage.models import (
    LeverageExposureSourceContribution,
    LeveragePositionContribution,
    UnsupportedLeverageExposure,
)
from manco_risk.risk.leverage.physical_instrument_result import (
    PhysicalInstrumentExposureResult,
)


class PhysicalInstrumentExposureEngine:
    """Calculate leverage exposure from physical instruments.

    Physical instruments include equities, bonds, ETFs, listed funds, and indices.
    Raw exposure is the absolute market value in the fund's base currency.
    """

    PHYSICAL_INSTRUMENT_ASSET_CLASSES = {"Equity", "Bond", "Index", "ETF", "Listed Fund"}

    def calculate(self, portfolio: RiskReadyPortfolio) -> PhysicalInstrumentExposureResult:
        """Calculate physical instrument leverage exposure.

        Parameters
        ----------
        portfolio
            Risk-ready portfolio with enriched positions.

        Returns
        -------
        PhysicalInstrumentExposureResult
            Position-level contributions, aggregated source contribution,
            unsupported exposures, and warnings.
        """
        position_contributions: list[LeveragePositionContribution] = []
        unsupported_exposures: list[UnsupportedLeverageExposure] = []
        warnings: list[str] = []

        total_gross_exposure = Decimal("0")
        total_commitment_exposure = Decimal("0")

        for position in portfolio.positions:
            if position.asset_class in self.PHYSICAL_INSTRUMENT_ASSET_CLASSES:
                contribution = self._contribution_from_position(position)
                position_contributions.append(contribution)
                total_gross_exposure += contribution.gross_exposure or Decimal("0")
                total_commitment_exposure += contribution.commitment_exposure or Decimal("0")

        source_contribution = (
            self._aggregate_source_contribution(total_gross_exposure, total_commitment_exposure)
            if position_contributions
            else None
        )

        return PhysicalInstrumentExposureResult(
            position_contributions=position_contributions,
            source_contribution=source_contribution,
            unsupported_exposures=unsupported_exposures,
            warnings=warnings,
        )

    def _contribution_from_position(
        self, position: EnrichedPosition
    ) -> LeveragePositionContribution:
        """Create leverage contribution record from a physical instrument position.

        Raw exposure and both gross and commitment exposures are the absolute
        market value in base currency for Phase 1 physical instruments.

        Parameters
        ----------
        position
            Enriched position (guaranteed physical instrument).

        Returns
        -------
        LeveragePositionContribution
            Position contribution with exposure amounts.
        """
        raw_exposure = abs(position.market_value_base_ccy)
        gross_exposure = abs(position.market_value_base_ccy)
        commitment_exposure = abs(position.market_value_base_ccy)

        return LeveragePositionContribution(
            position_id=position.position_id,
            isin=position.isin,
            position_name=None,
            asset_class=position.asset_class,
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            treatment=ExposureTreatment.INCLUDED,
            market_value_base_ccy=position.market_value_base_ccy,
            raw_exposure=raw_exposure,
            gross_exposure=gross_exposure,
            commitment_exposure=commitment_exposure,
            exclusion_reason=None,
        )

    def _aggregate_source_contribution(
        self, total_gross_exposure: Decimal, total_commitment_exposure: Decimal
    ) -> LeverageExposureSourceContribution:
        """Create aggregated source-level contribution.

        Parameters
        ----------
        total_gross_exposure
            Sum of gross exposures from all physical instrument positions.
        total_commitment_exposure
            Sum of commitment exposures from all physical instrument positions.

        Returns
        -------
        LeverageExposureSourceContribution
            Aggregated source contribution.
        """
        return LeverageExposureSourceContribution(
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            gross_exposure=total_gross_exposure,
            commitment_exposure=total_commitment_exposure,
            treatment=ExposureTreatment.INCLUDED,
        )
