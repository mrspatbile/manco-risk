"""Historical equity stress engine.

Selects the worst scenario from a historical window of precomputed portfolio P&Ls.
No market data fetching, no revaluation, no shock rate calculation.
"""

from datetime import date
from decimal import Decimal

from manco_risk.risk.exceptions import UnsupportedAssetClassError
from manco_risk.risk.models.historical_stress_input import HistoricalStressInput
from manco_risk.risk.models.historical_stress_result import HistoricalStressResult


class HistoricalEquityStressEngine:
    """Pure historical equity stress engine.

    Selects the worst-case scenario from a historical window of precomputed
    portfolio-level P&Ls and reports it as a stress result.

    Does not:
    - Fetch market data
    - Calculate shock rates
    - Revalue historical holdings
    - Generate scenario P&Ls

    Selection rule:
    1. Validate portfolio asset classes (reuse forward stress validation)
    2. Find worst scenario: min(scenario_pnls, by total_pnl)
    3. Calculate loss percentage: max(0, -worst_pnl / current_nav)
    4. Return result with worst scenario metadata and window bounds

    Supported asset classes:
    - EQUITY
    - ETF
    - LISTED_FUND
    - INDEX
    - CASH (base-currency only)

    Unsupported asset classes cause failure (strict policy).
    Foreign-currency cash causes failure.
    """

    # Reuse asset class validation from forward stress engine
    SUPPORTED_ASSET_CLASSES = {"EQUITY", "ETF", "LISTED_FUND", "INDEX", "CASH"}

    def calculate(self, input: HistoricalStressInput) -> HistoricalStressResult:
        """Select worst scenario from historical window.

        Parameters
        ----------
        input : HistoricalStressInput
            Portfolio and precomputed scenario P&Ls.

        Returns
        -------
        HistoricalStressResult
            Worst scenario from window with metadata and loss percentage.

        Raises
        ------
        UnsupportedAssetClassError
            If any position has an unsupported asset class or if cash is
            in a foreign currency.
        """
        portfolio = input.portfolio
        scenario_pnls = input.scenario_pnls
        current_nav = portfolio.nav
        current_valuation_date = portfolio.valuation_date

        # Validate portfolio asset classes
        self._validate_portfolio_asset_classes(portfolio)

        # Find worst scenario: minimum total_pnl (most negative = worst loss)
        worst_scenario = min(scenario_pnls, key=lambda s: s.total_pnl)
        worst_scenario_pnl = worst_scenario.total_pnl

        # Extract scenario date from worst scenario
        # ScenarioPnL has optional scenario_date and scenario_id
        if worst_scenario.scenario_date is None:
            # If no scenario_date, use the valuation_date as fallback
            worst_scenario_date = date.fromisoformat(current_valuation_date)
        else:
            worst_scenario_date = worst_scenario.scenario_date

        # Calculate loss percentage
        loss_pct_nav = max(Decimal("0"), -worst_scenario_pnl / current_nav)

        # Construct result
        result = HistoricalStressResult(
            fund_id=portfolio.fund_id,
            valuation_date=date.fromisoformat(current_valuation_date),
            scenario_id=input.scenario_id,
            scenario_name=input.scenario_name,
            scenario_type=input.scenario_type,
            scenario_source=input.scenario_source,
            shock_type=input.shock_type,
            window_start_date=input.window_start_date,
            window_end_date=input.window_end_date,
            worst_scenario_date=worst_scenario_date,
            worst_scenario_pnl=worst_scenario_pnl,
            loss_pct_nav=loss_pct_nav,
            num_scenarios=len(scenario_pnls),
            description=input.description,
        )

        return result

    def _validate_portfolio_asset_classes(self, portfolio) -> None:
        """Validate that all positions have supported asset classes.

        Parameters
        ----------
        portfolio : RiskReadyPortfolio
            Portfolio to validate.

        Raises
        ------
        UnsupportedAssetClassError
            If any position has an unsupported asset class or
            if cash is in a foreign currency.
        """
        for position in portfolio.positions:
            asset_class = position.asset_class

            # Check if asset class is supported
            if asset_class not in self.SUPPORTED_ASSET_CLASSES:
                raise UnsupportedAssetClassError(
                    asset_class,
                    position.isin,
                    f"Asset class not in supported list: {self.SUPPORTED_ASSET_CLASSES}",
                )

            # For cash, validate it is base-currency only
            if asset_class == "CASH":
                if position.instrument_currency != portfolio.fund_base_currency:
                    raise UnsupportedAssetClassError(
                        asset_class,
                        position.isin,
                        f"Foreign-currency cash not supported in Phase 1 "
                        f"(found {position.instrument_currency}, expected {portfolio.fund_base_currency})",
                    )
