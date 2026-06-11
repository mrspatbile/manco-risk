"""Tests for CombinedStressEngine and combined stress models.

Covers:
- CombinedStressScenario model validation
- CombinedStressInput model validation
- CombinedStressPortfolioResult model validation
- CombinedStressEngine partitioning, dispatch, and aggregation

Portfolio partitioning:
    equity sub-portfolio  — EQUITY, ETF, LISTED_FUND, INDEX (no cash)
    FI sub-portfolio      — BOND only (no cash)
    cash positions        — excluded from both sub-engines; contribute zero P&L

Sub-engine dispatch:
    equity_scenario set AND equity positions exist → run EquityStressEngine → equity_result
    equity_scenario set AND no equity positions   → equity_result = None
    equity_scenario is None                       → skip equity engine
    fi_scenario set AND bond positions exist      → run FixedIncomeStressEngine → fi_result
    fi_scenario set AND no bond positions         → fi_result = None
    fi_scenario is None                           → skip FI engine

Aggregation:
    total_pnl    = equity_pnl + fi_pnl
    stressed_nav = current_nav + total_pnl
    loss_pct_nav = max(0, -total_pnl / current_nav)
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.engines.combined_stress import CombinedStressEngine
from manco_risk.risk.engines.duration_based_pricer import DurationBasedFixedIncomePricer
from manco_risk.risk.exceptions import UnsupportedAssetClassError
from manco_risk.risk.models.combined_stress_input import CombinedStressInput
from manco_risk.risk.models.combined_stress_scenario import CombinedStressScenario
from manco_risk.risk.models.fixed_income_stress_scenario import FixedIncomeStressScenario
from manco_risk.risk.models.stress_scenario import StressScenario

# ---------------------------------------------------------------------------
# Position helpers
# ---------------------------------------------------------------------------

BASE_CCY = "EUR"
FUND_ID = 1


def make_equity_position(
    position_id: int = 1,
    isin: str = "IE0031442068",
    market_value: Decimal = Decimal("100000"),
    asset_class: str = "EQUITY",
) -> EnrichedPosition:
    return EnrichedPosition(
        fund_id=FUND_ID,
        position_snapshot_id=1,
        position_id=position_id,
        isin=isin,
        valuation_date="2026-06-10",
        quantity=Decimal("1000"),
        market_value=market_value,
        position_currency=BASE_CCY,
        asset_class=asset_class,
        instrument_currency=BASE_CCY,
        market_value_base_ccy=market_value,
        fund_base_currency=BASE_CCY,
        weight=Decimal("0.4"),
    )


def make_bond_position(
    position_id: int = 2,
    isin: str = "US912828YK09",
    market_value: Decimal = Decimal("80000"),
    modified_duration: Decimal | None = Decimal("5.0"),
    spread_duration: Decimal | None = Decimal("5.0"),
) -> EnrichedPosition:
    return EnrichedPosition(
        fund_id=FUND_ID,
        position_snapshot_id=1,
        position_id=position_id,
        isin=isin,
        valuation_date="2026-06-10",
        quantity=Decimal("80"),
        market_value=market_value,
        position_currency=BASE_CCY,
        asset_class="BOND",
        instrument_currency=BASE_CCY,
        market_value_base_ccy=market_value,
        fund_base_currency=BASE_CCY,
        weight=Decimal("0.32"),
        modified_duration=modified_duration,
        spread_duration=spread_duration,
    )


def make_cash_position(
    position_id: int = 3,
    isin: str = "EUR_CASH",
    market_value: Decimal = Decimal("70000"),
    currency: str = BASE_CCY,
) -> EnrichedPosition:
    return EnrichedPosition(
        fund_id=FUND_ID,
        position_snapshot_id=1,
        position_id=position_id,
        isin=isin,
        valuation_date="2026-06-10",
        quantity=market_value,
        market_value=market_value,
        position_currency=currency,
        asset_class="CASH",
        instrument_currency=currency,
        market_value_base_ccy=market_value,
        fund_base_currency=BASE_CCY,
        weight=Decimal("0.28"),
    )


def make_portfolio(
    positions: list[EnrichedPosition],
    nav: Decimal = Decimal("250000"),
) -> RiskReadyPortfolio:
    return RiskReadyPortfolio(
        fund_id=FUND_ID,
        valuation_date="2026-06-10",
        fund_base_currency=BASE_CCY,
        nav=nav,
        positions=positions,
    )


# ---------------------------------------------------------------------------
# Scenario helpers
# ---------------------------------------------------------------------------


def make_equity_scenario(shock_rate: Decimal = Decimal("-0.20")) -> StressScenario:
    return StressScenario(
        scenario_id="EQ_DOWN_20",
        scenario_name="Equity down 20%",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="PARALLEL_EQUITY",
        shock_rate=shock_rate,
        description="Parallel 20% equity decline.",
    )


def make_fi_scenario(
    rate_shock_bps: int = 100,
    spread_shock_bps: int = 0,
) -> FixedIncomeStressScenario:
    return FixedIncomeStressScenario(
        scenario_id="FI_RATE_UP_100",
        scenario_name="Rates up 100bps",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="RATE_SHOCK",
        rate_shock_bps=rate_shock_bps,
        spread_shock_bps=spread_shock_bps,
        description="Parallel rate shock +100bps.",
    )


def make_combined_scenario(
    equity: StressScenario | None = None,
    fi: FixedIncomeStressScenario | None = None,
    scenario_id: str = "COMBINED_01",
) -> CombinedStressScenario:
    if equity is None and fi is None:
        equity = make_equity_scenario()
    return CombinedStressScenario(
        scenario_id=scenario_id,
        scenario_name="Combined stress scenario",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        description="Combined equity and FI stress.",
        equity_scenario=equity,
        fi_scenario=fi,
    )


def make_engine() -> CombinedStressEngine:
    return CombinedStressEngine(DurationBasedFixedIncomePricer())


# ===========================================================================
# CombinedStressScenario model validation
# ===========================================================================


class TestCombinedStressScenarioValidation:
    def test_both_none_raises(self) -> None:
        with pytest.raises(ValidationError, match="at least one"):
            CombinedStressScenario(
                scenario_id="X",
                scenario_name="X",
                scenario_type="HYPOTHETICAL",
                scenario_source="MANAGER_DEFINED",
                description="x",
                equity_scenario=None,
                fi_scenario=None,
            )

    def test_equity_only_is_valid(self) -> None:
        s = CombinedStressScenario(
            scenario_id="EQ_ONLY",
            scenario_name="Equity only",
            scenario_type="HYPOTHETICAL",
            scenario_source="MANAGER_DEFINED",
            description="Equity-only combined scenario.",
            equity_scenario=make_equity_scenario(),
            fi_scenario=None,
        )
        assert s.equity_scenario is not None
        assert s.fi_scenario is None

    def test_fi_only_is_valid(self) -> None:
        s = CombinedStressScenario(
            scenario_id="FI_ONLY",
            scenario_name="FI only",
            scenario_type="HYPOTHETICAL",
            scenario_source="MANAGER_DEFINED",
            description="FI-only combined scenario.",
            equity_scenario=None,
            fi_scenario=make_fi_scenario(),
        )
        assert s.equity_scenario is None
        assert s.fi_scenario is not None

    def test_both_provided_is_valid(self) -> None:
        s = make_combined_scenario(equity=make_equity_scenario(), fi=make_fi_scenario())
        assert s.equity_scenario is not None
        assert s.fi_scenario is not None

    def test_empty_scenario_id_raises(self) -> None:
        with pytest.raises(ValidationError, match="scenario_id"):
            CombinedStressScenario(
                scenario_id="  ",
                scenario_name="X",
                scenario_type="HYPOTHETICAL",
                scenario_source="MANAGER_DEFINED",
                description="x",
                equity_scenario=make_equity_scenario(),
            )


# ===========================================================================
# CombinedStressInput model validation
# ===========================================================================


class TestCombinedStressInputValidation:
    def test_empty_scenarios_raises(self) -> None:
        portfolio = make_portfolio([make_equity_position()])
        with pytest.raises(ValidationError, match="non-empty"):
            CombinedStressInput(portfolio=portfolio, scenarios=[])

    def test_valid_input(self) -> None:
        portfolio = make_portfolio([make_equity_position()])
        inp = CombinedStressInput(portfolio=portfolio, scenarios=[make_combined_scenario()])
        assert len(inp.scenarios) == 1


# ===========================================================================
# CombinedStressEngine — mixed portfolio (equity + bond + cash)
# ===========================================================================


class TestCombinedStressEngineMixedPortfolio:
    def test_combined_pnl_equals_equity_plus_fi(self) -> None:
        """Combined P&L = equity_pnl + fi_pnl; cash contributes zero."""
        eq_pos = make_equity_position(market_value=Decimal("100000"))
        bond_pos = make_bond_position(market_value=Decimal("80000"))
        cash_pos = make_cash_position(market_value=Decimal("70000"))
        nav = Decimal("250000")
        portfolio = make_portfolio([eq_pos, bond_pos, cash_pos], nav=nav)

        shock_rate = Decimal("-0.20")
        # equity P&L = -0.20 * 100000 = -20000
        # FI P&L: -5.0 * (100/10000) * 80000 = -5 * 0.01 * 80000 = -4000
        expected_eq_pnl = Decimal("-20000")
        expected_fi_pnl = Decimal("-4000.000000000000")
        expected_total = expected_eq_pnl + expected_fi_pnl

        combined_scenario = make_combined_scenario(
            equity=make_equity_scenario(shock_rate=shock_rate),
            fi=make_fi_scenario(rate_shock_bps=100, spread_shock_bps=0),
        )
        engine = make_engine()
        results = engine.stress(
            CombinedStressInput(portfolio=portfolio, scenarios=[combined_scenario])
        )

        assert len(results) == 1
        result = results[0]
        assert result.equity_result is not None
        assert result.fi_result is not None
        assert result.equity_result.total_pnl == pytest.approx(float(expected_eq_pnl), rel=1e-6)
        assert result.fi_result.total_pnl == pytest.approx(float(expected_fi_pnl), rel=1e-6)
        assert float(result.total_pnl) == pytest.approx(float(expected_total), rel=1e-6)

    def test_cash_contributes_zero_pnl(self) -> None:
        """Cash is excluded from sub-engines and contributes zero P&L."""
        cash_pos = make_cash_position(market_value=Decimal("70000"))
        bond_pos = make_bond_position(market_value=Decimal("80000"))
        nav = Decimal("250000")
        portfolio = make_portfolio([cash_pos, bond_pos], nav=nav)

        scenario = make_combined_scenario(fi=make_fi_scenario(rate_shock_bps=100))
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert result.num_cash_positions == 1
        assert result.cash_value_base_ccy == Decimal("70000")
        # total_pnl should equal FI P&L only (no equity scenario)
        assert result.equity_result is None
        assert result.fi_result is not None
        assert result.total_pnl == result.fi_result.total_pnl

    def test_cash_not_in_either_sub_result(self) -> None:
        """Sub-results contain only equity or bond position counts; cash absent."""
        eq_pos = make_equity_position()
        bond_pos = make_bond_position()
        cash_pos = make_cash_position()
        portfolio = make_portfolio([eq_pos, bond_pos, cash_pos])

        scenario = make_combined_scenario(equity=make_equity_scenario(), fi=make_fi_scenario())
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert result.equity_result is not None
        assert result.fi_result is not None
        # equity sub-result: num_cash_positions should be 0 (no cash sent)
        assert result.equity_result.num_cash_positions == 0
        # FI sub-result: num_cash_positions should be 0 (no cash sent)
        assert result.fi_result.num_cash_positions == 0
        # combined result tracks cash
        assert result.num_cash_positions == 1

    def test_stressed_nav_formula(self) -> None:
        eq_pos = make_equity_position(market_value=Decimal("100000"))
        bond_pos = make_bond_position(market_value=Decimal("80000"))
        nav = Decimal("200000")
        portfolio = make_portfolio([eq_pos, bond_pos], nav=nav)

        scenario = make_combined_scenario(
            equity=make_equity_scenario(shock_rate=Decimal("-0.10")),
            fi=make_fi_scenario(rate_shock_bps=50),
        )
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert float(result.stressed_nav) == pytest.approx(
            float(result.current_nav + result.total_pnl), rel=1e-9
        )

    def test_loss_pct_nav_formula(self) -> None:
        eq_pos = make_equity_position(market_value=Decimal("100000"))
        nav = Decimal("200000")
        portfolio = make_portfolio([eq_pos], nav=nav)

        scenario = make_combined_scenario(equity=make_equity_scenario(shock_rate=Decimal("-0.30")))
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        expected = max(Decimal("0"), -result.total_pnl / result.current_nav)
        assert float(result.loss_pct_nav) == pytest.approx(float(expected), rel=1e-9)

    def test_gain_scenario_loss_pct_nav_is_zero(self) -> None:
        eq_pos = make_equity_position(market_value=Decimal("100000"))
        portfolio = make_portfolio([eq_pos], nav=Decimal("100000"))

        scenario = make_combined_scenario(equity=make_equity_scenario(shock_rate=Decimal("0.10")))
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert result.loss_pct_nav == Decimal("0")
        assert result.total_pnl > Decimal("0")


# ===========================================================================
# CombinedStressEngine — equity-only scenario
# ===========================================================================


class TestCombinedStressEngineEquityOnly:
    def test_fi_result_is_none(self) -> None:
        eq_pos = make_equity_position()
        bond_pos = make_bond_position()
        portfolio = make_portfolio([eq_pos, bond_pos])

        scenario = make_combined_scenario(equity=make_equity_scenario(), fi=None)
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert result.fi_result is None
        assert result.equity_result is not None

    def test_no_equity_positions_returns_none_equity_result(self) -> None:
        bond_pos = make_bond_position()
        portfolio = make_portfolio([bond_pos])

        scenario = make_combined_scenario(equity=make_equity_scenario(), fi=None)
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert result.equity_result is None
        assert result.fi_result is None
        assert result.total_pnl == Decimal("0")

    def test_all_cash_portfolio_equity_only_scenario_returns_zero(self) -> None:
        cash_pos = make_cash_position()
        portfolio = make_portfolio([cash_pos])

        scenario = make_combined_scenario(equity=make_equity_scenario(), fi=None)
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert result.equity_result is None
        assert result.fi_result is None
        assert result.total_pnl == Decimal("0")
        assert result.num_cash_positions == 1


# ===========================================================================
# CombinedStressEngine — FI-only scenario
# ===========================================================================


class TestCombinedStressEngineFIOnly:
    def test_equity_result_is_none(self) -> None:
        eq_pos = make_equity_position()
        bond_pos = make_bond_position()
        portfolio = make_portfolio([eq_pos, bond_pos])

        scenario = make_combined_scenario(equity=None, fi=make_fi_scenario())
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert result.equity_result is None
        assert result.fi_result is not None

    def test_no_bond_positions_returns_none_fi_result(self) -> None:
        eq_pos = make_equity_position()
        portfolio = make_portfolio([eq_pos])

        scenario = make_combined_scenario(equity=None, fi=make_fi_scenario())
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert result.fi_result is None
        assert result.equity_result is None
        assert result.total_pnl == Decimal("0")

    def test_all_cash_portfolio_fi_only_scenario_returns_zero(self) -> None:
        cash_pos = make_cash_position()
        portfolio = make_portfolio([cash_pos])

        scenario = make_combined_scenario(equity=None, fi=make_fi_scenario())
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert result.equity_result is None
        assert result.fi_result is None
        assert result.total_pnl == Decimal("0")
        assert result.num_cash_positions == 1


# ===========================================================================
# CombinedStressEngine — all-cash portfolio
# ===========================================================================


class TestCombinedStressEngineAllCash:
    def test_combined_scenario_returns_zero_pnl(self) -> None:
        cash_pos = make_cash_position()
        portfolio = make_portfolio([cash_pos])

        scenario = make_combined_scenario(equity=make_equity_scenario(), fi=make_fi_scenario())
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert result.total_pnl == Decimal("0")
        assert result.equity_result is None
        assert result.fi_result is None
        assert result.num_cash_positions == 1


# ===========================================================================
# CombinedStressEngine — all-equity portfolio
# ===========================================================================


class TestCombinedStressEngineAllEquity:
    def test_fi_only_scenario_returns_zero_pnl(self) -> None:
        eq_pos = make_equity_position()
        portfolio = make_portfolio([eq_pos])

        scenario = make_combined_scenario(equity=None, fi=make_fi_scenario())
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert result.fi_result is None
        assert result.total_pnl == Decimal("0")


# ===========================================================================
# CombinedStressEngine — all-bond portfolio
# ===========================================================================


class TestCombinedStressEngineAllBond:
    def test_equity_only_scenario_returns_zero_pnl(self) -> None:
        bond_pos = make_bond_position()
        portfolio = make_portfolio([bond_pos])

        scenario = make_combined_scenario(equity=make_equity_scenario(), fi=None)
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert result.equity_result is None
        assert result.total_pnl == Decimal("0")


# ===========================================================================
# CombinedStressEngine — error cases
# ===========================================================================


class TestCombinedStressEngineErrors:
    def test_unsupported_asset_class_raises(self) -> None:
        unknown_pos = EnrichedPosition(
            fund_id=FUND_ID,
            position_snapshot_id=1,
            position_id=99,
            isin="XX0000000000",
            valuation_date="2026-06-10",
            quantity=Decimal("1"),
            market_value=Decimal("10000"),
            position_currency=BASE_CCY,
            asset_class="DERIVATIVE",
            instrument_currency=BASE_CCY,
            market_value_base_ccy=Decimal("10000"),
            fund_base_currency=BASE_CCY,
            weight=Decimal("0.04"),
        )
        portfolio = make_portfolio([unknown_pos])
        scenario = make_combined_scenario(equity=make_equity_scenario())
        engine = make_engine()

        with pytest.raises(UnsupportedAssetClassError, match="DERIVATIVE"):
            engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))

    def test_foreign_currency_cash_raises(self) -> None:
        foreign_cash = make_cash_position(currency="USD")
        portfolio = make_portfolio([foreign_cash])
        scenario = make_combined_scenario(equity=make_equity_scenario())
        engine = make_engine()

        with pytest.raises(UnsupportedAssetClassError, match="CASH"):
            engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))


# ===========================================================================
# CombinedStressEngine — multiple scenarios
# ===========================================================================


class TestCombinedStressEngineMultipleScenarios:
    def test_results_in_input_order(self) -> None:
        eq_pos = make_equity_position()
        portfolio = make_portfolio([eq_pos])

        s1 = make_combined_scenario(
            equity=make_equity_scenario(shock_rate=Decimal("-0.10")),
            scenario_id="SCENARIO_A",
        )
        s2 = make_combined_scenario(
            equity=make_equity_scenario(shock_rate=Decimal("-0.30")),
            scenario_id="SCENARIO_B",
        )
        engine = make_engine()
        results = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[s1, s2]))

        assert len(results) == 2
        assert results[0].scenario_id == "SCENARIO_A"
        assert results[1].scenario_id == "SCENARIO_B"
        # Larger shock produces larger loss
        assert results[1].loss_pct_nav > results[0].loss_pct_nav

    def test_result_count_equals_scenario_count(self) -> None:
        eq_pos = make_equity_position()
        portfolio = make_portfolio([eq_pos])

        scenarios = [
            make_combined_scenario(
                equity=make_equity_scenario(shock_rate=Decimal(f"-0.{i}0")),
                scenario_id=f"SC_{i}",
            )
            for i in range(1, 5)
        ]
        engine = make_engine()
        results = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=scenarios))
        assert len(results) == 4


# ===========================================================================
# ETF, LISTED_FUND, INDEX asset classes routed to equity sub-engine
# ===========================================================================


class TestCombinedStressEngineEquityLikeClasses:
    @pytest.mark.parametrize("asset_class", ["ETF", "LISTED_FUND", "INDEX"])
    def test_equity_like_asset_class_routed_to_equity(self, asset_class: str) -> None:
        pos = make_equity_position(asset_class=asset_class)
        portfolio = make_portfolio([pos])

        scenario = make_combined_scenario(equity=make_equity_scenario(Decimal("-0.20")))
        engine = make_engine()
        result = engine.stress(CombinedStressInput(portfolio=portfolio, scenarios=[scenario]))[0]

        assert result.equity_result is not None
        assert result.fi_result is None
        # P&L = -0.20 * 100000 = -20000
        assert float(result.total_pnl) == pytest.approx(-20000.0, rel=1e-6)
