"""Contagion linkage engine.

Implements simple contagion triggering based on linked fund liquidity stress.

This engine checks whether any linked fund's coverage ratio falls below a
threshold, triggering contagion that increases redemption demand in the
next month via a configured multiplier.

Contagion logic:
- Disabled config: no contagion (returns False)
- Enabled config + linked fund below threshold: contagion triggered
- Contagion applies a multiplier to next month's redemption demand
- No graph/network effects; purely threshold-based
"""

from decimal import Decimal

from manco_risk.risk.liquidity.lmt.models import ContagionConfig, LiquiditySnapshot


class ContagionEngine:
    """Contagion linkage calculator.

    Checks whether any linked fund's coverage ratio falls below the contagion
    trigger threshold, indicating liquidity stress that propagates to this fund
    via increased redemption demand in the next month.

    This engine is stateless and deterministic. It does not:
    - Maintain state or linkage graphs
    - Fetch external data
    - Modify inputs

    It only checks: is any linked fund under stress?
    """

    def calculate(
        self,
        linked_fund_snapshots: dict[str, list[LiquiditySnapshot]] | None,
        current_month_index: int,
        config: ContagionConfig,
    ) -> bool:
        """Check if contagion is triggered.

        Args:
            linked_fund_snapshots: Dict mapping fund ID → list of 12 monthly snapshots.
              None if no linked funds. Key type is str (fund ID).
            current_month_index: Current month (0-11). Used to index into snapshot list.
            config: Contagion configuration (threshold, multiplier, enabled flag).

        Returns:
            bool: True if contagion triggered (any linked fund below threshold).
              False if contagion disabled, no linked snapshots, or all linked funds
              are above threshold.

        Raises:
            ValueError: If month index is out of range (< 0 or >= 12).
        """
        # Validate month index first
        if current_month_index < 0 or current_month_index >= 12:
            raise ValueError(
                f"current_month_index must be in range [0, 11], got {current_month_index}"
            )

        # Contagion disabled
        if not config.enabled:
            return False

        # No linked fund data provided
        if not linked_fund_snapshots:
            return False

        # Check if any linked fund is below threshold
        # Note: if config.enabled is True, contagion_trigger_threshold is guaranteed non-None
        # by ContagionConfig validators
        threshold = config.contagion_trigger_threshold
        assert threshold is not None  # For type checker

        for fund_id, snapshots in linked_fund_snapshots.items():
            if len(snapshots) != 12:
                raise ValueError(
                    f"linked_fund_snapshots[{fund_id}] must have exactly 12 snapshots, "
                    f"got {len(snapshots)}"
                )

            # Get snapshot for current month
            snapshot = snapshots[current_month_index]
            if snapshot.coverage_ratio < threshold:
                # Linked fund is under stress
                return True

        # No linked fund is under stress
        return False

    @staticmethod
    def calculate_multiplier_impact(
        current_redemption: Decimal,
        multiplier: Decimal,
    ) -> Decimal:
        """Calculate impact of contagion multiplier on redemption demand.

        Args:
            current_redemption: Current month's redemption amount.
            multiplier: Contagion multiplier (e.g., 1.2 = 120%).

        Returns:
            Decimal: Additional redemption demand due to contagion.
              Formula: (multiplier - 1.0) * current_redemption
              E.g., 1.2 multiplier on 10M = 2M additional (10M * 0.2)
        """
        if multiplier < Decimal("1.0"):
            raise ValueError(f"contagion_multiplier must be >= 1.0, got {multiplier}")

        adjustment = multiplier - Decimal("1.0")
        return current_redemption * adjustment
