"""Equity-like scenario P&L generator.

Generates fixed-portfolio scenario P&Ls from historical returns for equity-like instruments.
"""

from datetime import date
from decimal import Decimal

from manco_risk.risk.exceptions import (
    InvalidScenarioInputError,
    MissingHistoricalDataError,
    UnsupportedAssetClassError,
)
from manco_risk.risk.models.equity_scenario_pnl import (
    EquityScenarioPnLInput,
    EquityScenarioPnLResult,
)
from manco_risk.risk.models.scenario_pnl import ScenarioPnL


class EquityScenarioPnLGenerator:
    """Generate scenario P&Ls for fixed equity-like portfolios.

    Supported asset classes: EQUITY, ETF, LISTED_FUND, INDEX, CASH.

    For each supported non-cash position:
        position_pnl = market_value_base_ccy * historical_return

    Cash positions:
        cash_pnl = 0 (constant)

    Portfolio scenario P&L:
        portfolio_pnl = sum(position_pnl)

    Unsupported asset classes cause failure (strict policy).
    Missing return data causes failure (strict policy).
    """

    SUPPORTED_ASSET_CLASSES = {"EQUITY", "ETF", "LISTED_FUND", "INDEX", "CASH"}

    def generate(self, input: EquityScenarioPnLInput) -> EquityScenarioPnLResult:
        """Generate scenario P&Ls from portfolio and historical returns.

        Parameters
        ----------
        input : EquityScenarioPnLInput
            Portfolio and return data.

        Returns
        -------
        EquityScenarioPnLResult
            Scenario P&Ls ready for VaR engine.

        Raises
        ------
        UnsupportedAssetClassError
            If any position has unsupported asset class.
        MissingHistoricalDataError
            If any non-cash position lacks return data (strict policy).
        InvalidScenarioInputError
            If input validation fails.
        """
        portfolio = input.portfolio
        historical_returns = input.historical_returns

        # Validate asset classes and count positions
        num_cash = 0
        num_equity_like = 0
        for position in portfolio.positions:
            if position.asset_class == "CASH":
                # Check currency: base-currency cash is OK, foreign-currency is not
                if position.instrument_currency != portfolio.fund_base_currency:
                    raise UnsupportedAssetClassError(
                        position.asset_class,
                        position.isin,
                        "Foreign-currency cash not supported in Phase 1",
                    )
                num_cash += 1
            elif position.asset_class in self.SUPPORTED_ASSET_CLASSES:
                num_equity_like += 1
            else:
                raise UnsupportedAssetClassError(
                    position.asset_class,
                    position.isin,
                    f"Asset class not in supported list: {self.SUPPORTED_ASSET_CLASSES}",
                )

        # Validate that all non-cash positions have return data
        for position in portfolio.positions:
            if position.asset_class != "CASH":
                if position.isin not in historical_returns:
                    raise MissingHistoricalDataError(position.isin, "entire time series")

        # Determine all scenario dates (must be consistent across all non-cash positions)
        scenario_dates: set[date] | None = None
        for position in portfolio.positions:
            if position.asset_class != "CASH":
                dates_for_isin = set(historical_returns[position.isin].keys())
                if scenario_dates is None:
                    scenario_dates = dates_for_isin
                elif scenario_dates != dates_for_isin:
                    raise InvalidScenarioInputError(
                        f"Scenario dates mismatch: {position.isin} has different dates than other positions"
                    )

        if scenario_dates is None:
            # No non-cash positions; empty scenario list
            scenario_dates = set()

        # Sort scenario dates for deterministic order
        sorted_scenario_dates = sorted(scenario_dates)

        # Generate scenario P&Ls for each date
        scenario_pnls: list[ScenarioPnL] = []
        for scenario_date in sorted_scenario_dates:
            portfolio_pnl = Decimal("0")

            for position in portfolio.positions:
                if position.asset_class == "CASH":
                    # Cash has zero return in all scenarios
                    position_pnl = Decimal("0")
                else:
                    # Equity-like: market_value_base_ccy * return
                    try:
                        position_return = historical_returns[position.isin][scenario_date]
                    except KeyError:
                        raise MissingHistoricalDataError(position.isin, scenario_date.isoformat())

                    # Ensure return is Decimal
                    if not isinstance(position_return, Decimal):
                        position_return = Decimal(str(position_return))

                    position_pnl = position.market_value_base_ccy * position_return

                portfolio_pnl += position_pnl

            scenario_pnls.append(
                ScenarioPnL(
                    scenario_date=scenario_date,
                    total_pnl=portfolio_pnl,
                )
            )

        # Construct result
        result = EquityScenarioPnLResult(
            scenario_pnls=scenario_pnls,
            num_scenarios=len(scenario_pnls),
            num_cash_positions=num_cash,
            num_equity_like_positions=num_equity_like,
        )

        return result
