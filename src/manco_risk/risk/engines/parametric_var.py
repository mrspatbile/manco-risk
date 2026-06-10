"""Parametric normal VaR calculation engine.

Pure portfolio-return based parametric VaR assuming normal distribution.
No scenario generation, no market data fetching, no persistence.
"""

import statistics
from datetime import date
from decimal import Decimal

from manco_risk.risk.models.parametric_var_input import ParametricNormalVaRInput
from manco_risk.risk.models.parametric_var_result import ParametricNormalVaRResult


class ParametricNormalVaR:
    """Parametric normal VaR engine for equity-like portfolios.

    Given a portfolio and a series of scenario P&Ls, converts P&Ls to returns,
    computes mean and standard deviation, and applies normal distribution quantile
    to estimate Value-at-Risk.

    Workflow:
    1. Convert scenario P&Ls to portfolio returns: return_i = pnl_i / nav
    2. Compute arithmetic mean return
    3. Compute sample standard deviation (n - 1)
    4. Calculate left-tail z-score: z = NormalDist().inv_cdf(1 - confidence_level)
    5. Estimate parametric return: parametric_return = mean + z * std_dev
    6. Report as positive loss magnitude if negative, else zero

    Example:
        >>> portfolio = RiskReadyPortfolio(...)
        >>> pnls = [ScenarioPnL(scenario_date=date(2024,1,1), total_pnl=Decimal("-100")), ...]
        >>> input = ParametricNormalVaRInput(
        ...     portfolio=portfolio,
        ...     confidence_level=Decimal("0.95"),
        ...     horizon_days=1,
        ...     scenario_pnls=pnls
        ... )
        >>> engine = ParametricNormalVaR()
        >>> result = engine.calculate(input)
        >>> print(result.var_pct_nav)  # e.g., Decimal("0.025")
    """

    def calculate(self, input: ParametricNormalVaRInput) -> ParametricNormalVaRResult:
        """Calculate parametric normal VaR from scenario P&Ls.

        Parameters
        ----------
        input : ParametricNormalVaRInput
            Portfolio, confidence level, horizon, and scenario P&Ls.

        Returns
        -------
        ParametricNormalVaRResult
            VaR loss threshold, distributional parameters, and metadata.

        Raises
        ------
        ValueError
            If input validation fails (handled by Pydantic).
        ZeroDivisionError
            If NAV is zero (should not occur; validated by RiskReadyPortfolio).
        """
        # Extract inputs
        portfolio = input.portfolio
        confidence_level = input.confidence_level
        scenario_pnls = input.scenario_pnls
        nav = portfolio.nav

        # Convert scenario P&Ls to portfolio returns
        portfolio_returns = [Decimal(str(pnl.total_pnl / nav)) for pnl in scenario_pnls]

        # Calculate arithmetic mean return
        mean_return = Decimal(str(sum(portfolio_returns) / len(portfolio_returns)))

        # Calculate sample standard deviation using n - 1
        n = len(portfolio_returns)
        if n < 2:
            raise ValueError(f"Cannot compute std dev with {n} observations")

        # Variance: sum of squared deviations / (n - 1)
        squared_deviations = [(r - mean_return) ** Decimal("2") for r in portfolio_returns]
        variance = sum(squared_deviations) / Decimal(n - 1)

        # Standard deviation: sqrt(variance)
        # Use Decimal for precision
        std_dev_decimal = variance.sqrt()

        # Get left-tail z-score using statistics.NormalDist
        # For confidence_level = 0.95, we want the 5th percentile (left tail)
        # which is inv_cdf(1 - 0.95) = inv_cdf(0.05) ≈ -1.645
        confidence_float = float(confidence_level)
        tail_prob = 1.0 - confidence_float
        z_score_float = statistics.NormalDist().inv_cdf(tail_prob)
        z_score = Decimal(str(z_score_float))

        # Calculate parametric return
        parametric_return = mean_return + z_score * std_dev_decimal

        # Convert to loss magnitude
        if parametric_return < Decimal("0"):
            var_pct_nav = abs(parametric_return)
        else:
            var_pct_nav = Decimal("0")

        # Compute VaR in base currency
        var_value = var_pct_nav * nav

        # Construct result
        result = ParametricNormalVaRResult(
            fund_id=portfolio.fund_id,
            valuation_date=date.fromisoformat(portfolio.valuation_date),
            confidence_level=confidence_level,
            horizon_days=input.horizon_days,
            var_value=var_value,
            var_pct_nav=var_pct_nav,
            mean_return=mean_return,
            std_dev=std_dev_decimal,
            num_observations=n,
            z_score=z_score,
        )

        return result
