"""UCITS global exposure module.

Pure UCITS global exposure measurement framework.
Focuses on derivative-based global exposure under commitment approach.

Responsibilities (Phase 1):
- UCITS global exposure method taxonomy
- UCITS global exposure status classification
- Global exposure aggregation (commitment approach)
- Limit status indication (100% NAV limit)

Does NOT include:
- AIFMD leverage calculation
- VaR approaches (absolute or relative)
- Pricing models or QuantLib
- Greeks calculation
- Database persistence
- Reporting outputs
- Limit monitoring
"""

from manco_risk.risk.ucits.commitment_engine import UCITSCommitmentGlobalExposureEngine
from manco_risk.risk.ucits.global_exposure_models import (
    UCITSGlobalExposureInput,
    UCITSGlobalExposureMethod,
    UCITSGlobalExposureResult,
    UCITSGlobalExposureStatus,
)

__all__ = [
    "UCITSCommitmentGlobalExposureEngine",
    "UCITSGlobalExposureInput",
    "UCITSGlobalExposureMethod",
    "UCITSGlobalExposureResult",
    "UCITSGlobalExposureStatus",
]
