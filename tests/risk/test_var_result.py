"""Tests for HistoricalVaRResult model."""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.models.var_result import HistoricalVaRResult


def test_var_result_valid():
    """Valid HistoricalVaRResult constructs successfully."""
    result = HistoricalVaRResult(
        fund_id=1,
        valuation_date=date(2024, 6, 10),
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        var_value=Decimal("2500.00"),
        var_pct_nav=Decimal("0.025"),
        num_scenarios=250,
        quantile_index=12,
    )
    assert result.fund_id == 1
    assert result.var_pct_nav == Decimal("0.025")


def test_var_result_zero_var():
    """HistoricalVaRResult accepts zero VaR."""
    result = HistoricalVaRResult(
        fund_id=1,
        valuation_date=date(2024, 6, 10),
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        var_value=Decimal("0.00"),
        var_pct_nav=Decimal("0.00"),
        num_scenarios=250,
        quantile_index=0,
    )
    assert result.var_value == Decimal("0.00")


def test_var_result_negative_var_value():
    """Negative VaR value is rejected."""
    with pytest.raises(ValueError, match="VaR value must be non-negative"):
        HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 6, 10),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("-500.00"),
            var_pct_nav=Decimal("0.005"),
            num_scenarios=250,
            quantile_index=12,
        )


def test_var_result_negative_var_pct_nav():
    """Negative VaR % NAV is rejected."""
    with pytest.raises(ValueError, match="VaR % NAV must be non-negative"):
        HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 6, 10),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("500.00"),
            var_pct_nav=Decimal("-0.005"),
            num_scenarios=250,
            quantile_index=12,
        )


def test_var_result_horizon_days_not_one():
    """Horizon days != 1 is rejected for Phase 1."""
    with pytest.raises(ValueError, match="Phase 1 supports only horizon_days=1"):
        HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 6, 10),
            confidence_level=Decimal("0.95"),
            horizon_days=10,
            var_value=Decimal("2500.00"),
            var_pct_nav=Decimal("0.025"),
            num_scenarios=250,
            quantile_index=12,
        )


def test_var_result_zero_num_scenarios():
    """Zero scenarios is rejected."""
    with pytest.raises(ValueError, match="Number of scenarios must be positive"):
        HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 6, 10),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("2500.00"),
            var_pct_nav=Decimal("0.025"),
            num_scenarios=0,
            quantile_index=0,
        )


def test_var_result_negative_quantile_index():
    """Negative quantile index is rejected."""
    with pytest.raises(ValueError, match="Quantile index must be non-negative"):
        HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 6, 10),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("2500.00"),
            var_pct_nav=Decimal("0.025"),
            num_scenarios=250,
            quantile_index=-1,
        )


def test_var_result_frozen():
    """HistoricalVaRResult is frozen (immutable)."""
    result = HistoricalVaRResult(
        fund_id=1,
        valuation_date=date(2024, 6, 10),
        confidence_level=Decimal("0.95"),
        horizon_days=1,
        var_value=Decimal("2500.00"),
        var_pct_nav=Decimal("0.025"),
        num_scenarios=250,
        quantile_index=12,
    )
    with pytest.raises(ValueError):
        result.var_value = Decimal("3000.00")
