"""LMT (Liquidity Management Tools) simulation module.

Provides typed models and engines for LMT simulation: redemption gates,
swing pricing, suspensions, contagion linkage, and redemption backlog tracking.

This module defines the domain model contract and implements specialized
engines (gate, swing, suspension, etc.) for LMT tool triggering and execution.
"""

from manco_risk.risk.liquidity.lmt.backlog_engine import BacklogEngine
from manco_risk.risk.liquidity.lmt.contagion_engine import ContagionEngine
from manco_risk.risk.liquidity.lmt.gate_engine import GateEngine, GateResult
from manco_risk.risk.liquidity.lmt.models import (
    BacklogState,
    ContagionConfig,
    GateTriggerConfig,
    LiquiditySnapshot,
    LMTMonthlyResult,
    LMTScenarioConfig,
    LMTSimulationInput,
    LMTSimulationResult,
    MonthlyRedemptionInput,
    ScenarioVariant,
    SuspensionConfig,
    SwingPricingConfig,
)
from manco_risk.risk.liquidity.lmt.simulation_engine import LMTSimulationEngine
from manco_risk.risk.liquidity.lmt.suspension_engine import (
    SuspensionEngine,
    SuspensionResult,
)
from manco_risk.risk.liquidity.lmt.swing_pricing_engine import (
    SwingPricingEngine,
    SwingPricingResult,
)
from manco_risk.risk.liquidity.models import (
    InvestorConcentrationResult,  # noqa: F401
    PortfolioLiquidityProfileResult,  # noqa: F401
)

# Rebuild LiquiditySnapshot to resolve forward references to liquidity models
LiquiditySnapshot.model_rebuild()

__all__ = [
    "GateTriggerConfig",
    "SwingPricingConfig",
    "SuspensionConfig",
    "ContagionConfig",
    "LMTScenarioConfig",
    "MonthlyRedemptionInput",
    "BacklogState",
    "LMTMonthlyResult",
    "LMTSimulationInput",
    "LMTSimulationResult",
    "LiquiditySnapshot",
    "ScenarioVariant",
    "GateResult",
    "GateEngine",
    "SuspensionResult",
    "SuspensionEngine",
    "SwingPricingResult",
    "SwingPricingEngine",
    "BacklogEngine",
    "ContagionEngine",
    "LMTSimulationEngine",
]
