"""Liquidity bucket classification engine.

Classifies position TTL values into liquidity buckets based on a bucket scheme.

Does NOT:
- Perform TTL calculation (use ttl_engine for that)
- Aggregate buckets (use portfolio_profile_engine)
- Include bucket-specific business logic
"""

from manco_risk.risk.liquidity.models import (
    LiquidityBucketClassification,
    LiquidityBucketScheme,
    TimeToLiquidateResult,
)


class BucketClassificationEngine:
    """Classify position TTL into liquidity buckets.

    Given a position TTL result and a bucket scheme, determines which bucket
    the position's TTL falls into.

    Matching rule:
    - Find the first bucket where: bucket.min_days <= ttl <= bucket.max_days
    - If ttl > all bounded buckets, use the unbounded bucket (if exists)
    """

    def classify(
        self,
        ttl_result: TimeToLiquidateResult,
        bucket_scheme: LiquidityBucketScheme,
    ) -> LiquidityBucketClassification:
        """Classify position TTL into a liquidity bucket.

        Parameters
        ----------
        ttl_result
            Time-to-liquidate result for a position.
        bucket_scheme
            Bucket scheme defining TTL ranges.

        Returns
        -------
        LiquidityBucketClassification
            Position classification with assigned bucket name.

        Raises
        ------
        ValueError
            If TTL does not fall into any bucket in the scheme.
        """
        bucket_name = self._find_bucket(ttl_result.days_to_liquidate, bucket_scheme)

        if bucket_name is None:
            raise ValueError(
                f"TTL {ttl_result.days_to_liquidate} does not fall into any bucket in scheme"
            )

        return LiquidityBucketClassification(
            position_id=ttl_result.position_id,
            isin=ttl_result.isin,
            asset_class=ttl_result.asset_class,
            market_value=ttl_result.market_value,
            days_to_liquidate=ttl_result.days_to_liquidate,
            bucket_name=bucket_name,
        )

    def _find_bucket(self, ttl_days, bucket_scheme: LiquidityBucketScheme) -> str | None:
        """Find bucket containing ttl_days.

        Matches first bucket where min_days <= ttl <= max_days.
        If max_days is None, bucket is unbounded and accepts any ttl >= min_days.
        """
        for bucket in bucket_scheme.buckets:
            if bucket.min_days <= ttl_days:
                if bucket.max_days is None or ttl_days <= bucket.max_days:
                    return bucket.name
        return None
