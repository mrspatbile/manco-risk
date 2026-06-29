"""Liquidity-adjusted VaR calculation engine.

Combines base VaR with a liquidity adjustment cost to account for the cost
of liquidating positions under market stress.

Does NOT:
- Calculate base VaR (accepts base VaR amount as input)
- Model gates, swing pricing, or suspension
- Include multi-period or queue effects
- Model contagion or correlation stress
"""

from datetime import date
from decimal import Decimal

from manco_risk.risk.liquidity.models import (
    LiquidityAdjustedVaRAssumption,
    LiquidityAdjustedVaRResult,
)


class LiquidityAdjustedVaREngine:
    """Calculate VaR adjusted for liquidity costs.

    Adds a liquidity cost adjustment to base VaR to account for the cost
    of liquidating positions. The adjustment is additive:
    - liquidity_adjustment = portfolio_value × liquidity_cost_rate
    - liquidity_adjusted_var = base_var + liquidity_adjustment

    This is a simple, transparent approach suitable for:
    - Bid-ask spread adjustments
    - Market impact costs
    - Liquidity horizon effects (simplified)
    - Haircut costs during stressed liquidation

    Not suitable for:
    - Complex market microstructure modeling
    - Correlated liquidity stress
    - Multi-period redemption scenarios
    """

    def calculate(
        self,
        fund_id: int,
        valuation_date: date,
        portfolio_value: Decimal,
        base_var_amount: Decimal,
        base_var_rate: Decimal,
        assumption: LiquidityAdjustedVaRAssumption,
    ) -> LiquidityAdjustedVaRResult:
        """Calculate liquidity-adjusted VaR.

        Parameters
        ----------
        fund_id
            Fund identifier.
        valuation_date
            Date of calculation.
        portfolio_value
            Fund NAV or portfolio market value (positive, Decimal).
        base_var_amount
            Base VaR loss amount in base currency (non-negative, Decimal).
        base_var_rate
            Base VaR as percentage of portfolio (non-negative, Decimal).
        assumption
            Liquidity adjustment assumption (cost rate and optional label).

        Returns
        -------
        LiquidityAdjustedVaRResult
            Adjusted VaR with liquidity cost included.

        Raises
        ------
        ValueError
            If inputs are invalid.
        """
        liquidity_adjustment = portfolio_value * assumption.liquidity_cost_rate

        liquidity_adjusted_var_amount = base_var_amount + liquidity_adjustment

        liquidity_adjusted_var_rate = liquidity_adjusted_var_amount / portfolio_value

        return LiquidityAdjustedVaRResult(
            fund_id=fund_id,
            valuation_date=valuation_date,
            portfolio_value=portfolio_value,
            base_var_amount=base_var_amount,
            base_var_rate=base_var_rate,
            liquidity_cost_rate=assumption.liquidity_cost_rate,
            liquidity_adjustment=liquidity_adjustment,
            liquidity_adjusted_var_amount=liquidity_adjusted_var_amount,
            liquidity_adjusted_var_rate=liquidity_adjusted_var_rate,
            methodology_label=assumption.methodology_label,
        )
