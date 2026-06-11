"""Equity-like stress testing engine.

Pure calculation of stressed portfolio values and P&L from deterministic
equity-like shocks. No scenario generation, no market data fetching, no persistence.
"""

from datetime import date
from decimal import Decimal

from manco_risk.risk.exceptions import UnsupportedAssetClassError
from manco_risk.risk.models.stress_portfolio_result import StressPortfolioResult
from manco_risk.risk.models.stress_position_result import StressPositionResult
from manco_risk.risk.models.stress_test_input import StressTestInput


class EquityStressEngine:
    """Pure stress testing engine for equity-like portfolios.

    Applies deterministic shocks to a fixed portfolio and calculates
    stressed values, P&L, and NAV impact.

    Supported asset classes:
    - EQUITY
    - ETF
    - LISTED_FUND
    - INDEX
    - CASH (base-currency only)

    Unsupported asset classes cause failure (strict policy).

    Shock formula (equity-like):
        stressed_value = current_market_value * (1 + shock_rate)
        position_pnl = stressed_value - current_market_value

    Cash treatment (base-currency only):
        stressed_value = current_market_value
        position_pnl = 0

    Portfolio aggregation:
        total_pnl = sum(position_pnl)
        stressed_nav = current_nav + total_pnl
        loss_pct_nav = max(0, -total_pnl / current_nav)

    Special cases:
    - All-cash portfolio is valid: returns zero total_pnl and zero loss_pct_nav.
    - Positive shock produces gain: total_pnl > 0, loss_pct_nav = 0.
    """

    SUPPORTED_ASSET_CLASSES = {"EQUITY", "ETF", "LISTED_FUND", "INDEX", "CASH"}

    def stress(self, input: StressTestInput) -> list[StressPortfolioResult]:
        """Apply stress scenarios to a portfolio.

        Parameters
        ----------
        input : StressTestInput
            Portfolio and stress scenarios to apply.

        Returns
        -------
        list[StressPortfolioResult]
            Stressed portfolio results, one per scenario, in order.

        Raises
        ------
        UnsupportedAssetClassError
            If any position has an unsupported asset class or if cash is
            in a foreign currency.
        """
        portfolio = input.portfolio
        scenarios = input.scenarios

        # Validate portfolio asset classes once
        self._validate_portfolio_asset_classes(portfolio)

        # Apply each scenario to the portfolio
        results = []
        for scenario in scenarios:
            result = self._apply_scenario(portfolio, scenario)
            results.append(result)

        return results

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

    def _apply_scenario(self, portfolio, scenario) -> StressPortfolioResult:
        """Apply a single scenario to a portfolio.

        Parameters
        ----------
        portfolio : RiskReadyPortfolio
            Portfolio to stress.
        scenario : StressScenario
            Scenario to apply.

        Returns
        -------
        StressPortfolioResult
            Stressed portfolio result.
        """
        shock_rate = scenario.shock_rate
        current_nav = portfolio.nav
        current_valuation_date = portfolio.valuation_date

        # Calculate stressed position results
        stressed_positions: list[StressPositionResult] = []
        total_pnl = Decimal("0")
        num_cash = 0

        for position in portfolio.positions:
            current_value = position.market_value_base_ccy

            if position.asset_class == "CASH":
                # Cash unchanged
                stressed_value = current_value
                position_pnl = Decimal("0")
                num_cash += 1
            else:
                # Equity-like: apply shock
                stressed_value = current_value * (Decimal("1") + shock_rate)
                position_pnl = stressed_value - current_value

            # Accumulate portfolio P&L
            total_pnl += position_pnl

            # Create position result
            stressed_position = StressPositionResult(
                position_id=position.position_id,
                isin=position.isin,
                position_name=None,  # Not available in enriched position
                asset_class=position.asset_class,
                shock_type=scenario.shock_type,
                shock_rate=shock_rate,
                current_market_value_base_ccy=current_value,
                stressed_market_value_base_ccy=stressed_value,
                position_pnl=position_pnl,
            )
            stressed_positions.append(stressed_position)

        # Calculate stressed NAV and loss percentage
        stressed_nav = current_nav + total_pnl
        loss_pct_nav = max(Decimal("0"), -total_pnl / current_nav)

        # Create portfolio result
        result = StressPortfolioResult(
            fund_id=portfolio.fund_id,
            valuation_date=date.fromisoformat(current_valuation_date),
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.scenario_name,
            scenario_type=scenario.scenario_type,
            scenario_source=scenario.scenario_source,
            shock_type=scenario.shock_type,
            shock_rate=shock_rate,
            current_nav=current_nav,
            stressed_nav=stressed_nav,
            total_pnl=total_pnl,
            loss_pct_nav=loss_pct_nav,
            stressed_positions=stressed_positions,
            num_positions_stressed=len(stressed_positions) - num_cash,
            num_cash_positions=num_cash,
        )

        return result
