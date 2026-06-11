"""Historical Expected Shortfall calculation engine.

Pure aggregation of scenario P&Ls into an Expected Shortfall metric,
using the matched HistoricalVaR result to define the tail.

No scenario generation, no market data fetching, no persistence.
"""

from datetime import date
from decimal import Decimal

from manco_risk.risk.models.expected_shortfall_input import HistoricalExpectedShortfallInput
from manco_risk.risk.models.expected_shortfall_result import HistoricalExpectedShortfallResult


class HistoricalExpectedShortfall:
    """Pure ES aggregation engine for historical scenario P&Ls.

    Given a portfolio, scenario P&Ls, and a matched HistoricalVaR result,
    computes the Expected Shortfall: the conditional mean of losses at or
    beyond the VaR threshold.

    The engine:
    1. Accepts a list of portfolio P&Ls (one per historical scenario).
    2. Accepts a matched HistoricalVaR result (defines the VaR threshold).
    3. Sorts P&Ls ascending (worst loss first).
    4. Identifies tail P&Ls at or beyond the VaR quantile.
    5. Computes mean of tail P&Ls.
    6. Reports the loss as a positive magnitude.

    Key properties:
    - ES >= VaR (always, by definition: conditional mean >= quantile)
    - Tail includes the VaR observation (tail = sorted_pnls[: quantile_index + 1])
    - num_tail_observations indicates tail sample size

    Invariant (all methods):

    Expected Shortfall must be greater than or equal to the matching VaR result
    when both are calculated on the same portfolio, horizon, confidence level,
    distribution, and sign convention. This holds for all ES methods:

    - Historical ES >= Historical VaR (this implementation)
    - Parametric normal ES >= Parametric normal VaR (future)
    - Parametric Student-t ES >= Parametric Student-t VaR (future, if implemented)
    - Variance-covariance ES >= Variance-covariance VaR (future, if implemented)

    When implementing new ES methods, include a consistency test against
    the matching VaR method to validate this invariant.

    Example:
        >>> portfolio = RiskReadyPortfolio(...)
        >>> pnls = [ScenarioPnL(scenario_date=date(2024,1,1), total_pnl=Decimal("-100")), ...]
        >>> var_result = HistoricalVaRResult(...)
        >>> input = HistoricalExpectedShortfallInput(
        ...     portfolio=portfolio,
        ...     scenario_pnls=pnls,
        ...     var_result=var_result
        ... )
        >>> engine = HistoricalExpectedShortfall()
        >>> result = engine.calculate(input)
        >>> print(result.es_pct_nav)  # e.g., Decimal("0.035")
        >>> assert result.es_value >= result.linked_var_value
    """

    def calculate(
        self, input: HistoricalExpectedShortfallInput
    ) -> HistoricalExpectedShortfallResult:
        """Calculate Historical ES from scenario P&Ls and matched VaR result.

        Parameters
        ----------
        input : HistoricalExpectedShortfallInput
            Portfolio, scenario P&Ls, and matched HistoricalVaR result.

        Returns
        -------
        HistoricalExpectedShortfallResult
            ES loss threshold, tail metrics, and VaR linkage.

        Raises
        ------
        ValueError
            If input validation fails (handled by Pydantic).
        """
        # Extract inputs
        portfolio = input.portfolio
        scenario_pnls = input.scenario_pnls
        var_result = input.var_result
        nav = portfolio.nav

        # Extract P&L values and sort ascending (worst loss first)
        pnl_values = [pnl.total_pnl for pnl in scenario_pnls]
        sorted_pnls = sorted(pnl_values)

        # Define tail: all P&Ls at or beyond the VaR quantile (including the VaR observation)
        quantile_index = var_result.quantile_index
        tail_pnls = sorted_pnls[: quantile_index + 1]
        num_tail_observations = len(tail_pnls)

        # Compute conditional mean of tail P&Ls
        tail_sum = sum(tail_pnls)
        tail_mean = tail_sum / Decimal(num_tail_observations)

        # Convert to loss magnitude (negative P&L → positive ES)
        # Note: tail_mean is typically negative (losses); convert to positive magnitude
        if tail_mean < Decimal("0"):
            es_value = abs(tail_mean)
        else:
            es_value = Decimal("0")

        # Compute ES as percentage of NAV
        es_pct_nav = es_value / nav

        # Construct result
        result = HistoricalExpectedShortfallResult(
            fund_id=portfolio.fund_id,
            valuation_date=date.fromisoformat(portfolio.valuation_date),
            confidence_level=var_result.confidence_level,
            horizon_days=var_result.horizon_days,
            es_value=es_value,
            es_pct_nav=es_pct_nav,
            num_tail_observations=num_tail_observations,
            num_observations=len(sorted_pnls),
            quantile_index=quantile_index,
            linked_var_value=var_result.var_value,
            linked_var_pct_nav=var_result.var_pct_nav,
        )

        return result
