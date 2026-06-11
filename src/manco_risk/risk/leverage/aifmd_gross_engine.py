"""AIFMD gross leverage aggregation engine.

Aggregates source-layer exposure into AIFMD gross method result.
Pure calculation layer with no pricing, derivatives handling, or persistence.
"""

from decimal import Decimal

from manco_risk.risk.leverage.aifmd_aggregation_models import AIFMDLeverageAggregationInput
from manco_risk.risk.leverage.enums import ExposureTreatment, LeverageMethod
from manco_risk.risk.leverage.models import (
    LeverageExposureSourceContribution,
    LeverageMethodResult,
    UnsupportedLeverageExposure,
)


class AIFMDGrossLeverageEngine:
    """Calculate AIFMD gross leverage from source results.

    Aggregates gross exposures from all leverage sources.
    Respects treatment flags: EXCLUDED contributes zero, INCLUDED or PENDING_METHOD_RULE
    contribute their gross_exposure.

    Formula:
        gross leverage = total gross exposure / NAV
    """

    def calculate(self, input: AIFMDLeverageAggregationInput) -> LeverageMethodResult:
        """Calculate AIFMD gross leverage.

        Parameters
        ----------
        input
            Aggregation input with portfolio and all source results.

        Returns
        -------
        LeverageMethodResult
            Gross method result with total exposure, leverage ratio, and audit trail.
        """
        total_exposure = Decimal("0")
        source_contributions: list[LeverageExposureSourceContribution] = []
        unsupported_exposures: list[UnsupportedLeverageExposure] = []
        warnings: list[str] = []

        # Aggregate physical instrument exposure
        if input.physical_result is not None:
            if input.physical_result.source_contribution is not None:
                contribution = input.physical_result.source_contribution
                if contribution.treatment != ExposureTreatment.EXCLUDED:
                    total_exposure += contribution.gross_exposure
                source_contributions.append(contribution)

            unsupported_exposures.extend(input.physical_result.unsupported_exposures)
            warnings.extend(input.physical_result.warnings)

        # Aggregate cash exposure (already zero in source layer)
        if input.cash_result is not None:
            if input.cash_result.source_contribution is not None:
                contribution = input.cash_result.source_contribution
                # Cash is excluded at source layer (gross_exposure = 0, treatment = EXCLUDED)
                # but include it in contribution list for audit
                source_contributions.append(contribution)

            unsupported_exposures.extend(input.cash_result.unsupported_exposures)
            warnings.extend(input.cash_result.warnings)

        # Aggregate direct borrowing and reinvested borrowing
        if input.direct_borrowing_result is not None:
            for contribution in input.direct_borrowing_result.source_contributions:
                if contribution.treatment != ExposureTreatment.EXCLUDED:
                    total_exposure += contribution.gross_exposure
                source_contributions.append(contribution)

            warnings.extend(input.direct_borrowing_result.warnings)

        # Aggregate SFT exposure
        if input.sft_result is not None:
            for contribution in input.sft_result.source_contributions:
                if contribution.treatment != ExposureTreatment.EXCLUDED:
                    total_exposure += contribution.gross_exposure
                source_contributions.append(contribution)

            warnings.extend(input.sft_result.warnings)

        # Aggregate derivative exposure
        if input.derivative_result is not None:
            if input.derivative_result.source_contribution is not None:
                contribution = input.derivative_result.source_contribution
                if contribution.treatment != ExposureTreatment.EXCLUDED:
                    total_exposure += contribution.gross_exposure
                source_contributions.append(contribution)

            unsupported_exposures.extend(input.derivative_result.unsupported_exposures)
            warnings.extend(input.derivative_result.warnings)

        # Calculate leverage ratio
        nav = input.portfolio.nav
        leverage_ratio = total_exposure / nav if nav > Decimal("0") else Decimal("0")

        return LeverageMethodResult(
            method=LeverageMethod.AIFMD_GROSS,
            nav=nav,
            total_exposure=total_exposure,
            leverage_ratio=leverage_ratio,
            position_contributions=[],  # Gross aggregation doesn't track position level
            source_contributions=source_contributions,
            unsupported_exposures=unsupported_exposures,
            warnings=warnings,
        )
