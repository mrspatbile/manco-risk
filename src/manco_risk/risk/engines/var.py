"""Historical VaR calculation engine.

Pure aggregation of scenario P&Ls into a Value-at-Risk metric.
No scenario generation, no market data fetching, no persistence.
"""

import math
from datetime import date
from decimal import Decimal

from manco_risk.risk.models.var_input import HistoricalVaRInput
from manco_risk.risk.models.var_result import HistoricalVaRResult


class HistoricalVaR:
    """Pure VaR aggregation engine for historical scenario P&Ls.

    Given a portfolio and a distribution of P&Ls (historical scenarios),
    computes the Value-at-Risk at a specified confidence level.

    The engine:
    1. Accepts a list of portfolio P&Ls (one per historical date or scenario).
    2. Sorts P&Ls ascending (worst loss first).
    3. Selects the quantile at (1 - confidence_level).
    4. Reports the loss as a positive magnitude.

    Example:
        >>> portfolio = RiskReadyPortfolio(...)
        >>> pnls = [ScenarioPnL(scenario_date=date(2024,1,1), total_pnl=Decimal("100")), ...]
        >>> input = HistoricalVaRInput(
        ...     portfolio=portfolio,
        ...     confidence_level=Decimal("0.95"),
        ...     horizon_days=1,
        ...     scenario_pnls=pnls
        ... )
        >>> engine = HistoricalVaR()
        >>> result = engine.calculate(input)
        >>> print(result.var_pct_nav)  # e.g., Decimal("0.025")
    """

    def calculate(self, input: HistoricalVaRInput) -> HistoricalVaRResult:
        """Calculate Historical VaR from scenario P&Ls.

        Parameters
        ----------
        input : HistoricalVaRInput
            Portfolio, confidence level, horizon, and scenario P&Ls.

        Returns
        -------
        HistoricalVaRResult
            VaR loss threshold and metadata.

        Raises
        ------
        ValueError
            If input validation fails (handled by Pydantic).
        """
        # Extract inputs
        portfolio = input.portfolio
        confidence_level = input.confidence_level
        scenario_pnls = input.scenario_pnls
        nav = portfolio.nav

        # Extract P&L values and sort ascending (worst loss first)
        pnl_values = [pnl.total_pnl for pnl in scenario_pnls]
        sorted_pnls = sorted(pnl_values)

        # Compute quantile index using empirical quantile rule
        n = len(sorted_pnls)
        quantile_index = math.floor(n * (1 - confidence_level))

        # Clamp to valid range (safety check, should not occur with valid confidence_level)
        quantile_index = min(quantile_index, n - 1)

        # Select the P&L at the quantile
        selected_pnl = sorted_pnls[quantile_index]

        # Convert to loss magnitude (negative P&L → positive VaR)
        if selected_pnl < Decimal("0"):
            var_value = abs(selected_pnl)
        else:
            var_value = Decimal("0")

        # Compute VaR as percentage of NAV
        var_pct_nav = var_value / nav

        # Construct result
        result = HistoricalVaRResult(
            fund_id=portfolio.fund_id,
            valuation_date=date.fromisoformat(portfolio.valuation_date),
            confidence_level=confidence_level,
            horizon_days=input.horizon_days,
            var_value=var_value,
            var_pct_nav=var_pct_nav,
            num_scenarios=n,
            quantile_index=quantile_index,
        )

        return result
