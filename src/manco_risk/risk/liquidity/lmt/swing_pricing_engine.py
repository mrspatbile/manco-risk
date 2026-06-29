"""Swing pricing engine.

Implements swing pricing logic: adjusts dealing NAV to pass estimated
liquidity costs to transacting investors and protect remaining investors.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.risk.liquidity.lmt.models import SwingPricingConfig


class SwingPricingResult(BaseModel):
    """Swing pricing evaluation result.

    Output of swing pricing trigger logic: whether swing pricing was activated,
    calculated factors, and swing cost transferred to transacting investors.

    Fields:
    - swing_pricing_activated: Whether swing pricing was triggered and is active.
    - raw_swing_factor: Swing factor before capping to max (Decimal, >= 0).
      Represents the 'pure' cost calculation before regulatory/policy caps.
    - applied_swing_factor: Swing factor after capping to max (Decimal, [0, max]).
      This is the factor actually applied to NAV.
    - exceeded_maximum_factor: Whether raw_swing_factor > max_swing_factor.
      Useful for compliance escalation if max is regularly hit.
    - swing_cost_amount: Dollar amount of swing cost transferred to transacting
      investors (Decimal, >= 0). Calculated as applied_swing_factor times basis.
    - redemption_rate: Redemption amount as fraction of NAV (Decimal, >= 0).
      This is the triggering condition (redemption_amount / fund_nav).
    - cost_basis: Which basis was used ("nav" or "flow", from config).
      Preserved for traceability and audit.
    """

    swing_pricing_activated: bool
    raw_swing_factor: Decimal
    applied_swing_factor: Decimal
    exceeded_maximum_factor: bool
    swing_cost_amount: Decimal
    redemption_rate: Decimal
    cost_basis: str

    model_config = ConfigDict(frozen=True)

    @field_validator(
        "raw_swing_factor", "applied_swing_factor", "swing_cost_amount", "redemption_rate"
    )
    @classmethod
    def validate_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("amount/factor must be non-negative")
        return v

    @field_validator("applied_swing_factor")
    @classmethod
    def validate_applied_within_max(cls, v: Decimal) -> Decimal:
        if v > 1:
            raise ValueError("applied_swing_factor cannot exceed 1.0")
        return v

    @field_validator("cost_basis")
    @classmethod
    def validate_cost_basis(cls, v: str) -> str:
        if v not in ("nav", "flow"):
            raise ValueError("cost_basis must be 'nav' or 'flow'")
        return v

    @field_validator("applied_swing_factor")
    @classmethod
    def validate_activation_consistency(cls, v: Decimal, info) -> Decimal:
        activated = info.data.get("swing_pricing_activated")
        if activated is not None:
            if activated and v <= Decimal("0"):
                raise ValueError("swing_pricing_activated=True requires applied_swing_factor > 0")
            if not activated and v > Decimal("0"):
                raise ValueError("swing_pricing_activated=False requires applied_swing_factor == 0")
        return v


class SwingPricingEngine:
    """Swing pricing trigger and cost calculation engine.

    Adjusts dealing NAV to pass estimated liquidity costs to transacting
    investors, protecting the fund's remaining investors from dilution.

    Behavior:
    - If swing pricing is disabled: no swing applied.
    - If redemption amount is zero: no swing applied.
    - If redemption_rate <= threshold: no swing applied.
    - If redemption_rate > threshold: swing activated.
      - Calculate raw swing factor from estimated liquidity cost.
      - Cap at maximum swing factor.
      - Track whether cap was exceeded.

    Cost basis determines how swing cost is expressed:
    - "nav": swing factor and cost are % of fund NAV.
    - "flow": swing factor and cost are % of redemption flow.

    This engine is stateless and deterministic; it evaluates swing pricing
    for a single period given current NAV, redemption demand, and cost.
    """

    def calculate(
        self,
        redemption_amount: Decimal,
        fund_nav: Decimal,
        estimated_liquidity_cost: Decimal,
        config: SwingPricingConfig,
    ) -> SwingPricingResult:
        """Calculate swing pricing activation and cost.

        Args:
            redemption_amount: Redemption requested (Decimal, >= 0).
            fund_nav: Fund NAV at valuation (Decimal, > 0).
            estimated_liquidity_cost: Estimated cost of liquidating assets
              to meet redemption (Decimal, >= 0).
            config: Swing pricing configuration.

        Returns:
            SwingPricingResult with activation status, factors, and cost.

        Raises:
            ValueError: If inputs violate constraints (negative amounts,
              invalid NAV, etc.).
        """
        if redemption_amount < 0:
            raise ValueError("redemption_amount must be non-negative")
        if fund_nav <= 0:
            raise ValueError("fund_nav must be positive")
        if estimated_liquidity_cost < 0:
            raise ValueError("estimated_liquidity_cost must be non-negative")

        # If swing pricing is disabled, no swing applied
        if not config.enabled:
            return SwingPricingResult(
                swing_pricing_activated=False,
                raw_swing_factor=Decimal("0"),
                applied_swing_factor=Decimal("0"),
                exceeded_maximum_factor=False,
                swing_cost_amount=Decimal("0"),
                redemption_rate=Decimal("0"),
                cost_basis=config.cost_basis,
            )

        # If redemption amount is zero, no swing applied
        if redemption_amount == Decimal("0"):
            return SwingPricingResult(
                swing_pricing_activated=False,
                raw_swing_factor=Decimal("0"),
                applied_swing_factor=Decimal("0"),
                exceeded_maximum_factor=False,
                swing_cost_amount=Decimal("0"),
                redemption_rate=Decimal("0"),
                cost_basis=config.cost_basis,
            )

        # Calculate redemption rate (as fraction of NAV)
        redemption_rate = redemption_amount / fund_nav

        # Check if redemption rate exceeds threshold (strict inequality)
        if redemption_rate <= config.trigger_threshold:
            return SwingPricingResult(
                swing_pricing_activated=False,
                raw_swing_factor=Decimal("0"),
                applied_swing_factor=Decimal("0"),
                exceeded_maximum_factor=False,
                swing_cost_amount=Decimal("0"),
                redemption_rate=redemption_rate,
                cost_basis=config.cost_basis,
            )

        # Swing pricing is triggered
        # Calculate raw swing factor based on cost basis
        if config.cost_basis == "nav":
            raw_swing_factor = estimated_liquidity_cost / fund_nav
        else:  # config.cost_basis == "flow"
            raw_swing_factor = estimated_liquidity_cost / redemption_amount

        # Cap raw factor at maximum
        applied_swing_factor = min(raw_swing_factor, config.max_swing_factor)
        exceeded_maximum = raw_swing_factor > config.max_swing_factor

        # If applied factor is zero (no cost), swing is not activated
        if applied_swing_factor == Decimal("0"):
            return SwingPricingResult(
                swing_pricing_activated=False,
                raw_swing_factor=raw_swing_factor,
                applied_swing_factor=Decimal("0"),
                exceeded_maximum_factor=exceeded_maximum,
                swing_cost_amount=Decimal("0"),
                redemption_rate=redemption_rate,
                cost_basis=config.cost_basis,
            )

        # Calculate swing cost based on cost basis
        if config.cost_basis == "nav":
            swing_cost_amount = applied_swing_factor * fund_nav
        else:  # config.cost_basis == "flow"
            swing_cost_amount = applied_swing_factor * redemption_amount

        return SwingPricingResult(
            swing_pricing_activated=True,
            raw_swing_factor=raw_swing_factor,
            applied_swing_factor=applied_swing_factor,
            exceeded_maximum_factor=exceeded_maximum,
            swing_cost_amount=swing_cost_amount,
            redemption_rate=redemption_rate,
            cost_basis=config.cost_basis,
        )
