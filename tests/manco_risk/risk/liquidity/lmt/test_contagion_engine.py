"""Tests for contagion linkage engine."""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.liquidity.lmt.contagion_engine import ContagionEngine
from manco_risk.risk.liquidity.lmt.models import ContagionConfig, LiquiditySnapshot
from manco_risk.risk.liquidity.models import (
    PortfolioLiquidityBucketSummary,
    PortfolioLiquidityProfileResult,
)


class TestContagionEngineDisabled:
    """Tests for disabled contagion."""

    def test_disabled_contagion_returns_false(self):
        """Disabled contagion should never trigger."""
        engine = ContagionEngine()
        config = ContagionConfig(
            enabled=False,
            contagion_trigger_threshold=Decimal("0.8"),
            contagion_multiplier=Decimal("1.2"),
        )

        # Even with linked snapshots, should return False
        linked_snapshots = {
            "fund_002": [
                LiquiditySnapshot(
                    valuation_date=date(2026, 1, 1),
                    fund_nav=Decimal("50000000"),
                    available_liquidity=Decimal("1000000"),
                    coverage_ratio=Decimal("0.05"),  # Far below threshold
                    portfolio_liquidity_profile=PortfolioLiquidityProfileResult(
                        fund_id=2,
                        valuation_date=date(2026, 1, 1),
                        total_portfolio_value=Decimal("50000000"),
                        bucket_summaries=[
                            PortfolioLiquidityBucketSummary(
                                bucket_name="liquid",
                                total_market_value=Decimal("1000000"),
                                position_count=10,
                                percentage_of_portfolio=Decimal("1.0"),
                            )
                        ],
                    ),
                    investor_concentration=None,
                )
            ]
            * 12
        }

        result = engine.calculate(linked_snapshots, 0, config)
        assert result is False


class TestContagionEngineNoLinkedSnapshots:
    """Tests for missing linked snapshot data."""

    def test_no_linked_snapshots_returns_false(self):
        """No linked snapshots provided should return False."""
        engine = ContagionEngine()
        config = ContagionConfig(
            enabled=True,
            contagion_trigger_threshold=Decimal("0.8"),
            contagion_multiplier=Decimal("1.2"),
        )

        result = engine.calculate(None, 0, config)
        assert result is False

    def test_empty_linked_snapshots_dict_returns_false(self):
        """Empty linked snapshots dict should return False."""
        engine = ContagionEngine()
        config = ContagionConfig(
            enabled=True,
            contagion_trigger_threshold=Decimal("0.8"),
            contagion_multiplier=Decimal("1.2"),
        )

        result = engine.calculate({}, 0, config)
        assert result is False


class TestContagionEngineAboveThreshold:
    """Tests for linked funds above threshold."""

    def test_linked_fund_above_threshold_no_trigger(self):
        """Linked fund above threshold should not trigger contagion."""
        engine = ContagionEngine()
        config = ContagionConfig(
            enabled=True,
            contagion_trigger_threshold=Decimal("0.8"),
            contagion_multiplier=Decimal("1.2"),
        )

        # Linked fund with coverage ratio above threshold
        linked_snapshots = {
            "fund_002": [
                LiquiditySnapshot(
                    valuation_date=date(2026, 1, 1),
                    fund_nav=Decimal("100000000"),
                    available_liquidity=Decimal("85000000"),
                    coverage_ratio=Decimal("0.85"),  # Above threshold
                    portfolio_liquidity_profile=PortfolioLiquidityProfileResult(
                        fund_id=2,
                        valuation_date=date(2026, 1, 1),
                        total_portfolio_value=Decimal("100000000"),
                        bucket_summaries=[
                            PortfolioLiquidityBucketSummary(
                                bucket_name="liquid",
                                total_market_value=Decimal("85000000"),
                                position_count=100,
                                percentage_of_portfolio=Decimal("1.0"),
                            )
                        ],
                    ),
                    investor_concentration=None,
                )
            ]
            * 12
        }

        result = engine.calculate(linked_snapshots, 0, config)
        assert result is False


class TestContagionEngineBelowThreshold:
    """Tests for linked funds below threshold."""

    def test_linked_fund_below_threshold_triggers(self):
        """Linked fund below threshold should trigger contagion."""
        engine = ContagionEngine()
        config = ContagionConfig(
            enabled=True,
            contagion_trigger_threshold=Decimal("0.8"),
            contagion_multiplier=Decimal("1.2"),
        )

        # Linked fund with coverage ratio below threshold
        linked_snapshots = {
            "fund_002": [
                LiquiditySnapshot(
                    valuation_date=date(2026, 1, 1),
                    fund_nav=Decimal("100000000"),
                    available_liquidity=Decimal("75000000"),
                    coverage_ratio=Decimal("0.75"),  # Below threshold
                    portfolio_liquidity_profile=PortfolioLiquidityProfileResult(
                        fund_id=2,
                        valuation_date=date(2026, 1, 1),
                        total_portfolio_value=Decimal("100000000"),
                        bucket_summaries=[
                            PortfolioLiquidityBucketSummary(
                                bucket_name="liquid",
                                total_market_value=Decimal("75000000"),
                                position_count=100,
                                percentage_of_portfolio=Decimal("1.0"),
                            )
                        ],
                    ),
                    investor_concentration=None,
                )
            ]
            * 12
        }

        result = engine.calculate(linked_snapshots, 0, config)
        assert result is True

    def test_at_threshold_boundary(self):
        """Coverage ratio at threshold should not trigger."""
        engine = ContagionEngine()
        config = ContagionConfig(
            enabled=True,
            contagion_trigger_threshold=Decimal("0.8"),
            contagion_multiplier=Decimal("1.2"),
        )

        linked_snapshots = {
            "fund_002": [
                LiquiditySnapshot(
                    valuation_date=date(2026, 1, 1),
                    fund_nav=Decimal("100000000"),
                    available_liquidity=Decimal("80000000"),
                    coverage_ratio=Decimal("0.8"),  # Exactly at threshold
                    portfolio_liquidity_profile=PortfolioLiquidityProfileResult(
                        fund_id=2,
                        valuation_date=date(2026, 1, 1),
                        total_portfolio_value=Decimal("100000000"),
                        bucket_summaries=[
                            PortfolioLiquidityBucketSummary(
                                bucket_name="liquid",
                                total_market_value=Decimal("80000000"),
                                position_count=100,
                                percentage_of_portfolio=Decimal("1.0"),
                            )
                        ],
                    ),
                    investor_concentration=None,
                )
            ]
            * 12
        }

        result = engine.calculate(linked_snapshots, 0, config)
        assert result is False


class TestContagionEngineMultipleLinkedFunds:
    """Tests for multiple linked funds."""

    def test_one_linked_fund_below_threshold_triggers(self):
        """If any linked fund is below threshold, contagion triggers."""
        engine = ContagionEngine()
        config = ContagionConfig(
            enabled=True,
            contagion_trigger_threshold=Decimal("0.8"),
            contagion_multiplier=Decimal("1.2"),
        )

        linked_snapshots = {
            "fund_002": [  # Above threshold
                LiquiditySnapshot(
                    valuation_date=date(2026, 1, 1),
                    fund_nav=Decimal("100000000"),
                    available_liquidity=Decimal("90000000"),
                    coverage_ratio=Decimal("0.9"),
                    portfolio_liquidity_profile=PortfolioLiquidityProfileResult(
                        fund_id=2,
                        valuation_date=date(2026, 1, 1),
                        total_portfolio_value=Decimal("100000000"),
                        bucket_summaries=[
                            PortfolioLiquidityBucketSummary(
                                bucket_name="liquid",
                                total_market_value=Decimal("90000000"),
                                position_count=100,
                                percentage_of_portfolio=Decimal("1.0"),
                            )
                        ],
                    ),
                    investor_concentration=None,
                )
            ]
            * 12,
            "fund_003": [  # Below threshold
                LiquiditySnapshot(
                    valuation_date=date(2026, 1, 1),
                    fund_nav=Decimal("50000000"),
                    available_liquidity=Decimal("30000000"),
                    coverage_ratio=Decimal("0.6"),
                    portfolio_liquidity_profile=PortfolioLiquidityProfileResult(
                        fund_id=3,
                        valuation_date=date(2026, 1, 1),
                        total_portfolio_value=Decimal("50000000"),
                        bucket_summaries=[
                            PortfolioLiquidityBucketSummary(
                                bucket_name="liquid",
                                total_market_value=Decimal("30000000"),
                                position_count=50,
                                percentage_of_portfolio=Decimal("1.0"),
                            )
                        ],
                    ),
                    investor_concentration=None,
                )
            ]
            * 12,
        }

        result = engine.calculate(linked_snapshots, 0, config)
        assert result is True

    def test_all_linked_funds_above_threshold_no_trigger(self):
        """All linked funds above threshold should not trigger."""
        engine = ContagionEngine()
        config = ContagionConfig(
            enabled=True,
            contagion_trigger_threshold=Decimal("0.8"),
            contagion_multiplier=Decimal("1.2"),
        )

        linked_snapshots = {
            "fund_002": [
                LiquiditySnapshot(
                    valuation_date=date(2026, 1, 1),
                    fund_nav=Decimal("100000000"),
                    available_liquidity=Decimal("85000000"),
                    coverage_ratio=Decimal("0.85"),
                    portfolio_liquidity_profile=PortfolioLiquidityProfileResult(
                        fund_id=2,
                        valuation_date=date(2026, 1, 1),
                        total_portfolio_value=Decimal("100000000"),
                        bucket_summaries=[
                            PortfolioLiquidityBucketSummary(
                                bucket_name="liquid",
                                total_market_value=Decimal("85000000"),
                                position_count=100,
                                percentage_of_portfolio=Decimal("1.0"),
                            )
                        ],
                    ),
                    investor_concentration=None,
                )
            ]
            * 12,
            "fund_003": [
                LiquiditySnapshot(
                    valuation_date=date(2026, 1, 1),
                    fund_nav=Decimal("50000000"),
                    available_liquidity=Decimal("42000000"),
                    coverage_ratio=Decimal("0.84"),
                    portfolio_liquidity_profile=PortfolioLiquidityProfileResult(
                        fund_id=3,
                        valuation_date=date(2026, 1, 1),
                        total_portfolio_value=Decimal("50000000"),
                        bucket_summaries=[
                            PortfolioLiquidityBucketSummary(
                                bucket_name="liquid",
                                total_market_value=Decimal("42000000"),
                                position_count=50,
                                percentage_of_portfolio=Decimal("1.0"),
                            )
                        ],
                    ),
                    investor_concentration=None,
                )
            ]
            * 12,
        }

        result = engine.calculate(linked_snapshots, 0, config)
        assert result is False


class TestContagionEngineMonthIndexValidation:
    """Tests for month index validation."""

    def test_negative_month_index_raises_error(self):
        """Negative month index should raise ValueError."""
        engine = ContagionEngine()
        config = ContagionConfig(
            enabled=True,
            contagion_trigger_threshold=Decimal("0.8"),
            contagion_multiplier=Decimal("1.2"),
        )

        with pytest.raises(ValueError, match="must be in range"):
            engine.calculate({}, -1, config)

    def test_month_index_12_raises_error(self):
        """Month index 12 (out of range) should raise ValueError."""
        engine = ContagionEngine()
        config = ContagionConfig(
            enabled=True,
            contagion_trigger_threshold=Decimal("0.8"),
            contagion_multiplier=Decimal("1.2"),
        )

        linked_snapshots = {"fund_002": [None] * 12}  # type: ignore

        with pytest.raises(ValueError, match="must be in range"):
            engine.calculate(linked_snapshots, 12, config)

    def test_all_valid_month_indices_accepted(self):
        """Month indices 0-11 should all be accepted."""
        engine = ContagionEngine()
        config = ContagionConfig(
            enabled=False,  # Disabled, so no error from snapshots
            contagion_trigger_threshold=Decimal("0.8"),
            contagion_multiplier=Decimal("1.2"),
        )

        for month in range(12):
            result = engine.calculate(None, month, config)
            assert result is False


class TestContagionEngineMultiplierImpact:
    """Tests for multiplier impact calculation."""

    def test_calculate_multiplier_impact(self):
        """Calculate multiplier impact correctly."""
        base_redemption = Decimal("5000000")
        multiplier = Decimal("1.2")

        impact = ContagionEngine.calculate_multiplier_impact(base_redemption, multiplier)

        # 1.2x means 20% increase = 5M * 0.2 = 1M
        assert impact == Decimal("1000000")

    def test_multiplier_1_0_no_impact(self):
        """Multiplier of 1.0 should have no impact."""
        base_redemption = Decimal("5000000")
        multiplier = Decimal("1.0")

        impact = ContagionEngine.calculate_multiplier_impact(base_redemption, multiplier)

        assert impact == Decimal("0")

    def test_multiplier_below_1_0_raises_error(self):
        """Multiplier below 1.0 should raise ValueError."""
        base_redemption = Decimal("5000000")
        multiplier = Decimal("0.9")

        with pytest.raises(ValueError, match="must be >= 1.0"):
            ContagionEngine.calculate_multiplier_impact(base_redemption, multiplier)


class TestContagionEngineMonthSpecific:
    """Tests for month-specific contagion checking."""

    def test_contagion_checked_for_specific_month(self):
        """Contagion should be evaluated for the specified month."""
        engine = ContagionEngine()
        config = ContagionConfig(
            enabled=True,
            contagion_trigger_threshold=Decimal("0.8"),
            contagion_multiplier=Decimal("1.2"),
        )

        # Create snapshots with varying coverage ratios
        snapshots = []
        for month in range(12):
            # Month 0-5: above threshold, Month 6-11: below threshold
            coverage = Decimal("0.9") if month < 6 else Decimal("0.7")
            snapshots.append(
                LiquiditySnapshot(
                    valuation_date=date(2026, month % 12 + 1, 1),
                    fund_nav=Decimal("100000000"),
                    available_liquidity=Decimal("50000000"),
                    coverage_ratio=coverage,
                    portfolio_liquidity_profile=PortfolioLiquidityProfileResult(
                        fund_id=2,
                        valuation_date=date(2026, month % 12 + 1, 1),
                        total_portfolio_value=Decimal("100000000"),
                        bucket_summaries=[
                            PortfolioLiquidityBucketSummary(
                                bucket_name="liquid",
                                total_market_value=Decimal("50000000"),
                                position_count=100,
                                percentage_of_portfolio=Decimal("1.0"),
                            )
                        ],
                    ),
                    investor_concentration=None,
                )
            )

        linked_snapshots = {"fund_002": snapshots}

        # Months 0-5 should not trigger
        for month in range(6):
            result = engine.calculate(linked_snapshots, month, config)
            assert result is False

        # Months 6-11 should trigger
        for month in range(6, 12):
            result = engine.calculate(linked_snapshots, month, config)
            assert result is True
