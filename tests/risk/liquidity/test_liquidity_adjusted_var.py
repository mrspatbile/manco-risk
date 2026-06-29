"""Tests for liquidity-adjusted VaR domain models and engine.

Tests liquidity adjustment assumptions, results, and calculations.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.liquidity import (
    LiquidityAdjustedVaRAssumption,
    LiquidityAdjustedVaREngine,
    LiquidityAdjustedVaRResult,
)


class TestLiquidityAdjustedVaRAssumption:
    def test_valid_assumption(self):
        """Valid liquidity adjustment assumption."""
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0.02"),
            methodology_label="bid-ask spread",
        )
        assert assumption.liquidity_cost_rate == Decimal("0.02")
        assert assumption.methodology_label == "bid-ask spread"

    def test_zero_liquidity_cost(self):
        """Zero cost is valid."""
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0"),
        )
        assert assumption.liquidity_cost_rate == Decimal("0")

    def test_100_percent_liquidity_cost(self):
        """100% cost (extreme case) is valid."""
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("1"),
            methodology_label="worst-case liquidation",
        )
        assert assumption.liquidity_cost_rate == Decimal("1")

    def test_no_methodology_label(self):
        """Methodology label is optional."""
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0.02"),
        )
        assert assumption.methodology_label is None

    def test_negative_cost_raises(self):
        """Negative cost raises ValueError."""
        with pytest.raises(ValueError, match="liquidity_cost_rate must be in range"):
            LiquidityAdjustedVaRAssumption(
                liquidity_cost_rate=Decimal("-0.01"),
            )

    def test_cost_greater_than_one_raises(self):
        """Cost > 100% raises ValueError."""
        with pytest.raises(ValueError, match="liquidity_cost_rate must be in range"):
            LiquidityAdjustedVaRAssumption(
                liquidity_cost_rate=Decimal("1.5"),
            )

    def test_empty_methodology_label_raises(self):
        """Empty string methodology label raises ValueError."""
        with pytest.raises(ValueError, match="methodology_label must be non-empty"):
            LiquidityAdjustedVaRAssumption(
                liquidity_cost_rate=Decimal("0.02"),
                methodology_label="",
            )


class TestLiquidityAdjustedVaRResult:
    def test_valid_result(self):
        """Valid liquidity-adjusted VaR result."""
        result = LiquidityAdjustedVaRResult(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("1000000"),
            base_var_amount=Decimal("50000"),
            base_var_rate=Decimal("0.05"),
            liquidity_cost_rate=Decimal("0.02"),
            liquidity_adjustment=Decimal("20000"),
            liquidity_adjusted_var_amount=Decimal("70000"),
            liquidity_adjusted_var_rate=Decimal("0.07"),
            methodology_label="bid-ask spread",
        )
        assert result.liquidity_adjusted_var_amount == Decimal("70000")
        assert result.liquidity_adjusted_var_rate == Decimal("0.07")

    def test_zero_base_var(self):
        """Zero base VaR with liquidity adjustment."""
        result = LiquidityAdjustedVaRResult(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("1000000"),
            base_var_amount=Decimal("0"),
            base_var_rate=Decimal("0"),
            liquidity_cost_rate=Decimal("0.01"),
            liquidity_adjustment=Decimal("10000"),
            liquidity_adjusted_var_amount=Decimal("10000"),
            liquidity_adjusted_var_rate=Decimal("0.01"),
            methodology_label=None,
        )
        assert result.base_var_amount == Decimal("0")
        assert result.liquidity_adjusted_var_amount == Decimal("10000")

    def test_zero_liquidity_cost(self):
        """Zero liquidity cost adjustment."""
        result = LiquidityAdjustedVaRResult(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("1000000"),
            base_var_amount=Decimal("50000"),
            base_var_rate=Decimal("0.05"),
            liquidity_cost_rate=Decimal("0"),
            liquidity_adjustment=Decimal("0"),
            liquidity_adjusted_var_amount=Decimal("50000"),
            liquidity_adjusted_var_rate=Decimal("0.05"),
            methodology_label=None,
        )
        assert result.liquidity_adjustment == Decimal("0")
        assert result.liquidity_adjusted_var_amount == Decimal("50000")

    def test_zero_portfolio_value_raises(self):
        """Zero portfolio value raises ValueError."""
        with pytest.raises(ValueError, match="portfolio_value must be positive"):
            LiquidityAdjustedVaRResult(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                portfolio_value=Decimal("0"),
                base_var_amount=Decimal("50000"),
                base_var_rate=Decimal("0.05"),
                liquidity_cost_rate=Decimal("0.02"),
                liquidity_adjustment=Decimal("20000"),
                liquidity_adjusted_var_amount=Decimal("70000"),
                liquidity_adjusted_var_rate=Decimal("0.07"),
                methodology_label=None,
            )

    def test_negative_base_var_raises(self):
        """Negative base VaR raises ValueError."""
        with pytest.raises(ValueError, match="base_var_amount must be non-negative"):
            LiquidityAdjustedVaRResult(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                portfolio_value=Decimal("1000000"),
                base_var_amount=Decimal("-50000"),
                base_var_rate=Decimal("0.05"),
                liquidity_cost_rate=Decimal("0.02"),
                liquidity_adjustment=Decimal("20000"),
                liquidity_adjusted_var_amount=Decimal("70000"),
                liquidity_adjusted_var_rate=Decimal("0.07"),
                methodology_label=None,
            )

    def test_accounting_consistency_valid(self):
        """Adjusted VaR = base VaR + adjustment validation passes."""
        result = LiquidityAdjustedVaRResult(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("1000000"),
            base_var_amount=Decimal("50000"),
            base_var_rate=Decimal("0.05"),
            liquidity_cost_rate=Decimal("0.02"),
            liquidity_adjustment=Decimal("20000"),
            liquidity_adjusted_var_amount=Decimal("70000"),
            liquidity_adjusted_var_rate=Decimal("0.07"),
            methodology_label=None,
        )
        assert (
            result.base_var_amount + result.liquidity_adjustment
            == result.liquidity_adjusted_var_amount
        )

    def test_accounting_consistency_rate_valid(self):
        """Adjusted VaR rate = adjusted amount / portfolio value validation."""
        result = LiquidityAdjustedVaRResult(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("1000000"),
            base_var_amount=Decimal("50000"),
            base_var_rate=Decimal("0.05"),
            liquidity_cost_rate=Decimal("0.02"),
            liquidity_adjustment=Decimal("20000"),
            liquidity_adjusted_var_amount=Decimal("70000"),
            liquidity_adjusted_var_rate=Decimal("0.07"),
            methodology_label=None,
        )
        expected_rate = result.liquidity_adjusted_var_amount / result.portfolio_value
        assert abs(result.liquidity_adjusted_var_rate - expected_rate) < Decimal("0.000001")


class TestLiquidityAdjustedVaREngine:
    def test_basic_calculation(self):
        """Basic liquidity adjustment calculation."""
        engine = LiquidityAdjustedVaREngine()
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0.02"),
            methodology_label="bid-ask spread",
        )
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("1000000"),
            base_var_amount=Decimal("50000"),
            base_var_rate=Decimal("0.05"),
            assumption=assumption,
        )

        assert result.fund_id == 1
        assert result.valuation_date == date(2026, 6, 30)
        assert result.portfolio_value == Decimal("1000000")
        assert result.base_var_amount == Decimal("50000")
        assert result.liquidity_adjustment == Decimal("20000")
        assert result.liquidity_adjusted_var_amount == Decimal("70000")
        assert result.liquidity_adjusted_var_rate == Decimal("0.07")

    def test_zero_liquidity_cost(self):
        """Zero liquidity cost produces no adjustment."""
        engine = LiquidityAdjustedVaREngine()
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0"),
        )
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("1000000"),
            base_var_amount=Decimal("50000"),
            base_var_rate=Decimal("0.05"),
            assumption=assumption,
        )

        assert result.liquidity_adjustment == Decimal("0")
        assert result.liquidity_adjusted_var_amount == Decimal("50000")
        assert result.liquidity_adjusted_var_rate == Decimal("0.05")

    def test_zero_base_var(self):
        """Zero base VaR with positive liquidity cost."""
        engine = LiquidityAdjustedVaREngine()
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0.05"),
            methodology_label="liquidation cost",
        )
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("1000000"),
            base_var_amount=Decimal("0"),
            base_var_rate=Decimal("0"),
            assumption=assumption,
        )

        assert result.liquidity_adjustment == Decimal("50000")
        assert result.liquidity_adjusted_var_amount == Decimal("50000")
        assert result.liquidity_adjusted_var_rate == Decimal("0.05")

    def test_high_liquidity_cost(self):
        """High liquidity cost adjustment."""
        engine = LiquidityAdjustedVaREngine()
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0.10"),
        )
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("2000000"),
            base_var_amount=Decimal("100000"),
            base_var_rate=Decimal("0.05"),
            assumption=assumption,
        )

        assert result.liquidity_adjustment == Decimal("200000")
        assert result.liquidity_adjusted_var_amount == Decimal("300000")
        assert result.liquidity_adjusted_var_rate == Decimal("0.15")

    def test_small_portfolio(self):
        """Calculation on small portfolio."""
        engine = LiquidityAdjustedVaREngine()
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0.01"),
        )
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("100000"),
            base_var_amount=Decimal("5000"),
            base_var_rate=Decimal("0.05"),
            assumption=assumption,
        )

        assert result.liquidity_adjustment == Decimal("1000")
        assert result.liquidity_adjusted_var_amount == Decimal("6000")

    def test_large_portfolio(self):
        """Calculation on large portfolio."""
        engine = LiquidityAdjustedVaREngine()
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0.02"),
        )
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("100000000"),
            base_var_amount=Decimal("5000000"),
            base_var_rate=Decimal("0.05"),
            assumption=assumption,
        )

        assert result.liquidity_adjustment == Decimal("2000000")
        assert result.liquidity_adjusted_var_amount == Decimal("7000000")

    def test_methodology_label_preserved(self):
        """Methodology label is preserved in result."""
        engine = LiquidityAdjustedVaREngine()
        label = "liquidity horizon 5 days"
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0.03"),
            methodology_label=label,
        )
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("1000000"),
            base_var_amount=Decimal("50000"),
            base_var_rate=Decimal("0.05"),
            assumption=assumption,
        )

        assert result.methodology_label == label

    def test_decimal_precision(self):
        """High precision Decimal calculations."""
        engine = LiquidityAdjustedVaREngine()
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0.0123456"),
        )
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("999999.99"),
            base_var_amount=Decimal("12345.67"),
            base_var_rate=Decimal("0.0123456789"),
            assumption=assumption,
        )

        expected_adjustment = Decimal("999999.99") * Decimal("0.0123456")
        assert abs(result.liquidity_adjustment - expected_adjustment) < Decimal("0.001")

    def test_metadata_preservation(self):
        """Fund ID and valuation date preserved."""
        engine = LiquidityAdjustedVaREngine()
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0.02"),
        )
        fund_id = 42
        val_date = date(2026, 3, 15)
        result = engine.calculate(
            fund_id=fund_id,
            valuation_date=val_date,
            portfolio_value=Decimal("1000000"),
            base_var_amount=Decimal("50000"),
            base_var_rate=Decimal("0.05"),
            assumption=assumption,
        )

        assert result.fund_id == fund_id
        assert result.valuation_date == val_date


class TestLiquidityAdjustedVaRIntegration:
    """Integration tests with realistic scenarios."""

    def test_small_spread_adjustment(self):
        """Typical bid-ask spread adjustment (1-2 bps)."""
        engine = LiquidityAdjustedVaREngine()
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0.0002"),
            methodology_label="bid-ask spread",
        )
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("50000000"),
            base_var_amount=Decimal("2000000"),
            base_var_rate=Decimal("0.04"),
            assumption=assumption,
        )

        assert result.liquidity_adjustment == Decimal("10000")
        assert abs(result.liquidity_adjusted_var_rate - Decimal("0.0402")) < Decimal("0.00001")

    def test_stressed_liquidation_cost(self):
        """High liquidation cost under stress (5-10%)."""
        engine = LiquidityAdjustedVaREngine()
        assumption = LiquidityAdjustedVaRAssumption(
            liquidity_cost_rate=Decimal("0.075"),
            methodology_label="stressed liquidation cost",
        )
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            portfolio_value=Decimal("100000000"),
            base_var_amount=Decimal("5000000"),
            base_var_rate=Decimal("0.05"),
            assumption=assumption,
        )

        assert result.liquidity_adjustment == Decimal("7500000")
        assert result.liquidity_adjusted_var_rate == Decimal("0.125")

    def test_multi_scenario_same_portfolio(self):
        """Multiple liquidity scenarios on same portfolio."""
        engine = LiquidityAdjustedVaREngine()
        portfolio_value = Decimal("50000000")
        base_var = Decimal("2500000")
        base_var_rate = Decimal("0.05")

        scenarios = [
            (Decimal("0.0001"), "tight spread"),
            (Decimal("0.002"), "normal conditions"),
            (Decimal("0.05"), "stressed liquidation"),
        ]

        results = []
        for cost_rate, label in scenarios:
            assumption = LiquidityAdjustedVaRAssumption(
                liquidity_cost_rate=cost_rate,
                methodology_label=label,
            )
            result = engine.calculate(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                portfolio_value=portfolio_value,
                base_var_amount=base_var,
                base_var_rate=base_var_rate,
                assumption=assumption,
            )
            results.append(result)

        assert results[0].liquidity_adjusted_var_rate == Decimal("0.0501")
        assert results[1].liquidity_adjusted_var_rate == Decimal("0.052")
        assert results[2].liquidity_adjusted_var_rate == Decimal("0.10")
