"""Tests for LMT domain models: validation, consistency, and edge cases."""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.liquidity.lmt.models import (
    BacklogState,
    ContagionConfig,
    GateTriggerConfig,
    LMTMonthlyResult,
    LMTScenarioConfig,
    LMTSimulationInput,
    LMTSimulationResult,
    MonthlyRedemptionInput,
    SuspensionConfig,
    SwingPricingConfig,
)


class TestGateTriggerConfig:
    """Tests for GateTriggerConfig validation."""

    def test_valid_gate_config(self):
        """Create valid gate config with reasonable thresholds."""
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
            description="Standard gate configuration",
        )
        assert config.enabled is True
        assert config.coverage_ratio_threshold == Decimal("1.0")
        assert config.max_gate_ratio == Decimal("0.5")

    def test_disabled_gate_config(self):
        """Gate config can be disabled."""
        config = GateTriggerConfig(
            enabled=False,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )
        assert config.enabled is False

    def test_coverage_ratio_threshold_positive(self):
        """Coverage ratio threshold must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            GateTriggerConfig(
                enabled=True,
                coverage_ratio_threshold=Decimal("0"),
                max_gate_ratio=Decimal("0.5"),
            )

    def test_max_gate_ratio_in_range(self):
        """Max gate ratio must be in (0, 1]."""
        # Valid: 0.5, 1.0
        for ratio in [Decimal("0.1"), Decimal("0.5"), Decimal("1.0")]:
            config = GateTriggerConfig(
                enabled=True,
                coverage_ratio_threshold=Decimal("1.0"),
                max_gate_ratio=ratio,
            )
            assert config.max_gate_ratio == ratio

        # Invalid: 0, 1.1
        with pytest.raises(ValueError, match="must be in"):
            GateTriggerConfig(
                enabled=True,
                coverage_ratio_threshold=Decimal("1.0"),
                max_gate_ratio=Decimal("0"),
            )
        with pytest.raises(ValueError, match="must be in"):
            GateTriggerConfig(
                enabled=True,
                coverage_ratio_threshold=Decimal("1.0"),
                max_gate_ratio=Decimal("1.1"),
            )

    def test_description_stripped(self):
        """Description is stripped of whitespace."""
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
            description="  gate config  ",
        )
        assert config.description == "gate config"

    def test_description_empty_rejected(self):
        """Empty description string is rejected."""
        with pytest.raises(ValueError, match="must be non-empty"):
            GateTriggerConfig(
                enabled=True,
                coverage_ratio_threshold=Decimal("1.0"),
                max_gate_ratio=Decimal("0.5"),
                description="   ",
            )

    def test_frozen_model(self):
        """Model is immutable after creation."""
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )
        with pytest.raises(Exception):
            config.enabled = False


class TestSwingPricingConfig:
    """Tests for SwingPricingConfig validation."""

    def test_valid_swing_config_nav_basis(self):
        """Create valid swing config with NAV cost basis."""
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )
        assert config.enabled is True
        assert config.cost_basis == "nav"

    def test_valid_swing_config_flow_basis(self):
        """Create valid swing config with flow cost basis."""
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="flow",
        )
        assert config.cost_basis == "flow"

    def test_trigger_threshold_in_range(self):
        """Trigger threshold must be in [0, 1]."""
        # Valid
        for threshold in [Decimal("0"), Decimal("0.10"), Decimal("1.0")]:
            config = SwingPricingConfig(
                enabled=True,
                trigger_threshold=threshold,
                max_swing_factor=Decimal("0.02"),
                cost_basis="nav",
            )
            assert config.trigger_threshold == threshold

        # Invalid
        with pytest.raises(ValueError, match="must be in"):
            SwingPricingConfig(
                enabled=True,
                trigger_threshold=Decimal("-0.1"),
                max_swing_factor=Decimal("0.02"),
                cost_basis="nav",
            )

    def test_max_swing_factor_in_range(self):
        """Max swing factor must be in [0, 1]."""
        # Valid
        for factor in [Decimal("0"), Decimal("0.02"), Decimal("1.0")]:
            config = SwingPricingConfig(
                enabled=True,
                trigger_threshold=Decimal("0.10"),
                max_swing_factor=factor,
                cost_basis="nav",
            )
            assert config.max_swing_factor == factor

        # Invalid
        with pytest.raises(ValueError, match="must be in"):
            SwingPricingConfig(
                enabled=True,
                trigger_threshold=Decimal("0.10"),
                max_swing_factor=Decimal("1.1"),
                cost_basis="nav",
            )

    def test_cost_basis_validation(self):
        """Cost basis must be 'nav' or 'flow'."""
        with pytest.raises(ValueError, match="must be 'nav' or 'flow'"):
            SwingPricingConfig(
                enabled=True,
                trigger_threshold=Decimal("0.10"),
                max_swing_factor=Decimal("0.02"),
                cost_basis="invalid",
            )

    def test_disabled_swing_config(self):
        """Swing config can be disabled."""
        config = SwingPricingConfig(
            enabled=False,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )
        assert config.enabled is False


class TestSuspensionConfig:
    """Tests for SuspensionConfig validation."""

    def test_valid_suspension_config(self):
        """Create valid suspension config."""
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall", "nav_unreliable"],
            review_frequency_days=7,
            max_suspension_days=30,
            requires_investor_notification=True,
            requires_nca_notification=True,
        )
        assert config.enabled is True
        assert len(config.trigger_criteria) == 2
        assert config.review_frequency_days == 7

    def test_trigger_criteria_non_empty(self):
        """Trigger criteria must be non-empty if enabled."""
        with pytest.raises(ValueError, match="must be non-empty"):
            SuspensionConfig(
                enabled=True,
                trigger_criteria=[],
                review_frequency_days=7,
            )

    def test_trigger_criteria_stripped(self):
        """Trigger criteria strings are stripped."""
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["  liquidity_shortfall  ", "nav_unreliable"],
            review_frequency_days=7,
        )
        assert config.trigger_criteria[0] == "liquidity_shortfall"

    def test_trigger_criteria_empty_string_rejected(self):
        """Empty strings in trigger criteria are rejected."""
        with pytest.raises(ValueError, match="must be non-empty"):
            SuspensionConfig(
                enabled=True,
                trigger_criteria=["liquidity_shortfall", "   "],
                review_frequency_days=7,
            )

    def test_review_frequency_positive(self):
        """Review frequency must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            SuspensionConfig(
                enabled=True,
                trigger_criteria=["liquidity_shortfall"],
                review_frequency_days=0,
            )

    def test_max_suspension_days_optional(self):
        """Max suspension days is optional."""
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=7,
            max_suspension_days=None,
        )
        assert config.max_suspension_days is None

    def test_max_suspension_days_positive_if_set(self):
        """Max suspension days must be positive if set."""
        with pytest.raises(ValueError, match="must be positive"):
            SuspensionConfig(
                enabled=True,
                trigger_criteria=["liquidity_shortfall"],
                review_frequency_days=7,
                max_suspension_days=0,
            )

    def test_disabled_suspension_config(self):
        """Suspension config can be disabled."""
        config = SuspensionConfig(
            enabled=False,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=7,
        )
        assert config.enabled is False


class TestContagionConfig:
    """Tests for ContagionConfig validation."""

    def test_contagion_disabled(self):
        """Contagion can be disabled (no other fields required)."""
        config = ContagionConfig(enabled=False)
        assert config.enabled is False
        assert config.contagion_trigger_threshold is None
        assert config.contagion_multiplier is None

    def test_contagion_enabled_requires_threshold(self):
        """If contagion enabled, trigger threshold required."""
        with pytest.raises(ValueError, match="contagion_trigger_threshold"):
            ContagionConfig(
                enabled=True,
                contagion_trigger_threshold=None,
                contagion_multiplier=Decimal("1.5"),
            )

    def test_contagion_enabled_requires_multiplier(self):
        """If contagion enabled, multiplier required."""
        with pytest.raises(ValueError, match="contagion_multiplier"):
            ContagionConfig(
                enabled=True,
                contagion_trigger_threshold=Decimal("1.0"),
                contagion_multiplier=None,
            )

    def test_contagion_trigger_threshold_positive(self):
        """Contagion trigger threshold must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            ContagionConfig(
                enabled=True,
                contagion_trigger_threshold=Decimal("0"),
                contagion_multiplier=Decimal("1.5"),
            )

    def test_contagion_multiplier_minimum(self):
        """Contagion multiplier must be >= 1.0."""
        # Valid: 1.0, 1.5
        for multiplier in [Decimal("1.0"), Decimal("1.5"), Decimal("2.0")]:
            config = ContagionConfig(
                enabled=True,
                contagion_trigger_threshold=Decimal("1.0"),
                contagion_multiplier=multiplier,
            )
            assert config.contagion_multiplier == multiplier

        # Invalid: 0.9
        with pytest.raises(ValueError, match="must be >= 1.0"):
            ContagionConfig(
                enabled=True,
                contagion_trigger_threshold=Decimal("1.0"),
                contagion_multiplier=Decimal("0.9"),
            )

    def test_linked_fund_ids_optional(self):
        """Linked fund IDs are optional."""
        config = ContagionConfig(
            enabled=True,
            contagion_trigger_threshold=Decimal("1.0"),
            contagion_multiplier=Decimal("1.5"),
            linked_fund_ids=None,
        )
        assert config.linked_fund_ids is None

    def test_linked_fund_ids_non_empty(self):
        """If provided, linked fund IDs must be non-empty."""
        with pytest.raises(ValueError, match="must be non-empty"):
            ContagionConfig(
                enabled=True,
                contagion_trigger_threshold=Decimal("1.0"),
                contagion_multiplier=Decimal("1.5"),
                linked_fund_ids=[],
            )

    def test_linked_fund_ids_no_empty_strings(self):
        """Linked fund IDs cannot contain empty strings."""
        with pytest.raises(ValueError, match="must be non-empty"):
            ContagionConfig(
                enabled=True,
                contagion_trigger_threshold=Decimal("1.0"),
                contagion_multiplier=Decimal("1.5"),
                linked_fund_ids=["FUND001", ""],
            )

    def test_linked_fund_ids_valid(self):
        """Valid linked fund IDs."""
        config = ContagionConfig(
            enabled=True,
            contagion_trigger_threshold=Decimal("1.0"),
            contagion_multiplier=Decimal("1.5"),
            linked_fund_ids=["FUND001", "FUND002"],
        )
        assert config.linked_fund_ids == ["FUND001", "FUND002"]


class TestMonthlyRedemptionInput:
    """Tests for MonthlyRedemptionInput validation."""

    def test_valid_monthly_redemption(self):
        """Create valid monthly redemption input."""
        redemption = MonthlyRedemptionInput(
            month_index=0,
            redemption_amount=Decimal("1000000"),
            margin_call_amount=Decimal("50000"),
            description="Month 1 scenario",
        )
        assert redemption.month_index == 0
        assert redemption.redemption_amount == Decimal("1000000")

    def test_month_index_non_negative(self):
        """Month index must be non-negative."""
        with pytest.raises(ValueError, match="must be non-negative"):
            MonthlyRedemptionInput(
                month_index=-1,
                redemption_amount=Decimal("1000000"),
            )

    def test_redemption_amount_non_negative(self):
        """Redemption amount must be non-negative."""
        with pytest.raises(ValueError, match="must be non-negative"):
            MonthlyRedemptionInput(
                month_index=0,
                redemption_amount=Decimal("-1000000"),
            )

    def test_margin_call_amount_non_negative(self):
        """Margin call amount must be non-negative."""
        with pytest.raises(ValueError, match="must be non-negative"):
            MonthlyRedemptionInput(
                month_index=0,
                redemption_amount=Decimal("1000000"),
                margin_call_amount=Decimal("-50000"),
            )

    def test_margin_call_default_zero(self):
        """Margin call amount defaults to 0."""
        redemption = MonthlyRedemptionInput(
            month_index=0,
            redemption_amount=Decimal("1000000"),
        )
        assert redemption.margin_call_amount == Decimal("0")

    def test_zero_redemption_allowed(self):
        """Zero redemption is allowed."""
        redemption = MonthlyRedemptionInput(
            month_index=0,
            redemption_amount=Decimal("0"),
        )
        assert redemption.redemption_amount == Decimal("0")


class TestBacklogState:
    """Tests for BacklogState validation."""

    def test_valid_backlog_state(self):
        """Create valid backlog state."""
        backlog = BacklogState(
            month_index=0,
            beginning_backlog=Decimal("0"),
            new_redemptions=Decimal("1000000"),
            total_redemptions_due=Decimal("1000000"),
            redeemed_in_month=Decimal("800000"),
            ending_backlog=Decimal("200000"),
            deferral_reason="gate",
        )
        assert backlog.month_index == 0
        assert backlog.ending_backlog == Decimal("200000")

    def test_backlog_accounting_consistency(self):
        """Total redemptions must equal beginning + new."""
        with pytest.raises(ValueError, match="total_redemptions_due mismatch"):
            BacklogState(
                month_index=0,
                beginning_backlog=Decimal("100000"),
                new_redemptions=Decimal("1000000"),
                total_redemptions_due=Decimal("900000"),  # Wrong!
                redeemed_in_month=Decimal("800000"),
                ending_backlog=Decimal("100000"),
            )

    def test_ending_backlog_accounting_consistency(self):
        """Ending backlog must equal total - redeemed."""
        with pytest.raises(ValueError, match="ending_backlog mismatch"):
            BacklogState(
                month_index=0,
                beginning_backlog=Decimal("100000"),
                new_redemptions=Decimal("1000000"),
                total_redemptions_due=Decimal("1100000"),
                redeemed_in_month=Decimal("800000"),
                ending_backlog=Decimal("400000"),  # Wrong! Should be 300000
            )

    def test_redeemed_cannot_exceed_total(self):
        """Redeemed amount cannot exceed total due."""
        with pytest.raises(ValueError, match="must be non-negative|cannot exceed"):
            BacklogState(
                month_index=0,
                beginning_backlog=Decimal("0"),
                new_redemptions=Decimal("1000000"),
                total_redemptions_due=Decimal("1000000"),
                redeemed_in_month=Decimal("1500000"),  # Exceeds total!
                ending_backlog=Decimal("-500000"),
            )

    def test_zero_backlog_allowed(self):
        """Zero beginning and ending backlog allowed (no deferral)."""
        backlog = BacklogState(
            month_index=0,
            beginning_backlog=Decimal("0"),
            new_redemptions=Decimal("1000000"),
            total_redemptions_due=Decimal("1000000"),
            redeemed_in_month=Decimal("1000000"),
            ending_backlog=Decimal("0"),
        )
        assert backlog.ending_backlog == Decimal("0")


class TestLMTMonthlyResult:
    """Tests for LMTMonthlyResult validation."""

    def test_valid_monthly_result(self):
        """Create valid monthly result."""
        result = LMTMonthlyResult(
            month_index=0,
            valuation_date=date(2026, 1, 31),
            fund_nav=Decimal("100000000"),
            redemption_amount=Decimal("10000000"),
            available_liquidity=Decimal("8000000"),
            coverage_ratio=Decimal("0.8"),
            gate_activated=True,
            gate_deferred_amount=Decimal("2000000"),
            swing_pricing_activated=False,
            swing_factor_applied=Decimal("0"),
            suspension_activated=False,
            suspension_reason=None,
            contagion_triggered=False,
            ending_nav=Decimal("98000000"),
            backlog_amount=Decimal("2000000"),
            warnings=[],
        )
        assert result.gate_activated is True
        assert result.gate_deferred_amount == Decimal("2000000")

    def test_gate_deferred_cannot_exceed_redemption(self):
        """Gate deferred amount cannot exceed redemption."""
        with pytest.raises(ValueError, match="cannot exceed"):
            LMTMonthlyResult(
                month_index=0,
                valuation_date=date(2026, 1, 31),
                fund_nav=Decimal("100000000"),
                redemption_amount=Decimal("10000000"),
                available_liquidity=Decimal("8000000"),
                coverage_ratio=Decimal("0.8"),
                gate_activated=True,
                gate_deferred_amount=Decimal("15000000"),  # Exceeds redemption!
                swing_pricing_activated=False,
                swing_factor_applied=Decimal("0"),
                suspension_activated=False,
                suspension_reason=None,
                contagion_triggered=False,
                ending_nav=Decimal("95000000"),
                backlog_amount=Decimal("15000000"),
            )

    def test_suspension_reason_required_if_activated(self):
        """If suspension activated, reason must be provided."""
        with pytest.raises(ValueError, match="suspension_reason required"):
            LMTMonthlyResult(
                month_index=0,
                valuation_date=date(2026, 1, 31),
                fund_nav=Decimal("100000000"),
                redemption_amount=Decimal("10000000"),
                available_liquidity=Decimal("0"),
                coverage_ratio=Decimal("0"),
                gate_activated=False,
                gate_deferred_amount=Decimal("0"),
                swing_pricing_activated=False,
                swing_factor_applied=Decimal("0"),
                suspension_activated=True,
                suspension_reason=None,  # Missing!
                contagion_triggered=False,
                ending_nav=Decimal("100000000"),
                backlog_amount=Decimal("10000000"),
            )

    def test_suspension_reason_not_allowed_if_not_activated(self):
        """If suspension not activated, reason should not be provided."""
        with pytest.raises(ValueError, match="should be None"):
            LMTMonthlyResult(
                month_index=0,
                valuation_date=date(2026, 1, 31),
                fund_nav=Decimal("100000000"),
                redemption_amount=Decimal("10000000"),
                available_liquidity=Decimal("8000000"),
                coverage_ratio=Decimal("0.8"),
                gate_activated=False,
                gate_deferred_amount=Decimal("0"),
                swing_pricing_activated=False,
                swing_factor_applied=Decimal("0"),
                suspension_activated=False,
                suspension_reason="some reason",  # Should be None!
                contagion_triggered=False,
                ending_nav=Decimal("98000000"),
                backlog_amount=Decimal("0"),
            )

    def test_swing_factor_in_range(self):
        """Swing factor applied must be in [0, 1]."""
        with pytest.raises(ValueError, match="must be <= 1.0"):
            LMTMonthlyResult(
                month_index=0,
                valuation_date=date(2026, 1, 31),
                fund_nav=Decimal("100000000"),
                redemption_amount=Decimal("10000000"),
                available_liquidity=Decimal("8000000"),
                coverage_ratio=Decimal("0.8"),
                gate_activated=False,
                gate_deferred_amount=Decimal("0"),
                swing_pricing_activated=True,
                swing_factor_applied=Decimal("1.5"),  # Invalid!
                suspension_activated=False,
                suspension_reason=None,
                contagion_triggered=False,
                ending_nav=Decimal("98000000"),
                backlog_amount=Decimal("0"),
            )

    def test_coverage_ratio_can_be_none(self):
        """Coverage ratio can be None (e.g., no redemptions)."""
        result = LMTMonthlyResult(
            month_index=0,
            valuation_date=date(2026, 1, 31),
            fund_nav=Decimal("100000000"),
            redemption_amount=Decimal("0"),
            available_liquidity=Decimal("100000000"),
            coverage_ratio=None,
            gate_activated=False,
            gate_deferred_amount=Decimal("0"),
            swing_pricing_activated=False,
            swing_factor_applied=Decimal("0"),
            suspension_activated=False,
            suspension_reason=None,
            contagion_triggered=False,
            ending_nav=Decimal("100000000"),
            backlog_amount=Decimal("0"),
        )
        assert result.coverage_ratio is None


class TestLMTSimulationInput:
    """Tests for LMTSimulationInput validation."""

    def test_valid_simulation_input(self):
        """Create valid simulation input."""
        gate_config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )
        swing_config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )
        suspension_config = SuspensionConfig(
            enabled=False,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=7,
        )
        contagion_config = ContagionConfig(enabled=False)

        scenario = LMTScenarioConfig(
            gate_config=gate_config,
            swing_config=swing_config,
            suspension_config=suspension_config,
            contagion_config=contagion_config,
        )

        redemptions = [
            MonthlyRedemptionInput(month_index=0, redemption_amount=Decimal("1000000")),
            MonthlyRedemptionInput(month_index=1, redemption_amount=Decimal("500000")),
        ]

        sim_input = LMTSimulationInput(
            fund_id=1,
            valuation_date=date(2026, 1, 1),
            fund_nav=Decimal("100000000"),
            scenario_config=scenario,
            monthly_redemptions=redemptions,
        )
        assert sim_input.fund_id == 1
        assert len(sim_input.monthly_redemptions) == 2

    def test_fund_id_positive(self):
        """Fund ID must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            LMTSimulationInput(
                fund_id=0,
                valuation_date=date(2026, 1, 1),
                fund_nav=Decimal("100000000"),
                scenario_config=LMTScenarioConfig(
                    gate_config=GateTriggerConfig(
                        enabled=False,
                        coverage_ratio_threshold=Decimal("1.0"),
                        max_gate_ratio=Decimal("0.5"),
                    ),
                    swing_config=SwingPricingConfig(
                        enabled=False,
                        trigger_threshold=Decimal("0.10"),
                        max_swing_factor=Decimal("0.02"),
                        cost_basis="nav",
                    ),
                    suspension_config=SuspensionConfig(
                        enabled=False,
                        trigger_criteria=["test"],
                        review_frequency_days=7,
                    ),
                    contagion_config=ContagionConfig(enabled=False),
                ),
                monthly_redemptions=[
                    MonthlyRedemptionInput(month_index=0, redemption_amount=Decimal("1000000")),
                ],
            )

    def test_fund_nav_positive(self):
        """Fund NAV must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            LMTSimulationInput(
                fund_id=1,
                valuation_date=date(2026, 1, 1),
                fund_nav=Decimal("0"),
                scenario_config=LMTScenarioConfig(
                    gate_config=GateTriggerConfig(
                        enabled=False,
                        coverage_ratio_threshold=Decimal("1.0"),
                        max_gate_ratio=Decimal("0.5"),
                    ),
                    swing_config=SwingPricingConfig(
                        enabled=False,
                        trigger_threshold=Decimal("0.10"),
                        max_swing_factor=Decimal("0.02"),
                        cost_basis="nav",
                    ),
                    suspension_config=SuspensionConfig(
                        enabled=False,
                        trigger_criteria=["test"],
                        review_frequency_days=7,
                    ),
                    contagion_config=ContagionConfig(enabled=False),
                ),
                monthly_redemptions=[
                    MonthlyRedemptionInput(month_index=0, redemption_amount=Decimal("1000000")),
                ],
            )

    def test_monthly_redemptions_sequential_indices(self):
        """Monthly indices must be sequential starting from 0."""
        with pytest.raises(ValueError, match="must be sequential"):
            LMTSimulationInput(
                fund_id=1,
                valuation_date=date(2026, 1, 1),
                fund_nav=Decimal("100000000"),
                scenario_config=LMTScenarioConfig(
                    gate_config=GateTriggerConfig(
                        enabled=False,
                        coverage_ratio_threshold=Decimal("1.0"),
                        max_gate_ratio=Decimal("0.5"),
                    ),
                    swing_config=SwingPricingConfig(
                        enabled=False,
                        trigger_threshold=Decimal("0.10"),
                        max_swing_factor=Decimal("0.02"),
                        cost_basis="nav",
                    ),
                    suspension_config=SuspensionConfig(
                        enabled=False,
                        trigger_criteria=["test"],
                        review_frequency_days=7,
                    ),
                    contagion_config=ContagionConfig(enabled=False),
                ),
                monthly_redemptions=[
                    MonthlyRedemptionInput(month_index=0, redemption_amount=Decimal("1000000")),
                    MonthlyRedemptionInput(month_index=2, redemption_amount=Decimal("500000")),
                ],
            )


class TestLMTSimulationResult:
    """Tests for LMTSimulationResult validation."""

    def test_valid_simulation_result(self):
        """Create valid simulation result."""
        monthly_results = [
            LMTMonthlyResult(
                month_index=0,
                valuation_date=date(2026, 1, 31),
                fund_nav=Decimal("100000000"),
                redemption_amount=Decimal("10000000"),
                available_liquidity=Decimal("8000000"),
                coverage_ratio=Decimal("0.8"),
                gate_activated=True,
                gate_deferred_amount=Decimal("2000000"),
                swing_pricing_activated=False,
                swing_factor_applied=Decimal("0"),
                suspension_activated=False,
                suspension_reason=None,
                contagion_triggered=False,
                ending_nav=Decimal("98000000"),
                backlog_amount=Decimal("2000000"),
            ),
        ]

        result = LMTSimulationResult(
            fund_id=1,
            valuation_date=date(2026, 1, 1),
            initial_nav=Decimal("100000000"),
            final_nav=Decimal("98000000"),
            total_redemptions=Decimal("10000000"),
            total_backlog_accumulated=Decimal("2000000"),
            months_with_backlog=1,
            gate_activation_count=1,
            swing_pricing_activation_count=0,
            suspension_activation_count=0,
            contagion_triggered_count=0,
            monthly_results=monthly_results,
        )
        assert result.gate_activation_count == 1

    def test_activation_counts_match_monthly_results(self):
        """Activation counts must match actual activations in monthly results."""
        monthly_results = [
            LMTMonthlyResult(
                month_index=0,
                valuation_date=date(2026, 1, 31),
                fund_nav=Decimal("100000000"),
                redemption_amount=Decimal("10000000"),
                available_liquidity=Decimal("8000000"),
                coverage_ratio=Decimal("0.8"),
                gate_activated=True,  # Activated
                gate_deferred_amount=Decimal("2000000"),
                swing_pricing_activated=False,
                swing_factor_applied=Decimal("0"),
                suspension_activated=False,
                suspension_reason=None,
                contagion_triggered=False,
                ending_nav=Decimal("98000000"),
                backlog_amount=Decimal("2000000"),
            ),
        ]

        with pytest.raises(ValueError, match="gate_activation_count mismatch"):
            LMTSimulationResult(
                fund_id=1,
                valuation_date=date(2026, 1, 1),
                initial_nav=Decimal("100000000"),
                final_nav=Decimal("98000000"),
                total_redemptions=Decimal("10000000"),
                total_backlog_accumulated=Decimal("2000000"),
                months_with_backlog=1,
                gate_activation_count=0,  # Wrong! Should be 1
                swing_pricing_activation_count=0,
                suspension_activation_count=0,
                contagion_triggered_count=0,
                monthly_results=monthly_results,
            )

    def test_monthly_indices_sequential(self):
        """Monthly results must have sequential indices."""
        monthly_results = [
            LMTMonthlyResult(
                month_index=0,
                valuation_date=date(2026, 1, 31),
                fund_nav=Decimal("100000000"),
                redemption_amount=Decimal("10000000"),
                available_liquidity=Decimal("8000000"),
                coverage_ratio=Decimal("0.8"),
                gate_activated=False,
                gate_deferred_amount=Decimal("0"),
                swing_pricing_activated=False,
                swing_factor_applied=Decimal("0"),
                suspension_activated=False,
                suspension_reason=None,
                contagion_triggered=False,
                ending_nav=Decimal("98000000"),
                backlog_amount=Decimal("0"),
            ),
            LMTMonthlyResult(
                month_index=2,  # Wrong! Should be 1
                valuation_date=date(2026, 2, 28),
                fund_nav=Decimal("98000000"),
                redemption_amount=Decimal("5000000"),
                available_liquidity=Decimal("5000000"),
                coverage_ratio=Decimal("1.0"),
                gate_activated=False,
                gate_deferred_amount=Decimal("0"),
                swing_pricing_activated=False,
                swing_factor_applied=Decimal("0"),
                suspension_activated=False,
                suspension_reason=None,
                contagion_triggered=False,
                ending_nav=Decimal("93000000"),
                backlog_amount=Decimal("0"),
            ),
        ]

        with pytest.raises(ValueError, match="must have sequential"):
            LMTSimulationResult(
                fund_id=1,
                valuation_date=date(2026, 1, 1),
                initial_nav=Decimal("100000000"),
                final_nav=Decimal("93000000"),
                total_redemptions=Decimal("15000000"),
                total_backlog_accumulated=Decimal("0"),
                months_with_backlog=0,
                gate_activation_count=0,
                swing_pricing_activation_count=0,
                suspension_activation_count=0,
                contagion_triggered_count=0,
                monthly_results=monthly_results,
            )

    def test_activation_counts_cannot_exceed_months(self):
        """Activation counts cannot exceed number of months."""
        monthly_results = [
            LMTMonthlyResult(
                month_index=0,
                valuation_date=date(2026, 1, 31),
                fund_nav=Decimal("100000000"),
                redemption_amount=Decimal("10000000"),
                available_liquidity=Decimal("8000000"),
                coverage_ratio=Decimal("0.8"),
                gate_activated=True,
                gate_deferred_amount=Decimal("2000000"),
                swing_pricing_activated=False,
                swing_factor_applied=Decimal("0"),
                suspension_activated=False,
                suspension_reason=None,
                contagion_triggered=False,
                ending_nav=Decimal("98000000"),
                backlog_amount=Decimal("2000000"),
            ),
        ]

        with pytest.raises(ValueError, match="cannot exceed"):
            LMTSimulationResult(
                fund_id=1,
                valuation_date=date(2026, 1, 1),
                initial_nav=Decimal("100000000"),
                final_nav=Decimal("98000000"),
                total_redemptions=Decimal("10000000"),
                total_backlog_accumulated=Decimal("2000000"),
                months_with_backlog=1,
                gate_activation_count=5,  # More than 1 month!
                swing_pricing_activation_count=0,
                suspension_activation_count=0,
                contagion_triggered_count=0,
                monthly_results=monthly_results,
            )
