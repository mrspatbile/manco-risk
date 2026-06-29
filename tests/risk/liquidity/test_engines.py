"""Tests for liquidity calculation engines.

Tests TTL calculation, bucket classification, and portfolio aggregation.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.liquidity import (
    BucketClassificationEngine,
    LiquidationAssumptionSet,
    LiquidationCapacityAssumption,
    LiquidityBucketClassification,
    LiquidityBucketDefinition,
    LiquidityBucketScheme,
    PortfolioLiquidityProfileEngine,
    PositionLiquidityInput,
    TimeToLiquidateEngine,
)


class TestTimeToLiquidateEngine:
    @pytest.fixture
    def basic_assumptions(self):
        """Standard liquidation assumptions for testing."""
        scheme = LiquidityBucketScheme(
            buckets=[
                LiquidityBucketDefinition(name="T+0", min_days=0, max_days=0),
                LiquidityBucketDefinition(name="T+1-5", min_days=1, max_days=5),
                LiquidityBucketDefinition(name="T+5+", min_days=6, max_days=None),
            ]
        )
        capacity_assumptions = [
            LiquidationCapacityAssumption(
                asset_class="Equities", market_value_per_day=Decimal("100000")
            ),
            LiquidationCapacityAssumption(
                asset_class="Bonds", market_value_per_day=Decimal("50000")
            ),
        ]
        return LiquidationAssumptionSet(
            bucket_scheme=scheme, capacity_assumptions=capacity_assumptions
        )

    def test_ttl_basic_calculation(self, basic_assumptions):
        """Test basic TTL calculation: 2 day position."""
        engine = TimeToLiquidateEngine()
        position = PositionLiquidityInput(
            position_id=1,
            isin="US0378331005",
            asset_class="Equities",
            market_value=Decimal("200000"),
        )
        result = engine.calculate(position, basic_assumptions)
        assert result.position_id == 1
        assert result.market_value == Decimal("200000")
        assert result.days_to_liquidate == Decimal("2")
        assert result.liquidation_capacity_per_day == Decimal("100000")

    def test_ttl_zero_market_value(self, basic_assumptions):
        """TTL of zero for zero market value."""
        engine = TimeToLiquidateEngine()
        position = PositionLiquidityInput(
            position_id=1,
            isin=None,
            asset_class="Equities",
            market_value=Decimal("0"),
        )
        result = engine.calculate(position, basic_assumptions)
        assert result.market_value == Decimal("0")
        assert result.days_to_liquidate == Decimal("0")

    def test_ttl_fractional_days(self, basic_assumptions):
        """TTL with fractional days."""
        engine = TimeToLiquidateEngine()
        position = PositionLiquidityInput(
            position_id=1,
            isin=None,
            asset_class="Equities",
            market_value=Decimal("50000"),
        )
        result = engine.calculate(position, basic_assumptions)
        assert result.days_to_liquidate == Decimal("0.5")

    def test_ttl_very_small_position(self, basic_assumptions):
        """TTL for very small position."""
        engine = TimeToLiquidateEngine()
        position = PositionLiquidityInput(
            position_id=1,
            isin=None,
            asset_class="Equities",
            market_value=Decimal("1000"),
        )
        result = engine.calculate(position, basic_assumptions)
        assert result.days_to_liquidate == Decimal("0.01")

    def test_ttl_large_position_multiple_days(self, basic_assumptions):
        """TTL for large position exceeding one day capacity."""
        engine = TimeToLiquidateEngine()
        position = PositionLiquidityInput(
            position_id=1,
            isin=None,
            asset_class="Equities",
            market_value=Decimal("500000"),
        )
        result = engine.calculate(position, basic_assumptions)
        assert result.days_to_liquidate == Decimal("5")

    def test_ttl_bonds_different_capacity(self, basic_assumptions):
        """TTL respects different capacity for different asset class."""
        engine = TimeToLiquidateEngine()
        position = PositionLiquidityInput(
            position_id=1,
            isin=None,
            asset_class="Bonds",
            market_value=Decimal("100000"),
        )
        result = engine.calculate(position, basic_assumptions)
        assert result.days_to_liquidate == Decimal("2")
        assert result.liquidation_capacity_per_day == Decimal("50000")

    def test_ttl_missing_capacity_raises(self, basic_assumptions):
        """TTL raises ValueError if asset class not in assumptions."""
        engine = TimeToLiquidateEngine()
        position = PositionLiquidityInput(
            position_id=1,
            isin=None,
            asset_class="Derivatives",
            market_value=Decimal("100000"),
        )
        with pytest.raises(ValueError, match="No liquidation capacity assumption found"):
            engine.calculate(position, basic_assumptions)

    def test_ttl_preserves_isin(self, basic_assumptions):
        """TTL result preserves ISIN from input."""
        engine = TimeToLiquidateEngine()
        position = PositionLiquidityInput(
            position_id=1,
            isin="US0378331005",
            asset_class="Equities",
            market_value=Decimal("100000"),
        )
        result = engine.calculate(position, basic_assumptions)
        assert result.isin == "US0378331005"

    def test_ttl_none_isin(self, basic_assumptions):
        """TTL result preserves None ISIN."""
        engine = TimeToLiquidateEngine()
        position = PositionLiquidityInput(
            position_id=1,
            isin=None,
            asset_class="Equities",
            market_value=Decimal("100000"),
        )
        result = engine.calculate(position, basic_assumptions)
        assert result.isin is None


class TestBucketClassificationEngine:
    @pytest.fixture
    def bucket_scheme(self):
        """Standard bucket scheme for testing."""
        return LiquidityBucketScheme(
            buckets=[
                LiquidityBucketDefinition(name="T+0", min_days=0, max_days=0),
                LiquidityBucketDefinition(name="T+1-5", min_days=1, max_days=5),
                LiquidityBucketDefinition(name="T+5+", min_days=6, max_days=None),
            ]
        )

    def test_classify_exact_lower_boundary(self, bucket_scheme):
        """Classification at exact lower boundary of bucket."""
        engine = BucketClassificationEngine()
        ttl_result = self._make_ttl_result(days=Decimal("1"))
        classification = engine.classify(ttl_result, bucket_scheme)
        assert classification.bucket_name == "T+1-5"

    def test_classify_exact_upper_boundary(self, bucket_scheme):
        """Classification at exact upper boundary of bucket."""
        engine = BucketClassificationEngine()
        ttl_result = self._make_ttl_result(days=Decimal("5"))
        classification = engine.classify(ttl_result, bucket_scheme)
        assert classification.bucket_name == "T+1-5"

    def test_classify_zero_days_to_t_plus_0(self, bucket_scheme):
        """TTL of 0 classifies to T+0."""
        engine = BucketClassificationEngine()
        ttl_result = self._make_ttl_result(days=Decimal("0"))
        classification = engine.classify(ttl_result, bucket_scheme)
        assert classification.bucket_name == "T+0"

    def test_classify_unbounded_bucket(self, bucket_scheme):
        """Very large TTL classifies to unbounded T+5+ bucket."""
        engine = BucketClassificationEngine()
        ttl_result = self._make_ttl_result(days=Decimal("1000"))
        classification = engine.classify(ttl_result, bucket_scheme)
        assert classification.bucket_name == "T+5+"

    def test_classify_boundary_between_buckets_raises(self, bucket_scheme):
        """TTL in gap between buckets raises ValueError (scheme has gaps by design)."""
        engine = BucketClassificationEngine()
        ttl_result = self._make_ttl_result(days=Decimal("0.9"))
        with pytest.raises(ValueError, match="does not fall into any bucket"):
            engine.classify(ttl_result, bucket_scheme)

    def test_classify_boundary_just_above_t_plus_5(self, bucket_scheme):
        """TTL just at start of T+5+ bucket (6.0)."""
        engine = BucketClassificationEngine()
        ttl_result = self._make_ttl_result(days=Decimal("6.0"))
        classification = engine.classify(ttl_result, bucket_scheme)
        assert classification.bucket_name == "T+5+"

    def test_classify_fractional_days_in_middle(self, bucket_scheme):
        """Fractional TTL in middle of bucket."""
        engine = BucketClassificationEngine()
        ttl_result = self._make_ttl_result(days=Decimal("2.5"))
        classification = engine.classify(ttl_result, bucket_scheme)
        assert classification.bucket_name == "T+1-5"

    def test_classify_preserves_position_metadata(self, bucket_scheme):
        """Classification preserves position ID, ISIN, asset class."""
        engine = BucketClassificationEngine()
        ttl_result = self._make_ttl_result(
            position_id=99,
            isin="US0378331005",
            asset_class="Equities",
            days=Decimal("2"),
        )
        classification = engine.classify(ttl_result, bucket_scheme)
        assert classification.position_id == 99
        assert classification.isin == "US0378331005"
        assert classification.asset_class == "Equities"

    def test_classify_outside_all_buckets_above_raises(self, bucket_scheme):
        """TTL outside all bucket ranges (very large) stays in unbounded bucket."""
        engine = BucketClassificationEngine()
        ttl_result = self._make_ttl_result(days=Decimal("9999"))
        classification = engine.classify(ttl_result, bucket_scheme)
        assert classification.bucket_name == "T+5+"

    @staticmethod
    def _make_ttl_result(
        position_id=1,
        isin=None,
        asset_class="Equities",
        days=Decimal("0"),
    ):
        """Helper to create TTL result for testing."""
        from manco_risk.risk.liquidity import TimeToLiquidateResult

        return TimeToLiquidateResult(
            position_id=position_id,
            isin=isin,
            asset_class=asset_class,
            market_value=Decimal("100000"),
            days_to_liquidate=days,
            liquidation_capacity_per_day=Decimal("50000"),
        )


class TestPortfolioLiquidityProfileEngine:
    @pytest.fixture
    def bucket_scheme(self):
        """Standard bucket scheme for testing."""
        return LiquidityBucketScheme(
            buckets=[
                LiquidityBucketDefinition(name="T+0", min_days=0, max_days=0),
                LiquidityBucketDefinition(name="T+1-5", min_days=1, max_days=5),
                LiquidityBucketDefinition(name="T+5+", min_days=6, max_days=None),
            ]
        )

    def test_portfolio_single_bucket(self, bucket_scheme):
        """Portfolio with all positions in one bucket."""
        engine = PortfolioLiquidityProfileEngine()
        classifications = [
            self._make_classification(bucket="T+0", market_value=Decimal("100000")),
            self._make_classification(bucket="T+0", market_value=Decimal("200000")),
        ]
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            classifications=classifications,
            bucket_scheme=bucket_scheme,
        )
        assert result.total_portfolio_value == Decimal("300000")
        t_plus_0 = result.bucket_summaries[0]
        assert t_plus_0.bucket_name == "T+0"
        assert t_plus_0.total_market_value == Decimal("300000")
        assert t_plus_0.position_count == 2
        assert t_plus_0.percentage_of_portfolio == Decimal("1")

    def test_portfolio_multi_bucket_aggregation(self, bucket_scheme):
        """Portfolio with positions distributed across buckets."""
        engine = PortfolioLiquidityProfileEngine()
        classifications = [
            self._make_classification(bucket="T+0", market_value=Decimal("100000")),
            self._make_classification(bucket="T+1-5", market_value=Decimal("200000")),
            self._make_classification(bucket="T+5+", market_value=Decimal("700000")),
        ]
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            classifications=classifications,
            bucket_scheme=bucket_scheme,
        )
        assert result.total_portfolio_value == Decimal("1000000")
        assert len(result.bucket_summaries) == 3

        t_plus_0 = result.bucket_summaries[0]
        assert t_plus_0.percentage_of_portfolio == Decimal("0.1")

        t_plus_1_5 = result.bucket_summaries[1]
        assert t_plus_1_5.percentage_of_portfolio == Decimal("0.2")

        t_plus_5_plus = result.bucket_summaries[2]
        assert t_plus_5_plus.percentage_of_portfolio == Decimal("0.7")

    def test_portfolio_empty_bucket_retained(self, bucket_scheme):
        """Empty buckets from scheme are included in profile."""
        engine = PortfolioLiquidityProfileEngine()
        classifications = [
            self._make_classification(bucket="T+0", market_value=Decimal("500000")),
        ]
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            classifications=classifications,
            bucket_scheme=bucket_scheme,
        )
        assert len(result.bucket_summaries) == 3

        t_plus_0 = result.bucket_summaries[0]
        assert t_plus_0.total_market_value == Decimal("500000")
        assert t_plus_0.position_count == 1

        t_plus_1_5 = result.bucket_summaries[1]
        assert t_plus_1_5.total_market_value == Decimal("0")
        assert t_plus_1_5.position_count == 0

    def test_portfolio_percentages_sum_to_one(self, bucket_scheme):
        """Portfolio percentages sum to 1.0."""
        engine = PortfolioLiquidityProfileEngine()
        classifications = [
            self._make_classification(position_id=1, bucket="T+0", market_value=Decimal("333333")),
            self._make_classification(
                position_id=2, bucket="T+1-5", market_value=Decimal("333333")
            ),
            self._make_classification(position_id=3, bucket="T+5+", market_value=Decimal("333334")),
        ]
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            classifications=classifications,
            bucket_scheme=bucket_scheme,
        )
        total_pct = sum(s.percentage_of_portfolio for s in result.bucket_summaries)
        assert abs(total_pct - Decimal("1")) < Decimal("0.0001")

    def test_portfolio_zero_value_positions(self, bucket_scheme):
        """Portfolio with zero-value positions."""
        engine = PortfolioLiquidityProfileEngine()
        classifications = [
            self._make_classification(bucket="T+0", market_value=Decimal("0")),
            self._make_classification(bucket="T+0", market_value=Decimal("100000")),
        ]
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            classifications=classifications,
            bucket_scheme=bucket_scheme,
        )
        assert result.total_portfolio_value == Decimal("100000")
        t_plus_0 = result.bucket_summaries[0]
        assert t_plus_0.total_market_value == Decimal("100000")
        assert t_plus_0.position_count == 2

    def test_portfolio_zero_total_value_all_zero_positions(self, bucket_scheme):
        """Portfolio with zero total value."""
        engine = PortfolioLiquidityProfileEngine()
        classifications = [
            self._make_classification(bucket="T+0", market_value=Decimal("0")),
        ]
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            classifications=classifications,
            bucket_scheme=bucket_scheme,
        )
        assert result.total_portfolio_value == Decimal("0")
        t_plus_0 = result.bucket_summaries[0]
        assert t_plus_0.percentage_of_portfolio == Decimal("0")

    def test_portfolio_empty_classifications_list(self, bucket_scheme):
        """Portfolio with no classifications produces zero portfolio."""
        engine = PortfolioLiquidityProfileEngine()
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            classifications=[],
            bucket_scheme=bucket_scheme,
        )
        assert result.total_portfolio_value == Decimal("0")
        assert all(s.total_market_value == Decimal("0") for s in result.bucket_summaries)
        assert all(s.position_count == 0 for s in result.bucket_summaries)

    def test_portfolio_unknown_bucket_raises(self, bucket_scheme):
        """Classification referencing unknown bucket raises ValueError."""
        engine = PortfolioLiquidityProfileEngine()
        classifications = [
            self._make_classification(bucket="Unknown", market_value=Decimal("100000")),
        ]
        with pytest.raises(ValueError, match="unknown bucket"):
            engine.calculate(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                classifications=classifications,
                bucket_scheme=bucket_scheme,
            )

    def test_portfolio_preserves_fund_id_and_date(self, bucket_scheme):
        """Portfolio result preserves fund ID and valuation date."""
        engine = PortfolioLiquidityProfileEngine()
        fund_id = 42
        val_date = date(2026, 3, 15)
        result = engine.calculate(
            fund_id=fund_id,
            valuation_date=val_date,
            classifications=[],
            bucket_scheme=bucket_scheme,
        )
        assert result.fund_id == fund_id
        assert result.valuation_date == val_date

    @staticmethod
    def _make_classification(
        position_id=1,
        bucket="T+0",
        market_value=Decimal("100000"),
    ):
        """Helper to create classification for testing."""
        return LiquidityBucketClassification(
            position_id=position_id,
            isin=None,
            asset_class="Equities",
            market_value=market_value,
            days_to_liquidate=Decimal("0"),
            bucket_name=bucket,
        )


class TestEngineIntegration:
    """Integration tests combining multiple engines."""

    def test_ttl_then_classify_then_profile(self):
        """Full workflow: TTL → classify → portfolio profile."""
        scheme = LiquidityBucketScheme(
            buckets=[
                LiquidityBucketDefinition(name="T+0", min_days=0, max_days=0),
                LiquidityBucketDefinition(name="T+1-5", min_days=1, max_days=5),
                LiquidityBucketDefinition(name="T+5+", min_days=6, max_days=None),
            ]
        )
        assumptions = LiquidationAssumptionSet(
            bucket_scheme=scheme,
            capacity_assumptions=[
                LiquidationCapacityAssumption(
                    asset_class="Equities", market_value_per_day=Decimal("100000")
                )
            ],
        )

        ttl_engine = TimeToLiquidateEngine()
        bucket_engine = BucketClassificationEngine()
        profile_engine = PortfolioLiquidityProfileEngine()

        positions = [
            PositionLiquidityInput(
                position_id=1,
                isin=None,
                asset_class="Equities",
                market_value=Decimal("0"),  # 0 days -> T+0
            ),
            PositionLiquidityInput(
                position_id=2,
                isin=None,
                asset_class="Equities",
                market_value=Decimal("300000"),  # 3 days -> T+1-5
            ),
            PositionLiquidityInput(
                position_id=3,
                isin=None,
                asset_class="Equities",
                market_value=Decimal("800000"),  # 8 days -> T+5+
            ),
        ]

        ttl_results = [ttl_engine.calculate(pos, assumptions) for pos in positions]
        classifications = [bucket_engine.classify(ttl, scheme) for ttl in ttl_results]

        profile = profile_engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            classifications=classifications,
            bucket_scheme=scheme,
        )

        assert profile.total_portfolio_value == Decimal("1100000")
        assert profile.bucket_summaries[0].bucket_name == "T+0"
        assert profile.bucket_summaries[0].total_market_value == Decimal("0")
        assert profile.bucket_summaries[1].bucket_name == "T+1-5"
        assert profile.bucket_summaries[1].total_market_value == Decimal("300000")
        assert profile.bucket_summaries[2].bucket_name == "T+5+"
        assert profile.bucket_summaries[2].total_market_value == Decimal("800000")
