"""Tests for HistoricalVaR engine."""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.engines.var import HistoricalVaR
from manco_risk.risk.models.scenario_pnl import ScenarioPnL
from manco_risk.risk.models.var_input import HistoricalVaRInput


@pytest.fixture
def sample_portfolio():
    """Create a simple test portfolio with 100k NAV."""
    position = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=1,
        isin="US0378331005",
        valuation_date="2024-06-10",
        quantity=Decimal("1000"),
        market_value=Decimal("100000.00"),
        position_currency="EUR",
        asset_class="EQUITY",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("100000.00"),
        fund_base_currency="EUR",
        weight=Decimal("1.0"),
    )
    return RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("100000.00"),
        positions=[position],
    )


@pytest.fixture
def var_engine():
    """Create a HistoricalVaR engine instance."""
    return HistoricalVaR()


def test_var_single_scenario_loss(sample_portfolio, var_engine):
    """Single scenario with loss: VaR = that loss."""
    pnls = [
        ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-2500.00")),
    ]
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        scenario_pnls=pnls,
    )
    result = var_engine.calculate(input)

    # With one scenario, quantile_index = floor(1 * 0.05) = 0
    # selected_pnl = -2500, var_value = 2500
    assert result.var_value == Decimal("2500.00")
    assert result.var_pct_nav == Decimal("0.025")
    assert result.num_scenarios == 1


def test_var_single_scenario_gain(sample_portfolio, var_engine):
    """Single scenario with gain: VaR = 0."""
    pnls = [
        ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("5000.00")),
    ]
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        scenario_pnls=pnls,
    )
    result = var_engine.calculate(input)

    # selected_pnl = 5000 >= 0, so var_value = 0
    assert result.var_value == Decimal("0.00")
    assert result.var_pct_nav == Decimal("0.00")


def test_var_two_scenarios_50_percent(sample_portfolio, var_engine):
    """Two scenarios, 50% VaR: median loss."""
    pnls = [
        ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1000.00")),
        ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("-3000.00")),
    ]
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.50"),
        horizon_days=1,
        scenario_pnls=pnls,
    )
    result = var_engine.calculate(input)

    # quantile_index = floor(2 * 0.50) = 1
    # sorted: [-3000, -1000], selected = -1000
    assert result.var_value == Decimal("1000.00")
    assert result.var_pct_nav == Decimal("0.01")
    assert result.quantile_index == 1


def test_var_mixed_gains_losses_95_percent(sample_portfolio, var_engine):
    """Mixed gains and losses, 95% VaR."""
    pnls = [
        ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("1000.00")),
        ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("-500.00")),
        ScenarioPnL(scenario_date=date(2024, 1, 3), total_pnl=Decimal("2000.00")),
        ScenarioPnL(scenario_date=date(2024, 1, 4), total_pnl=Decimal("-1500.00")),
        ScenarioPnL(scenario_date=date(2024, 1, 5), total_pnl=Decimal("-3000.00")),
        ScenarioPnL(scenario_date=date(2024, 1, 6), total_pnl=Decimal("500.00")),
    ]
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        scenario_pnls=pnls,
    )
    result = var_engine.calculate(input)

    # quantile_index = floor(6 * 0.05) = 0
    # sorted: [-3000, -1500, -500, 500, 1000, 2000], selected = -3000
    assert result.var_value == Decimal("3000.00")
    assert result.var_pct_nav == Decimal("0.03")
    assert result.quantile_index == 0


def test_var_all_gains(sample_portfolio, var_engine):
    """All positive P&Ls: VaR = 0."""
    pnls = [
        ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("1000.00")),
        ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("2000.00")),
        ScenarioPnL(scenario_date=date(2024, 1, 3), total_pnl=Decimal("500.00")),
    ]
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        scenario_pnls=pnls,
    )
    result = var_engine.calculate(input)

    # All P&Ls >= 0, so var_value = 0 regardless of quantile
    assert result.var_value == Decimal("0.00")
    assert result.var_pct_nav == Decimal("0.00")


def test_var_all_losses(sample_portfolio, var_engine):
    """All negative P&Ls: follows quantile rule, not max loss."""
    pnls = [
        ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1000.00")),
        ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("-2000.00")),
        ScenarioPnL(scenario_date=date(2024, 1, 3), total_pnl=Decimal("-500.00")),
    ]
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        scenario_pnls=pnls,
    )
    result = var_engine.calculate(input)

    # quantile_index = floor(3 * 0.05) = 0
    # sorted: [-2000, -1000, -500], selected = -2000
    # NOT max loss (-2000), but quantile-based
    assert result.var_value == Decimal("2000.00")
    assert result.quantile_index == 0


def test_var_250_scenarios_95_percent(sample_portfolio, var_engine):
    """250 scenarios, 95% VaR: quantile_index = 12."""
    from datetime import timedelta

    start_date = date(2023, 1, 1)
    pnls = [
        ScenarioPnL(
            scenario_date=start_date + timedelta(days=i),
            total_pnl=Decimal(str(-100 * (i % 30))),
        )
        for i in range(250)
    ]
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        scenario_pnls=pnls,
    )
    result = var_engine.calculate(input)

    # quantile_index = floor(250 * 0.05) = floor(12.5) = 12
    assert result.quantile_index == 12
    assert result.num_scenarios == 250


def test_var_pct_nav_calculation(sample_portfolio, var_engine):
    """var_pct_nav is correctly computed as var_value / nav."""
    pnls = [
        ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-2500.00")),
    ]
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        scenario_pnls=pnls,
    )
    result = var_engine.calculate(input)

    # var_value = 2500, nav = 100000, so var_pct_nav = 2500 / 100000 = 0.025
    assert result.var_pct_nav == result.var_value / sample_portfolio.nav


def test_var_zero_pnl_scenario(sample_portfolio, var_engine):
    """Scenario with zero P&L is handled correctly."""
    pnls = [
        ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("0.00")),
        ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("-1000.00")),
    ]
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.50"),
        horizon_days=1,
        scenario_pnls=pnls,
    )
    result = var_engine.calculate(input)

    # quantile_index = floor(2 * 0.50) = 1
    # sorted: [-1000, 0], selected = 0
    # var_value = 0 (since selected_pnl >= 0)
    assert result.var_value == Decimal("0.00")


def test_var_valuation_date_from_portfolio(sample_portfolio, var_engine):
    """Result valuation_date matches portfolio valuation_date."""
    pnls = [
        ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1000.00")),
    ]
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        scenario_pnls=pnls,
    )
    result = var_engine.calculate(input)

    assert result.valuation_date == date(2024, 6, 10)


def test_var_fund_id_from_portfolio(sample_portfolio, var_engine):
    """Result fund_id matches portfolio fund_id."""
    pnls = [
        ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1000.00")),
    ]
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        scenario_pnls=pnls,
    )
    result = var_engine.calculate(input)

    assert result.fund_id == 1
