"""Portfolio-level fixed-income stress engine.

Orchestrates position-level pricing across a portfolio for one or more
fixed-income stress scenarios. The engine handles portfolio validation,
CASH pass-through, BOND delegation to the pricer, and P&L aggregation.

The engine contains no pricing formulas. All bond P&L computation is
delegated to the injected FixedIncomeStressPricer. Swapping to a future
QuantLibFixedIncomePricer requires only a different constructor argument:

    engine = FixedIncomeStressEngine(QuantLibFixedIncomePricer(...))

Supported asset classes:
    BOND  — delegated to the pricer
    CASH  — base-currency only; passed through unchanged (zero P&L)

Unsupported asset classes (EQUITY, ETF, INDEX, etc.) and foreign-currency
CASH raise UnsupportedAssetClassError immediately at portfolio validation.

Missing duration analytics (e.g., modified_duration is None) are surfaced
as MissingDurationError by the pricer, not by this engine.

Aggregation formulas:
    total_rate_pnl   = sum(position.rate_pnl)
    total_credit_pnl = sum(position.credit_pnl)
    total_pnl        = total_rate_pnl + total_credit_pnl
    stressed_nav     = current_nav + total_pnl
    loss_pct_nav     = max(0, -total_pnl / current_nav)
"""

from datetime import date
from decimal import Decimal

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.engines.fixed_income_pricer import FixedIncomeStressPricer
from manco_risk.risk.exceptions import UnsupportedAssetClassError
from manco_risk.risk.models.fixed_income_stress_input import FixedIncomeStressInput
from manco_risk.risk.models.fixed_income_stress_portfolio_result import (
    FixedIncomeStressPortfolioResult,
)
from manco_risk.risk.models.fixed_income_stress_position_result import (
    FixedIncomeStressPositionResult,
)
from manco_risk.risk.models.fixed_income_stress_scenario import FixedIncomeStressScenario


class FixedIncomeStressEngine:
    """Portfolio-level orchestrator for fixed-income stress testing.

    Applies one or more fixed-income stress scenarios to a portfolio,
    delegating all bond pricing to the injected pricer.

    Parameters
    ----------
    pricer : FixedIncomeStressPricer
        Pricer implementing position-level fixed-income P&L calculation.
        Use DurationBasedFixedIncomePricer for Phase 1 duration approximation.
        Future: QuantLibFixedIncomePricer for full cashflow repricing.
    """

    SUPPORTED_ASSET_CLASSES = frozenset({"BOND", "CASH"})

    def __init__(self, pricer: FixedIncomeStressPricer) -> None:
        self._pricer = pricer

    def stress(self, input: FixedIncomeStressInput) -> list[FixedIncomeStressPortfolioResult]:
        """Apply all scenarios to the portfolio.

        Parameters
        ----------
        input : FixedIncomeStressInput
            Portfolio and list of scenarios to apply.

        Returns
        -------
        list[FixedIncomeStressPortfolioResult]
            One result per scenario, in input order.

        Raises
        ------
        UnsupportedAssetClassError
            If any position has an unsupported asset class or if CASH is
            in a foreign currency.
        MissingDurationError
            Propagated from the pricer when a non-zero shock component
            requires a duration field that is None on a bond position.
        """
        portfolio = input.portfolio

        # Validate portfolio asset classes once before any scenario runs
        self._validate_portfolio(portfolio)

        return [self._apply_scenario(portfolio, scenario) for scenario in input.scenarios]

    def _validate_portfolio(self, portfolio: RiskReadyPortfolio) -> None:
        """Validate that all positions can be handled by this engine.

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
                    reason=f"not in supported set {set(self.SUPPORTED_ASSET_CLASSES)}",
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
        scenario: FixedIncomeStressScenario,
    ) -> FixedIncomeStressPortfolioResult:
        """Apply a single scenario to the portfolio.

        Parameters
        ----------
        portfolio : RiskReadyPortfolio
            Validated portfolio.
        scenario : FixedIncomeStressScenario
            Scenario to apply.

        Returns
        -------
        FixedIncomeStressPortfolioResult
            Aggregated result including position-level detail.
        """
        stressed_positions: list[FixedIncomeStressPositionResult] = []
        num_bond = 0
        num_cash = 0

        for position in portfolio.positions:
            if position.asset_class == "CASH":
                pos_result = self._price_cash_position(position, scenario)
                num_cash += 1
            else:
                pos_result = self._pricer.price_position(position, scenario)
                num_bond += 1
            stressed_positions.append(pos_result)

        total_rate_pnl = sum((p.rate_pnl for p in stressed_positions), Decimal("0"))
        total_credit_pnl = sum((p.credit_pnl for p in stressed_positions), Decimal("0"))
        total_pnl = total_rate_pnl + total_credit_pnl

        current_nav = portfolio.nav
        stressed_nav = current_nav + total_pnl
        loss_pct_nav = max(Decimal("0"), -total_pnl / current_nav)

        return FixedIncomeStressPortfolioResult(
            fund_id=portfolio.fund_id,
            valuation_date=date.fromisoformat(portfolio.valuation_date),
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.scenario_name,
            scenario_type=scenario.scenario_type,
            scenario_source=scenario.scenario_source,
            shock_type=scenario.shock_type,
            rate_shock_bps=scenario.rate_shock_bps,
            spread_shock_bps=scenario.spread_shock_bps,
            current_nav=current_nav,
            stressed_nav=stressed_nav,
            total_rate_pnl=total_rate_pnl,
            total_credit_pnl=total_credit_pnl,
            total_pnl=total_pnl,
            loss_pct_nav=loss_pct_nav,
            stressed_positions=stressed_positions,
            num_bond_positions=num_bond,
            num_cash_positions=num_cash,
        )

    @staticmethod
    def _price_cash_position(
        position: EnrichedPosition,
        scenario: FixedIncomeStressScenario,
    ) -> FixedIncomeStressPositionResult:
        """Return a zero-P&L result for a base-currency cash position.

        Cash positions are not affected by rate or spread shocks.
        """
        current_value = position.market_value_base_ccy
        return FixedIncomeStressPositionResult(
            position_id=position.position_id,
            isin=position.isin,
            position_name=None,
            asset_class=position.asset_class,
            shock_type=scenario.shock_type,
            rate_shock_bps=scenario.rate_shock_bps,
            spread_shock_bps=scenario.spread_shock_bps,
            modified_duration=None,
            spread_duration=None,
            current_dirty_value_base_ccy=current_value,
            stressed_dirty_value_base_ccy=current_value,
            rate_pnl=Decimal("0"),
            credit_pnl=Decimal("0"),
            total_pnl=Decimal("0"),
        )
