"""PRIIPs framework: Summary Risk Indicator (SRI) output.

Responsibilities:
- Combine pre-computed MRM and CRM classes into final SRI
- Apply PRIIPs SRI combination table (Commission Delegated Regulation 2017/653 Annex II)
- Normalize missing CRM to default class 1 (neutral credit risk)
- Return export-ready typed result

Does NOT include:
- MRM class calculation (volatile-equivalent VaR)
- CRM class calculation (credit rating analysis)
- Performance scenarios
- Cost calculation
- KID generation or formatting

Regulatory reference:
- Commission Delegated Regulation (EU) 2017/653, Annex II
"""

from manco_risk.risk.priips.constants import (
    CRM_DEFAULT_CLASS,
    CRM_MAX_CLASS,
    CRM_MIN_CLASS,
    MRM_MAX_CLASS,
    MRM_MIN_CLASS,
    SRI_COMBINATION_TABLE,
    SRI_MAX_CLASS,
    SRI_MIN_CLASS,
)
from manco_risk.risk.priips.sri import SRIInput, SRIResult
from manco_risk.risk.priips.sri_engine import SRIEngine

__all__ = [
    "SRIEngine",
    "SRIInput",
    "SRIResult",
    "SRI_MIN_CLASS",
    "SRI_MAX_CLASS",
    "MRM_MIN_CLASS",
    "MRM_MAX_CLASS",
    "CRM_MIN_CLASS",
    "CRM_MAX_CLASS",
    "CRM_DEFAULT_CLASS",
    "SRI_COMBINATION_TABLE",
]
