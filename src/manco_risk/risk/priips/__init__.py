"""PRIIPs framework: Summary Risk Indicator, Performance Scenarios, and Costs.

Responsibilities:
- Combine pre-computed MRM and CRM classes into final SRI
- Apply PRIIPs SRI combination table (Commission Delegated Regulation 2017/653 Annex II)
- Normalize missing CRM to default class 1 (neutral credit risk)
- Package pre-computed performance scenario returns
- Package pre-computed cost values
- Return export-ready typed results

Does NOT include:
- MRM class calculation (volatile-equivalent VaR)
- CRM class calculation (credit rating analysis)
- Performance scenario calculation or simulation
- Cost calculation or derivation
- KID generation or formatting

Regulatory reference:
- Commission Delegated Regulation (EU) 2017/653, Annex II (SRI)
- Commission Delegated Regulation (EU) 2017/653, Annex IV/V (scenarios)
- Commission Delegated Regulation (EU) 2017/653, Annex VI/VII (costs)
"""

from manco_risk.risk.priips.constants import (
    COST_TYPES,
    CRM_DEFAULT_CLASS,
    CRM_MAX_CLASS,
    CRM_MIN_CLASS,
    MRM_MAX_CLASS,
    MRM_MIN_CLASS,
    RHP_MIN_YEARS,
    SCENARIO_TYPES,
    SRI_COMBINATION_TABLE,
    SRI_MAX_CLASS,
    SRI_MIN_CLASS,
)
from manco_risk.risk.priips.costs import PRIIPSCostsInput, PRIIPSCostsResult
from manco_risk.risk.priips.costs_engine import PRIIPSCostsEngine
from manco_risk.risk.priips.performance_scenarios import (
    PerformanceScenariosInput,
    PerformanceScenariosResult,
)
from manco_risk.risk.priips.performance_scenarios_engine import (
    PerformanceScenariosEngine,
)
from manco_risk.risk.priips.sri import SRIInput, SRIResult
from manco_risk.risk.priips.sri_engine import SRIEngine
from manco_risk.risk.priips.summary import PRIIPSSummaryInput, PRIIPSSummaryResult
from manco_risk.risk.priips.summary_service import PRIIPSSummaryService

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
    "PerformanceScenariosEngine",
    "PerformanceScenariosInput",
    "PerformanceScenariosResult",
    "PRIIPSCostsEngine",
    "PRIIPSCostsInput",
    "PRIIPSCostsResult",
    "PRIIPSSummaryService",
    "PRIIPSSummaryInput",
    "PRIIPSSummaryResult",
    "SCENARIO_TYPES",
    "COST_TYPES",
    "RHP_MIN_YEARS",
]
