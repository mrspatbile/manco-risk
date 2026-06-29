"""Tests for liquidity domain models.

Validates model construction, field validation, and model-level invariants.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.liquidity import (
    LiquidationAssumptionSet,
    LiquidationCapacityAssumption,
    LiquidationHaircutAssumption,
    LiquidityBucketClassification,
    LiquidityBucketDefinition,
    LiquidityBucketScheme,
    PortfolioLiquidityBucketSummary,
    PortfolioLiquidityProfileResult,
    PositionLiquidityInput,
    TimeToLiquidateResult,
)


class TestLiquidityBucketDefinition:
    def test_valid_bucket_t_plus_0(self):
        bucket = LiquidityBucketDefinition(name="T+0", min_days=0, max_days=0)
        assert bucket.name == "T+0"
        assert bucket.min_days == 0
        assert bucket.max_days == 0

    def test_valid_bucket_t_plus_1_5(self):
        bucket = LiquidityBucketDefinition(name="T+1-5", min_days=1, max_days=5)
        assert bucket.min_days == 1
        assert bucket.max_days == 5

    def test_valid_bucket_unbounded(self):
        bucket = LiquidityBucketDefinition(name="T+5+", min_days=6, max_days=None)
        assert bucket.name == "T+5+"
        assert bucket.max_days is None

    def test_name_empty_raises(self):
        with pytest.raises(ValueError, match="name must be non-empty"):
            LiquidityBucketDefinition(name="", min_days=0, max_days=0)

    def test_name_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="name must be non-empty"):
            LiquidityBucketDefinition(name="   ", min_days=0, max_days=0)

    def test_min_days_negative_raises(self):
        with pytest.raises(ValueError, match="min_days must be >= 0"):
            LiquidityBucketDefinition(name="T+0", min_days=-1, max_days=0)

    def test_max_days_negative_raises(self):
        with pytest.raises(ValueError, match="max_days must be >= 0 or None"):
            LiquidityBucketDefinition(name="T+0", min_days=0, max_days=-1)

    def test_min_days_greater_than_max_days_raises(self):
        with pytest.raises(ValueError, match="min_days must be <= max_days"):
            LiquidityBucketDefinition(name="T+1-5", min_days=5, max_days=1)

    def test_frozen_raises_on_modification(self):
        bucket = LiquidityBucketDefinition(name="T+0", min_days=0, max_days=0)
        with pytest.raises(Exception):
            bucket.name = "T+1"  # type: ignore


class TestLiquidityBucketScheme:
    def test_valid_scheme_three_buckets(self):
        buckets = [
            LiquidityBucketDefinition(name="T+0", min_days=0, max_days=0),
            LiquidityBucketDefinition(name="T+1-5", min_days=1, max_days=5),
            LiquidityBucketDefinition(name="T+5+", min_days=6, max_days=None),
        ]
        scheme = LiquidityBucketScheme(buckets=buckets)
        assert len(scheme.buckets) == 3
        assert scheme.buckets[0].name == "T+0"

    def test_empty_buckets_raises(self):
        with pytest.raises(ValueError, match="buckets must contain at least one"):
            LiquidityBucketScheme(buckets=[])

    def test_overlapping_buckets_raises(self):
        buckets = [
            LiquidityBucketDefinition(name="T+0-5", min_days=0, max_days=5),
            LiquidityBucketDefinition(name="T+3-10", min_days=3, max_days=10),
        ]
        with pytest.raises(ValueError, match="overlap"):
            LiquidityBucketScheme(buckets=buckets)

    def test_unbounded_bucket_not_last_raises(self):
        buckets = [
            LiquidityBucketDefinition(name="T+0+", min_days=0, max_days=None),
            LiquidityBucketDefinition(name="T+5", min_days=5, max_days=10),
        ]
        with pytest.raises(ValueError, match="unbounded max_days"):
            LiquidityBucketScheme(buckets=buckets)

    def test_non_overlapping_with_gaps_valid(self):
        """Gaps are allowed; contiguity is not required."""
        buckets = [
            LiquidityBucketDefinition(name="T+0", min_days=0, max_days=0),
            LiquidityBucketDefinition(name="T+5-10", min_days=5, max_days=10),
        ]
        scheme = LiquidityBucketScheme(buckets=buckets)
        assert len(scheme.buckets) == 2

    def test_buckets_order_preserved(self):
        """Buckets provided in order are preserved; validation is order-independent."""
        buckets = [
            LiquidityBucketDefinition(name="T+0", min_days=0, max_days=0),
            LiquidityBucketDefinition(name="T+1-5", min_days=1, max_days=5),
            LiquidityBucketDefinition(name="T+5+", min_days=6, max_days=None),
        ]
        scheme = LiquidityBucketScheme(buckets=buckets)
        assert scheme.buckets[0].name == "T+0"
        assert scheme.buckets[2].name == "T+5+"


class TestLiquidationCapacityAssumption:
    def test_valid_assumption(self):
        assumption = LiquidationCapacityAssumption(
            asset_class="Equities", market_value_per_day=Decimal("1000000")
        )
        assert assumption.asset_class == "Equities"
        assert assumption.market_value_per_day == Decimal("1000000")

    def test_asset_class_empty_raises(self):
        with pytest.raises(ValueError, match="asset_class must be non-empty"):
            LiquidationCapacityAssumption(asset_class="", market_value_per_day=Decimal("1000000"))

    def test_market_value_zero_raises(self):
        with pytest.raises(ValueError, match="market_value_per_day must be positive"):
            LiquidationCapacityAssumption(asset_class="Equities", market_value_per_day=Decimal("0"))

    def test_market_value_negative_raises(self):
        with pytest.raises(ValueError, match="market_value_per_day must be positive"):
            LiquidationCapacityAssumption(
                asset_class="Equities", market_value_per_day=Decimal("-1000")
            )


class TestLiquidationHaircutAssumption:
    def test_valid_assumption_with_haircut(self):
        assumption = LiquidationHaircutAssumption(
            asset_class="Equities", haircut_rate=Decimal("0.02")
        )
        assert assumption.asset_class == "Equities"
        assert assumption.haircut_rate == Decimal("0.02")

    def test_valid_assumption_zero_haircut(self):
        assumption = LiquidationHaircutAssumption(asset_class="Equities", haircut_rate=Decimal("0"))
        assert assumption.haircut_rate == Decimal("0")

    def test_haircut_negative_raises(self):
        with pytest.raises(ValueError, match="haircut_rate must be in range"):
            LiquidationHaircutAssumption(asset_class="Equities", haircut_rate=Decimal("-0.01"))

    def test_haircut_one_or_greater_raises(self):
        with pytest.raises(ValueError, match="haircut_rate must be in range"):
            LiquidationHaircutAssumption(asset_class="Equities", haircut_rate=Decimal("1.0"))

    def test_haircut_just_below_one_valid(self):
        assumption = LiquidationHaircutAssumption(
            asset_class="Equities", haircut_rate=Decimal("0.9999")
        )
        assert assumption.haircut_rate == Decimal("0.9999")


class TestLiquidationAssumptionSet:
    def test_valid_set_with_capacity_only(self):
        scheme = LiquidityBucketScheme(
            buckets=[LiquidityBucketDefinition(name="T+0", min_days=0, max_days=None)]
        )
        capacity = LiquidationCapacityAssumption(
            asset_class="Equities", market_value_per_day=Decimal("1000000")
        )
        assumption_set = LiquidationAssumptionSet(
            bucket_scheme=scheme, capacity_assumptions=[capacity]
        )
        assert len(assumption_set.capacity_assumptions) == 1
        assert assumption_set.haircut_assumptions is None

    def test_valid_set_with_capacity_and_haircut(self):
        scheme = LiquidityBucketScheme(
            buckets=[LiquidityBucketDefinition(name="T+0", min_days=0, max_days=None)]
        )
        capacity = LiquidationCapacityAssumption(
            asset_class="Equities", market_value_per_day=Decimal("1000000")
        )
        haircut = LiquidationHaircutAssumption(asset_class="Equities", haircut_rate=Decimal("0.02"))
        assumption_set = LiquidationAssumptionSet(
            bucket_scheme=scheme,
            capacity_assumptions=[capacity],
            haircut_assumptions=[haircut],
        )
        assert len(assumption_set.haircut_assumptions) == 1

    def test_empty_capacity_assumptions_raises(self):
        scheme = LiquidityBucketScheme(
            buckets=[LiquidityBucketDefinition(name="T+0", min_days=0, max_days=None)]
        )
        with pytest.raises(ValueError, match="capacity_assumptions must contain"):
            LiquidationAssumptionSet(bucket_scheme=scheme, capacity_assumptions=[])

    def test_duplicate_asset_class_in_capacity_raises(self):
        scheme = LiquidityBucketScheme(
            buckets=[LiquidityBucketDefinition(name="T+0", min_days=0, max_days=None)]
        )
        capacity1 = LiquidationCapacityAssumption(
            asset_class="Equities", market_value_per_day=Decimal("1000000")
        )
        capacity2 = LiquidationCapacityAssumption(
            asset_class="Equities", market_value_per_day=Decimal("2000000")
        )
        with pytest.raises(ValueError, match="Duplicate asset_class"):
            LiquidationAssumptionSet(
                bucket_scheme=scheme,
                capacity_assumptions=[capacity1, capacity2],
            )

    def test_duplicate_asset_class_in_haircut_raises(self):
        scheme = LiquidityBucketScheme(
            buckets=[LiquidityBucketDefinition(name="T+0", min_days=0, max_days=None)]
        )
        capacity = LiquidationCapacityAssumption(
            asset_class="Equities", market_value_per_day=Decimal("1000000")
        )
        haircut1 = LiquidationHaircutAssumption(
            asset_class="Equities", haircut_rate=Decimal("0.01")
        )
        haircut2 = LiquidationHaircutAssumption(
            asset_class="Equities", haircut_rate=Decimal("0.02")
        )
        with pytest.raises(ValueError, match="Duplicate asset_class"):
            LiquidationAssumptionSet(
                bucket_scheme=scheme,
                capacity_assumptions=[capacity],
                haircut_assumptions=[haircut1, haircut2],
            )


class TestPositionLiquidityInput:
    def test_valid_input(self):
        input_data = PositionLiquidityInput(
            position_id=1,
            isin="US0378331005",
            asset_class="Equities",
            market_value=Decimal("100000"),
        )
        assert input_data.position_id == 1
        assert input_data.market_value == Decimal("100000")

    def test_isin_optional(self):
        input_data = PositionLiquidityInput(
            position_id=1, isin=None, asset_class="Equities", market_value=Decimal("50000")
        )
        assert input_data.isin is None

    def test_market_value_zero_valid(self):
        input_data = PositionLiquidityInput(
            position_id=1,
            isin=None,
            asset_class="Equities",
            market_value=Decimal("0"),
        )
        assert input_data.market_value == Decimal("0")

    def test_market_value_negative_raises(self):
        with pytest.raises(ValueError, match="market_value must be non-negative"):
            PositionLiquidityInput(
                position_id=1,
                isin=None,
                asset_class="Equities",
                market_value=Decimal("-1000"),
            )

    def test_asset_class_empty_raises(self):
        with pytest.raises(ValueError, match="asset_class must be non-empty"):
            PositionLiquidityInput(
                position_id=1,
                isin=None,
                asset_class="",
                market_value=Decimal("100000"),
            )


class TestTimeToLiquidateResult:
    def test_valid_result(self):
        result = TimeToLiquidateResult(
            position_id=1,
            isin="US0378331005",
            asset_class="Equities",
            market_value=Decimal("100000"),
            days_to_liquidate=Decimal("2.5"),
            liquidation_capacity_per_day=Decimal("50000"),
        )
        assert result.days_to_liquidate == Decimal("2.5")
        assert result.liquidation_capacity_per_day == Decimal("50000")

    def test_fractional_days_valid(self):
        result = TimeToLiquidateResult(
            position_id=1,
            isin=None,
            asset_class="Equities",
            market_value=Decimal("10000"),
            days_to_liquidate=Decimal("0.5"),
            liquidation_capacity_per_day=Decimal("20000"),
        )
        assert result.days_to_liquidate == Decimal("0.5")

    def test_days_to_liquidate_negative_raises(self):
        with pytest.raises(ValueError, match="days_to_liquidate must be non-negative"):
            TimeToLiquidateResult(
                position_id=1,
                isin=None,
                asset_class="Equities",
                market_value=Decimal("100000"),
                days_to_liquidate=Decimal("-1"),
                liquidation_capacity_per_day=Decimal("50000"),
            )

    def test_liquidation_capacity_zero_raises(self):
        with pytest.raises(ValueError, match="liquidation_capacity_per_day must be positive"):
            TimeToLiquidateResult(
                position_id=1,
                isin=None,
                asset_class="Equities",
                market_value=Decimal("100000"),
                days_to_liquidate=Decimal("2"),
                liquidation_capacity_per_day=Decimal("0"),
            )


class TestLiquidityBucketClassification:
    def test_valid_classification(self):
        classification = LiquidityBucketClassification(
            position_id=1,
            isin="US0378331005",
            asset_class="Equities",
            market_value=Decimal("100000"),
            days_to_liquidate=Decimal("2.5"),
            bucket_name="T+1-5",
        )
        assert classification.bucket_name == "T+1-5"

    def test_bucket_name_empty_raises(self):
        with pytest.raises(ValueError, match="bucket_name must be non-empty"):
            LiquidityBucketClassification(
                position_id=1,
                isin=None,
                asset_class="Equities",
                market_value=Decimal("100000"),
                days_to_liquidate=Decimal("2.5"),
                bucket_name="",
            )

    def test_market_value_negative_raises(self):
        with pytest.raises(ValueError, match="market_value must be non-negative"):
            LiquidityBucketClassification(
                position_id=1,
                isin=None,
                asset_class="Equities",
                market_value=Decimal("-1000"),
                days_to_liquidate=Decimal("2.5"),
                bucket_name="T+1-5",
            )


class TestPortfolioLiquidityBucketSummary:
    def test_valid_summary(self):
        summary = PortfolioLiquidityBucketSummary(
            bucket_name="T+1-5",
            total_market_value=Decimal("500000"),
            position_count=10,
            percentage_of_portfolio=Decimal("0.50"),
        )
        assert summary.total_market_value == Decimal("500000")
        assert summary.percentage_of_portfolio == Decimal("0.50")

    def test_percentage_zero_valid(self):
        summary = PortfolioLiquidityBucketSummary(
            bucket_name="Empty",
            total_market_value=Decimal("0"),
            position_count=0,
            percentage_of_portfolio=Decimal("0"),
        )
        assert summary.percentage_of_portfolio == Decimal("0")

    def test_percentage_one_valid(self):
        summary = PortfolioLiquidityBucketSummary(
            bucket_name="All",
            total_market_value=Decimal("1000000"),
            position_count=100,
            percentage_of_portfolio=Decimal("1"),
        )
        assert summary.percentage_of_portfolio == Decimal("1")

    def test_percentage_greater_than_one_raises(self):
        with pytest.raises(ValueError, match="percentage_of_portfolio must be in range"):
            PortfolioLiquidityBucketSummary(
                bucket_name="T+1-5",
                total_market_value=Decimal("500000"),
                position_count=10,
                percentage_of_portfolio=Decimal("1.1"),
            )

    def test_position_count_negative_raises(self):
        with pytest.raises(ValueError, match="position_count must be non-negative"):
            PortfolioLiquidityBucketSummary(
                bucket_name="T+1-5",
                total_market_value=Decimal("500000"),
                position_count=-1,
                percentage_of_portfolio=Decimal("0.50"),
            )


class TestPortfolioLiquidityProfileResult:
    def test_valid_profile(self):
        summaries = [
            PortfolioLiquidityBucketSummary(
                bucket_name="T+0",
                total_market_value=Decimal("200000"),
                position_count=5,
                percentage_of_portfolio=Decimal("0.20"),
            ),
            PortfolioLiquidityBucketSummary(
                bucket_name="T+1-5",
                total_market_value=Decimal("300000"),
                position_count=10,
                percentage_of_portfolio=Decimal("0.30"),
            ),
            PortfolioLiquidityBucketSummary(
                bucket_name="T+5+",
                total_market_value=Decimal("500000"),
                position_count=30,
                percentage_of_portfolio=Decimal("0.50"),
            ),
        ]
        result = PortfolioLiquidityProfileResult(
            fund_id=1,
            valuation_date=date(2026, 6, 29),
            total_portfolio_value=Decimal("1000000"),
            bucket_summaries=summaries,
        )
        assert result.fund_id == 1
        assert len(result.bucket_summaries) == 3

    def test_empty_bucket_summaries_raises(self):
        with pytest.raises(ValueError, match="bucket_summaries must contain"):
            PortfolioLiquidityProfileResult(
                fund_id=1,
                valuation_date=date(2026, 6, 29),
                total_portfolio_value=Decimal("0"),
                bucket_summaries=[],
            )

    def test_duplicate_bucket_name_raises(self):
        summaries = [
            PortfolioLiquidityBucketSummary(
                bucket_name="T+0",
                total_market_value=Decimal("500000"),
                position_count=10,
                percentage_of_portfolio=Decimal("0.50"),
            ),
            PortfolioLiquidityBucketSummary(
                bucket_name="T+0",
                total_market_value=Decimal("500000"),
                position_count=10,
                percentage_of_portfolio=Decimal("0.50"),
            ),
        ]
        with pytest.raises(ValueError, match="Duplicate bucket_name"):
            PortfolioLiquidityProfileResult(
                fund_id=1,
                valuation_date=date(2026, 6, 29),
                total_portfolio_value=Decimal("1000000"),
                bucket_summaries=summaries,
            )

    def test_percentages_do_not_sum_to_one_raises(self):
        summaries = [
            PortfolioLiquidityBucketSummary(
                bucket_name="T+0",
                total_market_value=Decimal("500000"),
                position_count=10,
                percentage_of_portfolio=Decimal("0.40"),  # Should be 0.50
            ),
            PortfolioLiquidityBucketSummary(
                bucket_name="T+1-5",
                total_market_value=Decimal("500000"),
                position_count=10,
                percentage_of_portfolio=Decimal("0.50"),
            ),
        ]
        with pytest.raises(ValueError, match="Bucket percentages must sum to 1.0"):
            PortfolioLiquidityProfileResult(
                fund_id=1,
                valuation_date=date(2026, 6, 29),
                total_portfolio_value=Decimal("1000000"),
                bucket_summaries=summaries,
            )

    def test_percentages_sum_to_one_within_tolerance(self):
        """Percentages are validated with 0.0001 tolerance for rounding."""
        summaries = [
            PortfolioLiquidityBucketSummary(
                bucket_name="T+0",
                total_market_value=Decimal("333333.33"),
                position_count=10,
                percentage_of_portfolio=Decimal("0.333333"),
            ),
            PortfolioLiquidityBucketSummary(
                bucket_name="T+1-5",
                total_market_value=Decimal("333333.34"),
                position_count=10,
                percentage_of_portfolio=Decimal("0.333334"),
            ),
            PortfolioLiquidityBucketSummary(
                bucket_name="T+5+",
                total_market_value=Decimal("333333.33"),
                position_count=10,
                percentage_of_portfolio=Decimal("0.333333"),
            ),
        ]
        result = PortfolioLiquidityProfileResult(
            fund_id=1,
            valuation_date=date(2026, 6, 29),
            total_portfolio_value=Decimal("1000000"),
            bucket_summaries=summaries,
        )
        assert len(result.bucket_summaries) == 3

    def test_zero_portfolio_value_with_zero_positions_valid(self):
        summaries = [
            PortfolioLiquidityBucketSummary(
                bucket_name="T+0",
                total_market_value=Decimal("0"),
                position_count=0,
                percentage_of_portfolio=Decimal("0"),
            ),
        ]
        result = PortfolioLiquidityProfileResult(
            fund_id=1,
            valuation_date=date(2026, 6, 29),
            total_portfolio_value=Decimal("0"),
            bucket_summaries=summaries,
        )
        assert result.total_portfolio_value == Decimal("0")
