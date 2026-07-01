"""Private asset analytics modules.

Covers private equity, infrastructure, real estate, and private debt analytics.

Responsibilities:
- Private equity multiples (DPI, RVPI, TVPI, MOIC)
- Infrastructure metrics (DSCR, LTV, duration, inflation sensitivity)
- Real estate stress calculations
- Private debt loan and covenant monitoring

Imports from:
- common/ — types and exceptions

Must not contain:
- Database queries
- File loading
- UI or notebook code
- Valuation platform logic
"""

from manco_risk.risk.private_assets.infrastructure import (
    InfrastructureAnalyticsResult,
    InfrastructureAssetInput,
)
from manco_risk.risk.private_assets.infrastructure_engine import InfrastructureEngine
from manco_risk.risk.private_assets.infrastructure_sensitivity import (
    InfrastructureSensitivityInput,
    InfrastructureSensitivityResult,
)
from manco_risk.risk.private_assets.infrastructure_sensitivity_engine import (
    InfrastructureSensitivityEngine,
)
from manco_risk.risk.private_assets.private_debt import (
    PrivateDebtLoanInput,
    PrivateDebtLoanResult,
)
from manco_risk.risk.private_assets.private_debt_engine import PrivateDebtEngine
from manco_risk.risk.private_assets.private_equity import (
    PrivateEquityAnalyticsResult,
    PrivateEquityCashFlow,
    PrivateEquityInvestmentInput,
)
from manco_risk.risk.private_assets.private_equity_engine import PrivateEquityEngine
from manco_risk.risk.private_assets.real_estate import (
    RealEstateStressInput,
    RealEstateStressResult,
)
from manco_risk.risk.private_assets.real_estate_engine import RealEstateStressEngine

__all__ = [
    "PrivateEquityCashFlow",
    "PrivateEquityInvestmentInput",
    "PrivateEquityAnalyticsResult",
    "PrivateEquityEngine",
    "InfrastructureAssetInput",
    "InfrastructureAnalyticsResult",
    "InfrastructureEngine",
    "InfrastructureSensitivityInput",
    "InfrastructureSensitivityResult",
    "InfrastructureSensitivityEngine",
    "RealEstateStressInput",
    "RealEstateStressResult",
    "RealEstateStressEngine",
    "PrivateDebtLoanInput",
    "PrivateDebtLoanResult",
    "PrivateDebtEngine",
]
