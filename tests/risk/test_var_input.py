"""Tests for HistoricalVaRInput model."""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.models.scenario_pnl import ScenarioPnL
from manco_risk.risk.models.var_input import HistoricalVaRInput


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
        position_currency="USD",
        asset_class="EQUITY",
        instrument_currency="USD",
        market_value_base_ccy=Decimal("92000.00"),
        fund_base_currency="EUR",
        weight=Decimal("1.0"),
    )
    return RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-06-10",
        fund_base_currency="EUR",
        nav=Decimal("92000.00"),
        positions=[position],
    )


@pytest.fixture
def sample_pnls():
    """Create sample scenario P&Ls."""
    return [
        ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("1000.00")),
        ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("-500.00")),
        ScenarioPnL(scenario_date=date(2024, 1, 3), total_pnl=Decimal("2000.00")),
    ]


def test_var_input_valid(sample_portfolio, sample_pnls):
    """Valid HistoricalVaRInput constructs successfully."""
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        scenario_pnls=sample_pnls,
    )
    assert input.confidence_level == Decimal("0.95")
    assert input.horizon_days == 1
    assert len(input.scenario_pnls) == 3


def test_var_input_confidence_level_too_low(sample_portfolio, sample_pnls):
    """Confidence level <= 0 is rejected."""
    with pytest.raises(ValueError, match="Confidence level must be in"):
        HistoricalVaRInput(
            portfolio=sample_portfolio,
            confidence_level=Decimal("0.00"),
            horizon_days=1,
            scenario_pnls=sample_pnls,
        )


def test_var_input_confidence_level_too_high(sample_portfolio, sample_pnls):
    """Confidence level >= 1 is rejected."""
    with pytest.raises(ValueError, match="Confidence level must be in"):
        HistoricalVaRInput(
            portfolio=sample_portfolio,
            confidence_level=Decimal("1.00"),
            horizon_days=1,
            scenario_pnls=sample_pnls,
        )


def test_var_input_confidence_level_negative(sample_portfolio, sample_pnls):
    """Negative confidence level is rejected."""
    with pytest.raises(ValueError, match="Confidence level must be in"):
        HistoricalVaRInput(
            portfolio=sample_portfolio,
            confidence_level=Decimal("-0.95"),
            horizon_days=1,
            scenario_pnls=sample_pnls,
        )


def test_var_input_horizon_days_not_one(sample_portfolio, sample_pnls):
    """Horizon days != 1 is rejected for Phase 1."""
    with pytest.raises(ValueError, match="Phase 1 supports only horizon_days=1"):
        HistoricalVaRInput(
            portfolio=sample_portfolio,
            confidence_level=Decimal("0.95"),
            horizon_days=10,
            scenario_pnls=sample_pnls,
        )


def test_var_input_empty_scenarios(sample_portfolio):
    """Empty scenario list is rejected."""
    with pytest.raises(ValueError, match="At least one scenario P&L is required"):
        HistoricalVaRInput(
            portfolio=sample_portfolio,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            scenario_pnls=[],
        )


def test_var_input_confidence_level_boundary_low(sample_portfolio, sample_pnls):
    """Confidence level just above 0 is accepted."""
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.001"),
        horizon_days=1,
        scenario_pnls=sample_pnls,
    )
    assert input.confidence_level == Decimal("0.001")


def test_var_input_confidence_level_boundary_high(sample_portfolio, sample_pnls):
    """Confidence level just below 1 is accepted."""
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.999"),
        horizon_days=1,
        scenario_pnls=sample_pnls,
    )
    assert input.confidence_level == Decimal("0.999")


def test_var_input_frozen(sample_portfolio, sample_pnls):
    """HistoricalVaRInput is frozen (immutable)."""
    input = HistoricalVaRInput(
        portfolio=sample_portfolio,
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        scenario_pnls=sample_pnls,
    )
    with pytest.raises(ValueError):
        input.confidence_level = Decimal("0.90")
