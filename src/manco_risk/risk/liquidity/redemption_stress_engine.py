"""Redemption stress testing engine.

Assesses liquidity coverage under redemption scenarios. Tests whether available
liquid assets can satisfy a redemption demand.

Does NOT:
- Model gates, swing pricing, or suspension logic
- Include queuing or multi-period effects
- Apply haircuts to available liquidity (haircuts affect proceeds, not coverage)
- Perform any allocation across investors or fund strategies
"""

from decimal import Decimal

from manco_risk.risk.liquidity.models import (
    PortfolioLiquidityProfileResult,
    RedemptionStressAssumption,
    RedemptionStressResult,
)


class RedemptionStressEngine:
    """Assess liquidity coverage under redemption scenarios.

    Given a portfolio liquidity profile, fund NAV, and redemption shock rate,
    calculates coverage ratio and shortfall.

    Methodology:
    - Redemption demand = NAV × shock_rate
    - Available liquidity = sum of bucket values identified as liquid
    - Coverage ratio = available_liquidity / redemption_amount
    - Shortfall = max(redemption_amount - available_liquidity, 0)
    - Buffer = max(available_liquidity - redemption_amount, 0)

    Coverage ratio > 1.0: sufficient liquidity (no gates needed)
    Coverage ratio < 1.0: shortfall (gates or gate+swing may be triggered)
    Coverage ratio = undefined: if redemption_amount = 0 (zero shock rate)
    """

    def calculate(
        self,
        portfolio_profile: PortfolioLiquidityProfileResult,
        fund_nav: Decimal,
        assumption: RedemptionStressAssumption,
    ) -> RedemptionStressResult:
        """Calculate redemption stress coverage.

        Parameters
        ----------
        portfolio_profile
            Portfolio liquidity profile with bucket summaries.
        fund_nav
            Fund NAV (or portfolio market value) in base currency.
        assumption
            Redemption stress assumption (shock rate, liquid bucket definition).

        Returns
        -------
        RedemptionStressResult
            Coverage ratio, shortfall, and buffer.

        Raises
        ------
        ValueError
            If a liquid bucket is not found in the portfolio profile.
        """
        redemption_amount = fund_nav * assumption.redemption_shock_rate

        available_liquidity = self._calculate_available_liquidity(
            portfolio_profile, assumption.liquid_bucket_names
        )

        if redemption_amount == Decimal("0"):
            coverage_ratio = Decimal("0")
            shortfall_amount = Decimal("0")
            remaining_buffer = available_liquidity
        else:
            coverage_ratio = available_liquidity / redemption_amount
            shortfall_amount = max(redemption_amount - available_liquidity, Decimal("0"))
            remaining_buffer = max(available_liquidity - redemption_amount, Decimal("0"))

        return RedemptionStressResult(
            fund_id=portfolio_profile.fund_id,
            valuation_date=portfolio_profile.valuation_date,
            redemption_shock_rate=assumption.redemption_shock_rate,
            redemption_amount=redemption_amount,
            available_liquidity=available_liquidity,
            coverage_ratio=coverage_ratio,
            shortfall_amount=shortfall_amount,
            remaining_liquidity_buffer=remaining_buffer,
            liquid_bucket_names=assumption.liquid_bucket_names,
        )

    def _calculate_available_liquidity(
        self,
        portfolio_profile: PortfolioLiquidityProfileResult,
        liquid_bucket_names: list[str],
    ) -> Decimal:
        """Sum market values of liquid buckets.

        Raises ValueError if a liquid bucket is not found in the profile.
        """
        liquid_set = set(liquid_bucket_names)
        profile_buckets = {s.bucket_name for s in portfolio_profile.bucket_summaries}

        missing_buckets = liquid_set - profile_buckets
        if missing_buckets:
            raise ValueError(f"Liquid buckets {missing_buckets} not found in portfolio profile")

        available = Decimal("0")
        for summary in portfolio_profile.bucket_summaries:
            if summary.bucket_name in liquid_bucket_names:
                available += summary.total_market_value

        return available
