"""Redemption backlog accounting engine.

Implements backlog tracking: records how much redemption demand is deferred
to future months due to insufficient liquidity or other constraints.

The backlog engine is a calculator, not a decision-maker. It does not decide
how much to redeem; it only records the monthly accounting given the amount
redeemed and reason for any deferral.
"""

from decimal import Decimal

from manco_risk.risk.liquidity.lmt.models import BacklogState


class BacklogEngine:
    """Redemption backlog accounting and tracking engine.

    Computes monthly backlog state: tracks how much redemption demand
    carries forward to future months.

    This engine is stateless and deterministic. It does not:
    - Decide how much to redeem (that's decided by liquidity/LMT engines)
    - Apply gates, swing pricing, suspension, contagion, or liquidity rules
    - Reduce next-month liquidity (that's for the future orchestrator)

    It only records:
    - Total redemption demand (beginning backlog + new redemptions)
    - Amount actually redeemed
    - Amount deferred to next month
    - Reason for deferral (if any)
    """

    def calculate(
        self,
        month_index: int,
        beginning_backlog: Decimal,
        new_redemptions: Decimal,
        redeemed_in_month: Decimal,
        deferral_reason: str | None = None,
    ) -> BacklogState:
        """Calculate monthly backlog state.

        Records redemption accounting for a single month: beginning backlog,
        new requests, amount redeemed, and amount deferred to next month.

        Args:
            month_index: 0-based month index (int, >= 0).
            beginning_backlog: Backlog carried from prior month (Decimal, >= 0).
            new_redemptions: New redemption requests in this month (Decimal, >= 0).
            redeemed_in_month: Amount actually redeemed (Decimal, >= 0).
              Must not exceed beginning_backlog + new_redemptions.
            deferral_reason: Why redemptions were deferred, if any (str or None).
              Only recorded if ending_backlog > 0. Caller-provided.
              Examples: "gate", "insufficient_liquidity", "suspension".

        Returns:
            BacklogState with complete monthly accounting.

        Raises:
            ValueError: If inputs violate constraints (negative amounts,
              redeemed exceeds total due, invalid month index, etc.).
        """
        if month_index < 0:
            raise ValueError("month_index must be non-negative")
        if beginning_backlog < 0:
            raise ValueError("beginning_backlog must be non-negative")
        if new_redemptions < 0:
            raise ValueError("new_redemptions must be non-negative")
        if redeemed_in_month < 0:
            raise ValueError("redeemed_in_month must be non-negative")

        if deferral_reason is not None and not deferral_reason.strip():
            raise ValueError("deferral_reason must be non-empty or None")

        # Calculate total redemption demand
        total_redemptions_due = beginning_backlog + new_redemptions

        # Validate that redeemed does not exceed total
        if redeemed_in_month > total_redemptions_due:
            raise ValueError(
                f"redeemed_in_month ({redeemed_in_month}) cannot exceed "
                f"total_redemptions_due ({total_redemptions_due})"
            )

        # Calculate ending backlog
        ending_backlog = total_redemptions_due - redeemed_in_month

        # Deferral reason only retained if ending backlog is positive
        # If all redemptions were met, reason should be None
        final_deferral_reason = deferral_reason if ending_backlog > Decimal("0") else None

        # Create and return BacklogState
        # BacklogState model will validate all accounting relationships
        return BacklogState(
            month_index=month_index,
            beginning_backlog=beginning_backlog,
            new_redemptions=new_redemptions,
            total_redemptions_due=total_redemptions_due,
            redeemed_in_month=redeemed_in_month,
            ending_backlog=ending_backlog,
            deferral_reason=final_deferral_reason,
        )
