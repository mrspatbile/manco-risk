"""Tests for fixed-income stress mapper.

Maps FixedIncomeStressPortfolioResult → StressTestResult ORM.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.database.models import (
    StressTestAssetScopeEnum,
    StressTestResultTypeEnum,
)
from manco_risk.database.stress_mappers import (
    map_fixed_income_stress_portfolio_result_to_orm,
)
from manco_risk.risk.models.fixed_income_stress_portfolio_result import (
    FixedIncomeStressPortfolioResult,
)


@pytest.fixture
def sample_fi_stress_result() -> FixedIncomeStressPortfolioResult:
    """Create a sample FI stress portfolio result."""
    return FixedIncomeStressPortfolioResult(
        fund_id=1,
        valuation_date=date(2024, 1, 15),
        scenario_id="FI_RATE_UP_100",
        scenario_name="Rates +100bps",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="RATE_SHOCK",
        rate_shock_bps=100,
        spread_shock_bps=0,
        current_nav=Decimal("10000000.00"),
        stressed_nav=Decimal("9850000.00"),
        total_rate_pnl=Decimal("-150000.00"),
        total_credit_pnl=Decimal("0.00"),
        total_pnl=Decimal("-150000.00"),
        loss_pct_nav=Decimal("0.015"),
        stressed_positions=[],
        num_bond_positions=5,
        num_cash_positions=2,
    )


def test_map_fixed_income_stress_portfolio_result_to_orm(
    sample_fi_stress_result: FixedIncomeStressPortfolioResult,
) -> None:
    """Mapper converts all FI fields correctly."""
    orm_result = map_fixed_income_stress_portfolio_result_to_orm(sample_fi_stress_result, 1)

    assert orm_result.calculation_run_id == 1
    assert orm_result.fund_id == 1
    assert orm_result.scenario_id == "FI_RATE_UP_100"
    assert orm_result.scenario_name == "Rates +100bps"
    assert orm_result.scenario_type == "HYPOTHETICAL"
    assert orm_result.scenario_source == "MANAGER_DEFINED"
    assert orm_result.shock_type == "RATE_SHOCK"
    assert orm_result.result_type == StressTestResultTypeEnum.HYPOTHETICAL
    assert orm_result.asset_scope == StressTestAssetScopeEnum.FIXED_INCOME


def test_mapper_sets_fi_specific_fields(
    sample_fi_stress_result: FixedIncomeStressPortfolioResult,
) -> None:
    """Rate and spread shocks stored as separate fields."""
    orm_result = map_fixed_income_stress_portfolio_result_to_orm(sample_fi_stress_result, 1)

    assert orm_result.rate_shock_bps == 100
    assert orm_result.spread_shock_bps == 0
    assert orm_result.total_rate_pnl == Decimal("-150000.00")
    assert orm_result.total_credit_pnl == Decimal("0.00")
    assert orm_result.num_positions_stressed == 5
    assert orm_result.num_cash_positions == 2


def test_mapper_sets_shock_rate_null(
    sample_fi_stress_result: FixedIncomeStressPortfolioResult,
) -> None:
    """shock_rate field set to None for FI (not applicable)."""
    orm_result = map_fixed_income_stress_portfolio_result_to_orm(sample_fi_stress_result, 1)

    assert orm_result.shock_rate is None


def test_mapper_transfers_nav_and_pnl(
    sample_fi_stress_result: FixedIncomeStressPortfolioResult,
) -> None:
    """NAV and P&L fields transferred correctly."""
    orm_result = map_fixed_income_stress_portfolio_result_to_orm(sample_fi_stress_result, 1)

    assert orm_result.current_nav == Decimal("10000000.00")
    assert orm_result.stressed_nav == Decimal("9850000.00")
    assert orm_result.total_pnl == Decimal("-150000.00")
    assert orm_result.loss_pct_nav == Decimal("0.015")


def test_mapper_spread_shock_only() -> None:
    """Mapper handles spread-only shock correctly."""
    result = FixedIncomeStressPortfolioResult(
        fund_id=1,
        valuation_date=date(2024, 1, 15),
        scenario_id="FI_SPREAD_UP_50",
        scenario_name="Spreads +50bps",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="SPREAD_SHOCK",
        rate_shock_bps=0,
        spread_shock_bps=50,
        current_nav=Decimal("10000000.00"),
        stressed_nav=Decimal("9950000.00"),
        total_rate_pnl=Decimal("0.00"),
        total_credit_pnl=Decimal("-50000.00"),
        total_pnl=Decimal("-50000.00"),
        loss_pct_nav=Decimal("0.005"),
        stressed_positions=[],
        num_bond_positions=3,
        num_cash_positions=1,
    )

    orm_result = map_fixed_income_stress_portfolio_result_to_orm(result, 1)

    assert orm_result.rate_shock_bps == 0
    assert orm_result.spread_shock_bps == 50
    assert orm_result.total_rate_pnl == Decimal("0.00")
    assert orm_result.total_credit_pnl == Decimal("-50000.00")


def test_mapper_combined_shocks() -> None:
    """Mapper handles combined rate and spread shocks."""
    result = FixedIncomeStressPortfolioResult(
        fund_id=1,
        valuation_date=date(2024, 1, 15),
        scenario_id="FI_COMBINED",
        scenario_name="Rates +100bps, Spreads +50bps",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="COMBINED",
        rate_shock_bps=100,
        spread_shock_bps=50,
        current_nav=Decimal("10000000.00"),
        stressed_nav=Decimal("9700000.00"),
        total_rate_pnl=Decimal("-200000.00"),
        total_credit_pnl=Decimal("-100000.00"),
        total_pnl=Decimal("-300000.00"),
        loss_pct_nav=Decimal("0.03"),
        stressed_positions=[],
        num_bond_positions=5,
        num_cash_positions=2,
    )

    orm_result = map_fixed_income_stress_portfolio_result_to_orm(result, 1)

    assert orm_result.shock_type == "COMBINED"
    assert orm_result.rate_shock_bps == 100
    assert orm_result.spread_shock_bps == 50
    assert orm_result.total_rate_pnl == Decimal("-200000.00")
    assert orm_result.total_credit_pnl == Decimal("-100000.00")


def test_mapper_negative_shocks_gain_scenario() -> None:
    """Mapper handles negative shocks (yield down, spread tighten = gains)."""
    result = FixedIncomeStressPortfolioResult(
        fund_id=1,
        valuation_date=date(2024, 1, 15),
        scenario_id="FI_RATE_DOWN_100",
        scenario_name="Rates -100bps",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="RATE_SHOCK",
        rate_shock_bps=-100,
        spread_shock_bps=0,
        current_nav=Decimal("10000000.00"),
        stressed_nav=Decimal("10150000.00"),
        total_rate_pnl=Decimal("150000.00"),
        total_credit_pnl=Decimal("0.00"),
        total_pnl=Decimal("150000.00"),
        loss_pct_nav=Decimal("0.00"),
        stressed_positions=[],
        num_bond_positions=5,
        num_cash_positions=2,
    )

    orm_result = map_fixed_income_stress_portfolio_result_to_orm(result, 1)

    assert orm_result.rate_shock_bps == -100
    assert orm_result.total_rate_pnl == Decimal("150000.00")
    assert orm_result.total_pnl == Decimal("150000.00")
    assert orm_result.loss_pct_nav == Decimal("0.00")


def test_mapper_pnl_decomposition_sums_to_total() -> None:
    """Verify that total_rate_pnl + total_credit_pnl = total_pnl."""
    result = FixedIncomeStressPortfolioResult(
        fund_id=1,
        valuation_date=date(2024, 1, 15),
        scenario_id="FI_COMBINED",
        scenario_name="Combined scenario",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="COMBINED",
        rate_shock_bps=100,
        spread_shock_bps=50,
        current_nav=Decimal("10000000.00"),
        stressed_nav=Decimal("9700000.00"),
        total_rate_pnl=Decimal("-200000.00"),
        total_credit_pnl=Decimal("-100000.00"),
        total_pnl=Decimal("-300000.00"),
        loss_pct_nav=Decimal("0.03"),
        stressed_positions=[],
        num_bond_positions=5,
        num_cash_positions=2,
    )

    orm_result = map_fixed_income_stress_portfolio_result_to_orm(result, 1)

    expected_total = orm_result.total_rate_pnl + orm_result.total_credit_pnl
    assert expected_total == orm_result.total_pnl


def test_mapper_decimal_precision_preserved() -> None:
    """Decimal precision preserved for monetary fields (Numeric(18,8))."""
    result = FixedIncomeStressPortfolioResult(
        fund_id=1,
        valuation_date=date(2024, 1, 15),
        scenario_id="FI_PRECISION_TEST",
        scenario_name="Precision test",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="RATE_SHOCK",
        rate_shock_bps=123,
        spread_shock_bps=456,
        current_nav=Decimal("10000000.12345678"),
        stressed_nav=Decimal("9999999.87654321"),
        total_rate_pnl=Decimal("-0.24691357"),
        total_credit_pnl=Decimal("-0.12345678"),
        total_pnl=Decimal("-0.37037035"),
        loss_pct_nav=Decimal("0.00000003"),
        stressed_positions=[],
        num_bond_positions=1,
        num_cash_positions=1,
    )

    orm_result = map_fixed_income_stress_portfolio_result_to_orm(result, 1)

    assert orm_result.current_nav == Decimal("10000000.12345678")
    assert orm_result.stressed_nav == Decimal("9999999.87654321")
    assert orm_result.total_rate_pnl == Decimal("-0.24691357")


def test_mapper_all_cash_portfolio() -> None:
    """Mapper handles all-cash portfolio (no bonds) correctly."""
    result = FixedIncomeStressPortfolioResult(
        fund_id=1,
        valuation_date=date(2024, 1, 15),
        scenario_id="FI_CASH_ONLY",
        scenario_name="All cash",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="RATE_SHOCK",
        rate_shock_bps=100,
        spread_shock_bps=0,
        current_nav=Decimal("1000000.00"),
        stressed_nav=Decimal("1000000.00"),
        total_rate_pnl=Decimal("0.00"),
        total_credit_pnl=Decimal("0.00"),
        total_pnl=Decimal("0.00"),
        loss_pct_nav=Decimal("0.00"),
        stressed_positions=[],
        num_bond_positions=0,
        num_cash_positions=3,
    )

    orm_result = map_fixed_income_stress_portfolio_result_to_orm(result, 1)

    assert orm_result.num_positions_stressed == 0
    assert orm_result.num_cash_positions == 3
    assert orm_result.total_rate_pnl == Decimal("0.00")
