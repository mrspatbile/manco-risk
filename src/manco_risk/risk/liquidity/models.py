"""Liquidity risk domain models.

Pure data models for liquidity calculations: bucket definitions, assumptions,
position-level and portfolio-level results.

Conventions:
- Monetary values stored as Decimal
- Rates, haircuts, ratios stored as Decimal (e.g., 0.05 = 5%)
- Days stored as positive integers
- Percentages stored as decimals, never raw percentages
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class LiquidityBucketDefinition(BaseModel):
    """Single liquidity bucket definition.

    Defines a TTL (time-to-liquidate) bucket by name and day range.

    Fields:
    - name: Bucket identifier (e.g., 'T+0', 'T+1-5').
    - min_days: Minimum TTL (inclusive), >= 0.
    - max_days: Maximum TTL (inclusive), >= min_days. None means unbounded.

    Examples:
    - T+0: min_days=0, max_days=0
    - T+1-5: min_days=1, max_days=5
    - T+5+: min_days=6, max_days=None
    - Illiquid: min_days=999, max_days=None
    """

    name: str
    min_days: int
    max_days: int | None

    model_config = ConfigDict(frozen=True)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must be non-empty")
        return v.strip()

    @field_validator("min_days")
    @classmethod
    def validate_min_days(cls, v: int) -> int:
        if v < 0:
            raise ValueError("min_days must be >= 0")
        return v

    @field_validator("max_days")
    @classmethod
    def validate_max_days(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("max_days must be >= 0 or None")
        return v

    @model_validator(mode="after")
    def validate_day_range(self) -> "LiquidityBucketDefinition":
        if self.max_days is not None and self.min_days > self.max_days:
            raise ValueError("min_days must be <= max_days")
        return self


class LiquidityBucketScheme(BaseModel):
    """Liquidity bucket scheme: ordered list of bucket definitions.

    Defines the classification scheme for TTL values.

    Fields:
    - buckets: List of LiquidityBucketDefinition in order.

    Invariants:
    - At least one bucket.
    - Buckets must be non-overlapping.
    - Buckets should cover all possible TTL values (no gaps).
    """

    buckets: list[LiquidityBucketDefinition]

    model_config = ConfigDict(frozen=True)

    @field_validator("buckets")
    @classmethod
    def validate_buckets(
        cls, v: list[LiquidityBucketDefinition]
    ) -> list[LiquidityBucketDefinition]:
        if not v:
            raise ValueError("buckets must contain at least one bucket")
        return v

    @model_validator(mode="after")
    def validate_non_overlapping(self) -> "LiquidityBucketScheme":
        sorted_buckets = sorted(self.buckets, key=lambda b: b.min_days)

        for i in range(len(sorted_buckets) - 1):
            current = sorted_buckets[i]
            next_bucket = sorted_buckets[i + 1]

            if current.max_days is None:
                raise ValueError(
                    f"Bucket '{current.name}' has unbounded max_days; "
                    f"cannot have subsequent buckets"
                )

            if next_bucket.min_days <= current.max_days:
                raise ValueError(
                    f"Buckets '{current.name}' and '{next_bucket.name}' overlap: "
                    f"{current.name} ends at {current.max_days}, "
                    f"{next_bucket.name} starts at {next_bucket.min_days}"
                )

        return self


class LiquidationCapacityAssumption(BaseModel):
    """Liquidation capacity assumption for an asset.

    Defines how much market value of an asset can be liquidated per day.

    Fields:
    - asset_class: Asset class identifier.
    - market_value_per_day: Amount (in base currency) that can be liquidated per day.
      Must be positive where liquidation is assumed possible.

    Example:
    - Equities: market_value_per_day = Decimal('1000000')
      (up to 1M per day)
    """

    asset_class: str
    market_value_per_day: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("asset_class")
    @classmethod
    def validate_asset_class(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("asset_class must be non-empty")
        return v.strip()

    @field_validator("market_value_per_day")
    @classmethod
    def validate_market_value_per_day(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("market_value_per_day must be positive")
        return v


class LiquidationHaircutAssumption(BaseModel):
    """Haircut assumption for liquidation proceeds.

    Represents a reduction in proceeds due to market impact, bid-ask spread,
    or other liquidation costs.

    Fields:
    - asset_class: Asset class identifier.
    - haircut_rate: Haircut as decimal (e.g., 0.05 = 5% haircut).
      Stored as Decimal, range [0, 1).

    Example:
    - Equities: haircut_rate = 0.02 (2% haircut on proceeds)
    """

    asset_class: str
    haircut_rate: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("asset_class")
    @classmethod
    def validate_asset_class(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("asset_class must be non-empty")
        return v.strip()

    @field_validator("haircut_rate")
    @classmethod
    def validate_haircut_rate(cls, v: Decimal) -> Decimal:
        if v < 0 or v >= 1:
            raise ValueError("haircut_rate must be in range [0, 1)")
        return v


class LiquidationAssumptionSet(BaseModel):
    """Set of liquidation assumptions for TTL and liquidity calculations.

    Groups liquidation capacity and haircut assumptions by asset class.

    Fields:
    - bucket_scheme: Liquidity bucket scheme (defines TTL classification).
    - capacity_assumptions: Liquidation capacity by asset class.
    - haircut_assumptions: Liquidation haircut by asset class (optional).
    """

    bucket_scheme: LiquidityBucketScheme
    capacity_assumptions: list[LiquidationCapacityAssumption]
    haircut_assumptions: list[LiquidationHaircutAssumption] | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("capacity_assumptions")
    @classmethod
    def validate_capacity_assumptions(
        cls, v: list[LiquidationCapacityAssumption]
    ) -> list[LiquidationCapacityAssumption]:
        if not v:
            raise ValueError("capacity_assumptions must contain at least one assumption")
        asset_classes = {a.asset_class for a in v}
        if len(asset_classes) != len(v):
            raise ValueError("Duplicate asset_class in capacity_assumptions")
        return v

    @field_validator("haircut_assumptions")
    @classmethod
    def validate_haircut_assumptions(
        cls, v: list[LiquidationHaircutAssumption] | None
    ) -> list[LiquidationHaircutAssumption] | None:
        if v is not None:
            asset_classes = {a.asset_class for a in v}
            if len(asset_classes) != len(v):
                raise ValueError("Duplicate asset_class in haircut_assumptions")
        return v


class PositionLiquidityInput(BaseModel):
    """Position data for liquidity calculations.

    Minimal input needed for TTL and bucket classification.

    Fields:
    - position_id: Internal position identifier.
    - isin: ISIN identifier (optional).
    - asset_class: Asset class.
    - market_value: Position market value in base currency (Decimal, >= 0).
    """

    position_id: int
    isin: str | None
    asset_class: str
    market_value: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("asset_class")
    @classmethod
    def validate_asset_class(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("asset_class must be non-empty")
        return v.strip()

    @field_validator("market_value")
    @classmethod
    def validate_market_value(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("market_value must be non-negative")
        return v


class TimeToLiquidateResult(BaseModel):
    """Time-to-liquidate result for a single position.

    Result of TTL calculation: how many days to liquidate a position
    given liquidation capacity assumptions.

    Fields:
    - position_id: Internal position identifier.
    - isin: ISIN identifier (optional).
    - asset_class: Asset class.
    - market_value: Position market value (Decimal).
    - days_to_liquidate: Estimated days to liquidate (Decimal, >= 0).
      May be fractional (e.g., 0.5 days).
    - liquidation_capacity_per_day: Liquidation capacity assumption used (Decimal).
    """

    position_id: int
    isin: str | None
    asset_class: str
    market_value: Decimal
    days_to_liquidate: Decimal
    liquidation_capacity_per_day: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("market_value")
    @classmethod
    def validate_market_value(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("market_value must be non-negative")
        return v

    @field_validator("days_to_liquidate")
    @classmethod
    def validate_days_to_liquidate(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("days_to_liquidate must be non-negative")
        return v

    @field_validator("liquidation_capacity_per_day")
    @classmethod
    def validate_liquidation_capacity_per_day(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("liquidation_capacity_per_day must be positive")
        return v


class LiquidityBucketClassification(BaseModel):
    """Liquidity bucket classification for a single position.

    Result of classifying a position's TTL into a bucket.

    Fields:
    - position_id: Internal position identifier.
    - isin: ISIN identifier (optional).
    - asset_class: Asset class.
    - market_value: Position market value (Decimal).
    - days_to_liquidate: TTL result (Decimal).
    - bucket_name: Assigned bucket name (e.g., 'T+1-5').
    """

    position_id: int
    isin: str | None
    asset_class: str
    market_value: Decimal
    days_to_liquidate: Decimal
    bucket_name: str

    model_config = ConfigDict(frozen=True)

    @field_validator("market_value")
    @classmethod
    def validate_market_value(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("market_value must be non-negative")
        return v

    @field_validator("days_to_liquidate")
    @classmethod
    def validate_days_to_liquidate(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("days_to_liquidate must be non-negative")
        return v

    @field_validator("bucket_name")
    @classmethod
    def validate_bucket_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("bucket_name must be non-empty")
        return v.strip()


class PortfolioLiquidityBucketSummary(BaseModel):
    """Summary of positions in a single liquidity bucket.

    Aggregated bucket-level data for portfolio liquidity profile.

    Fields:
    - bucket_name: Bucket name (e.g., 'T+0').
    - total_market_value: Sum of market values in bucket (Decimal).
    - position_count: Number of positions in bucket.
    - percentage_of_portfolio: Bucket amount as percentage of total portfolio (Decimal).
      Stored as decimal (e.g., 0.25 = 25%), in range [0, 1].
    """

    bucket_name: str
    total_market_value: Decimal
    position_count: int
    percentage_of_portfolio: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("bucket_name")
    @classmethod
    def validate_bucket_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("bucket_name must be non-empty")
        return v.strip()

    @field_validator("total_market_value")
    @classmethod
    def validate_total_market_value(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("total_market_value must be non-negative")
        return v

    @field_validator("position_count")
    @classmethod
    def validate_position_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError("position_count must be non-negative")
        return v

    @field_validator("percentage_of_portfolio")
    @classmethod
    def validate_percentage_of_portfolio(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 1:
            raise ValueError("percentage_of_portfolio must be in range [0, 1]")
        return v


class PortfolioLiquidityProfileResult(BaseModel):
    """Portfolio-level liquidity profile result.

    Aggregated TTL and bucket classification across all positions.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Date of portfolio snapshot.
    - total_portfolio_value: Sum of all position market values (Decimal).
    - bucket_summaries: List of PortfolioLiquidityBucketSummary, one per bucket,
      ordered by bucket min_days ascending.
    """

    fund_id: int
    valuation_date: date
    total_portfolio_value: Decimal
    bucket_summaries: list[PortfolioLiquidityBucketSummary]

    model_config = ConfigDict(frozen=True)

    @field_validator("total_portfolio_value")
    @classmethod
    def validate_total_portfolio_value(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("total_portfolio_value must be non-negative")
        return v

    @field_validator("bucket_summaries")
    @classmethod
    def validate_bucket_summaries(
        cls, v: list[PortfolioLiquidityBucketSummary]
    ) -> list[PortfolioLiquidityBucketSummary]:
        if not v:
            raise ValueError("bucket_summaries must contain at least one bucket")

        bucket_names = {s.bucket_name for s in v}
        if len(bucket_names) != len(v):
            raise ValueError("Duplicate bucket_name in bucket_summaries")

        return v

    @model_validator(mode="after")
    def validate_percentages_sum(self) -> "PortfolioLiquidityProfileResult":
        if self.total_portfolio_value > 0:
            total_pct = sum(s.percentage_of_portfolio for s in self.bucket_summaries)
            if abs(total_pct - Decimal("1")) > Decimal("0.0001"):
                raise ValueError(f"Bucket percentages must sum to 1.0, got {total_pct}")

        position_count_sum = sum(s.position_count for s in self.bucket_summaries)
        if position_count_sum < 0:
            raise ValueError("Sum of position_count must be non-negative")

        return self


class RedemptionStressAssumption(BaseModel):
    """Redemption stress test assumption.

    Defines which buckets are considered liquid and the redemption shock scenario.

    Fields:
    - liquid_bucket_names: List of bucket names to include in available liquidity.
      For example, ["T+0", "T+1-5"] means only positions in these buckets can
      meet redemption demand.
    - redemption_shock_rate: Redemption as percentage of NAV (Decimal, [0, 1]).
      For example, 0.10 = 10% of NAV redeemed.

    Example:
    - All positions except illiquid bucket: liquid_bucket_names=["T+0", "T+1-5", "T+5+"]
    - Only same-day and next-day: liquid_bucket_names=["T+0", "T+1-5"]
    """

    liquid_bucket_names: list[str]
    redemption_shock_rate: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("liquid_bucket_names")
    @classmethod
    def validate_liquid_bucket_names(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("liquid_bucket_names must contain at least one bucket")
        for name in v:
            if not name or not name.strip():
                raise ValueError("bucket names must be non-empty")
        return v

    @field_validator("redemption_shock_rate")
    @classmethod
    def validate_redemption_shock_rate(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 1:
            raise ValueError("redemption_shock_rate must be in range [0, 1]")
        return v


class RedemptionStressResult(BaseModel):
    """Redemption stress test result.

    Results of a redemption stress scenario: coverage ratio, shortfall, and buffer.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Date of portfolio snapshot.
    - redemption_shock_rate: Shock rate applied (Decimal, [0, 1]).
    - redemption_amount: Stressed redemption in base currency (Decimal).
    - available_liquidity: Sum of values in liquid buckets (Decimal).
    - coverage_ratio: available_liquidity / redemption_amount.
      Ratio > 1.0: sufficient liquidity to cover redemption.
      Ratio < 1.0: shortfall; gates or gates+swing may be triggered.
      Ratio = 0: no redemption demand (zero shock rate).
    - shortfall_amount: max(redemption_amount - available_liquidity, 0).
      Amount that cannot be met without additional measures.
    - remaining_liquidity_buffer: max(available_liquidity - redemption_amount, 0).
      Liquidity remaining after meeting redemption.
    - liquid_bucket_names: Buckets included in available_liquidity (for traceability).
    """

    fund_id: int
    valuation_date: date
    redemption_shock_rate: Decimal
    redemption_amount: Decimal
    available_liquidity: Decimal
    coverage_ratio: Decimal
    shortfall_amount: Decimal
    remaining_liquidity_buffer: Decimal
    liquid_bucket_names: list[str]

    model_config = ConfigDict(frozen=True)

    @field_validator("redemption_shock_rate")
    @classmethod
    def validate_redemption_shock_rate(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 1:
            raise ValueError("redemption_shock_rate must be in range [0, 1]")
        return v

    @field_validator("redemption_amount", "available_liquidity")
    @classmethod
    def validate_amounts(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("monetary amounts must be non-negative")
        return v

    @field_validator("coverage_ratio")
    @classmethod
    def validate_coverage_ratio(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("coverage_ratio must be non-negative")
        return v

    @field_validator("shortfall_amount", "remaining_liquidity_buffer")
    @classmethod
    def validate_buffer_amounts(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("buffer amounts must be non-negative")
        return v

    @field_validator("liquid_bucket_names")
    @classmethod
    def validate_liquid_bucket_names(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("liquid_bucket_names must contain at least one bucket")
        return v

    @model_validator(mode="after")
    def validate_accounting_consistency(self) -> "RedemptionStressResult":
        """Verify accounting: shortfall and buffer together cover the redeemable amount."""
        if self.redemption_amount == Decimal("0"):
            if self.shortfall_amount != Decimal("0"):
                raise ValueError("If redemption_amount is 0, shortfall_amount must be 0")
            if self.remaining_liquidity_buffer != self.available_liquidity:
                raise ValueError(
                    "If redemption_amount is 0, remaining_liquidity_buffer must equal available_liquidity"
                )
        else:
            expected_shortfall = max(
                self.redemption_amount - self.available_liquidity, Decimal("0")
            )
            expected_buffer = max(self.available_liquidity - self.redemption_amount, Decimal("0"))

            if abs(self.shortfall_amount - expected_shortfall) > Decimal("0.01"):
                raise ValueError(
                    f"Shortfall mismatch: expected {expected_shortfall}, got {self.shortfall_amount}"
                )
            if abs(self.remaining_liquidity_buffer - expected_buffer) > Decimal("0.01"):
                raise ValueError(
                    f"Buffer mismatch: expected {expected_buffer}, got {self.remaining_liquidity_buffer}"
                )

        return self


class InvestorHolding(BaseModel):
    """Single investor holding in the fund.

    Fields:
    - investor_id: Unique investor identifier.
    - nav_amount: Investor NAV in base currency (Decimal, >= 0).
    """

    investor_id: str
    nav_amount: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("investor_id")
    @classmethod
    def validate_investor_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("investor_id must be non-empty")
        return v.strip()

    @field_validator("nav_amount")
    @classmethod
    def validate_nav_amount(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("nav_amount must be non-negative")
        return v


class TopNInvestor(BaseModel):
    """Single investor in a top-N ranking.

    Fields:
    - investor_id: Investor identifier.
    - total_amount: Investor NAV (Decimal).
    - percentage_of_nav: Investor as percentage of fund NAV (Decimal, [0, 1]).
    """

    investor_id: str
    total_amount: Decimal
    percentage_of_nav: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("investor_id")
    @classmethod
    def validate_investor_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("investor_id must be non-empty")
        return v.strip()

    @field_validator("total_amount")
    @classmethod
    def validate_total_amount(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("total_amount must be non-negative")
        return v

    @field_validator("percentage_of_nav")
    @classmethod
    def validate_percentage_of_nav(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 1:
            raise ValueError("percentage_of_nav must be in range [0, 1]")
        return v


class InvestorConcentrationResult(BaseModel):
    """Investor concentration analysis result.

    Analyzes investor base concentration and provides largest investor metrics.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Date of portfolio snapshot.
    - fund_nav: Fund NAV in base currency (Decimal, > 0).
    - total_investor_count: Total number of investors.
    - largest_investor_id: Identifier of largest investor.
    - largest_investor_amount: Largest investor NAV (Decimal).
    - largest_investor_percentage: Largest investor as % of fund NAV (Decimal, [0, 1]).
    - top_n_levels: List of N values calculated (e.g., [1, 5, 10]).
    - top_n_investors: Dict mapping N → sorted list of top-N investors.
      Each list is sorted by amount descending.
      Example: {1: [investor1], 5: [investor1, investor2, ...]}
    """

    fund_id: int
    valuation_date: date
    fund_nav: Decimal
    total_investor_count: int
    largest_investor_id: str
    largest_investor_amount: Decimal
    largest_investor_percentage: Decimal
    top_n_levels: list[int]
    top_n_investors: dict[int, list[TopNInvestor]]

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_nav")
    @classmethod
    def validate_fund_nav(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("fund_nav must be positive")
        return v

    @field_validator("total_investor_count")
    @classmethod
    def validate_total_investor_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError("total_investor_count must be non-negative")
        return v

    @field_validator("largest_investor_amount")
    @classmethod
    def validate_largest_investor_amount(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("largest_investor_amount must be non-negative")
        return v

    @field_validator("largest_investor_percentage")
    @classmethod
    def validate_largest_investor_percentage(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 1:
            raise ValueError("largest_investor_percentage must be in range [0, 1]")
        return v

    @field_validator("top_n_levels")
    @classmethod
    def validate_top_n_levels(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("top_n_levels must contain at least one level")
        for level in v:
            if level < 1:
                raise ValueError("top_n_levels must contain positive integers")
        return v

    @field_validator("top_n_investors")
    @classmethod
    def validate_top_n_investors(
        cls, v: dict[int, list[TopNInvestor]]
    ) -> dict[int, list[TopNInvestor]]:
        if not v:
            raise ValueError("top_n_investors must contain at least one level")
        for level, investors in v.items():
            if level < 1:
                raise ValueError("top_n_investors keys must be positive")
            if len(investors) > level:
                raise ValueError(f"top-{level} has {len(investors)} investors, expected <= {level}")
            investor_ids = {inv.investor_id for inv in investors}
            if len(investor_ids) != len(investors):
                raise ValueError(f"Duplicate investor IDs in top-{level}")
        return v

    @model_validator(mode="after")
    def validate_largest_investor_in_top_1(self) -> "InvestorConcentrationResult":
        """Largest investor must be first in top-1."""
        if 1 in self.top_n_investors and self.top_n_investors[1]:
            top_1_investor = self.top_n_investors[1][0]
            if top_1_investor.investor_id != self.largest_investor_id:
                raise ValueError("Largest investor must be first in top-1 ranking")
        return self


class LiquidityAdjustedVaRAssumption(BaseModel):
    """Liquidity adjustment assumption for VaR.

    Defines the liquidity cost to apply to base VaR.

    Fields:
    - liquidity_cost_rate: Cost of liquidating the portfolio (Decimal, [0, 1]).
      Represents bid-ask spread, market impact, haircut, or liquidation horizon cost.
      Stored as decimal (e.g., 0.02 = 2%).
    - methodology_label: Optional description of adjustment method
      (e.g., "bid-ask spread", "liquidation cost", "liquidity horizon").
    """

    liquidity_cost_rate: Decimal
    methodology_label: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("liquidity_cost_rate")
    @classmethod
    def validate_liquidity_cost_rate(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 1:
            raise ValueError("liquidity_cost_rate must be in range [0, 1]")
        return v

    @field_validator("methodology_label")
    @classmethod
    def validate_methodology_label(cls, v: str | None) -> str | None:
        if v is not None and (not v or not v.strip()):
            raise ValueError("methodology_label must be non-empty if provided")
        return v.strip() if v else None


class LiquidityAdjustedVaRResult(BaseModel):
    """Liquidity-adjusted VaR result.

    Combines base VaR with liquidity adjustment cost.

    Methodology:
    - liquidity_adjustment = portfolio_value × liquidity_cost_rate
    - liquidity_adjusted_var_amount = base_var_amount + liquidity_adjustment
    - liquidity_adjusted_var_rate = liquidity_adjusted_var_amount / portfolio_value

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Date of portfolio snapshot.
    - portfolio_value: Fund NAV or portfolio value (Decimal, positive).
    - base_var_amount: Base VaR loss amount (Decimal, non-negative).
    - base_var_rate: Base VaR as percentage of portfolio (Decimal, non-negative).
    - liquidity_cost_rate: Liquidity cost assumption (Decimal, [0, 1]).
    - liquidity_adjustment: Liquidity cost in currency units (Decimal, non-negative).
    - liquidity_adjusted_var_amount: Base VaR + adjustment (Decimal, non-negative).
    - liquidity_adjusted_var_rate: Adjusted VaR as % of portfolio (Decimal, non-negative).
    - methodology_label: Traceability label for adjustment method.
    """

    fund_id: int
    valuation_date: date
    portfolio_value: Decimal
    base_var_amount: Decimal
    base_var_rate: Decimal
    liquidity_cost_rate: Decimal
    liquidity_adjustment: Decimal
    liquidity_adjusted_var_amount: Decimal
    liquidity_adjusted_var_rate: Decimal
    methodology_label: str | None

    model_config = ConfigDict(frozen=True)

    @field_validator("portfolio_value")
    @classmethod
    def validate_portfolio_value(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("portfolio_value must be positive")
        return v

    @field_validator("base_var_amount")
    @classmethod
    def validate_base_var_amount(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("base_var_amount must be non-negative")
        return v

    @field_validator("base_var_rate")
    @classmethod
    def validate_base_var_rate(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("base_var_rate must be non-negative")
        return v

    @field_validator("liquidity_cost_rate")
    @classmethod
    def validate_liquidity_cost_rate(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 1:
            raise ValueError("liquidity_cost_rate must be in range [0, 1]")
        return v

    @field_validator("liquidity_adjustment", "liquidity_adjusted_var_amount")
    @classmethod
    def validate_var_amounts(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("VaR amounts must be non-negative")
        return v

    @field_validator("liquidity_adjusted_var_rate")
    @classmethod
    def validate_liquidity_adjusted_var_rate(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("liquidity_adjusted_var_rate must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_accounting_consistency(self) -> "LiquidityAdjustedVaRResult":
        """Verify liquidity_adjusted_var_amount = base_var_amount + liquidity_adjustment."""
        expected_adjusted = self.base_var_amount + self.liquidity_adjustment
        if abs(self.liquidity_adjusted_var_amount - expected_adjusted) > Decimal("0.01"):
            raise ValueError(
                f"Accounting error: adjusted VaR should be {expected_adjusted}, got {self.liquidity_adjusted_var_amount}"
            )

        expected_adjusted_rate = expected_adjusted / self.portfolio_value
        if abs(self.liquidity_adjusted_var_rate - expected_adjusted_rate) > Decimal("0.000001"):
            raise ValueError(
                f"Rate error: adjusted rate should be {expected_adjusted_rate}, got {self.liquidity_adjusted_var_rate}"
            )

        expected_adjustment = self.portfolio_value * self.liquidity_cost_rate
        if abs(self.liquidity_adjustment - expected_adjustment) > Decimal("0.01"):
            raise ValueError(
                f"Adjustment error: should be {expected_adjustment}, got {self.liquidity_adjustment}"
            )

        return self
