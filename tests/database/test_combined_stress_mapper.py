"""Tests for combined multi-asset stress mapper.

Maps CombinedStressPortfolioResult → StressTestResult ORM with asset_scope = MULTI_ASSET.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.database.models import (
    StressTestAssetScopeEnum,
    StressTestResultTypeEnum,
)
from manco_risk.database.stress_mappers import map_combined_stress_portfolio_result_to_orm
from manco_risk.risk.models.combined_stress_portfolio_result import CombinedStressPortfolioResult
from manco_risk.risk.models.fixed_income_stress_portfolio_result import (
    FixedIncomeStressPortfolioResult,
)
from manco_risk.risk.models.stress_portfolio_result import StressPortfolioResult


def make_equity_result(
    total_pnl: Decimal = Decimal("-20000"),
) -> StressPortfolioResult:
    current_nav = Decimal("250000")
    stressed_nav = current_nav + total_pnl
    loss_pct_nav = max(Decimal("0"), -total_pnl / current_nav)
    return StressPortfolioResult(
        fund_id=1,
        valuation_date=date(2026, 6, 10),
        scenario_id="EQ_DOWN_20",
        scenario_name="Equity down 20%",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="PARALLEL_EQUITY",
        shock_rate=Decimal("-0.20"),
        current_nav=current_nav,
        stressed_nav=stressed_nav,
        total_pnl=total_pnl,
        loss_pct_nav=loss_pct_nav,
        stressed_positions=[],
        num_positions_stressed=1,
        num_cash_positions=0,
    )


def make_fi_result(
    total_pnl: Decimal = Decimal("-4000"),
    total_rate_pnl: Decimal = Decimal("-4000"),
    total_credit_pnl: Decimal = Decimal("0"),
) -> FixedIncomeStressPortfolioResult:
    current_nav = Decimal("250000")
    stressed_nav = current_nav + total_pnl
    loss_pct_nav = max(Decimal("0"), -total_pnl / current_nav)
    return FixedIncomeStressPortfolioResult(
        fund_id=1,
        valuation_date=date(2026, 6, 10),
        scenario_id="FI_RATE_UP_100",
        scenario_name="Rates +100bps",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="RATE_SHOCK",
        rate_shock_bps=100,
        spread_shock_bps=0,
        current_nav=current_nav,
        stressed_nav=stressed_nav,
        total_rate_pnl=total_rate_pnl,
        total_credit_pnl=total_credit_pnl,
        total_pnl=total_pnl,
        loss_pct_nav=loss_pct_nav,
        stressed_positions=[],
        num_bond_positions=1,
        num_cash_positions=0,
    )


def make_combined_result(
    equity_result: StressPortfolioResult | None = None,
    fi_result: FixedIncomeStressPortfolioResult | None = None,
    num_cash_positions: int = 1,
    cash_value_base_ccy: Decimal = Decimal("70000"),
) -> CombinedStressPortfolioResult:
    if equity_result is None:
        equity_result = make_equity_result()
    eq_pnl = equity_result.total_pnl if equity_result else Decimal("0")
    fi_pnl = fi_result.total_pnl if fi_result else Decimal("0")
    total_pnl = eq_pnl + fi_pnl
    current_nav = Decimal("250000")
    stressed_nav = current_nav + total_pnl
    loss_pct_nav = max(Decimal("0"), -total_pnl / current_nav)
    return CombinedStressPortfolioResult(
        fund_id=1,
        valuation_date=date(2026, 6, 10),
        scenario_id="COMBINED_01",
        scenario_name="Combined stress",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        current_nav=current_nav,
        stressed_nav=stressed_nav,
        total_pnl=total_pnl,
        loss_pct_nav=loss_pct_nav,
        num_cash_positions=num_cash_positions,
        cash_value_base_ccy=cash_value_base_ccy,
        equity_result=equity_result,
        fi_result=fi_result,
    )


@pytest.fixture
def combined_result_with_both() -> CombinedStressPortfolioResult:
    return make_combined_result(
        equity_result=make_equity_result(),
        fi_result=make_fi_result(),
    )


@pytest.fixture
def combined_result_equity_only() -> CombinedStressPortfolioResult:
    return make_combined_result(equity_result=make_equity_result(), fi_result=None)


@pytest.fixture
def combined_result_fi_only() -> CombinedStressPortfolioResult:
    eq_pnl = Decimal("0")
    fi_result = make_fi_result()
    fi_pnl = fi_result.total_pnl
    total_pnl = eq_pnl + fi_pnl
    current_nav = Decimal("250000")
    return CombinedStressPortfolioResult(
        fund_id=1,
        valuation_date=date(2026, 6, 10),
        scenario_id="COMBINED_FI_ONLY",
        scenario_name="FI only",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        current_nav=current_nav,
        stressed_nav=current_nav + total_pnl,
        total_pnl=total_pnl,
        loss_pct_nav=max(Decimal("0"), -total_pnl / current_nav),
        num_cash_positions=1,
        cash_value_base_ccy=Decimal("70000"),
        equity_result=None,
        fi_result=fi_result,
    )


@pytest.fixture
def combined_result_all_cash() -> CombinedStressPortfolioResult:
    current_nav = Decimal("100000")
    return CombinedStressPortfolioResult(
        fund_id=1,
        valuation_date=date(2026, 6, 10),
        scenario_id="COMBINED_CASH",
        scenario_name="All cash",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        current_nav=current_nav,
        stressed_nav=current_nav,
        total_pnl=Decimal("0"),
        loss_pct_nav=Decimal("0"),
        num_cash_positions=3,
        cash_value_base_ccy=current_nav,
        equity_result=None,
        fi_result=None,
    )


# ---------------------------------------------------------------------------
# Scope and type
# ---------------------------------------------------------------------------


def test_mapper_sets_multi_asset_scope(
    combined_result_with_both: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_with_both, 42)
    assert orm.asset_scope == StressTestAssetScopeEnum.MULTI_ASSET


def test_mapper_sets_hypothetical_result_type(
    combined_result_with_both: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_with_both, 42)
    assert orm.result_type == StressTestResultTypeEnum.HYPOTHETICAL


def test_mapper_sets_calculation_run_id(
    combined_result_with_both: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_with_both, 99)
    assert orm.calculation_run_id == 99


# ---------------------------------------------------------------------------
# NAV and P&L fields
# ---------------------------------------------------------------------------


def test_mapper_maps_nav_and_pnl(
    combined_result_with_both: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_with_both, 1)
    assert orm.current_nav == combined_result_with_both.current_nav
    assert orm.stressed_nav == combined_result_with_both.stressed_nav
    assert orm.total_pnl == combined_result_with_both.total_pnl
    assert orm.loss_pct_nav == combined_result_with_both.loss_pct_nav


def test_mapper_maps_scenario_identity(
    combined_result_with_both: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_with_both, 1)
    assert orm.scenario_id == "COMBINED_01"
    assert orm.scenario_name == "Combined stress"
    assert orm.scenario_type == "HYPOTHETICAL"
    assert orm.scenario_source == "MANAGER_DEFINED"
    assert orm.fund_id == 1


# ---------------------------------------------------------------------------
# Shock fields — must be None on multi-asset row
# ---------------------------------------------------------------------------


def test_mapper_shock_rate_is_none(
    combined_result_with_both: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_with_both, 1)
    assert orm.shock_rate is None


def test_mapper_shock_type_is_none(
    combined_result_with_both: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_with_both, 1)
    assert orm.shock_type is None


def test_mapper_rate_spread_shock_bps_are_none(
    combined_result_with_both: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_with_both, 1)
    assert orm.rate_shock_bps is None
    assert orm.spread_shock_bps is None


def test_mapper_num_positions_stressed_is_none(
    combined_result_with_both: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_with_both, 1)
    assert orm.num_positions_stressed is None


# ---------------------------------------------------------------------------
# FI P&L decomposition on combined row (when fi_result is present)
# ---------------------------------------------------------------------------


def test_mapper_carries_fi_pnl_decomposition_when_fi_present(
    combined_result_with_both: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_with_both, 1)
    fi = combined_result_with_both.fi_result
    assert fi is not None
    assert orm.total_rate_pnl == fi.total_rate_pnl
    assert orm.total_credit_pnl == fi.total_credit_pnl


def test_mapper_fi_pnl_fields_none_when_no_fi_result(
    combined_result_equity_only: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_equity_only, 1)
    assert orm.total_rate_pnl is None
    assert orm.total_credit_pnl is None


def test_mapper_fi_pnl_fields_none_for_all_cash(
    combined_result_all_cash: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_all_cash, 1)
    assert orm.total_rate_pnl is None
    assert orm.total_credit_pnl is None


# ---------------------------------------------------------------------------
# Cash position count
# ---------------------------------------------------------------------------


def test_mapper_maps_num_cash_positions(
    combined_result_with_both: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_with_both, 1)
    assert orm.num_cash_positions == combined_result_with_both.num_cash_positions


def test_mapper_all_cash_portfolio_cash_count(
    combined_result_all_cash: CombinedStressPortfolioResult,
) -> None:
    orm = map_combined_stress_portfolio_result_to_orm(combined_result_all_cash, 1)
    assert orm.num_cash_positions == 3
    assert orm.total_pnl == Decimal("0")
