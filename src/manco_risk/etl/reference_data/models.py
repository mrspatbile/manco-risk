"""Typed models for reference data: fund profiles, risk policies, historical scenarios.

All models use Pydantic v2 with frozen=True for immutability.
Decimal is used for rates, ratios, and shocks; date for dates.
"""

from datetime import date
from decimal import Decimal
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict


class FundProfile(BaseModel):
    """Validated fund profile from fund_profile.json.

    Extracts core identification and metadata fields.
    Nested objects (redemption_terms, regulatory_classification) left unmodeled.
    """

    schema_version: str
    fund_id: str
    fund_name: str
    fund_type: str
    currency: str
    domicile: str
    inception_date: date
    target_nav_eur: Optional[Decimal] = None
    fund_short_name: Optional[str] = None
    strategy: Optional[str] = None
    regulator: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class RiskPolicy(BaseModel):
    """Validated risk policy from risk_policy.json.

    Extracts key VaR and backtesting parameters.
    Handles inconsistencies between fund types' field names.
    """

    schema_version: str
    fund_id: str
    var_confidence_level: Optional[Decimal] = None
    var_lookback_days: Optional[int] = None
    backtesting_window_days: Optional[int] = None
    historical_scenario_names: Optional[list[str]] = None

    model_config = ConfigDict(frozen=True)


class HistoricalScenario(BaseModel):
    """Single historical scenario with shock parameters.

    Scenario ID (e.g., "2008") is the key in the JSON file.
    """

    scenario_id: str
    name: str
    description: str
    delta_equity: Decimal
    delta_y: Decimal
    delta_spread: Decimal
    fx_shocks: Dict[str, Decimal]

    model_config = ConfigDict(frozen=True)


class HistoricalScenarios(BaseModel):
    """Container for all historical scenarios.

    scenarios: Dict mapping scenario_id (e.g., "2008") to HistoricalScenario.
    """

    schema_version: str
    scenarios: Dict[str, HistoricalScenario]

    model_config = ConfigDict(frozen=True)
