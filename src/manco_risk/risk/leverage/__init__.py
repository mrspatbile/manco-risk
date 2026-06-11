"""Leverage analytics module.

Pure leverage taxonomy and source-level exposure models and engines.

Responsibilities (Phase 1):
- Leverage method taxonomy (AIFMD gross, AIFMD commitment, UCITS)
- Leverage source taxonomy
- Exposure treatment classification
- Position and source contribution models
- Unsupported exposure tracking
- Physical instrument exposure source engine

Does NOT include:
- AIFMD gross aggregation engine
- AIFMD commitment aggregation engine
- Persistence or reporting
- Limit monitoring
- Derivative conversion formulas
- Direct borrowing calculations
- SFT calculations
- Cash treatment (MRS-159)
"""

from manco_risk.risk.leverage.enums import (
    ExposureTreatment,
    LeverageMethod,
    LeverageSource,
)
from manco_risk.risk.leverage.models import (
    LeverageExposureSourceContribution,
    LeverageInput,
    LeverageMethodResult,
    LeveragePositionContribution,
    LeverageResult,
    UnsupportedLeverageExposure,
)
from manco_risk.risk.leverage.physical_instrument_engine import (
    PhysicalInstrumentExposureEngine,
)
from manco_risk.risk.leverage.physical_instrument_result import (
    PhysicalInstrumentExposureResult,
)

__all__ = [
    "ExposureTreatment",
    "LeverageMethod",
    "LeverageSource",
    "LeverageExposureSourceContribution",
    "LeverageInput",
    "LeverageMethodResult",
    "LeveragePositionContribution",
    "LeverageResult",
    "UnsupportedLeverageExposure",
    "PhysicalInstrumentExposureEngine",
    "PhysicalInstrumentExposureResult",
]
