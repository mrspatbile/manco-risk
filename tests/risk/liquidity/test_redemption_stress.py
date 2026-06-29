"""Tests for redemption stress domain models and engine.

Tests redemption stress assumptions, results, and stress calculations.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.liquidity import (
    PortfolioLiquidityBucketSummary,
    PortfolioLiquidityProfileResult,
    RedemptionStressAssumption,
    RedemptionStressEngine,
    RedemptionStressResult,
)


class TestRedemptionStressAssumption:
    def test_valid_assumption(self):
        """Valid redemption stress assumption."""
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+0", "T+1-5"],
            redemption_shock_rate=Decimal("0.10"),
        )
        assert len(assumption.liquid_bucket_names) == 2
        assert assumption.redemption_shock_rate == Decimal("0.10")

    def test_single_liquid_bucket(self):
        """Valid assumption with single liquid bucket."""
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+0"],
            redemption_shock_rate=Decimal("0.05"),
        )
        assert assumption.liquid_bucket_names == ["T+0"]

    def test_zero_shock_rate(self):
        """Zero redemption shock is valid."""
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+0"],
            redemption_shock_rate=Decimal("0"),
        )
        assert assumption.redemption_shock_rate == Decimal("0")

    def test_full_redemption_shock(self):
        """100% redemption shock is valid."""
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+0", "T+1-5", "T+5+"],
            redemption_shock_rate=Decimal("1"),
        )
        assert assumption.redemption_shock_rate == Decimal("1")

    def test_empty_liquid_bucket_names_raises(self):
        """Empty liquid bucket list raises ValueError."""
        with pytest.raises(ValueError, match="liquid_bucket_names must contain"):
            RedemptionStressAssumption(
                liquid_bucket_names=[],
                redemption_shock_rate=Decimal("0.10"),
            )

    def test_empty_bucket_name_raises(self):
        """Empty string in bucket names raises ValueError."""
        with pytest.raises(ValueError, match="bucket names must be non-empty"):
            RedemptionStressAssumption(
                liquid_bucket_names=["T+0", ""],
                redemption_shock_rate=Decimal("0.10"),
            )

    def test_negative_shock_rate_raises(self):
        """Negative shock rate raises ValueError."""
        with pytest.raises(ValueError, match="redemption_shock_rate must be in range"):
            RedemptionStressAssumption(
                liquid_bucket_names=["T+0"],
                redemption_shock_rate=Decimal("-0.1"),
            )

    def test_shock_rate_greater_than_one_raises(self):
        """Shock rate > 1 raises ValueError."""
        with pytest.raises(ValueError, match="redemption_shock_rate must be in range"):
            RedemptionStressAssumption(
                liquid_bucket_names=["T+0"],
                redemption_shock_rate=Decimal("1.5"),
            )


class TestRedemptionStressResult:
    def test_valid_result_with_coverage(self):
        """Valid result with sufficient liquidity."""
        result = RedemptionStressResult(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            redemption_shock_rate=Decimal("0.10"),
            redemption_amount=Decimal("100000"),
            available_liquidity=Decimal("150000"),
            coverage_ratio=Decimal("1.5"),
            shortfall_amount=Decimal("0"),
            remaining_liquidity_buffer=Decimal("50000"),
            liquid_bucket_names=["T+0", "T+1-5"],
        )
        assert result.coverage_ratio == Decimal("1.5")
        assert result.shortfall_amount == Decimal("0")

    def test_valid_result_with_shortfall(self):
        """Valid result with insufficient liquidity."""
        result = RedemptionStressResult(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            redemption_shock_rate=Decimal("0.50"),
            redemption_amount=Decimal("500000"),
            available_liquidity=Decimal("300000"),
            coverage_ratio=Decimal("0.6"),
            shortfall_amount=Decimal("200000"),
            remaining_liquidity_buffer=Decimal("0"),
            liquid_bucket_names=["T+0", "T+1-5"],
        )
        assert result.coverage_ratio == Decimal("0.6")
        assert result.shortfall_amount == Decimal("200000")

    def test_valid_result_exact_coverage(self):
        """Valid result with exact coverage (ratio = 1)."""
        result = RedemptionStressResult(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            redemption_shock_rate=Decimal("0.10"),
            redemption_amount=Decimal("100000"),
            available_liquidity=Decimal("100000"),
            coverage_ratio=Decimal("1"),
            shortfall_amount=Decimal("0"),
            remaining_liquidity_buffer=Decimal("0"),
            liquid_bucket_names=["T+0"],
        )
        assert result.coverage_ratio == Decimal("1")

    def test_zero_redemption_shock(self):
        """Valid result with zero shock rate."""
        result = RedemptionStressResult(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            redemption_shock_rate=Decimal("0"),
            redemption_amount=Decimal("0"),
            available_liquidity=Decimal("1000000"),
            coverage_ratio=Decimal("0"),
            shortfall_amount=Decimal("0"),
            remaining_liquidity_buffer=Decimal("1000000"),
            liquid_bucket_names=["T+0"],
        )
        assert result.redemption_amount == Decimal("0")
        assert result.remaining_liquidity_buffer == Decimal("1000000")

    def test_negative_redemption_shock_raises(self):
        """Negative shock rate raises ValueError."""
        with pytest.raises(ValueError, match="redemption_shock_rate must be in range"):
            RedemptionStressResult(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                redemption_shock_rate=Decimal("-0.1"),
                redemption_amount=Decimal("0"),
                available_liquidity=Decimal("0"),
                coverage_ratio=Decimal("0"),
                shortfall_amount=Decimal("0"),
                remaining_liquidity_buffer=Decimal("0"),
                liquid_bucket_names=["T+0"],
            )

    def test_negative_redemption_amount_raises(self):
        """Negative redemption amount raises ValueError."""
        with pytest.raises(ValueError, match="monetary amounts must be non-negative"):
            RedemptionStressResult(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                redemption_shock_rate=Decimal("0.10"),
                redemption_amount=Decimal("-100000"),
                available_liquidity=Decimal("0"),
                coverage_ratio=Decimal("0"),
                shortfall_amount=Decimal("0"),
                remaining_liquidity_buffer=Decimal("0"),
                liquid_bucket_names=["T+0"],
            )

    def test_accounting_consistency_valid(self):
        """Shortfall and buffer values computed consistently."""
        result = RedemptionStressResult(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            redemption_shock_rate=Decimal("0.30"),
            redemption_amount=Decimal("300000"),
            available_liquidity=Decimal("200000"),
            coverage_ratio=Decimal("0.67"),
            shortfall_amount=Decimal("100000"),
            remaining_liquidity_buffer=Decimal("0"),
            liquid_bucket_names=["T+0"],
        )
        assert result.shortfall_amount == Decimal("100000")
        assert result.remaining_liquidity_buffer == Decimal("0")

    def test_accounting_consistency_zero_shock_invalid(self):
        """Zero shock with non-zero shortfall fails validation."""
        with pytest.raises(ValueError, match="If redemption_amount is 0"):
            RedemptionStressResult(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                redemption_shock_rate=Decimal("0"),
                redemption_amount=Decimal("0"),
                available_liquidity=Decimal("100000"),
                coverage_ratio=Decimal("0"),
                shortfall_amount=Decimal("1"),  # Should be 0
                remaining_liquidity_buffer=Decimal("99999"),
                liquid_bucket_names=["T+0"],
            )


class TestRedemptionStressEngine:
    @pytest.fixture
    def sample_portfolio(self):
        """Sample portfolio with three buckets."""
        return PortfolioLiquidityProfileResult(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            total_portfolio_value=Decimal("1000000"),
            bucket_summaries=[
                PortfolioLiquidityBucketSummary(
                    bucket_name="T+0",
                    total_market_value=Decimal("200000"),
                    position_count=10,
                    percentage_of_portfolio=Decimal("0.20"),
                ),
                PortfolioLiquidityBucketSummary(
                    bucket_name="T+1-5",
                    total_market_value=Decimal("300000"),
                    position_count=15,
                    percentage_of_portfolio=Decimal("0.30"),
                ),
                PortfolioLiquidityBucketSummary(
                    bucket_name="T+5+",
                    total_market_value=Decimal("500000"),
                    position_count=50,
                    percentage_of_portfolio=Decimal("0.50"),
                ),
            ],
        )

    def test_full_coverage_case(self, sample_portfolio):
        """Sufficient liquidity to cover redemption."""
        engine = RedemptionStressEngine()
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+0", "T+1-5", "T+5+"],
            redemption_shock_rate=Decimal("0.40"),
        )
        result = engine.calculate(sample_portfolio, Decimal("1000000"), assumption)

        assert result.redemption_amount == Decimal("400000")
        assert result.available_liquidity == Decimal("1000000")
        assert result.coverage_ratio == Decimal("2.5")
        assert result.shortfall_amount == Decimal("0")
        assert result.remaining_liquidity_buffer == Decimal("600000")

    def test_shortfall_case(self, sample_portfolio):
        """Insufficient liquidity to cover redemption."""
        engine = RedemptionStressEngine()
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+0"],
            redemption_shock_rate=Decimal("0.50"),
        )
        result = engine.calculate(sample_portfolio, Decimal("1000000"), assumption)

        assert result.redemption_amount == Decimal("500000")
        assert result.available_liquidity == Decimal("200000")
        assert result.coverage_ratio == Decimal("0.4")
        assert result.shortfall_amount == Decimal("300000")
        assert result.remaining_liquidity_buffer == Decimal("0")

    def test_zero_redemption_shock(self, sample_portfolio):
        """Zero redemption shock (no stress)."""
        engine = RedemptionStressEngine()
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+0"],
            redemption_shock_rate=Decimal("0"),
        )
        result = engine.calculate(sample_portfolio, Decimal("1000000"), assumption)

        assert result.redemption_amount == Decimal("0")
        assert result.coverage_ratio == Decimal("0")
        assert result.shortfall_amount == Decimal("0")
        assert result.remaining_liquidity_buffer == Decimal("200000")

    def test_full_redemption_shock(self, sample_portfolio):
        """100% redemption (full NAV redeemed)."""
        engine = RedemptionStressEngine()
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+0", "T+1-5"],
            redemption_shock_rate=Decimal("1"),
        )
        result = engine.calculate(sample_portfolio, Decimal("1000000"), assumption)

        assert result.redemption_amount == Decimal("1000000")
        assert result.available_liquidity == Decimal("500000")
        assert result.coverage_ratio == Decimal("0.5")
        assert result.shortfall_amount == Decimal("500000")

    def test_partial_liquid_buckets(self, sample_portfolio):
        """Only subset of buckets considered liquid."""
        engine = RedemptionStressEngine()
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+0", "T+1-5"],
            redemption_shock_rate=Decimal("0.40"),
        )
        result = engine.calculate(sample_portfolio, Decimal("1000000"), assumption)

        assert result.redemption_amount == Decimal("400000")
        assert result.available_liquidity == Decimal("500000")
        assert result.coverage_ratio == Decimal("1.25")
        assert result.shortfall_amount == Decimal("0")
        assert result.remaining_liquidity_buffer == Decimal("100000")

    def test_single_liquid_bucket(self, sample_portfolio):
        """Only T+5+ considered liquid."""
        engine = RedemptionStressEngine()
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+5+"],
            redemption_shock_rate=Decimal("0.30"),
        )
        result = engine.calculate(sample_portfolio, Decimal("1000000"), assumption)

        assert result.redemption_amount == Decimal("300000")
        assert result.available_liquidity == Decimal("500000")
        assert abs(result.coverage_ratio - Decimal("1.67")) < Decimal("0.01")

    def test_unknown_liquid_bucket_raises(self, sample_portfolio):
        """Reference to unknown bucket raises ValueError."""
        engine = RedemptionStressEngine()
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+0", "Unknown"],
            redemption_shock_rate=Decimal("0.10"),
        )
        with pytest.raises(ValueError, match="not found in portfolio profile"):
            engine.calculate(sample_portfolio, Decimal("1000000"), assumption)

    def test_zero_nav(self, sample_portfolio):
        """Zero NAV results in zero redemption amount."""
        engine = RedemptionStressEngine()
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+0", "T+1-5"],
            redemption_shock_rate=Decimal("0.50"),
        )
        result = engine.calculate(sample_portfolio, Decimal("0"), assumption)

        assert result.redemption_amount == Decimal("0")
        assert result.coverage_ratio == Decimal("0")
        assert result.shortfall_amount == Decimal("0")
        assert result.remaining_liquidity_buffer == Decimal("500000")

    def test_no_liquid_buckets_assumption_raises(self):
        """Empty liquid bucket list raises ValueError in assumption."""
        with pytest.raises(ValueError, match="liquid_bucket_names must contain"):
            RedemptionStressAssumption(
                liquid_bucket_names=[],
                redemption_shock_rate=Decimal("0.10"),
            )

    def test_very_small_redemption_shock(self, sample_portfolio):
        """Very small redemption shock."""
        engine = RedemptionStressEngine()
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+0"],
            redemption_shock_rate=Decimal("0.001"),
        )
        result = engine.calculate(sample_portfolio, Decimal("1000000"), assumption)

        assert result.redemption_amount == Decimal("1000")
        assert result.coverage_ratio == Decimal("200")

    def test_preserves_fund_metadata(self, sample_portfolio):
        """Result preserves fund ID and valuation date."""
        engine = RedemptionStressEngine()
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=["T+0"],
            redemption_shock_rate=Decimal("0.10"),
        )
        result = engine.calculate(sample_portfolio, Decimal("1000000"), assumption)

        assert result.fund_id == 1
        assert result.valuation_date == date(2026, 6, 30)

    def test_preserves_assumption_metadata(self, sample_portfolio):
        """Result preserves liquid bucket names from assumption."""
        engine = RedemptionStressEngine()
        liquid_buckets = ["T+0", "T+1-5"]
        assumption = RedemptionStressAssumption(
            liquid_bucket_names=liquid_buckets,
            redemption_shock_rate=Decimal("0.10"),
        )
        result = engine.calculate(sample_portfolio, Decimal("1000000"), assumption)

        assert result.liquid_bucket_names == liquid_buckets


class TestRedemptionStressIntegration:
    """Integration tests combining liquidity profile with stress scenarios."""

    def test_stress_multiple_scenarios_same_portfolio(self):
        """Multiple stress scenarios on same portfolio."""
        portfolio = PortfolioLiquidityProfileResult(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            total_portfolio_value=Decimal("1000000"),
            bucket_summaries=[
                PortfolioLiquidityBucketSummary(
                    bucket_name="T+0",
                    total_market_value=Decimal("100000"),
                    position_count=5,
                    percentage_of_portfolio=Decimal("0.10"),
                ),
                PortfolioLiquidityBucketSummary(
                    bucket_name="T+1-5",
                    total_market_value=Decimal("400000"),
                    position_count=20,
                    percentage_of_portfolio=Decimal("0.40"),
                ),
                PortfolioLiquidityBucketSummary(
                    bucket_name="T+5+",
                    total_market_value=Decimal("500000"),
                    position_count=50,
                    percentage_of_portfolio=Decimal("0.50"),
                ),
            ],
        )

        engine = RedemptionStressEngine()
        nav = Decimal("1000000")

        scenarios = [
            (["T+0", "T+1-5", "T+5+"], Decimal("0.10"), "Conservative (10% shock, all liquid)"),
            (["T+0", "T+1-5"], Decimal("0.30"), "Moderate (30% shock, T+0 & T+1-5)"),
            (["T+0"], Decimal("0.50"), "Stress (50% shock, T+0 only)"),
        ]

        for liquid_buckets, shock_rate, scenario_name in scenarios:
            assumption = RedemptionStressAssumption(
                liquid_bucket_names=liquid_buckets,
                redemption_shock_rate=shock_rate,
            )
            result = engine.calculate(portfolio, nav, assumption)

            if scenario_name == "Conservative (10% shock, all liquid)":
                assert result.coverage_ratio == Decimal("10")
                assert result.shortfall_amount == Decimal("0")

            elif scenario_name == "Moderate (30% shock, T+0 & T+1-5)":
                assert result.redemption_amount == Decimal("300000")
                assert result.available_liquidity == Decimal("500000")
                assert abs(result.coverage_ratio - Decimal("1.67")) < Decimal("0.01")

            elif scenario_name == "Stress (50% shock, T+0 only)":
                assert result.redemption_amount == Decimal("500000")
                assert result.available_liquidity == Decimal("100000")
                assert result.coverage_ratio == Decimal("0.2")
