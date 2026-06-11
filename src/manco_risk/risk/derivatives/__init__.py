"""Derivative pricing module.

Pure pricing interface and models for fair value and Greeks.
Prepares for future QuantLib-backed pricing without requiring the dependency.

Responsibilities (Phase 1):
- Pricing input and result models
- Pricer protocol/interface
- Manual/pass-through pricer for testing

Does NOT include:
- QuantLib dependency
- Actual pricing calculations
- Market data loading
- Integration with leverage engines
"""

from manco_risk.risk.derivatives.manual_pricer import ManualDerivativePricer
from manco_risk.risk.derivatives.pricer import (
    DerivativePricer,
)
from manco_risk.risk.derivatives.pricing_models import (
    DerivativePricingInput,
    DerivativePricingResult,
)

__all__ = [
    "DerivativePricer",
    "DerivativePricingInput",
    "DerivativePricingResult",
    "ManualDerivativePricer",
]
