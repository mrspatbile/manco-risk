"""Derivative pricing to exposure conversion.

Converts pricing results (fair value, Greeks, especially delta) into
leverage exposure records compatible with the DerivativeExposureEngine.

Pure converter with no database or repository imports.
"""

from manco_risk.risk.derivatives.exposure_conversion_models import (
    OptionExposureConversionInput,
    OptionExposureConversionResult,
)
from manco_risk.risk.leverage.derivative_models import (
    DerivativeExposure,
    DerivativeExposureSource,
    DerivativePayoffType,
    DerivativeRecord,
    DerivativeType,
    DerivativeValuation,
    DerivativeValuationSource,
)


class OptionDeltaExposureConverter:
    """Convert option pricing results to delta-adjusted exposure.

    Converts DerivativePricingResult (fair value, delta, etc.) into
    DerivativeRecord with delta-adjusted exposure for leverage computation.

    Exposure formula:
    delta_adjusted_exposure = abs(delta) * spot * abs(quantity) * multiplier

    Delta is taken in absolute value because:
    - Call delta is positive; put delta is negative
    - For exposure magnitude, both long and short positions contribute equally
    - Quantity sign represents direction; delta sign represents option payoff
    - The combined effect is multiplicative; taking absolute value of delta
      ensures negative quantity (short) still produces positive exposure

    Raises:
    - ValueError if delta is None (cannot compute delta-adjusted exposure)
    - ValueError if any input validation fails
    """

    def convert(self, input: OptionExposureConversionInput) -> OptionExposureConversionResult:
        """Convert option pricing result to derivative exposure record.

        Parameters
        ----------
        input
            Option exposure conversion input with pricing result and spot.

        Returns
        -------
        OptionExposureConversionResult
            Derivative record with delta-adjusted exposure, fair value, warnings.

        Raises
        ------
        ValueError
            If delta is None, underlying spot is invalid, or other validation fails.
        """
        if input.pricing_result.delta is None:
            raise ValueError(
                f"Delta is required for delta-adjusted exposure conversion; "
                f"derivative_id={input.derivative_id} has no delta"
            )

        # Extract delta from pricing result
        delta = input.pricing_result.delta
        fair_value = input.pricing_result.fair_value_base_ccy

        # Compute delta-adjusted exposure:
        # Use absolute values because:
        # - delta sign encodes payoff direction (call positive, put negative)
        # - quantity sign encodes position direction (long positive, short negative)
        # - For exposure magnitude, we need the product of absolute values
        delta_adjusted_exposure = (
            abs(delta) * input.underlying_spot * abs(input.quantity) * input.contract_multiplier
        )

        # Create valuation from pricing result
        valuation = DerivativeValuation(
            fair_value_base_ccy=fair_value,
            valuation_source=DerivativeValuationSource.PROVIDED_MODEL_VALUE,
            pricing_model=input.pricing_result.pricing_model,
            valuation_date=input.pricing_result.pricing_date,
        )

        # Create exposure with delta-adjusted amount
        exposure = DerivativeExposure(
            delta_adjusted_exposure_base_ccy=delta_adjusted_exposure,
            exposure_source=DerivativeExposureSource.PROVIDED_DELTA_ADJUSTED,
        )

        # Create derivative record
        derivative_record = DerivativeRecord(
            derivative_id=input.derivative_id,
            derivative_type=DerivativeType.OPTION,
            payoff_type=DerivativePayoffType.NON_LINEAR,
            underlying_identifier=input.underlying_identifier,
            currency=input.currency,
            valuation=valuation,
            exposure=exposure,
            description=input.description,
        )

        return OptionExposureConversionResult(
            derivative_record=derivative_record,
            delta_adjusted_exposure_base_ccy=delta_adjusted_exposure,
            fair_value_base_ccy=fair_value,
            warnings=input.pricing_result.warnings,
        )
