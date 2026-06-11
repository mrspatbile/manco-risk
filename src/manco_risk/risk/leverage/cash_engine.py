"""Cash and cash-equivalent leverage exposure calculation engine.

Calculates leverage exposure for cash and cash-equivalent positions.

Key methodology:
- Base-currency cash is qualifying cash excluded from AIFMD gross exposure (Phase 1).
- Foreign-currency cash is tracked as unsupported (FX exposure complexity).
- Raw exposure is the market value (for tracking), but gross/commitment exposures are zero.

Does NOT include:
- AIFMD gross or commitment aggregation
- Borrowing or reinvested cash
- Leverage ratio calculation or limit monitoring
"""

from decimal import Decimal

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.leverage.cash_result import CashExposureResult
from manco_risk.risk.leverage.enums import ExposureTreatment, LeverageSource
from manco_risk.risk.leverage.models import (
    LeverageExposureSourceContribution,
    LeveragePositionContribution,
    UnsupportedLeverageExposure,
)


class CashExposureEngine:
    """Calculate leverage exposure from cash and cash-equivalent positions.

    Phase 1 treatment:
    - Base-currency cash is excluded from leverage exposure (qualifying cash).
    - Foreign-currency cash is tracked as unsupported (FX complexity).
    """

    CASH_ASSET_CLASS = "Cash"
    EXCLUSION_REASON = "Qualifying cash and cash equivalents excluded from leverage exposure"

    def calculate(self, portfolio: RiskReadyPortfolio) -> CashExposureResult:
        """Calculate cash leverage exposure.

        Parameters
        ----------
        portfolio
            Risk-ready portfolio with enriched positions.

        Returns
        -------
        CashExposureResult
            Position-level contributions (with zero exposure),
            aggregated source contribution (if any base-currency cash),
            unsupported cash exposures (foreign-currency),
            and warnings.
        """
        position_contributions: list[LeveragePositionContribution] = []
        unsupported_exposures: list[UnsupportedLeverageExposure] = []
        warnings: list[str] = []

        total_raw_exposure = Decimal("0")
        has_base_currency_cash = False

        for position in portfolio.positions:
            if position.asset_class == self.CASH_ASSET_CLASS:
                if position.position_currency == portfolio.fund_base_currency:
                    contribution = self._base_currency_cash_contribution(position)
                    position_contributions.append(contribution)
                    total_raw_exposure += abs(position.market_value_base_ccy)
                    has_base_currency_cash = True
                else:
                    unsupported = UnsupportedLeverageExposure(
                        position_id=position.position_id,
                        isin=position.isin,
                        asset_class=position.asset_class,
                        source=LeverageSource.CASH_AND_CASH_EQUIVALENT,
                        reason=f"Foreign-currency cash ({position.position_currency}) not yet supported for leverage; use base-currency cash",
                    )
                    unsupported_exposures.append(unsupported)
                    warnings.append(
                        f"Position {position.position_id}: Foreign-currency cash in {position.position_currency} not supported"
                    )

        source_contribution = (
            self._aggregate_source_contribution(total_raw_exposure)
            if has_base_currency_cash
            else None
        )

        return CashExposureResult(
            position_contributions=position_contributions,
            source_contribution=source_contribution,
            unsupported_exposures=unsupported_exposures,
            warnings=warnings,
        )

    def _base_currency_cash_contribution(
        self, position: EnrichedPosition
    ) -> LeveragePositionContribution:
        """Create leverage contribution record for base-currency cash.

        Base-currency cash is excluded from leverage exposure (zero gross and commitment).
        Raw exposure is tracked for reference.

        Parameters
        ----------
        position
            Enriched position (guaranteed base-currency cash).

        Returns
        -------
        LeveragePositionContribution
            Position contribution with zero gross/commitment exposure.
        """
        raw_exposure = abs(position.market_value_base_ccy)

        return LeveragePositionContribution(
            position_id=position.position_id,
            isin=position.isin,
            position_name=None,
            asset_class=position.asset_class,
            source=LeverageSource.CASH_AND_CASH_EQUIVALENT,
            treatment=ExposureTreatment.EXCLUDED,
            market_value_base_ccy=position.market_value_base_ccy,
            raw_exposure=raw_exposure,
            gross_exposure=Decimal("0"),
            commitment_exposure=Decimal("0"),
            exclusion_reason=self.EXCLUSION_REASON,
        )

    def _aggregate_source_contribution(
        self, total_raw_exposure: Decimal
    ) -> LeverageExposureSourceContribution:
        """Create aggregated source-level contribution.

        Source contribution has zero exposure because base-currency cash is excluded
        from leverage calculation. Raw total is not exposed at source level.

        Parameters
        ----------
        total_raw_exposure
            Sum of raw cash amounts (not used in leverage exposure, but tracked).

        Returns
        -------
        LeverageExposureSourceContribution
            Aggregated source contribution with zero exposure.
        """
        return LeverageExposureSourceContribution(
            source=LeverageSource.CASH_AND_CASH_EQUIVALENT,
            gross_exposure=Decimal("0"),
            commitment_exposure=Decimal("0"),
            treatment=ExposureTreatment.EXCLUDED,
            exclusion_reason=self.EXCLUSION_REASON,
        )
