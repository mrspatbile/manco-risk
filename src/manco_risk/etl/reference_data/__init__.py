"""Reference data loaders for fund profiles, risk policies, and scenarios.

Responsibilities:
- Load and validate reference data from JSON files
- Return typed Pydantic models
- Extract key fields from nested JSON structures
- Handle field name variations across fund types

No database persistence, business logic, or data transformations.
"""

from manco_risk.etl.reference_data.fund_profile_loader import FundProfileLoader
from manco_risk.etl.reference_data.models import (
    FundProfile,
    HistoricalScenario,
    HistoricalScenarios,
    RiskPolicy,
)
from manco_risk.etl.reference_data.risk_policy_loader import RiskPolicyLoader
from manco_risk.etl.reference_data.scenario_loader import HistoricalScenarioLoader

__all__ = [
    "FundProfile",
    "RiskPolicy",
    "HistoricalScenario",
    "HistoricalScenarios",
    "FundProfileLoader",
    "RiskPolicyLoader",
    "HistoricalScenarioLoader",
]
