"""Pure VaR backtesting engine for alignment and regulatory counting.

Aligns time series of VaR forecasts with realised P&L observations,
detects breaches, and computes explicit regulatory counts.

Phase 1: alignment and counting only. No statistical tests.
"""

from datetime import date
from decimal import Decimal

from manco_risk.risk.models.backtest_input import (
    BacktestInput,
)
from manco_risk.risk.models.backtest_result import BacktestObservation, BacktestResult


class VaRBacktestingEngine:
    """Pure VaR backtesting engine.

    Given a time series of VaR forecasts and realised P&L observations,
    aligns them by date, detects breaches, and computes regulatory counts.

    Example:
        >>> var_forecasts = [
        ...     VaRForecastObservation(
        ...         forecast_date=date(2024, 1, 1),
        ...         var_value=Decimal("0.025"),
        ...         confidence_level=Decimal("0.95"),
        ...         horizon_days=1,
        ...     ),
        ... ]
        >>> pnls = [
        ...     RealisedPnLObservation(
        ...         pnl_date=date(2024, 1, 1),
        ...         realised_pnl=Decimal("-0.010"),
        ...     ),
        ... ]
        >>> input = BacktestInput(
        ...     var_forecasts=var_forecasts,
        ...     realised_pnls=pnls,
        ...     confidence_level=Decimal("0.95"),
        ...     horizon_days=1,
        ... )
        >>> engine = VaRBacktestingEngine()
        >>> result = engine.calculate(input)
        >>> print(result.num_breaches)  # 0 (not breached: -0.010 >= -0.025)
    """

    def calculate(self, input: BacktestInput) -> BacktestResult:
        """Calculate backtesting counts from aligned VaR and P&L observations.

        Parameters
        ----------
        input : BacktestInput
            VaR forecasts, realised P&Ls, and test parameters.

        Returns
        -------
        BacktestResult
            Regulatory counts and diagnostics (alignment, breaches, missing dates).

        Raises
        ------
        ValueError
            If input validation fails (handled by Pydantic).
        """
        # Extract and count input observations
        var_forecasts = input.var_forecasts
        realised_pnls = input.realised_pnls
        num_var_forecasts = len(var_forecasts)
        num_pnl_observations = len(realised_pnls)

        # Build lookup dictionaries for O(1) alignment
        var_by_date = {obs.forecast_date: obs for obs in var_forecasts}
        pnl_by_date = {obs.pnl_date: obs for obs in realised_pnls}

        # Collect all dates from both series
        var_dates_set = set(var_by_date.keys())
        pnl_dates_set = set(pnl_by_date.keys())

        # Identify aligned, missing, and unmatched dates
        aligned_dates = sorted(var_dates_set & pnl_dates_set)
        missing_var_dates = sorted(pnl_dates_set - var_dates_set)
        missing_pnl_dates = sorted(var_dates_set - pnl_dates_set)

        num_valid_aligned = len(aligned_dates)

        # Build aligned observations and detect breaches
        aligned_observations: list[BacktestObservation] = []
        breach_dates: list[date] = []
        num_breaches = 0

        for obs_date in aligned_dates:
            var_obs = var_by_date[obs_date]
            pnl_obs = pnl_by_date[obs_date]

            var_value = var_obs.var_value
            realised_pnl = pnl_obs.realised_pnl

            # Breach condition: realised_pnl < -var_value (strict inequality)
            is_breach = realised_pnl < -var_value

            aligned_obs = BacktestObservation(
                observation_date=obs_date,
                var_value=var_value,
                realised_pnl=realised_pnl,
                is_breach=is_breach,
            )
            aligned_observations.append(aligned_obs)

            if is_breach:
                num_breaches += 1
                breach_dates.append(obs_date)

        # Calculate counts and ratios
        num_non_breaches = num_valid_aligned - num_breaches
        expected_breach_probability = Decimal("1") - input.confidence_level
        expected_breach_count = Decimal(num_valid_aligned) * expected_breach_probability

        # Calculate breach ratio (handle empty case)
        breach_ratio: Decimal | None = None
        if num_valid_aligned > 0:
            breach_ratio = Decimal(num_breaches) / Decimal(num_valid_aligned)

        # Determine backtest date range (from aligned observations)
        backtest_start_date: date | None = None
        backtest_end_date: date | None = None
        if aligned_dates:
            backtest_start_date = aligned_dates[0]
            backtest_end_date = aligned_dates[-1]

        # Construct result
        result = BacktestResult(
            num_var_forecasts=num_var_forecasts,
            num_pnl_observations=num_pnl_observations,
            num_valid_aligned=num_valid_aligned,
            num_breaches=num_breaches,
            num_non_breaches=num_non_breaches,
            expected_breach_probability=expected_breach_probability,
            expected_breach_count=expected_breach_count,
            breach_ratio=breach_ratio,
            backtest_start_date=backtest_start_date,
            backtest_end_date=backtest_end_date,
            breach_dates=breach_dates,
            missing_var_dates=missing_var_dates,
            missing_pnl_dates=missing_pnl_dates,
            aligned_observations=aligned_observations,
        )

        return result
