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
from manco_risk.risk.ucits.borrowing import (
    UCITSBorrowingInput,
    UCITSBorrowingResult,
    UCITSBorrowingStatus,
)
from manco_risk.risk.ucits.borrowing_engine import UCITSBorrowingEngine
from manco_risk.risk.ucits.commitment_engine import UCITSCommitmentGlobalExposureEngine
from manco_risk.risk.ucits.concentration import (
    UCITSConcentrationInput,
    UCITSConcentrationResult,
    UCITSConcentrationStatus,
)
from manco_risk.risk.ucits.concentration_engine import UCITSConcentrationEngine
from manco_risk.risk.ucits.constants import (
    SRRI_VOLATILITY_BANDS,
    UCITS_ABSOLUTE_VAR_LIMIT_RATIO,
    UCITS_BORROWING_LIMIT_RATIO,
    UCITS_ISSUER_CONCENTRATION_LIMIT_RATIO,
    UCITS_OTC_COUNTERPARTY_LIMIT_RATIO,
    UCITS_OTC_CREDIT_INSTITUTION_LIMIT_RATIO,
    UCITS_RELATIVE_VAR_LIMIT_RATIO,
)
from manco_risk.risk.ucits.global_exposure_models import (
    UCITSGlobalExposureInput,
    UCITSGlobalExposureMethod,
    UCITSGlobalExposureResult,
    UCITSGlobalExposureStatus,
)
from manco_risk.risk.ucits.monitoring_summary import UCITSMonitoringSummary
from manco_risk.risk.ucits.monitoring_summary_service import UCITSMonitoringSummaryService
from manco_risk.risk.ucits.otc_counterparty import (
    UCITSCounterpartyCategory,
    UCITSOTCCounterpartyInput,
    UCITSOTCCounterpartyResult,
    UCITSOTCCounterpartyStatus,
)
from manco_risk.risk.ucits.otc_counterparty_engine import UCITSOTCCounterpartyEngine
from manco_risk.risk.ucits.relative_var import (
    UCITSRelativeVaRInput,
    UCITSRelativeVaRResult,
    UCITSRelativeVaRStatus,
)
from manco_risk.risk.ucits.relative_var_engine import UCITSRelativeVaREngine
from manco_risk.risk.ucits.srri import SRRIInput, SRRIResult
from manco_risk.risk.ucits.srri_engine import SRRIEngine

__all__ = [
    "SRRIEngine",
    "SRRIInput",
    "SRRIResult",
    "SRRI_VOLATILITY_BANDS",
    "UCITSAbsoluteVaREngine",
    "UCITSAbsoluteVaRInput",
    "UCITSAbsoluteVaRResult",
    "UCITSAbsoluteVaRStatus",
    "UCITS_ABSOLUTE_VAR_LIMIT_RATIO",
    "UCITSBorrowingEngine",
    "UCITSBorrowingInput",
    "UCITSBorrowingResult",
    "UCITSBorrowingStatus",
    "UCITS_BORROWING_LIMIT_RATIO",
    "UCITSCommitmentGlobalExposureEngine",
    "UCITSConcentrationEngine",
    "UCITSConcentrationInput",
    "UCITSConcentrationResult",
    "UCITSConcentrationStatus",
    "UCITS_ISSUER_CONCENTRATION_LIMIT_RATIO",
    "UCITSCounterpartyCategory",
    "UCITSGlobalExposureInput",
    "UCITSGlobalExposureMethod",
    "UCITSGlobalExposureResult",
    "UCITSGlobalExposureStatus",
    "UCITSMonitoringSummary",
    "UCITSMonitoringSummaryService",
    "UCITSOTCCounterpartyEngine",
    "UCITSOTCCounterpartyInput",
    "UCITSOTCCounterpartyResult",
    "UCITSOTCCounterpartyStatus",
    "UCITS_OTC_COUNTERPARTY_LIMIT_RATIO",
    "UCITS_OTC_CREDIT_INSTITUTION_LIMIT_RATIO",
    "UCITSRelativeVaREngine",
    "UCITSRelativeVaRInput",
    "UCITSRelativeVaRResult",
    "UCITSRelativeVaRStatus",
    "UCITS_RELATIVE_VAR_LIMIT_RATIO",
]
