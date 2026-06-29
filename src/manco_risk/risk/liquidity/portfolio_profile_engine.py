"""Portfolio liquidity profile aggregation engine.

Aggregates individual position bucket classifications into a portfolio-level
liquidity profile with bucket summaries.

Does NOT:
- Perform TTL calculation or bucket classification (use engines for those)
- Include stress testing or scenarios
- Handle investor concentration or redemption scenarios
"""

from datetime import date
from decimal import Decimal

from manco_risk.risk.liquidity.models import (
    LiquidityBucketClassification,
    LiquidityBucketScheme,
    PortfolioLiquidityBucketSummary,
    PortfolioLiquidityProfileResult,
)


class PortfolioLiquidityProfileEngine:
    """Aggregate position classifications into portfolio liquidity profile.

    Given classified positions and a bucket scheme, produces a portfolio-level
    summary with:
    - Aggregated market value per bucket
    - Position count per bucket
    - Percentage of portfolio per bucket
    - All buckets in scheme (including empty ones)
    """

    def calculate(
        self,
        fund_id: int,
        valuation_date: date,
        classifications: list[LiquidityBucketClassification],
        bucket_scheme: LiquidityBucketScheme,
    ) -> PortfolioLiquidityProfileResult:
        """Calculate portfolio liquidity profile.

        Parameters
        ----------
        fund_id
            Fund identifier.
        valuation_date
            Date of portfolio snapshot.
        classifications
            List of position bucket classifications.
        bucket_scheme
            Bucket scheme (defines which buckets to report).

        Returns
        -------
        PortfolioLiquidityProfileResult
            Portfolio profile with summaries for all buckets in scheme.
        """
        total_portfolio_value = sum((c.market_value for c in classifications), Decimal("0"))

        bucket_totals: dict[str, tuple[Decimal, int]] = {
            bucket.name: (Decimal("0"), 0) for bucket in bucket_scheme.buckets
        }

        for classification in classifications:
            bucket_name = classification.bucket_name
            if bucket_name not in bucket_totals:
                raise ValueError(f"Classification references unknown bucket: {bucket_name}")
            current_value, current_count = bucket_totals[bucket_name]
            bucket_totals[bucket_name] = (
                current_value + classification.market_value,
                current_count + 1,
            )

        summaries: list[PortfolioLiquidityBucketSummary] = []
        for bucket in bucket_scheme.buckets:
            bucket_value, bucket_count = bucket_totals[bucket.name]

            if total_portfolio_value > Decimal("0"):
                pct = bucket_value / total_portfolio_value
            else:
                pct = Decimal("0")

            summary = PortfolioLiquidityBucketSummary(
                bucket_name=bucket.name,
                total_market_value=bucket_value,
                position_count=bucket_count,
                percentage_of_portfolio=pct,
            )
            summaries.append(summary)

        return PortfolioLiquidityProfileResult(
            fund_id=fund_id,
            valuation_date=valuation_date,
            total_portfolio_value=total_portfolio_value,
            bucket_summaries=summaries,
        )
