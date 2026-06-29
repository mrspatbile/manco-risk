"""Subscription/redemption suspension engine.

Implements suspension logic: temporary exceptional control when the fund cannot
operate normal subscriptions/redemptions fairly or safely.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.risk.liquidity.lmt.models import SuspensionConfig


class SuspensionResult(BaseModel):
    """Suspension evaluation result.

    Output of suspension trigger logic: whether suspension was activated,
    the reason (if any), and which criteria triggered it.

    Fields:
    - suspension_activated: Whether suspension was triggered and is active.
    - suspension_reason: Why suspension was activated (required if activated).
      Example: "liquidity_shortfall", "nav_unreliable", "market_disruption".
    - triggered_criteria: List of criteria names that were active and matched
      config. Empty if not activated or no matches. Preserved for traceability.
    """

    suspension_activated: bool
    suspension_reason: str | None
    triggered_criteria: list[str]

    model_config = ConfigDict(frozen=True)

    @field_validator("suspension_reason")
    @classmethod
    def validate_suspension_reason(cls, v: str | None, info) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("suspension_reason must be non-empty or None")
        if info.data.get("suspension_activated") and not v:
            raise ValueError("suspension_reason required if suspension_activated=True")
        if not info.data.get("suspension_activated") and v:
            raise ValueError("suspension_reason should be None if suspension_activated=False")
        return v.strip() if v else None

    @field_validator("triggered_criteria")
    @classmethod
    def validate_triggered_criteria(cls, v: list[str]) -> list[str]:
        for criterion in v:
            if not criterion or not criterion.strip():
                raise ValueError("Each triggered_criteria entry must be non-empty")
        return v


class SuspensionEngine:
    """Subscription/redemption suspension trigger engine.

    When exceptional conditions arise, suspension temporarily halts normal
    subscriptions and redemptions to protect the fund and investors.

    Behavior:
    - If suspension is disabled: no suspension.
    - If redemption amount is zero: no suspension.
    - If suspension is enabled and any triggered criterion matches config:
      activation triggered with matching criterion as reason.
    - If suspension is enabled but no criteria match: no suspension.

    This engine is stateless and deterministic; it evaluates suspension logic
    for a single period given current conditions and configuration.
    """

    def calculate(
        self,
        redemption_amount: Decimal,
        config: SuspensionConfig,
        triggered_criteria: list[str],
    ) -> SuspensionResult:
        """Evaluate suspension activation.

        Args:
            redemption_amount: Redemption requested (Decimal, >= 0).
            config: Suspension configuration.
            triggered_criteria: List of currently-active condition names.
              Each is checked against config.trigger_criteria.

        Returns:
            SuspensionResult with activation status, reason, and matching criteria.

        Raises:
            ValueError: If redemption_amount is negative.
        """
        if redemption_amount < 0:
            raise ValueError("redemption_amount must be non-negative")

        # If suspension is disabled, no suspension
        if not config.enabled:
            return SuspensionResult(
                suspension_activated=False,
                suspension_reason=None,
                triggered_criteria=[],
            )

        # If redemption amount is zero, no suspension
        if redemption_amount == Decimal("0"):
            return SuspensionResult(
                suspension_activated=False,
                suspension_reason=None,
                triggered_criteria=[],
            )

        # Check which triggered criteria match config
        config_criteria_set = set(config.trigger_criteria)
        matching_criteria = [c for c in triggered_criteria if c in config_criteria_set]

        # If no matches, no suspension
        if not matching_criteria:
            return SuspensionResult(
                suspension_activated=False,
                suspension_reason=None,
                triggered_criteria=[],
            )

        # At least one match: activate suspension
        # Use first matching criterion as reason for traceability
        reason = matching_criteria[0]

        return SuspensionResult(
            suspension_activated=True,
            suspension_reason=reason,
            triggered_criteria=matching_criteria,
        )
