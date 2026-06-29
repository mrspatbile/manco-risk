"""Tests for redemption gate engine."""

from decimal import Decimal

import pytest

from manco_risk.risk.liquidity.lmt.gate_engine import GateEngine, GateResult
from manco_risk.risk.liquidity.lmt.models import GateTriggerConfig


class TestGateResult:
    """Tests for GateResult model validation."""

    def test_valid_gate_result(self):
        """Create valid gate result."""
        result = GateResult(
            gate_activated=True,
            executable_amount=Decimal("500000"),
            deferred_amount=Decimal("500000"),
        )
        assert result.gate_activated is True
        assert result.executable_amount == Decimal("500000")

    def test_no_gate_result(self):
        """Gate result when gate not activated."""
        result = GateResult(
            gate_activated=False,
            executable_amount=Decimal("1000000"),
            deferred_amount=Decimal("0"),
        )
        assert result.gate_activated is False
        assert result.deferred_amount == Decimal("0")

    def test_amounts_non_negative(self):
        """Amounts must be non-negative."""
        with pytest.raises(ValueError, match="must be non-negative"):
            GateResult(
                gate_activated=True,
                executable_amount=Decimal("-100000"),
                deferred_amount=Decimal("0"),
            )

    def test_frozen_model(self):
        """GateResult is immutable."""
        result = GateResult(
            gate_activated=False,
            executable_amount=Decimal("1000000"),
            deferred_amount=Decimal("0"),
        )
        with pytest.raises(Exception):
            result.gate_activated = True


class TestGateEngineBasic:
    """Basic gate engine behavior tests."""

    def test_gate_disabled_full_execution(self):
        """If gate is disabled, execute full redemption."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=False,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("0.5"),  # Insufficient liquidity
            config=config,
        )

        assert result.gate_activated is False
        assert result.executable_amount == Decimal("1000000")
        assert result.deferred_amount == Decimal("0")

    def test_sufficient_liquidity_no_gate(self):
        """If coverage >= threshold, no gate activation."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("1.5"),  # Coverage > threshold
            config=config,
        )

        assert result.gate_activated is False
        assert result.executable_amount == Decimal("1000000")
        assert result.deferred_amount == Decimal("0")

    def test_insufficient_liquidity_gate_activates(self):
        """If coverage < threshold, gate activates."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("0.5"),  # Coverage < threshold
            config=config,
        )

        assert result.gate_activated is True
        assert result.executable_amount == Decimal("500000")
        assert result.deferred_amount == Decimal("500000")

    def test_zero_redemption_no_gate_activation(self):
        """If redemption is zero, gate does not activate."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("0"),
            coverage_ratio=Decimal("0"),  # Even with zero coverage
            config=config,
        )

        assert result.gate_activated is False
        assert result.executable_amount == Decimal("0")
        assert result.deferred_amount == Decimal("0")


class TestGateEngineThresholdLogic:
    """Tests for coverage ratio threshold logic."""

    def test_coverage_exactly_at_threshold(self):
        """Coverage exactly at threshold should not trigger gate."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("1.0"),  # Exactly at threshold
            config=config,
        )

        assert result.gate_activated is False
        assert result.executable_amount == Decimal("1000000")

    def test_coverage_just_below_threshold(self):
        """Coverage just below threshold triggers gate."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("0.99"),  # Just below threshold
            config=config,
        )

        assert result.gate_activated is True
        assert result.executable_amount == Decimal("500000")
        assert result.deferred_amount == Decimal("500000")

    def test_custom_threshold_0_5(self):
        """Custom threshold of 0.5."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("0.5"),
            max_gate_ratio=Decimal("0.5"),
        )

        # Coverage below 0.5 triggers gate
        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("0.4"),
            config=config,
        )
        assert result.gate_activated is True

        # Coverage at 0.5 does not trigger gate
        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("0.5"),
            config=config,
        )
        assert result.gate_activated is False

    def test_custom_threshold_2_0(self):
        """Custom threshold of 2.0 (very conservative)."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("2.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("1.5"),  # Below 2.0
            config=config,
        )

        assert result.gate_activated is True
        assert result.executable_amount == Decimal("500000")


class TestGateEngineMaxGateRatio:
    """Tests for max_gate_ratio application."""

    def test_max_gate_ratio_50_percent(self):
        """Max gate ratio 0.5 limits execution to 50%."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("0.1"),  # Very low coverage
            config=config,
        )

        assert result.executable_amount == Decimal("500000")
        assert result.deferred_amount == Decimal("500000")

    def test_max_gate_ratio_25_percent(self):
        """Max gate ratio 0.25 limits execution to 25%."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.25"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("0.0"),
            config=config,
        )

        assert result.executable_amount == Decimal("250000")
        assert result.deferred_amount == Decimal("750000")

    def test_max_gate_ratio_100_percent(self):
        """Max gate ratio 1.0 allows full execution if triggered."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("1.0"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("0.5"),  # Low coverage
            config=config,
        )

        # Even with gate activated, max_gate_ratio=1.0 allows full execution
        assert result.executable_amount == Decimal("1000000")
        assert result.deferred_amount == Decimal("0")

    def test_min_of_redemption_and_gate_cap(self):
        """Executable = min(redemption, max_gate_ratio * redemption)."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.6"),
        )

        # 60% of 1M = 600k
        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("0.1"),
            config=config,
        )

        assert result.executable_amount == Decimal("600000")
        assert result.deferred_amount == Decimal("400000")


class TestGateEngineEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_small_redemption(self):
        """Very small redemption amount is handled correctly."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("0.01"),
            coverage_ratio=Decimal("0.0"),
            config=config,
        )

        assert result.gate_activated is True
        assert result.executable_amount == Decimal("0.005")
        assert result.deferred_amount == Decimal("0.005")

    def test_very_large_redemption(self):
        """Very large redemption amount is handled correctly."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000000000"),  # 1 trillion
            coverage_ratio=Decimal("0.5"),
            config=config,
        )

        assert result.executable_amount == Decimal("500000000000")
        assert result.deferred_amount == Decimal("500000000000")

    def test_high_precision_decimal_amounts(self):
        """High precision decimal amounts are handled correctly."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000.123456789"),
            coverage_ratio=Decimal("0.0"),
            config=config,
        )

        expected_executable = Decimal("500000.0617283945")
        assert result.executable_amount == expected_executable

    def test_coverage_zero(self):
        """Coverage ratio of zero triggers gate."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("0"),
            config=config,
        )

        assert result.gate_activated is True
        assert result.executable_amount == Decimal("500000")

    def test_coverage_very_high(self):
        """Very high coverage ratio does not trigger gate."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("100.0"),
            config=config,
        )

        assert result.gate_activated is False
        assert result.executable_amount == Decimal("1000000")

    def test_input_validation_negative_redemption(self):
        """Negative redemption amount is rejected."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        with pytest.raises(ValueError, match="must be non-negative"):
            engine.calculate(
                redemption_amount=Decimal("-1000000"),
                coverage_ratio=Decimal("0.5"),
                config=config,
            )

    def test_input_validation_negative_coverage_ratio(self):
        """Negative coverage ratio is rejected."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        with pytest.raises(ValueError, match="must be non-negative"):
            engine.calculate(
                redemption_amount=Decimal("1000000"),
                coverage_ratio=Decimal("-0.5"),
                config=config,
            )


class TestGateEngineRealWorldScenarios:
    """Tests for realistic fund scenarios."""

    def test_normal_market_conditions(self):
        """Normal market: good liquidity, modest redemptions."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        # Fund has 100M NAV, 80M liquid, 10M redemptions requested
        # Coverage = 80M / 10M = 8.0 (very good)
        result = engine.calculate(
            redemption_amount=Decimal("10000000"),
            coverage_ratio=Decimal("8.0"),
            config=config,
        )

        assert result.gate_activated is False
        assert result.executable_amount == Decimal("10000000")

    def test_stress_market_conditions(self):
        """Stress: liquidity tightens, gate triggers."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        # Fund has 100M NAV, 8M liquid, 10M redemptions
        # Coverage = 8M / 10M = 0.8 (insufficient)
        result = engine.calculate(
            redemption_amount=Decimal("10000000"),
            coverage_ratio=Decimal("0.8"),
            config=config,
        )

        assert result.gate_activated is True
        assert result.executable_amount == Decimal("5000000")  # 50% of 10M
        assert result.deferred_amount == Decimal("5000000")

    def test_severe_liquidity_crisis(self):
        """Severe: almost no liquidity, gate severely limits redemptions."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.2"),  # Very restrictive gate
        )

        # Fund has 100M NAV, 1M liquid, 20M redemptions
        # Coverage = 1M / 20M = 0.05 (critical)
        result = engine.calculate(
            redemption_amount=Decimal("20000000"),
            coverage_ratio=Decimal("0.05"),
            config=config,
        )

        assert result.gate_activated is True
        assert result.executable_amount == Decimal("4000000")  # 20% of 20M
        assert result.deferred_amount == Decimal("16000000")

    def test_multiple_months_no_gate_first_month(self):
        """Month 1: good liquidity, no gate."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        result = engine.calculate(
            redemption_amount=Decimal("5000000"),
            coverage_ratio=Decimal("2.0"),
            config=config,
        )

        assert result.gate_activated is False
        assert result.executable_amount == Decimal("5000000")

    def test_multiple_months_with_gate_second_month(self):
        """Month 2: liquidity tightens after Month 1 redemptions."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        # After Month 1 redemption, NAV reduced, liquidity ratio down
        result = engine.calculate(
            redemption_amount=Decimal("5000000"),
            coverage_ratio=Decimal("0.8"),  # Below threshold
            config=config,
        )

        assert result.gate_activated is True
        assert result.executable_amount == Decimal("2500000")
        assert result.deferred_amount == Decimal("2500000")


class TestGateEngineStateless:
    """Tests confirming engine is stateless."""

    def test_multiple_calls_independent(self):
        """Multiple calls to engine produce independent results."""
        engine = GateEngine()
        config = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )

        # First call
        result1 = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("0.5"),
            config=config,
        )

        # Second call with different input
        result2 = engine.calculate(
            redemption_amount=Decimal("2000000"),
            coverage_ratio=Decimal("1.5"),
            config=config,
        )

        # Results should be independent
        assert result1.gate_activated is True
        assert result1.executable_amount == Decimal("500000")

        assert result2.gate_activated is False
        assert result2.executable_amount == Decimal("2000000")

    def test_engine_reusable(self):
        """Engine can be reused across multiple scenarios."""
        engine = GateEngine()

        config1 = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("1.0"),
            max_gate_ratio=Decimal("0.5"),
        )
        result1 = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("0.5"),
            config=config1,
        )

        config2 = GateTriggerConfig(
            enabled=True,
            coverage_ratio_threshold=Decimal("0.5"),
            max_gate_ratio=Decimal("0.25"),
        )
        result2 = engine.calculate(
            redemption_amount=Decimal("1000000"),
            coverage_ratio=Decimal("0.5"),
            config=config2,
        )

        # Different configs produce different results
        assert result1.gate_activated is True
        assert result2.gate_activated is False
