"""Tests for ScenarioPnL model."""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.models.scenario_pnl import ScenarioPnL


def test_scenario_pnl_with_date():
    """ScenarioPnL with scenario_date is valid."""
    pnl = ScenarioPnL(
        scenario_date=date(2024, 1, 1),
        total_pnl=Decimal("1000.50"),
    )
    assert pnl.scenario_date == date(2024, 1, 1)
    assert pnl.scenario_id is None
    assert pnl.total_pnl == Decimal("1000.50")


def test_scenario_pnl_with_id():
    """ScenarioPnL with scenario_id is valid."""
    pnl = ScenarioPnL(
        scenario_id="stress_001",
        total_pnl=Decimal("-2500.00"),
    )
    assert pnl.scenario_date is None
    assert pnl.scenario_id == "stress_001"
    assert pnl.total_pnl == Decimal("-2500.00")


def test_scenario_pnl_with_both_identifiers():
    """ScenarioPnL with both scenario_date and scenario_id is valid."""
    pnl = ScenarioPnL(
        scenario_date=date(2024, 6, 10),
        scenario_id="historical",
        total_pnl=Decimal("500.00"),
    )
    assert pnl.scenario_date == date(2024, 6, 10)
    assert pnl.scenario_id == "historical"
    assert pnl.total_pnl == Decimal("500.00")


def test_scenario_pnl_missing_both_identifiers():
    """ScenarioPnL without both scenario_date and scenario_id is rejected."""
    with pytest.raises(ValueError, match="At least one of scenario_date or scenario_id"):
        ScenarioPnL(total_pnl=Decimal("100.00"))


def test_scenario_pnl_negative_pnl():
    """ScenarioPnL accepts negative P&L (loss)."""
    pnl = ScenarioPnL(
        scenario_date=date(2024, 1, 1),
        total_pnl=Decimal("-5000.75"),
    )
    assert pnl.total_pnl == Decimal("-5000.75")


def test_scenario_pnl_zero_pnl():
    """ScenarioPnL accepts zero P&L."""
    pnl = ScenarioPnL(
        scenario_id="zero_scenario",
        total_pnl=Decimal("0.00"),
    )
    assert pnl.total_pnl == Decimal("0.00")


def test_scenario_pnl_pnl_from_float():
    """ScenarioPnL accepts P&L as float and converts to Decimal."""
    pnl = ScenarioPnL(
        scenario_date=date(2024, 1, 1),
        total_pnl=1000.50,
    )
    assert isinstance(pnl.total_pnl, Decimal)
    assert pnl.total_pnl == Decimal("1000.50")


def test_scenario_pnl_frozen():
    """ScenarioPnL is frozen (immutable)."""
    pnl = ScenarioPnL(
        scenario_date=date(2024, 1, 1),
        total_pnl=Decimal("100.00"),
    )
    with pytest.raises(ValueError):
        pnl.total_pnl = Decimal("200.00")
