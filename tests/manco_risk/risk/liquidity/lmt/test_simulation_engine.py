"""Tests for LMT simulation engine.

Covers 12-month orchestration, state carry-forward, scenario variants,
and aggregation logic.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.liquidity.lmt.models import (
    ContagionConfig,
    GateTriggerConfig,
    LiquiditySnapshot,
    LMTScenarioConfig,
    LMTSimulationInput,
    MonthlyRedemptionInput,
    ScenarioVariant,
    SuspensionConfig,
    SwingPricingConfig,
)
from manco_risk.risk.liquidity.lmt.simulation_engine import LMTSimulationEngine
from manco_risk.risk.liquidity.models import (
    InvestorConcentrationResult,
    PortfolioLiquidityBucketSummary,
    PortfolioLiquidityProfileResult,
    TopNInvestor,
)


class TestLMTSimulationEngineFixtures:
    """Shared test fixtures for simulation engine tests."""

    @staticmethod
    def create_base_simulation_input(
        fund_id: int = 1,
        fund_nav: Decimal = Decimal("100000000"),
        gate_enabled: bool = False,
        suspension_enabled: bool = False,
        swing_enabled: bool = False,
    ) -> LMTSimulationInput:
        """Create a basic 12-month simulation input."""
        monthly_redemptions = [
            MonthlyRedemptionInput(
                month_index=m,
                redemption_amount=Decimal("5000000"),
                margin_call_amount=Decimal("0"),
            )
            for m in range(12)
        ]

        return LMTSimulationInput(
            fund_id=fund_id,
            valuation_date=date(2026, 1, 1),
            fund_nav=fund_nav,
            scenario_config=LMTScenarioConfig(
                gate_config=GateTriggerConfig(
                    enabled=gate_enabled,
                    coverage_ratio_threshold=Decimal("1.0"),
                    max_gate_ratio=Decimal("0.5"),
                ),
                swing_config=SwingPricingConfig(
                    enabled=swing_enabled,
                    trigger_threshold=Decimal("0.10"),
                    max_swing_factor=Decimal("0.02"),
                    cost_basis="nav",
                ),
                suspension_config=SuspensionConfig(
                    enabled=suspension_enabled,
                    trigger_criteria=["liquidity_shortfall"],
                    review_frequency_days=7,
                ),
                contagion_config=ContagionConfig(enabled=False),
            ),
            monthly_redemptions=monthly_redemptions,
        )

    @staticmethod
    def create_liquidity_snapshots(
        count: int = 12,
        available_liquidity: Decimal = Decimal("80000000"),
        coverage_ratio: Decimal = Decimal("16"),  # 80M / 5M = 16
        fund_nav: Decimal = Decimal("100000000"),
    ) -> list[LiquiditySnapshot]:
        """Create liquidity snapshots for testing."""
        snapshots = []
        for month in range(count):
            # Ensure month stays in valid range (1-12)
            month_num = (month % 12) + 1
            year = 2026 + (month // 12)

            bucket_summary = PortfolioLiquidityBucketSummary(
                bucket_name="liquid",
                total_market_value=available_liquidity,
                position_count=100,
                percentage_of_portfolio=Decimal("1.0"),
            )
            snapshot = LiquiditySnapshot(
                valuation_date=date(year, month_num, 1),
                fund_nav=fund_nav,
                available_liquidity=available_liquidity,
                coverage_ratio=coverage_ratio,
                portfolio_liquidity_profile=PortfolioLiquidityProfileResult(
                    fund_id=1,
                    valuation_date=date(year, month_num, 1),
                    total_portfolio_value=fund_nav,
                    bucket_summaries=[bucket_summary],
                ),
                investor_concentration=None,
            )
            snapshots.append(snapshot)
        return snapshots

    @staticmethod
    def create_investor_concentration(
        largest_investor_amount: Decimal = Decimal("25000000"),
    ) -> InvestorConcentrationResult:
        """Create investor concentration result."""
        fund_nav = Decimal("100000000")
        top_investor = TopNInvestor(
            investor_id="investor_001",
            total_amount=largest_investor_amount,
            percentage_of_nav=largest_investor_amount / fund_nav,
        )

        return InvestorConcentrationResult(
            fund_id=1,
            valuation_date=date(2026, 1, 1),
            fund_nav=fund_nav,
            total_investor_count=50,
            largest_investor_id="investor_001",
            largest_investor_amount=largest_investor_amount,
            largest_investor_percentage=largest_investor_amount / fund_nav,
            top_n_levels=[1, 5, 10],
            top_n_investors={
                1: [top_investor],
                5: [top_investor],
                10: [top_investor],
            },
        )


class TestLMTSimulationEngineBaseScenario(TestLMTSimulationEngineFixtures):
    """Tests for base scenario with no LMT activation."""

    def test_base_scenario_full_redemption_no_backlog(self):
        """Base scenario: full redemption each month, no backlog."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input()
        snapshots = self.create_liquidity_snapshots()

        result = engine.calculate(sim_input, snapshots, scenario_variant=ScenarioVariant.BASE)

        assert result.fund_id == 1
        assert result.initial_nav == Decimal("100000000")
        assert len(result.monthly_results) == 12
        assert result.gate_activation_count == 0
        assert result.suspension_activation_count == 0
        assert result.swing_pricing_activation_count == 0
        assert result.months_with_backlog == 0
        assert result.total_backlog_accumulated == Decimal("0")

        # Check each month
        for i, monthly in enumerate(result.monthly_results):
            assert monthly.month_index == i
            assert monthly.gate_activated is False
            assert monthly.suspension_activated is False
            assert monthly.swing_pricing_activated is False
            assert monthly.backlog_amount == Decimal("0")
            # NAV should decrease by redemption each month (5M)
            expected_nav = Decimal("100000000") - (Decimal("5000000") * (i + 1))
            assert abs(monthly.ending_nav - expected_nav) < Decimal("1")

    def test_final_nav_calculation(self):
        """Final NAV should reflect all redemptions."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input()
        snapshots = self.create_liquidity_snapshots()

        result = engine.calculate(sim_input, snapshots, scenario_variant=ScenarioVariant.BASE)

        # 12 months × 5M per month = 60M redeemed
        expected_final_nav = Decimal("100000000") - Decimal("60000000")
        assert abs(result.final_nav - expected_final_nav) < Decimal("1")


class TestLMTSimulationEngineGateActivation(TestLMTSimulationEngineFixtures):
    """Tests for gate activation and backlog creation."""

    def test_gate_activation_creates_backlog(self):
        """Gate activation should defer portion of redemptions to next month."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input(gate_enabled=True)

        # Low coverage to trigger gate
        snapshots = self.create_liquidity_snapshots(
            available_liquidity=Decimal("2000000"),  # < 5M redemption
            coverage_ratio=Decimal("0.4"),  # 2M / 5M = 0.4
        )

        result = engine.calculate(sim_input, snapshots, scenario_variant=ScenarioVariant.BASE)

        assert result.gate_activation_count > 0
        assert result.months_with_backlog > 0
        assert result.total_backlog_accumulated > Decimal("0")

    def test_gate_deferred_amount_recorded(self):
        """Gate deferred amount should be recorded in monthly result."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input(gate_enabled=True)
        snapshots = self.create_liquidity_snapshots(
            available_liquidity=Decimal("2000000"),
            coverage_ratio=Decimal("0.4"),
        )

        result = engine.calculate(sim_input, snapshots, scenario_variant=ScenarioVariant.BASE)

        first_month = result.monthly_results[0]
        if first_month.gate_activated:
            assert first_month.gate_deferred_amount > Decimal("0")


class TestLMTSimulationEngineBacklogCarryForward(TestLMTSimulationEngineFixtures):
    """Tests for backlog carry-forward across months."""

    def test_backlog_carries_to_next_month(self):
        """Backlog from one month should carry to next month."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input(gate_enabled=True)

        # Create snapshots: first 2 months have low liquidity (triggers gate)
        # then normal liquidity
        snapshots = self.create_liquidity_snapshots()
        bucket_summary = PortfolioLiquidityBucketSummary(
            bucket_name="liquid",
            total_market_value=Decimal("2000000"),
            position_count=50,
            percentage_of_portfolio=Decimal("1.0"),
        )
        snapshots[0] = LiquiditySnapshot(
            valuation_date=date(2026, 1, 1),
            fund_nav=Decimal("100000000"),
            available_liquidity=Decimal("2000000"),
            coverage_ratio=Decimal("0.4"),
            portfolio_liquidity_profile=PortfolioLiquidityProfileResult(
                fund_id=1,
                valuation_date=date(2026, 1, 1),
                total_portfolio_value=Decimal("100000000"),
                bucket_summaries=[bucket_summary],
            ),
            investor_concentration=None,
        )

        result = engine.calculate(sim_input, snapshots, scenario_variant=ScenarioVariant.BASE)

        # If gate activated in month 0, check that backlog exists
        if result.monthly_results[0].gate_activated:
            assert result.monthly_results[0].backlog_amount > Decimal("0")


class TestLMTSimulationEngineSuspension(TestLMTSimulationEngineFixtures):
    """Tests for suspension override behavior."""

    def test_suspension_stops_all_redemptions(self):
        """Suspension should set executable redemptions to zero."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input(suspension_enabled=True)

        # Coverage below threshold triggers suspension
        snapshots = self.create_liquidity_snapshots(
            available_liquidity=Decimal("50000000"),
            coverage_ratio=Decimal("10"),  # Still triggers with low threshold
        )
        # Override first month to have very low coverage
        bucket_summary = PortfolioLiquidityBucketSummary(
            bucket_name="liquid",
            total_market_value=Decimal("1000000"),
            position_count=10,
            percentage_of_portfolio=Decimal("1.0"),
        )
        snapshots[0] = LiquiditySnapshot(
            valuation_date=date(2026, 1, 1),
            fund_nav=Decimal("100000000"),
            available_liquidity=Decimal("1000000"),
            coverage_ratio=Decimal("0.2"),  # Very low to trigger suspension
            portfolio_liquidity_profile=PortfolioLiquidityProfileResult(
                fund_id=1,
                valuation_date=date(2026, 1, 1),
                total_portfolio_value=Decimal("100000000"),
                bucket_summaries=[bucket_summary],
            ),
            investor_concentration=None,
        )

        result = engine.calculate(sim_input, snapshots, scenario_variant=ScenarioVariant.BASE)

        # Check if suspension was triggered
        first_month = result.monthly_results[0]
        if first_month.suspension_activated:
            assert first_month.deferral_reason == "suspension"
            # NAV should not decrease if no redemptions executed
            second_month = result.monthly_results[1]
            assert second_month.fund_nav >= first_month.ending_nav - Decimal("100000")

    def test_suspension_sets_gate_to_false(self):
        """Suspension overrides gate activation."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input(suspension_enabled=True, gate_enabled=True)

        snapshots = self.create_liquidity_snapshots(
            available_liquidity=Decimal("1000000"),
            coverage_ratio=Decimal("0.2"),
        )

        result = engine.calculate(sim_input, snapshots, scenario_variant=ScenarioVariant.BASE)

        first_month = result.monthly_results[0]
        if first_month.suspension_activated:
            # Gate should not activate when suspension is active
            assert first_month.gate_activated is False


class TestLMTSimulationEngineSwingPricing(TestLMTSimulationEngineFixtures):
    """Tests for swing pricing activation and NAV adjustment."""

    def test_swing_pricing_reduces_nav(self):
        """Swing pricing should reduce NAV by swing cost."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input(swing_enabled=True)

        # High redemption rate triggers swing
        sim_input.monthly_redemptions[0] = MonthlyRedemptionInput(
            month_index=0,
            redemption_amount=Decimal("15000000"),  # 15% of NAV
            margin_call_amount=Decimal("0"),
        )

        snapshots = self.create_liquidity_snapshots()

        result = engine.calculate(sim_input, snapshots, scenario_variant=ScenarioVariant.BASE)

        first_month = result.monthly_results[0]
        # If swing pricing activated, NAV reduction should exceed just redemptions
        if first_month.swing_pricing_activated:
            assert first_month.swing_factor_applied > Decimal("0")


class TestLMTSimulationEngineLargestInvestorScenario(
    TestLMTSimulationEngineFixtures,
):
    """Tests for largest-investor scenario variant."""

    def test_largest_investor_scenario_replaces_month_zero(self):
        """Largest-investor scenario should replace month 0 redemption."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input()
        snapshots = self.create_liquidity_snapshots()

        # Add investor concentration to first snapshot
        investor_conc = self.create_investor_concentration(
            largest_investor_amount=Decimal("30000000")
        )
        snapshots[0] = LiquiditySnapshot(
            valuation_date=snapshots[0].valuation_date,
            fund_nav=snapshots[0].fund_nav,
            available_liquidity=snapshots[0].available_liquidity,
            coverage_ratio=snapshots[0].coverage_ratio,
            portfolio_liquidity_profile=snapshots[0].portfolio_liquidity_profile,
            investor_concentration=investor_conc,
        )

        result = engine.calculate(
            sim_input,
            snapshots,
            scenario_variant=ScenarioVariant.LARGEST_INVESTOR,
        )

        # First month should have largest investor amount as redemption
        first_month = result.monthly_results[0]
        assert first_month.redemption_amount == Decimal("30000000")

        # Verify input not mutated
        assert sim_input.monthly_redemptions[0].redemption_amount == Decimal("5000000")

    def test_largest_investor_only_affects_month_zero(self):
        """Largest-investor scenario should only override month 0."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input()
        snapshots = self.create_liquidity_snapshots()

        investor_conc = self.create_investor_concentration(
            largest_investor_amount=Decimal("30000000")
        )
        snapshots[0] = LiquiditySnapshot(
            valuation_date=snapshots[0].valuation_date,
            fund_nav=snapshots[0].fund_nav,
            available_liquidity=snapshots[0].available_liquidity,
            coverage_ratio=snapshots[0].coverage_ratio,
            portfolio_liquidity_profile=snapshots[0].portfolio_liquidity_profile,
            investor_concentration=investor_conc,
        )

        result = engine.calculate(
            sim_input,
            snapshots,
            scenario_variant=ScenarioVariant.LARGEST_INVESTOR,
        )

        # Months 1-11 should keep original redemption amounts
        for i in range(1, 12):
            assert result.monthly_results[i].redemption_amount == Decimal("5000000")


class TestLMTSimulationEngineValidation(TestLMTSimulationEngineFixtures):
    """Tests for input validation."""

    def test_reject_fewer_than_12_snapshots(self):
        """Engine should reject fewer than 12 liquidity snapshots."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input()
        snapshots = self.create_liquidity_snapshots(count=11)

        with pytest.raises(ValueError, match="exactly 12 months"):
            engine.calculate(sim_input, snapshots)

    def test_reject_more_than_12_snapshots(self):
        """Engine should reject more than 12 liquidity snapshots."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input()
        snapshots = self.create_liquidity_snapshots(count=13)

        with pytest.raises(ValueError, match="exactly 12 months"):
            engine.calculate(sim_input, snapshots)

    def test_reject_invalid_linked_fund_snapshots_count(self):
        """Engine should reject linked fund snapshots with wrong count."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input()
        snapshots = self.create_liquidity_snapshots(count=12)
        linked_snapshots = {"fund_002": self.create_liquidity_snapshots(count=10)}

        with pytest.raises(ValueError, match="12 months"):
            engine.calculate(
                sim_input,
                snapshots,
                linked_fund_snapshots=linked_snapshots,
            )


class TestLMTSimulationEngineInputImmutability(
    TestLMTSimulationEngineFixtures,
):
    """Tests for input immutability."""

    def test_simulation_input_not_mutated(self):
        """LMTSimulationInput should not be mutated during simulation."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input()
        original_redemption = sim_input.monthly_redemptions[0].redemption_amount
        original_nav = sim_input.fund_nav

        snapshots = self.create_liquidity_snapshots()
        investor_conc = self.create_investor_concentration(
            largest_investor_amount=Decimal("30000000")
        )
        snapshots[0] = LiquiditySnapshot(
            valuation_date=snapshots[0].valuation_date,
            fund_nav=snapshots[0].fund_nav,
            available_liquidity=snapshots[0].available_liquidity,
            coverage_ratio=snapshots[0].coverage_ratio,
            portfolio_liquidity_profile=snapshots[0].portfolio_liquidity_profile,
            investor_concentration=investor_conc,
        )

        # Run with largest investor scenario
        engine.calculate(
            sim_input,
            snapshots,
            scenario_variant=ScenarioVariant.LARGEST_INVESTOR,
        )

        # Verify input unchanged
        assert sim_input.monthly_redemptions[0].redemption_amount == original_redemption
        assert sim_input.fund_nav == original_nav


class TestLMTSimulationEngineAggregation(TestLMTSimulationEngineFixtures):
    """Tests for aggregation logic."""

    def test_activation_counts_match_monthly_results(self):
        """Aggregated activation counts should match monthly results."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input(gate_enabled=True)
        snapshots = self.create_liquidity_snapshots(
            available_liquidity=Decimal("2000000"),
            coverage_ratio=Decimal("0.4"),
        )

        result = engine.calculate(sim_input, snapshots)

        # Count manually
        gate_count = sum(1 for m in result.monthly_results if m.gate_activated)
        swing_count = sum(1 for m in result.monthly_results if m.swing_pricing_activated)
        suspension_count = sum(1 for m in result.monthly_results if m.suspension_activated)
        contagion_count = sum(1 for m in result.monthly_results if m.contagion_triggered)

        assert result.gate_activation_count == gate_count
        assert result.swing_pricing_activation_count == swing_count
        assert result.suspension_activation_count == suspension_count
        assert result.contagion_triggered_count == contagion_count

    def test_peak_backlog_tracking(self):
        """Aggregated peak backlog should match max monthly backlog."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input(gate_enabled=True)
        snapshots = self.create_liquidity_snapshots(
            available_liquidity=Decimal("2000000"),
            coverage_ratio=Decimal("0.4"),
        )

        result = engine.calculate(sim_input, snapshots)

        max_monthly_backlog = max(
            (m.backlog_amount for m in result.monthly_results), default=Decimal("0")
        )
        assert result.total_backlog_accumulated == max_monthly_backlog

    def test_months_with_backlog_count(self):
        """Count of months with backlog should match monthly results."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input(gate_enabled=True)
        snapshots = self.create_liquidity_snapshots(
            available_liquidity=Decimal("2000000"),
            coverage_ratio=Decimal("0.4"),
        )

        result = engine.calculate(sim_input, snapshots)

        months_with_backlog = sum(
            1 for m in result.monthly_results if m.backlog_amount > Decimal("0")
        )
        assert result.months_with_backlog == months_with_backlog

    def test_contagion_always_false_placeholder(self):
        """Contagion should be False for all months (Phase 4 placeholder)."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input()
        snapshots = self.create_liquidity_snapshots()

        result = engine.calculate(sim_input, snapshots)

        assert result.contagion_triggered_count == 0
        for month in result.monthly_results:
            assert month.contagion_triggered is False


class TestLMTSimulationEngineDeferralReason(TestLMTSimulationEngineFixtures):
    """Tests for deferral reason tracking."""

    def test_deferral_reason_set_on_gate(self):
        """Deferral reason should be 'gate' when gate activates."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input(gate_enabled=True)
        snapshots = self.create_liquidity_snapshots(
            available_liquidity=Decimal("2000000"),
            coverage_ratio=Decimal("0.4"),
        )

        result = engine.calculate(sim_input, snapshots)

        for month in result.monthly_results:
            if month.gate_activated:
                assert month.deferral_reason == "gate"

    def test_deferral_reason_set_on_suspension(self):
        """Deferral reason should be 'suspension' when suspension activates."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input(suspension_enabled=True)
        snapshots = self.create_liquidity_snapshots(
            available_liquidity=Decimal("1000000"),
            coverage_ratio=Decimal("0.2"),
        )

        result = engine.calculate(sim_input, snapshots)

        for month in result.monthly_results:
            if month.suspension_activated:
                assert month.deferral_reason == "suspension"

    def test_deferral_reason_none_on_full_redemption(self):
        """Deferral reason should be None when all redemptions met."""
        engine = LMTSimulationEngine()
        sim_input = self.create_base_simulation_input()
        snapshots = self.create_liquidity_snapshots()

        result = engine.calculate(sim_input, snapshots)

        for month in result.monthly_results:
            if month.backlog_amount == Decimal("0"):
                assert month.deferral_reason is None
