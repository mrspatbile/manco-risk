"""Redemption gate engine.

Implements gate logic: limits redemption execution when liquidity coverage
drops below configured thresholds, deferring the excess to future periods.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.risk.liquidity.lmt.models import GateTriggerConfig


class GateResult(BaseModel):
    """Redemption gate evaluation result.

    Output of gate trigger logic: whether gate activated and resulting
    split between executable and deferred redemption amounts.

    Fields:
    - gate_activated: Whether gate was triggered and is active.
    - executable_amount: Amount that can be redeemed immediately (Decimal, >= 0).
    - deferred_amount: Amount deferred to next period (Decimal, >= 0).
      deferred_amount = redemption_amount - executable_amount (always).
    """

    gate_activated: bool
    executable_amount: Decimal
    deferred_amount: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("executable_amount", "deferred_amount")
    @classmethod
    def validate_amounts(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("amount must be non-negative")
        return v

    @field_validator("deferred_amount")
    @classmethod
    def validate_deferred_amount_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("deferred_amount must be non-negative")
        return v


class GateEngine:
    """Redemption gate trigger and execution limit engine.

    When liquidity coverage falls below a configured threshold, the gate
    activates and limits the executable redemption to a fraction of total
    demand, deferring the remainder to future periods.

    Behavior:
    - If gate is disabled: execute full redemption request.
    - If redemption amount is zero: gate does not activate.
    - If coverage ratio >= threshold: no gate activation, execute full request.
    - If coverage ratio < threshold: gate activates.
      - executable_amount = min(redemption_amount, max_gate_ratio * redemption_amount)
      - deferred_amount = redemption_amount - executable_amount

    This engine is stateless; it computes gate logic for a single period
    given current liquidity and redemption demand.
    """

    def calculate(
        self,
        redemption_amount: Decimal,
        coverage_ratio: Decimal,
        config: GateTriggerConfig,
    ) -> GateResult:
        """Calculate gate activation and redemption split.

        Args:
            redemption_amount: Total redemption requested (Decimal, >= 0).
            coverage_ratio: Available liquidity / redemption_amount (Decimal, >= 0).
              Special case: if redemption_amount is 0, coverage_ratio may be None
              or infinity; gate logic handles this.
            config: Gate trigger configuration.

        Returns:
            GateResult with activation status and executable/deferred amounts.

        Raises:
            ValueError: If inputs violate basic constraints (negative amounts).
        """
        if redemption_amount < 0:
            raise ValueError("redemption_amount must be non-negative")
        if coverage_ratio < 0:
            raise ValueError("coverage_ratio must be non-negative")

        # If gate is disabled, execute full redemption
        if not config.enabled:
            return GateResult(
                gate_activated=False,
                executable_amount=redemption_amount,
                deferred_amount=Decimal("0"),
            )

        # If redemption is zero, gate does not activate
        if redemption_amount == Decimal("0"):
            return GateResult(
                gate_activated=False,
                executable_amount=Decimal("0"),
                deferred_amount=Decimal("0"),
            )

        # Check if liquidity is sufficient
        if coverage_ratio >= config.coverage_ratio_threshold:
            return GateResult(
                gate_activated=False,
                executable_amount=redemption_amount,
                deferred_amount=Decimal("0"),
            )

        # Gate activates: limit executable redemption
        max_executable = config.max_gate_ratio * redemption_amount
        executable_amount = min(redemption_amount, max_executable)
        deferred_amount = redemption_amount - executable_amount

        return GateResult(
            gate_activated=True,
            executable_amount=executable_amount,
            deferred_amount=deferred_amount,
        )
