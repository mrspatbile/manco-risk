"""UCITS framework: global exposure and monitoring.

Responsibilities:
- Global exposure measurement (commitment approach)
- VaR-based monitoring (absolute VaR)
- UCITS-specific constants and thresholds

Does NOT include:
- AIFMD leverage calculation
- Pricing models or QuantLib
- Greeks calculation
- Database persistence
- Reporting outputs
"""

from manco_risk.risk.ucits.absolute_var import (
    UCITSAbsoluteVaRInput,
    UCITSAbsoluteVaRResult,
    UCITSAbsoluteVaRStatus,
)
from manco_risk.risk.ucits.absolute_var_engine import UCITSAbsoluteVaREngine
from manco_risk.risk.ucits.commitment_engine import UCITSCommitmentGlobalExposureEngine
from manco_risk.risk.ucits.constants import UCITS_ABSOLUTE_VAR_LIMIT_RATIO
from manco_risk.risk.ucits.global_exposure_models import (
    UCITSGlobalExposureInput,
    UCITSGlobalExposureMethod,
    UCITSGlobalExposureResult,
    UCITSGlobalExposureStatus,
)

__all__ = [
    "UCITSAbsoluteVaREngine",
    "UCITSAbsoluteVaRInput",
    "UCITSAbsoluteVaRResult",
    "UCITSAbsoluteVaRStatus",
    "UCITS_ABSOLUTE_VAR_LIMIT_RATIO",
    "UCITSCommitmentGlobalExposureEngine",
    "UCITSGlobalExposureInput",
    "UCITSGlobalExposureMethod",
    "UCITSGlobalExposureResult",
    "UCITSGlobalExposureStatus",
]
