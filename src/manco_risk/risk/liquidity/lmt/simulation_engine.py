"""LMT simulation engine.

Orchestrates 12-month liquidity management tools (LMT) simulation.

This engine coordinates stateless calculation engines (suspension, gate, swing, backlog)
in a deterministic sequence for each month. The orchestrator owns all simulation state
(NAV, backlog, date) and produces monthly and aggregated results.

The engine does NOT:
- Call Issue #6 liquidity engines (consumes pre-computed snapshots only)
- Mutate input models (builds local immutable paths for scenarios)
- Perform reporting, UI, or export operations
- Implement contagion yet (placeholder logic only)
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from manco_risk.risk.liquidity.lmt.backlog_engine import BacklogEngine
from manco_risk.risk.liquidity.lmt.contagion_engine import ContagionEngine
from manco_risk.risk.liquidity.lmt.gate_engine import GateEngine
from manco_risk.risk.liquidity.lmt.models import (
    LiquiditySnapshot,
    LMTMonthlyResult,
    LMTSimulationInput,
    LMTSimulationResult,
    MonthlyRedemptionInput,
    ScenarioVariant,
)
from manco_risk.risk.liquidity.lmt.suspension_engine import SuspensionEngine
from manco_risk.risk.liquidity.lmt.swing_pricing_engine import SwingPricingEngine

if TYPE_CHECKING:
    pass


class LMTSimulationEngine:
    """LMT simulation orchestrator for 12-month pathway.

    Coordinates stateless LMT engines (suspension, gate, swing, backlog) in a
    deterministic sequence. The orchestrator maintains simulation state (NAV,
    backlog) and produces monthly and aggregated results.

    Behavior:
    - Accepts pre-computed LiquiditySnapshot objects (from Issue #6)
    - Does NOT mutate input models
    - Builds immutable local redemption paths for scenario variants
    - Executes engines in fixed order: suspension → gate → swing → backlog → NAV
    - Returns complete LMTSimulationResult with 12 monthly results
    """

    def __init__(self):
        """Initialize engine with stateless calculators."""
        self.suspension_engine = SuspensionEngine()
        self.gate_engine = GateEngine()
        self.swing_engine = SwingPricingEngine()
        self.backlog_engine = BacklogEngine()
        self.contagion_engine = ContagionEngine()

    def calculate(
        self,
        simulation_input: LMTSimulationInput,
        liquidity_snapshots: list[LiquiditySnapshot],
        linked_fund_snapshots: dict[str, list[LiquiditySnapshot]] | None = None,
        scenario_variant: ScenarioVariant = ScenarioVariant.BASE,
    ) -> LMTSimulationResult:
        """Run 12-month LMT simulation.

        Args:
            simulation_input: Configuration, initial NAV, and scenario config.
            liquidity_snapshots: Pre-computed monthly liquidity snapshots (exactly 12).
            linked_fund_snapshots: Optional linked fund snapshots for contagion.
              Key: fund ID; Value: list of 12 monthly snapshots.
            scenario_variant: BASE or LARGEST_INVESTOR (default BASE).

        Returns:
            LMTSimulationResult with 12 monthly outcomes and aggregations.

        Raises:
            ValueError: If liquidity_snapshots length != 12 or indices mismatch.
        """
        # Validate inputs
        if len(liquidity_snapshots) != 12:
            raise ValueError(
                f"liquidity_snapshots must have exactly 12 months, got {len(liquidity_snapshots)}"
            )

        if linked_fund_snapshots:
            for fund_id, snapshots in linked_fund_snapshots.items():
                if len(snapshots) != 12:
                    raise ValueError(
                        f"linked_fund_snapshots[{fund_id}] must have 12 months, got {len(snapshots)}"
                    )

        # Build immutable local monthly redemption path
        monthly_redemptions = self._prepare_monthly_redemptions(
            simulation_input.monthly_redemptions,
            scenario_variant,
            liquidity_snapshots,
        )

        # Initialize simulation state
        current_nav = simulation_input.fund_nav
        current_backlog = Decimal("0")
        monthly_results: list[LMTMonthlyResult] = []

        # 12-month loop
        for month_index in range(12):
            snapshot = liquidity_snapshots[month_index]
            monthly_input = monthly_redemptions[month_index]

            # A. Calculate total redemption demand
            total_redemption_demand = current_backlog + monthly_input.redemption_amount

            # B. EVALUATE SUSPENSION (first — it's an override)
            triggered_criteria = self._build_triggered_criteria(snapshot)
            suspension_result = self.suspension_engine.calculate(
                redemption_amount=total_redemption_demand,
                config=simulation_input.scenario_config.suspension_config,
                triggered_criteria=triggered_criteria,
            )

            # Initialize deferral reason
            deferral_reason: str | None = None

            if suspension_result.suspension_activated:
                # Suspension overrides everything; no redemptions
                redemption_executable = Decimal("0")
                gate_activated = False
                gate_deferred_amount = Decimal("0")
                swing_pricing_activated = False
                swing_factor_applied = Decimal("0")
                swing_cost = Decimal("0")
                deferral_reason = "suspension"
            else:
                # C. EVALUATE GATE
                gate_result = self.gate_engine.calculate(
                    redemption_amount=total_redemption_demand,
                    coverage_ratio=snapshot.coverage_ratio,
                    config=simulation_input.scenario_config.gate_config,
                )
                gate_activated = gate_result.gate_activated
                gate_deferred_amount = gate_result.deferred_amount

                # D. EVALUATE SWING PRICING
                # Estimated liquidity cost from shortfall (if coverage < 1.0)
                estimated_liquidity_cost = max(
                    total_redemption_demand - snapshot.available_liquidity,
                    Decimal("0"),
                )

                swing_result = self.swing_engine.calculate(
                    redemption_amount=gate_result.executable_amount,
                    fund_nav=current_nav,
                    estimated_liquidity_cost=estimated_liquidity_cost,
                    config=simulation_input.scenario_config.swing_config,
                )
                swing_pricing_activated = swing_result.swing_pricing_activated
                swing_factor_applied = swing_result.applied_swing_factor
                swing_cost = (
                    swing_result.swing_cost_amount if swing_pricing_activated else Decimal("0")
                )

                # E. COMPUTE FINAL EXECUTABLE REDEMPTION
                redemption_executable = min(
                    gate_result.executable_amount,
                    snapshot.available_liquidity,
                )

                # F. DETERMINE DEFERRAL REASON
                if gate_activated and gate_deferred_amount > Decimal("0"):
                    deferral_reason = "gate"
                elif total_redemption_demand - redemption_executable > Decimal("0.01"):
                    deferral_reason = "insufficient_liquidity"

            # G. UPDATE BACKLOG (accounting only)
            backlog_result = self.backlog_engine.calculate(
                month_index=month_index,
                beginning_backlog=current_backlog,
                new_redemptions=monthly_input.redemption_amount + monthly_input.margin_call_amount,
                redeemed_in_month=redemption_executable,
            )

            # H. UPDATE NAV
            nav_after_redemption = current_nav - redemption_executable
            ending_nav = nav_after_redemption - swing_cost

            if ending_nav < Decimal("0"):
                raise ValueError(f"NAV cannot go negative at month {month_index}: {ending_nav}")

            # I. BUILD WARNINGS
            warnings = []
            if gate_activated:
                warnings.append("Gate activated")
            if suspension_result.suspension_activated:
                warnings.append("Fund suspension activated")
            if snapshot.coverage_ratio < Decimal("1.0"):
                warnings.append("Coverage ratio below 100%")
            if backlog_result.ending_backlog > current_nav * Decimal("0.1"):
                warnings.append("Backlog exceeds 10% of NAV")
            if scenario_variant == ScenarioVariant.LARGEST_INVESTOR and month_index == 0:
                warnings.append("Largest investor redemption scenario")

            # J. CHECK CONTAGION (before creating monthly result)
            contagion_triggered = self.contagion_engine.calculate(
                linked_fund_snapshots=linked_fund_snapshots,
                current_month_index=month_index,
                config=simulation_input.scenario_config.contagion_config,
            )

            # If contagion triggered and not month 11, apply multiplier to next month
            if contagion_triggered and month_index < 11:
                contagion_multiplier = (
                    simulation_input.scenario_config.contagion_config.contagion_multiplier
                )
                # Type guard: if contagion is triggered, multiplier is guaranteed non-None
                assert contagion_multiplier is not None
                additional_demand = ContagionEngine.calculate_multiplier_impact(
                    current_redemption=monthly_redemptions[month_index + 1].redemption_amount,
                    multiplier=contagion_multiplier,
                )
                # Create new MonthlyRedemptionInput with increased demand
                monthly_redemptions[month_index + 1] = MonthlyRedemptionInput(
                    month_index=month_index + 1,
                    redemption_amount=(
                        monthly_redemptions[month_index + 1].redemption_amount + additional_demand
                    ),
                    margin_call_amount=monthly_redemptions[month_index + 1].margin_call_amount,
                    description=(
                        f"{monthly_redemptions[month_index + 1].description or ''} "
                        f"(contagion adjustment: +{additional_demand})"
                    ).strip(),
                )

            # K. CREATE MONTHLY RESULT
            monthly_result = LMTMonthlyResult(
                month_index=month_index,
                valuation_date=snapshot.valuation_date,
                fund_nav=current_nav,
                redemption_amount=total_redemption_demand,
                available_liquidity=snapshot.available_liquidity,
                coverage_ratio=snapshot.coverage_ratio,
                gate_activated=gate_activated,
                gate_deferred_amount=gate_deferred_amount,
                swing_pricing_activated=swing_pricing_activated,
                swing_factor_applied=swing_factor_applied,
                suspension_activated=suspension_result.suspension_activated,
                suspension_reason=suspension_result.suspension_reason,
                contagion_triggered=contagion_triggered,
                ending_nav=ending_nav,
                backlog_amount=backlog_result.ending_backlog,
                deferral_reason=deferral_reason,
                warnings=warnings,
            )

            monthly_results.append(monthly_result)

            # L. CARRY STATE TO NEXT MONTH
            current_nav = ending_nav
            current_backlog = backlog_result.ending_backlog

        # L. AGGREGATE RESULTS
        total_redemptions = sum(
            m.ending_nav if m.month_index == 0 else Decimal("0") for m in monthly_results
        )
        # Actually compute total redeemed across all months
        total_redemptions = Decimal("0")
        for result in monthly_results:
            total_redemptions += result.redemption_amount - result.backlog_amount

        total_backlog_accumulated = max(
            (m.backlog_amount for m in monthly_results), default=Decimal("0")
        )
        months_with_backlog = sum(1 for m in monthly_results if m.backlog_amount > Decimal("0"))
        gate_activation_count = sum(1 for m in monthly_results if m.gate_activated)
        swing_pricing_activation_count = sum(
            1 for m in monthly_results if m.swing_pricing_activated
        )
        suspension_activation_count = sum(1 for m in monthly_results if m.suspension_activated)
        contagion_triggered_count = sum(1 for m in monthly_results if m.contagion_triggered)

        # Build simulation result
        return LMTSimulationResult(
            fund_id=simulation_input.fund_id,
            valuation_date=simulation_input.valuation_date,
            initial_nav=simulation_input.fund_nav,
            final_nav=monthly_results[-1].ending_nav,
            total_redemptions=total_redemptions,
            total_backlog_accumulated=total_backlog_accumulated,
            months_with_backlog=months_with_backlog,
            gate_activation_count=gate_activation_count,
            swing_pricing_activation_count=swing_pricing_activation_count,
            suspension_activation_count=suspension_activation_count,
            contagion_triggered_count=contagion_triggered_count,
            monthly_results=monthly_results,
            warnings=[],
        )

    @staticmethod
    def _prepare_monthly_redemptions(
        base_redemptions: list[MonthlyRedemptionInput],
        scenario_variant: ScenarioVariant,
        liquidity_snapshots: list[LiquiditySnapshot],
    ) -> list[MonthlyRedemptionInput]:
        """Build immutable monthly redemption path for scenario.

        Does not mutate input. Creates a local copy and modifies if needed.

        Args:
            base_redemptions: Base redemption scenario (from input).
            scenario_variant: Scenario type.
            liquidity_snapshots: For looking up investor concentration.

        Returns:
            List of 12 MonthlyRedemptionInput objects (may be modified copy).
        """
        # Copy base (immutable)
        path = list(base_redemptions)

        # Modify copy if needed
        if scenario_variant == ScenarioVariant.LARGEST_INVESTOR:
            if liquidity_snapshots[0].investor_concentration:
                largest_investor_amount = liquidity_snapshots[
                    0
                ].investor_concentration.largest_investor_amount
                path[0] = MonthlyRedemptionInput(
                    month_index=0,
                    redemption_amount=largest_investor_amount,
                    margin_call_amount=base_redemptions[0].margin_call_amount,
                    description=f"Largest investor scenario: {largest_investor_amount}",
                )

        return path

    @staticmethod
    def _build_triggered_criteria(snapshot: LiquiditySnapshot) -> list[str]:
        """Build list of triggered suspension criteria based on liquidity snapshot.

        Args:
            snapshot: Monthly liquidity snapshot.

        Returns:
            List of triggered criterion names (e.g., ["liquidity_shortfall"]).
        """
        triggered = []

        # Criterion: liquidity_shortfall
        if snapshot.coverage_ratio < Decimal("1.0"):
            triggered.append("liquidity_shortfall")

        return triggered
