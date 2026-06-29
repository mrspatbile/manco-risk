"""Derivative leverage exposure calculation engine.

Calculates leverage exposure from derivatives using provided exposure fields.
Does NOT price, calculate Greeks, or model derivative valuation.

Fair value is stored for NAV context but is NOT used for leverage exposure.
Exposure selection uses priority order: delta > equivalent underlying > notional.

Final AIFMD gross and commitment treatment is determined later in aggregation layer.

Does NOT include:
- Pricing models or QuantLib
- Greeks calculation
- Volatility surfaces
- Curves
- Netting or hedging rules
- AIFMD aggregation
- Leverage ratio calculation or limit monitoring
"""

from decimal import Decimal

from manco_risk.risk.leverage.derivative_models import (
    DerivativeRecord,
)
from manco_risk.risk.leverage.derivative_result import DerivativeExposureResult
from manco_risk.risk.leverage.enums import ExposureTreatment, LeverageSource
from manco_risk.risk.leverage.models import (
    LeverageExposureSourceContribution,
    UnsupportedLeverageExposure,
)


class DerivativeExposureEngine:
    """Calculate leverage exposure from derivatives.

    Uses provided exposure fields in priority order (delta > equivalent underlying > notional).
    Fair value is not used as leverage exposure.
    Leaves final AIFMD treatment (inclusion/exclusion from gross or commitment) to
    a later aggregation layer.
    """

    def calculate(self, derivative_records: list[DerivativeRecord]) -> DerivativeExposureResult:
        """Calculate derivative leverage exposure.

        Parameters
        ----------
        derivative_records
            List of derivative records with valuation and exposure data.

        Returns
        -------
        DerivativeExposureResult
            Source-level exposure contribution for DERIVATIVE source (if any usable exposures),
            unsupported derivatives (if any), and warnings.
        """
        total_exposure = Decimal("0")
        unsupported_exposures: list[UnsupportedLeverageExposure] = []
        warnings: list[str] = []

        for record in derivative_records:
            selected_exposure = self._select_exposure(record)

            if selected_exposure is not None:
                total_exposure += selected_exposure
            else:
                unsupported = UnsupportedLeverageExposure(
                    isin=record.underlying_identifier,
                    asset_class=f"Derivative ({record.derivative_type.value})",
                    source=LeverageSource.DERIVATIVE,
                    reason="No usable exposure data (delta-adjusted, equivalent underlying, or notional not provided)",
                )
                unsupported_exposures.append(unsupported)
                warnings.append(
                    f"Derivative {record.derivative_id}: no usable exposure for leverage calculation"
                )

        source_contribution = (
            self._aggregate_source_contribution(total_exposure)
            if total_exposure > Decimal("0")
            else None
        )

        return DerivativeExposureResult(
            derivative_records=derivative_records,
            source_contribution=source_contribution,
            unsupported_exposures=unsupported_exposures,
            warnings=warnings,
        )

    def _select_exposure(self, record: DerivativeRecord) -> Decimal | None:
        """Select exposure in priority order for a derivative record.

        Priority order:
        1. delta_adjusted_exposure_base_ccy
        2. equivalent_underlying_exposure_base_ccy
        3. notional_base_ccy

        Parameters
        ----------
        record
            Derivative record with exposure data.

        Returns
        -------
        Decimal | None
            Selected exposure amount, or None if no usable exposure found.
        """
        if record.exposure.delta_adjusted_exposure_base_ccy is not None:
            return record.exposure.delta_adjusted_exposure_base_ccy

        if record.exposure.equivalent_underlying_exposure_base_ccy is not None:
            return record.exposure.equivalent_underlying_exposure_base_ccy

        if record.exposure.notional_base_ccy is not None:
            return record.exposure.notional_base_ccy

        return None

    def _aggregate_source_contribution(
        self, total_exposure: Decimal
    ) -> LeverageExposureSourceContribution:
        """Create aggregated source-level contribution.

        Parameters
        ----------
        total_exposure
            Sum of selected exposures from all derivatives.

        Returns
        -------
        LeverageExposureSourceContribution
            Source contribution with DERIVATIVE source.
        """
        return LeverageExposureSourceContribution(
            source=LeverageSource.DERIVATIVE,
            gross_exposure=total_exposure,
            commitment_exposure=None,
            treatment=ExposureTreatment.PENDING_METHOD_RULE,
        )
