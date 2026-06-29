"""Time-to-liquidate (TTL) calculation engine.

Estimates how many days are required to liquidate a position given
liquidation capacity assumptions.

Does NOT:
- Apply haircuts to proceeds (deferred to liquidation accounting)
- Include market impact modeling
- Handle partial liquidation strategies
- Calculate liquidation proceeds value
"""

from manco_risk.risk.liquidity.models import (
    LiquidationAssumptionSet,
    LiquidationCapacityAssumption,
    PositionLiquidityInput,
    TimeToLiquidateResult,
)


class TimeToLiquidateEngine:
    """Calculate time-to-liquidate for a position.

    Given a position and liquidation capacity assumptions, estimates the number
    of days required to liquidate the full position at the specified capacity.

    Formula:
    days_to_liquidate = position.market_value / capacity_per_day

    Fractional days are preserved (e.g., 2.5 days for a position half the daily capacity).
    """

    def calculate(
        self,
        position: PositionLiquidityInput,
        assumptions: LiquidationAssumptionSet,
    ) -> TimeToLiquidateResult:
        """Calculate time-to-liquidate for a position.

        Parameters
        ----------
        position
            Position data (asset_class, market_value).
        assumptions
            Liquidation capacity assumptions indexed by asset_class.

        Returns
        -------
        TimeToLiquidateResult
            Estimated days to liquidate; includes capacity assumption used.

        Raises
        ------
        ValueError
            If position asset_class not found in assumptions.
        """
        capacity = self._find_capacity(position.asset_class, assumptions)

        if capacity is None:
            raise ValueError(
                f"No liquidation capacity assumption found for asset_class: {position.asset_class}"
            )

        days_to_liquidate = position.market_value / capacity.market_value_per_day

        return TimeToLiquidateResult(
            position_id=position.position_id,
            isin=position.isin,
            asset_class=position.asset_class,
            market_value=position.market_value,
            days_to_liquidate=days_to_liquidate,
            liquidation_capacity_per_day=capacity.market_value_per_day,
        )

    def _find_capacity(
        self,
        asset_class: str,
        assumptions: LiquidationAssumptionSet,
    ) -> LiquidationCapacityAssumption | None:
        """Find liquidation capacity for asset class."""
        for capacity in assumptions.capacity_assumptions:
            if capacity.asset_class == asset_class:
                return capacity
        return None
