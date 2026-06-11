"""Manual/pass-through derivative pricer for testing.

Accepts explicit fair value and Greeks from caller.
Does not perform any pricing calculation; simply validates and returns input data.

Use case: Testing, manual inputs, validation of pricing interface.
Not for production pricing.
"""

from manco_risk.risk.derivatives.pricing_models import (
    DerivativePricingInput,
    DerivativePricingResult,
)


class ManualDerivativePricer:
    """Manual pass-through pricer for testing.

    Input: DerivativePricingInput with explicit fair_value and Greeks.
    Output: DerivativePricingResult with the same values.

    Rules:
    - fair_value_base_ccy is required (raises ValueError if None).
    - Greeks pass through if provided, stay None if not provided.
    - pricing_model defaults to "manual" if not provided.
    - warnings pass through unchanged.
    """

    def price(self, input: DerivativePricingInput) -> DerivativePricingResult:
        """Price by returning manually provided fair value and Greeks.

        Parameters
        ----------
        input
            Pricing input with required fair_value_base_ccy.

        Returns
        -------
        DerivativePricingResult
            Result with provided fair value and Greeks.

        Raises
        ------
        ValueError
            If fair_value_base_ccy is None (required).
        """
        if input.fair_value_base_ccy is None:
            raise ValueError(
                f"Derivative {input.derivative_id}: fair_value_base_ccy is required "
                "for manual pricer"
            )

        pricing_model = input.pricing_model or "manual"

        return DerivativePricingResult(
            derivative_id=input.derivative_id,
            pricing_date=input.pricing_date,
            fair_value_base_ccy=input.fair_value_base_ccy,
            delta=input.delta,
            gamma=input.gamma,
            vega=input.vega,
            dv01=input.dv01,
            theta=input.theta,
            rho=input.rho,
            pricing_model=pricing_model,
            warnings=input.warnings,
        )
