"""Derivative pricer interface and protocol.

Abstract interface for derivative pricing implementations.
Future implementations (QuantLib, Bloomberg, manual) implement this protocol.
"""

from typing import Protocol

from manco_risk.risk.derivatives.pricing_models import (
    DerivativePricingInput,
    DerivativePricingResult,
)


class DerivativePricer(Protocol):
    """Protocol for derivative pricing implementations.

    Any class implementing this protocol can be used to price derivatives.
    Future implementations:
    - QuantLibPricer: uses QuantLib for pricing and Greeks
    - ManualPricer: manual pass-through for testing
    - MockPricer: mock implementation for unit tests
    - BloombergPricer: integrates with Bloomberg pricing

    Protocol method:
    - price(input) -> DerivativePricingResult
    """

    def price(self, input: DerivativePricingInput) -> DerivativePricingResult:
        """Price a derivative and return fair value and Greeks.

        Parameters
        ----------
        input
            Pricing input with derivative_id, pricing_date, and optional Greeks.

        Returns
        -------
        DerivativePricingResult
            Pricing result with fair value and Greeks.

        Raises
        ------
        ValueError
            If input is invalid or pricing cannot proceed.
        """
        ...
