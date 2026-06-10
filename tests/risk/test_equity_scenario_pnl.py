"""Tests for equity scenario P&L input and result models."""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.models.equity_scenario_pnl import (
    EquityScenarioPnLInput,
    EquityScenarioPnLResult,
)
from manco_risk.risk.models.scenario_pnl import ScenarioPnL


@pytest.fixture
def sample_portfolio():
    """Create a simple test portfolio."""
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
def sample_returns():
    """Create sample historical returns."""
    return {
        "US0378331005": {
            date(2024, 1, 1): Decimal("-0.025"),
            date(2024, 1, 2): Decimal("0.010"),
        }
    }


def test_equity_scenario_pnl_input_valid(sample_portfolio, sample_returns):
    """Valid EquityScenarioPnLInput constructs successfully."""
    input = EquityScenarioPnLInput(
        portfolio=sample_portfolio,
        historical_returns=sample_returns,
    )
    assert input.portfolio == sample_portfolio
    assert len(input.historical_returns) == 1


def test_equity_scenario_pnl_input_empty_returns_allowed(sample_portfolio):
    """Empty historical returns are allowed (for cash-only portfolios)."""
    input = EquityScenarioPnLInput(
        portfolio=sample_portfolio,
        historical_returns={},
    )
    assert input.historical_returns == {}


def test_equity_scenario_pnl_input_returns_not_dict(sample_portfolio):
    """Non-dict historical returns rejected."""
    with pytest.raises(ValueError, match="historical_returns must be a dict"):
        EquityScenarioPnLInput(
            portfolio=sample_portfolio,
            historical_returns="not a dict",
        )


def test_equity_scenario_pnl_input_nested_not_dict(sample_portfolio):
    """Returns for ISIN must be dict."""
    with pytest.raises(ValueError, match="Returns for .* must be a dict"):
        EquityScenarioPnLInput(
            portfolio=sample_portfolio,
            historical_returns={
                "US0378331005": "not a dict",
            },
        )


def test_equity_scenario_pnl_input_date_key_validation(sample_portfolio):
    """Return date keys must be date objects."""
    with pytest.raises(ValueError, match="Return date key must be date"):
        EquityScenarioPnLInput(
            portfolio=sample_portfolio,
            historical_returns={
                "US0378331005": {
                    "2024-01-01": Decimal("-0.025"),  # string instead of date
                }
            },
        )


def test_equity_scenario_pnl_input_return_value_conversion(sample_portfolio):
    """Return values are converted to Decimal."""
    input = EquityScenarioPnLInput(
        portfolio=sample_portfolio,
        historical_returns={
            "US0378331005": {
                date(2024, 1, 1): -0.025,  # float, will be converted
            }
        },
    )
    # Value is converted to Decimal
    assert isinstance(input.historical_returns["US0378331005"][date(2024, 1, 1)], Decimal)
    assert input.historical_returns["US0378331005"][date(2024, 1, 1)] == Decimal("-0.025")


def test_equity_scenario_pnl_input_frozen(sample_portfolio, sample_returns):
    """EquityScenarioPnLInput is frozen."""
    input = EquityScenarioPnLInput(
        portfolio=sample_portfolio,
        historical_returns=sample_returns,
    )
    with pytest.raises(ValueError):
        input.portfolio = sample_portfolio


def test_equity_scenario_pnl_result_valid():
    """Valid EquityScenarioPnLResult constructs successfully."""
    pnl = ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1000.00"))
    result = EquityScenarioPnLResult(
        scenario_pnls=[pnl],
        num_scenarios=1,
        num_cash_positions=0,
        num_equity_like_positions=1,
    )
    assert result.num_scenarios == 1
    assert len(result.scenario_pnls) == 1


def test_equity_scenario_pnl_result_negative_num_scenarios():
    """Negative num_scenarios rejected."""
    with pytest.raises(ValueError, match="Number of scenarios must be non-negative"):
        EquityScenarioPnLResult(
            scenario_pnls=[],
            num_scenarios=-1,
            num_cash_positions=0,
            num_equity_like_positions=0,
        )


def test_equity_scenario_pnl_result_negative_cash_positions():
    """Negative num_cash_positions rejected."""
    with pytest.raises(ValueError, match="Number of cash positions must be non-negative"):
        EquityScenarioPnLResult(
            scenario_pnls=[],
            num_scenarios=0,
            num_cash_positions=-1,
            num_equity_like_positions=0,
        )


def test_equity_scenario_pnl_result_negative_equity_positions():
    """Negative num_equity_like_positions rejected."""
    with pytest.raises(ValueError, match="Number of equity-like positions must be non-negative"):
        EquityScenarioPnLResult(
            scenario_pnls=[],
            num_scenarios=0,
            num_cash_positions=0,
            num_equity_like_positions=-1,
        )


def test_equity_scenario_pnl_result_frozen():
    """EquityScenarioPnLResult is frozen."""
    result = EquityScenarioPnLResult(
        scenario_pnls=[],
        num_scenarios=0,
        num_cash_positions=0,
        num_equity_like_positions=0,
    )
    with pytest.raises(ValueError):
        result.num_scenarios = 5
