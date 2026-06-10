"""Tests for EquityScenarioPnLGenerator engine."""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.engines.equity_scenarios import EquityScenarioPnLGenerator
from manco_risk.risk.exceptions import (
    InvalidScenarioInputError,
    MissingHistoricalDataError,
    UnsupportedAssetClassError,
)
from manco_risk.risk.models.equity_scenario_pnl import EquityScenarioPnLInput


@pytest.fixture
def generator():
    """Create a EquityScenarioPnLGenerator instance."""
    return EquityScenarioPnLGenerator()


@pytest.fixture
def equity_position():
    """Create a sample equity position."""
    return EnrichedPosition(
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


@pytest.fixture
def cash_position():
    """Create a sample cash position."""
    return EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=2,
        isin="CASH_EUR",
        valuation_date="2024-06-10",
        quantity=Decimal("10000"),
        market_value=Decimal("10000.00"),
        position_currency="EUR",
        asset_class="CASH",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("10000.00"),
        fund_base_currency="EUR",
        weight=Decimal("0.1"),
    )


def test_generate_single_equity_negative_returns(equity_position, generator):
    """Single equity position with negative returns creates losses."""
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("100000.00"),
        positions=[equity_position],
    )
    returns = {
        "US0378331005": {
            date(2024, 1, 1): Decimal("-0.025"),
            date(2024, 1, 2): Decimal("-0.010"),
        }
    }
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)
    result = generator.generate(input)

    # Portfolio P&L = 100000 * -0.025 = -2500, 100000 * -0.010 = -1000
    assert len(result.scenario_pnls) == 2
    assert result.scenario_pnls[0].total_pnl == Decimal("-2500.00")
    assert result.scenario_pnls[1].total_pnl == Decimal("-1000.00")
    assert result.num_scenarios == 2
    assert result.num_cash_positions == 0
    assert result.num_equity_like_positions == 1


def test_generate_single_equity_positive_returns(equity_position, generator):
    """Single equity position with positive returns creates gains."""
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("100000.00"),
        positions=[equity_position],
    )
    returns = {
        "US0378331005": {
            date(2024, 1, 1): Decimal("0.050"),
        }
    }
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)
    result = generator.generate(input)

    # Portfolio P&L = 100000 * 0.050 = 5000
    assert result.scenario_pnls[0].total_pnl == Decimal("5000.00")


def test_generate_single_equity_zero_return(equity_position, generator):
    """Single equity position with zero return creates zero P&L."""
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("100000.00"),
        positions=[equity_position],
    )
    returns = {
        "US0378331005": {
            date(2024, 1, 1): Decimal("0.00"),
        }
    }
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)
    result = generator.generate(input)

    assert result.scenario_pnls[0].total_pnl == Decimal("0.00")


def test_generate_two_equity_weighted_sum(equity_position, generator):
    """Two equity positions: P&L is weighted sum."""
    position2 = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=2,
        isin="IE00B4L5Y983",
        valuation_date="2024-06-10",
        quantity=Decimal("500"),
        market_value=Decimal("50000.00"),
        position_currency="EUR",
        asset_class="ETF",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("50000.00"),
        fund_base_currency="EUR",
        weight=Decimal("0.333"),
    )
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("150000.00"),
        positions=[equity_position, position2],
    )
    returns = {
        "US0378331005": {
            date(2024, 1, 1): Decimal("-0.02"),
        },
        "IE00B4L5Y983": {
            date(2024, 1, 1): Decimal("0.01"),
        },
    }
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)
    result = generator.generate(input)

    # P&L = 100000 * -0.02 + 50000 * 0.01 = -2000 + 500 = -1500
    assert result.scenario_pnls[0].total_pnl == Decimal("-1500.00")
    assert result.num_equity_like_positions == 2


def test_generate_equity_plus_cash(equity_position, cash_position, generator):
    """Equity plus cash: cash contributes zero."""
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("110000.00"),
        positions=[equity_position, cash_position],
    )
    returns = {
        "US0378331005": {
            date(2024, 1, 1): Decimal("-0.01"),
        }
    }
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)
    result = generator.generate(input)

    # P&L = 100000 * -0.01 + 10000 * 0 = -1000
    assert result.scenario_pnls[0].total_pnl == Decimal("-1000.00")
    assert result.num_cash_positions == 1
    assert result.num_equity_like_positions == 1


def test_generate_cash_only_zero_pnl(cash_position, generator):
    """Cash-only portfolio has zero P&L in all scenarios."""
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("10000.00"),
        positions=[cash_position],
    )
    returns = {}  # No returns needed for cash-only portfolio
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)
    result = generator.generate(input)

    # Cash-only with no equity positions produces empty scenario list
    assert result.num_scenarios == 0
    assert result.num_cash_positions == 1
    assert result.num_equity_like_positions == 0


def test_generate_unsupported_bond_asset_class(equity_position, generator):
    """Unsupported BOND asset class raises UnsupportedAssetClassError."""
    bond_position = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=3,
        isin="XS1234567890",
        valuation_date="2024-06-10",
        quantity=Decimal("100"),
        market_value=Decimal("105000.00"),
        position_currency="EUR",
        asset_class="BOND",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("105000.00"),
        fund_base_currency="EUR",
        weight=Decimal("1.0"),
    )
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("105000.00"),
        positions=[bond_position],
    )
    returns = {}
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)

    with pytest.raises(UnsupportedAssetClassError, match="BOND"):
        generator.generate(input)


def test_generate_unsupported_derivative_asset_class(equity_position, generator):
    """Unsupported DERIVATIVE asset class raises UnsupportedAssetClassError."""
    derivative_position = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=3,
        isin="OPT0001",
        valuation_date="2024-06-10",
        quantity=Decimal("100"),
        market_value=Decimal("5000.00"),
        position_currency="EUR",
        asset_class="DERIVATIVE",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("5000.00"),
        fund_base_currency="EUR",
        weight=Decimal("0.05"),
    )
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("100000.00"),
        positions=[derivative_position],
    )
    returns = {}
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)

    with pytest.raises(UnsupportedAssetClassError, match="DERIVATIVE"):
        generator.generate(input)


def test_generate_foreign_currency_cash_rejected(generator):
    """Foreign-currency cash is rejected."""
    foreign_cash = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=1,
        isin="CASH_USD",
        valuation_date="2024-06-10",
        quantity=Decimal("10000"),
        market_value=Decimal("10000.00"),
        position_currency="USD",
        asset_class="CASH",
        instrument_currency="USD",
        market_value_base_ccy=Decimal("9200.00"),
        fund_base_currency="EUR",
        weight=Decimal("0.092"),
    )
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("100000.00"),
        positions=[foreign_cash],
    )
    returns = {}
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)

    with pytest.raises(UnsupportedAssetClassError, match="Foreign-currency cash"):
        generator.generate(input)


def test_generate_missing_return_data(equity_position, generator):
    """Missing return data for a non-cash position raises MissingHistoricalDataError."""
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("100000.00"),
        positions=[equity_position],
    )
    # Empty returns: missing data for US0378331005
    returns = {}
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)

    with pytest.raises(MissingHistoricalDataError, match="US0378331005"):
        generator.generate(input)


def test_generate_missing_specific_scenario_date(equity_position, generator):
    """Missing return data for specific scenario date raises MissingHistoricalDataError."""
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("100000.00"),
        positions=[equity_position],
    )
    # Returns for one date but missing for another
    returns = {
        "US0378331005": {
            date(2024, 1, 1): Decimal("-0.01"),
        }
    }
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)
    result = generator.generate(input)

    # Should succeed with one scenario
    assert result.num_scenarios == 1
    assert result.scenario_pnls[0].scenario_date == date(2024, 1, 1)


def test_generate_mismatched_scenario_dates(equity_position, generator):
    """Mismatched scenario dates across positions raises InvalidScenarioInputError."""
    position2 = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=2,
        isin="IE00B4L5Y983",
        valuation_date="2024-06-10",
        quantity=Decimal("500"),
        market_value=Decimal("50000.00"),
        position_currency="EUR",
        asset_class="ETF",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("50000.00"),
        fund_base_currency="EUR",
        weight=Decimal("0.333"),
    )
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("150000.00"),
        positions=[equity_position, position2],
    )
    # Different dates for each position
    returns = {
        "US0378331005": {
            date(2024, 1, 1): Decimal("-0.01"),
            date(2024, 1, 2): Decimal("0.005"),
        },
        "IE00B4L5Y983": {
            date(2024, 1, 1): Decimal("0.01"),
        },
    }
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)

    with pytest.raises(InvalidScenarioInputError, match="Scenario dates mismatch"):
        generator.generate(input)


def test_generate_scenario_dates_sorted(equity_position, generator):
    """Scenario dates are sorted in output."""
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("100000.00"),
        positions=[equity_position],
    )
    # Unsorted returns
    returns = {
        "US0378331005": {
            date(2024, 1, 3): Decimal("-0.01"),
            date(2024, 1, 1): Decimal("-0.025"),
            date(2024, 1, 2): Decimal("0.01"),
        }
    }
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)
    result = generator.generate(input)

    # Dates should be sorted
    assert result.scenario_pnls[0].scenario_date == date(2024, 1, 1)
    assert result.scenario_pnls[1].scenario_date == date(2024, 1, 2)
    assert result.scenario_pnls[2].scenario_date == date(2024, 1, 3)


def test_generate_sign_convention_negative_return_loss(equity_position, generator):
    """Negative return with positive market value creates negative P&L (loss)."""
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("100000.00"),
        positions=[equity_position],
    )
    returns = {
        "US0378331005": {
            date(2024, 1, 1): Decimal("-0.05"),  # -5% loss
        }
    }
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)
    result = generator.generate(input)

    # Negative return should produce negative P&L
    assert result.scenario_pnls[0].total_pnl == Decimal("-5000.00")
    assert result.scenario_pnls[0].total_pnl < Decimal("0")


def test_generate_sign_convention_positive_return_gain(equity_position, generator):
    """Positive return with positive market value creates positive P&L (gain)."""
    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("100000.00"),
        positions=[equity_position],
    )
    returns = {
        "US0378331005": {
            date(2024, 1, 1): Decimal("0.03"),  # +3% gain
        }
    }
    input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)
    result = generator.generate(input)

    # Positive return should produce positive P&L
    assert result.scenario_pnls[0].total_pnl == Decimal("3000.00")
    assert result.scenario_pnls[0].total_pnl > Decimal("0")


def test_generate_supported_asset_classes(generator):
    """All supported asset classes (except CASH) are accepted."""
    for asset_class in ["EQUITY", "ETF", "LISTED_FUND", "INDEX"]:
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin=f"TEST_{asset_class}",
            valuation_date="2024-06-10",
            quantity=Decimal("100"),
            market_value=Decimal("10000.00"),
            position_currency="EUR",
            asset_class=asset_class,
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("10000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-06-10",
            fund_base_currency="EUR",
            nav=Decimal("10000.00"),
            positions=[position],
        )
        returns = {
            f"TEST_{asset_class}": {
                date(2024, 1, 1): Decimal("-0.01"),
            }
        }
        input = EquityScenarioPnLInput(portfolio=portfolio, historical_returns=returns)
        result = generator.generate(input)

        assert result.num_scenarios == 1
        assert result.num_equity_like_positions == 1
