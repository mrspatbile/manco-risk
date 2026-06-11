"""Combined multi-asset stress testing engine.

Orchestrates EquityStressEngine and FixedIncomeStressEngine over a mixed portfolio
for one or more combined stress scenarios. Each sub-engine receives only the
positions it supports; cash is handled once at combined level with zero P&L.

Portfolio partitioning:
    equity_positions  — EQUITY, ETF, LISTED_FUND, INDEX (no cash)
    fi_positions      — BOND only (no cash)
    cash_positions    — CASH (base-currency only); contribute zero P&L

Sub-engine dispatch rules (per scenario):
    equity_scenario set AND equity positions exist → run EquityStressEngine
    equity_scenario set AND no equity positions   → equity_result = None
    equity_scenario is None                       → skip equity engine
    fi_scenario set AND bond positions exist      → run FixedIncomeStressEngine
    fi_scenario set AND no bond positions         → fi_result = None
    fi_scenario is None                           → skip FI engine

Aggregation:
    equity_pnl   = equity_result.total_pnl if equity_result else Decimal("0")
    fi_pnl       = fi_result.total_pnl     if fi_result     else Decimal("0")
    total_pnl    = equity_pnl + fi_pnl
    stressed_nav = current_nav + total_pnl
    loss_pct_nav = max(0, -total_pnl / current_nav)

Unsupported asset classes and foreign-currency cash raise UnsupportedAssetClassError.
"""

from decimal import Decimal

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.engines.equity_stress import EquityStressEngine
from manco_risk.risk.engines.fixed_income_pricer import FixedIncomeStressPricer
from manco_risk.risk.engines.fixed_income_stress import FixedIncomeStressEngine
from manco_risk.risk.exceptions import UnsupportedAssetClassError
from manco_risk.risk.models.combined_stress_input import CombinedStressInput
from manco_risk.risk.models.combined_stress_portfolio_result import (
    CombinedStressPortfolioResult,
)
from manco_risk.risk.models.combined_stress_scenario import CombinedStressScenario
from manco_risk.risk.models.fixed_income_stress_input import FixedIncomeStressInput
from manco_risk.risk.models.fixed_income_stress_portfolio_result import (
    FixedIncomeStressPortfolioResult,
)
from manco_risk.risk.models.stress_portfolio_result import StressPortfolioResult
from manco_risk.risk.models.stress_test_input import StressTestInput


class CombinedStressEngine:
    """Combined multi-asset stress testing orchestrator.

    Routes positions to EquityStressEngine and FixedIncomeStressEngine based on
    asset class. Cash is excluded from both sub-engines and treated as zero P&L
    at combined level.

    Parameters
    ----------
    fi_pricer : FixedIncomeStressPricer
        Pricer for fixed-income position-level P&L. Use DurationBasedFixedIncomePricer
        for Phase 1 duration approximation.
    """

    EQUITY_LIKE_CLASSES: frozenset[str] = frozenset({"EQUITY", "ETF", "LISTED_FUND", "INDEX"})
    FI_CLASSES: frozenset[str] = frozenset({"BOND"})
    SUPPORTED_ASSET_CLASSES: frozenset[str] = EQUITY_LIKE_CLASSES | FI_CLASSES | {"CASH"}

    def __init__(self, fi_pricer: FixedIncomeStressPricer) -> None:
        self._equity_engine = EquityStressEngine()
        self._fi_engine = FixedIncomeStressEngine(fi_pricer)

    def stress(self, input: CombinedStressInput) -> list[CombinedStressPortfolioResult]:
        """Apply combined stress scenarios to a mixed-asset portfolio.

        Parameters
        ----------
        input : CombinedStressInput
            Portfolio and list of combined stress scenarios.

        Returns
        -------
        list[CombinedStressPortfolioResult]
            One result per scenario, in input order.

        Raises
        ------
        UnsupportedAssetClassError
            If any position has an unsupported asset class or if CASH is in
            a foreign currency.
        MissingDurationError
            Propagated from the FI pricer when a non-zero shock component
            requires a duration field that is None on a bond position.
        """
        self._validate_portfolio(input.portfolio)
        return [self._apply_scenario(input.portfolio, s) for s in input.scenarios]

    def _validate_portfolio(self, portfolio: RiskReadyPortfolio) -> None:
        """Validate that all positions are in a supported asset class.

        Parameters
        ----------
        portfolio : RiskReadyPortfolio
            Portfolio to validate.

        Raises
        ------
        UnsupportedAssetClassError
            On first unsupported asset class or foreign-currency CASH.
        """
        for position in portfolio.positions:
            if position.asset_class not in self.SUPPORTED_ASSET_CLASSES:
                raise UnsupportedAssetClassError(
                    asset_class=position.asset_class,
                    isin=position.isin,
                    reason=f"not in combined engine supported set {set(self.SUPPORTED_ASSET_CLASSES)}",
                )
            if position.asset_class == "CASH":
                if position.instrument_currency != portfolio.fund_base_currency:
                    raise UnsupportedAssetClassError(
                        asset_class="CASH",
                        isin=position.isin,
                        reason=(
                            f"foreign-currency cash not supported "
                            f"(found {position.instrument_currency}, "
                            f"expected {portfolio.fund_base_currency})"
                        ),
                    )

    def _apply_scenario(
        self,
        portfolio: RiskReadyPortfolio,
        scenario: CombinedStressScenario,
    ) -> CombinedStressPortfolioResult:
        """Apply one combined scenario to the portfolio.

        Parameters
        ----------
        portfolio : RiskReadyPortfolio
            Validated portfolio.
        scenario : CombinedStressScenario
            Combined scenario to apply.

        Returns
        -------
        CombinedStressPortfolioResult
            Aggregated result including optional sub-results and combined P&L.
        """
        equity_positions, fi_positions, cash_positions = self._partition(portfolio)

        equity_result: StressPortfolioResult | None = None
        fi_result: FixedIncomeStressPortfolioResult | None = None

        if scenario.equity_scenario is not None and equity_positions:
            equity_portfolio = RiskReadyPortfolio(
                fund_id=portfolio.fund_id,
                valuation_date=portfolio.valuation_date,
                fund_base_currency=portfolio.fund_base_currency,
                nav=portfolio.nav,
                positions=equity_positions,
            )
            equity_result = self._equity_engine.stress(
                StressTestInput(
                    portfolio=equity_portfolio,
                    scenarios=[scenario.equity_scenario],
                )
            )[0]

        if scenario.fi_scenario is not None and fi_positions:
            fi_portfolio = RiskReadyPortfolio(
                fund_id=portfolio.fund_id,
                valuation_date=portfolio.valuation_date,
                fund_base_currency=portfolio.fund_base_currency,
                nav=portfolio.nav,
                positions=fi_positions,
            )
            fi_result = self._fi_engine.stress(
                FixedIncomeStressInput(
                    portfolio=fi_portfolio,
                    scenarios=[scenario.fi_scenario],
                )
            )[0]

        return self._aggregate(portfolio, scenario, equity_result, fi_result, cash_positions)

    def _partition(
        self, portfolio: RiskReadyPortfolio
    ) -> tuple[list[EnrichedPosition], list[EnrichedPosition], list[EnrichedPosition]]:
        """Partition positions into equity, FI, and cash groups.

        Parameters
        ----------
        portfolio : RiskReadyPortfolio
            Portfolio to partition.

        Returns
        -------
        tuple[list, list, list]
            (equity_positions, fi_positions, cash_positions)
        """
        equity: list[EnrichedPosition] = []
        fi: list[EnrichedPosition] = []
        cash: list[EnrichedPosition] = []

        for position in portfolio.positions:
            if position.asset_class in self.EQUITY_LIKE_CLASSES:
                equity.append(position)
            elif position.asset_class in self.FI_CLASSES:
                fi.append(position)
            else:
                cash.append(position)

        return equity, fi, cash

    def _aggregate(
        self,
        portfolio: RiskReadyPortfolio,
        scenario: CombinedStressScenario,
        equity_result: StressPortfolioResult | None,
        fi_result: FixedIncomeStressPortfolioResult | None,
        cash_positions: list[EnrichedPosition],
    ) -> CombinedStressPortfolioResult:
        """Aggregate sub-results into a combined portfolio result.

        Parameters
        ----------
        portfolio : RiskReadyPortfolio
            Original portfolio (NAV denominator source).
        scenario : CombinedStressScenario
            Scenario providing combined identity fields.
        equity_result : StressPortfolioResult | None
            Equity sub-result, or None.
        fi_result : FixedIncomeStressPortfolioResult | None
            FI sub-result, or None.
        cash_positions : list[EnrichedPosition]
            Cash positions excluded from sub-engines.

        Returns
        -------
        CombinedStressPortfolioResult
            Combined result.
        """
        current_nav = portfolio.nav
        equity_pnl = equity_result.total_pnl if equity_result is not None else Decimal("0")
        fi_pnl = fi_result.total_pnl if fi_result is not None else Decimal("0")
        total_pnl = equity_pnl + fi_pnl
        stressed_nav = current_nav + total_pnl
        loss_pct_nav = max(Decimal("0"), -total_pnl / current_nav)

        num_cash = len(cash_positions)
        cash_value = sum((p.market_value_base_ccy for p in cash_positions), Decimal("0"))

        from datetime import date

        valuation_date = date.fromisoformat(portfolio.valuation_date)

        return CombinedStressPortfolioResult(
            fund_id=portfolio.fund_id,
            valuation_date=valuation_date,
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.scenario_name,
            scenario_type=scenario.scenario_type,
            scenario_source=scenario.scenario_source,
            current_nav=current_nav,
            stressed_nav=stressed_nav,
            total_pnl=total_pnl,
            loss_pct_nav=loss_pct_nav,
            num_cash_positions=num_cash,
            cash_value_base_ccy=cash_value,
            equity_result=equity_result,
            fi_result=fi_result,
        )
