"""Protocol defining the fixed-income stress pricer interface.

The FixedIncomeStressPricer protocol separates the stress engine (portfolio
orchestration) from the position-level pricing methodology. This allows
the engine to be written once and extended by swapping the pricer:

    Phase 1: DurationBasedFixedIncomePricer  (this module's peer)
    Future:  QuantLibFixedIncomePricer       (not yet implemented)

Any class implementing price_position with the correct signature satisfies
the protocol; no explicit inheritance is required.
"""

from typing import Protocol

from manco_risk.etl.enriched_position import EnrichedPosition
from manco_risk.risk.models.fixed_income_stress_position_result import (
    FixedIncomeStressPositionResult,
)
from manco_risk.risk.models.fixed_income_stress_scenario import FixedIncomeStressScenario


class FixedIncomeStressPricer(Protocol):
    """Protocol for fixed-income position pricing under stress.

    A pricer computes the stressed dirty value and decomposed P&L for a
    single fixed-income position under one stress scenario.

    The stress engine calls price_position for each non-cash position and
    aggregates the results to a portfolio-level result. The engine does not
    contain pricing formulas; those belong entirely to the pricer.

    Interface:
    ----------
    price_position(position, scenario) -> FixedIncomeStressPositionResult

        position : EnrichedPosition
            Enriched position carrying market_value_base_ccy (used as the
            dirty market value proxy in Phase 1), modified_duration, and
            spread_duration.
        scenario : FixedIncomeStressScenario
            Scenario specifying rate_shock_bps and spread_shock_bps.

    Returns:
        FixedIncomeStressPositionResult with rate_pnl, credit_pnl, total_pnl,
        and stressed_dirty_value_base_ccy populated.

    Raises:
        MissingDurationError if a non-zero shock component requires a
        duration field that is None on the position.
    """

    def price_position(
        self,
        position: EnrichedPosition,
        scenario: FixedIncomeStressScenario,
    ) -> FixedIncomeStressPositionResult: ...
