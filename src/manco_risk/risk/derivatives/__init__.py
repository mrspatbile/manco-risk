"""Derivative pricing and exposure conversion module.

Pure pricing interface and models for fair value and Greeks.
Converts pricing results to leverage exposure records.
Prepares for future QuantLib-backed pricing without requiring the dependency.

Responsibilities:
- Pricing input and result models
- Pricer protocol/interface
- Manual/pass-through pricer for testing
- Exposure conversion models
- Option delta-adjusted exposure converter

Does NOT include:
- QuantLib dependency
- Actual pricing calculations
- Market data loading
- AIFMD/UCITS aggregation
"""

from manco_risk.risk.derivatives.exposure_conversion_models import (
    OptionExposureConversionInput,
    OptionExposureConversionResult,
)
from manco_risk.risk.derivatives.exposure_converter import (
    OptionDeltaExposureConverter,
)
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
    "OptionExposureConversionInput",
    "OptionExposureConversionResult",
    "OptionDeltaExposureConverter",
]
