"""Leverage analytics module.

Pure leverage taxonomy and source-level exposure models and engines.

Responsibilities (Phase 1):
- Leverage method taxonomy (AIFMD gross, AIFMD commitment, UCITS)
- Leverage source taxonomy
- Exposure treatment classification
- Position and source contribution models
- Unsupported exposure tracking
- Physical instrument exposure source engine
- Cash and cash-equivalent exposure source engine
- Direct borrowing exposure source engine

Does NOT include:
- AIFMD gross aggregation engine
- AIFMD commitment aggregation engine
- Persistence or reporting
- Limit monitoring
- Derivative conversion formulas
- SFT calculations
"""

from manco_risk.risk.leverage.borrowing_models import (
    BorrowingPurpose,
    BorrowingRecord,
    BorrowingTreatment,
)
from manco_risk.risk.leverage.cash_engine import CashExposureEngine
from manco_risk.risk.leverage.cash_result import CashExposureResult
from manco_risk.risk.leverage.direct_borrowing_engine import DirectBorrowingExposureEngine
from manco_risk.risk.leverage.direct_borrowing_result import DirectBorrowingExposureResult
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
    "BorrowingPurpose",
    "BorrowingRecord",
    "BorrowingTreatment",
    "CashExposureEngine",
    "CashExposureResult",
    "DirectBorrowingExposureEngine",
    "DirectBorrowingExposureResult",
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
