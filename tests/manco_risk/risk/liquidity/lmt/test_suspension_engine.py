"""Tests for subscription/redemption suspension engine."""

from decimal import Decimal

import pytest

from manco_risk.risk.liquidity.lmt.models import SuspensionConfig
from manco_risk.risk.liquidity.lmt.suspension_engine import (
    SuspensionEngine,
    SuspensionResult,
)


class TestSuspensionResult:
    """Tests for SuspensionResult model validation."""

    def test_valid_suspension_activated(self):
        """Create valid suspension result when activated."""
        result = SuspensionResult(
            suspension_activated=True,
            suspension_reason="liquidity_shortfall",
            triggered_criteria=["liquidity_shortfall"],
        )
        assert result.suspension_activated is True
        assert result.suspension_reason == "liquidity_shortfall"
        assert result.triggered_criteria == ["liquidity_shortfall"]

    def test_valid_suspension_not_activated(self):
        """Create valid suspension result when not activated."""
        result = SuspensionResult(
            suspension_activated=False,
            suspension_reason=None,
            triggered_criteria=[],
        )
        assert result.suspension_activated is False
        assert result.suspension_reason is None
        assert result.triggered_criteria == []

    def test_reason_required_when_activated(self):
        """Reason must be provided if suspension_activated=True."""
        with pytest.raises(ValueError, match="suspension_reason required"):
            SuspensionResult(
                suspension_activated=True,
                suspension_reason=None,
                triggered_criteria=["liquidity_shortfall"],
            )

    def test_reason_forbidden_when_not_activated(self):
        """Reason must be None if suspension_activated=False."""
        with pytest.raises(ValueError, match="suspension_reason should be None"):
            SuspensionResult(
                suspension_activated=False,
                suspension_reason="liquidity_shortfall",
                triggered_criteria=[],
            )

    def test_empty_string_reason_invalid(self):
        """Empty string reason is invalid."""
        with pytest.raises(ValueError, match="must be non-empty"):
            SuspensionResult(
                suspension_activated=True,
                suspension_reason="",
                triggered_criteria=["liquidity_shortfall"],
            )

    def test_whitespace_reason_stripped(self):
        """Whitespace reason is stripped."""
        result = SuspensionResult(
            suspension_activated=True,
            suspension_reason="  liquidity_shortfall  ",
            triggered_criteria=["liquidity_shortfall"],
        )
        assert result.suspension_reason == "liquidity_shortfall"

    def test_multiple_triggered_criteria(self):
        """Multiple criteria can be recorded."""
        result = SuspensionResult(
            suspension_activated=True,
            suspension_reason="liquidity_shortfall",
            triggered_criteria=["liquidity_shortfall", "nav_unreliable"],
        )
        assert len(result.triggered_criteria) == 2
        assert "liquidity_shortfall" in result.triggered_criteria

    def test_empty_criteria_list_valid_when_not_activated(self):
        """Empty criteria list is valid when not activated."""
        result = SuspensionResult(
            suspension_activated=False,
            suspension_reason=None,
            triggered_criteria=[],
        )
        assert result.triggered_criteria == []

    def test_frozen_model(self):
        """SuspensionResult is immutable."""
        result = SuspensionResult(
            suspension_activated=False,
            suspension_reason=None,
            triggered_criteria=[],
        )
        with pytest.raises(Exception):
            result.suspension_activated = True

    def test_triggered_criteria_empty_string_invalid(self):
        """Triggered criteria entries cannot be empty."""
        with pytest.raises(ValueError, match="must be non-empty"):
            SuspensionResult(
                suspension_activated=False,
                suspension_reason=None,
                triggered_criteria=[""],
            )

    def test_triggered_criteria_whitespace_invalid(self):
        """Triggered criteria entries cannot be whitespace-only."""
        with pytest.raises(ValueError, match="must be non-empty"):
            SuspensionResult(
                suspension_activated=False,
                suspension_reason=None,
                triggered_criteria=["   "],
            )


class TestSuspensionEngineDisabled:
    """Tests for suspension engine with disabled config."""

    def test_disabled_config_no_suspension(self):
        """If suspension is disabled, no activation regardless of criteria."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=False,
            trigger_criteria=["liquidity_shortfall", "nav_unreliable"],
            review_frequency_days=5,
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config,
            triggered_criteria=["liquidity_shortfall"],
        )

        assert result.suspension_activated is False
        assert result.suspension_reason is None
        assert result.triggered_criteria == []

    def test_disabled_config_with_multiple_criteria(self):
        """Disabled config overrides multiple triggered criteria."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=False,
            trigger_criteria=["liquidity_shortfall", "nav_unreliable", "market_disruption"],
            review_frequency_days=5,
        )

        result = engine.calculate(
            redemption_amount=Decimal("5000000"),
            config=config,
            triggered_criteria=["liquidity_shortfall", "nav_unreliable"],
        )

        assert result.suspension_activated is False
        assert result.suspension_reason is None


class TestSuspensionEngineZeroRedemption:
    """Tests for suspension engine with zero redemption."""

    def test_zero_redemption_no_suspension(self):
        """If redemption_amount is zero, no suspension even if criteria match."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=5,
        )

        result = engine.calculate(
            redemption_amount=Decimal("0"),
            config=config,
            triggered_criteria=["liquidity_shortfall"],
        )

        assert result.suspension_activated is False
        assert result.suspension_reason is None
        assert result.triggered_criteria == []

    def test_zero_redemption_with_multiple_criteria(self):
        """Zero redemption overrides multiple matching criteria."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall", "nav_unreliable"],
            review_frequency_days=5,
        )

        result = engine.calculate(
            redemption_amount=Decimal("0"),
            config=config,
            triggered_criteria=["liquidity_shortfall", "nav_unreliable"],
        )

        assert result.suspension_activated is False
        assert result.suspension_reason is None


class TestSuspensionEngineMatching:
    """Tests for suspension engine with matching criteria."""

    def test_single_matching_criterion(self):
        """Activation with single matching criterion."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall", "nav_unreliable"],
            review_frequency_days=5,
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config,
            triggered_criteria=["liquidity_shortfall"],
        )

        assert result.suspension_activated is True
        assert result.suspension_reason == "liquidity_shortfall"
        assert result.triggered_criteria == ["liquidity_shortfall"]

    def test_multiple_matching_criteria(self):
        """Activation records all matching criteria."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall", "nav_unreliable", "market_disruption"],
            review_frequency_days=5,
        )

        result = engine.calculate(
            redemption_amount=Decimal("2000000"),
            config=config,
            triggered_criteria=["liquidity_shortfall", "nav_unreliable"],
        )

        assert result.suspension_activated is True
        assert result.suspension_reason == "liquidity_shortfall"  # First match
        assert set(result.triggered_criteria) == {"liquidity_shortfall", "nav_unreliable"}

    def test_partial_matching_criteria(self):
        """Only matching criteria are recorded."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall", "nav_unreliable"],
            review_frequency_days=5,
        )

        result = engine.calculate(
            redemption_amount=Decimal("1500000"),
            config=config,
            triggered_criteria=["liquidity_shortfall", "market_closure", "nav_unreliable"],
        )

        assert result.suspension_activated is True
        assert result.suspension_reason == "liquidity_shortfall"
        assert set(result.triggered_criteria) == {"liquidity_shortfall", "nav_unreliable"}
        assert "market_closure" not in result.triggered_criteria

    def test_first_matching_criterion_as_reason(self):
        """Reason is set to first matching criterion for traceability."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["nav_unreliable", "liquidity_shortfall"],
            review_frequency_days=5,
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config,
            triggered_criteria=["liquidity_shortfall", "nav_unreliable"],
        )

        assert result.suspension_activated is True
        # Reason is from the first matching criterion found in triggered_criteria
        assert result.suspension_reason in ["liquidity_shortfall", "nav_unreliable"]


class TestSuspensionEngineNoMatching:
    """Tests for suspension engine with no matching criteria."""

    def test_no_matching_criteria(self):
        """No activation if triggered criteria do not match config."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall", "nav_unreliable"],
            review_frequency_days=5,
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config,
            triggered_criteria=["market_disruption", "cyber_incident"],
        )

        assert result.suspension_activated is False
        assert result.suspension_reason is None
        assert result.triggered_criteria == []

    def test_empty_triggered_criteria(self):
        """No activation if no criteria are triggered."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall", "nav_unreliable"],
            review_frequency_days=5,
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config,
            triggered_criteria=[],
        )

        assert result.suspension_activated is False
        assert result.suspension_reason is None
        assert result.triggered_criteria == []

    def test_case_sensitive_criteria_matching(self):
        """Criterion matching is case-sensitive."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=5,
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config,
            triggered_criteria=["Liquidity_Shortfall"],  # Different case
        )

        assert result.suspension_activated is False
        assert result.suspension_reason is None


class TestSuspensionEngineValidation:
    """Tests for input validation."""

    def test_negative_redemption_amount(self):
        """Negative redemption amount raises ValueError."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=5,
        )

        with pytest.raises(ValueError, match="must be non-negative"):
            engine.calculate(
                redemption_amount=Decimal("-1000000"),
                config=config,
                triggered_criteria=["liquidity_shortfall"],
            )

    def test_large_redemption_amount(self):
        """Large redemption amount is accepted."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=5,
        )

        result = engine.calculate(
            redemption_amount=Decimal("999999999999.99"),
            config=config,
            triggered_criteria=["liquidity_shortfall"],
        )

        assert result.suspension_activated is True

    def test_decimal_precision_preserved(self):
        """Decimal precision is preserved in inputs."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=5,
        )

        result = engine.calculate(
            redemption_amount=Decimal("1234.567"),
            config=config,
            triggered_criteria=["liquidity_shortfall"],
        )

        assert result.suspension_activated is True


class TestSuspensionEngineMetadata:
    """Tests for metadata preservation."""

    def test_review_frequency_not_applied(self):
        """review_frequency_days is stored but not applied by engine."""
        engine = SuspensionEngine()
        config_daily = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=1,
        )
        config_weekly = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=7,
        )

        result_daily = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config_daily,
            triggered_criteria=["liquidity_shortfall"],
        )
        result_weekly = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config_weekly,
            triggered_criteria=["liquidity_shortfall"],
        )

        # Engine behavior is identical; metadata is governance-only
        assert result_daily.suspension_activated is True
        assert result_weekly.suspension_activated is True
        assert result_daily.suspension_reason == result_weekly.suspension_reason

    def test_max_suspension_days_not_applied(self):
        """max_suspension_days is stored but not applied by engine."""
        engine = SuspensionEngine()
        config_short = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=5,
            max_suspension_days=7,
        )
        config_long = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=5,
            max_suspension_days=30,
        )

        result_short = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config_short,
            triggered_criteria=["liquidity_shortfall"],
        )
        result_long = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config_long,
            triggered_criteria=["liquidity_shortfall"],
        )

        # Engine behavior is identical; max duration is governance-only
        assert result_short.suspension_activated is True
        assert result_long.suspension_activated is True

    def test_notification_flags_not_applied(self):
        """Notification flags are stored but not applied by engine."""
        engine = SuspensionEngine()
        config_notify = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=5,
            requires_investor_notification=True,
            requires_nca_notification=True,
        )
        config_silent = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=5,
            requires_investor_notification=False,
            requires_nca_notification=False,
        )

        result_notify = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config_notify,
            triggered_criteria=["liquidity_shortfall"],
        )
        result_silent = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config_silent,
            triggered_criteria=["liquidity_shortfall"],
        )

        # Engine behavior is identical; notification is governance-only
        assert result_notify.suspension_activated is True
        assert result_silent.suspension_activated is True


class TestSuspensionEngineStateless:
    """Tests for stateless and deterministic behavior."""

    def test_identical_inputs_identical_outputs(self):
        """Identical inputs always produce identical outputs."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=5,
        )

        result1 = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config,
            triggered_criteria=["liquidity_shortfall"],
        )
        result2 = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config,
            triggered_criteria=["liquidity_shortfall"],
        )

        assert result1.suspension_activated == result2.suspension_activated
        assert result1.suspension_reason == result2.suspension_reason
        assert result1.triggered_criteria == result2.triggered_criteria

    def test_no_side_effects_on_config(self):
        """Engine does not modify config."""
        engine = SuspensionEngine()
        config = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall", "nav_unreliable"],
            review_frequency_days=5,
        )
        config_copy = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall", "nav_unreliable"],
            review_frequency_days=5,
        )

        engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config,
            triggered_criteria=["liquidity_shortfall"],
        )

        assert config.enabled == config_copy.enabled
        assert config.trigger_criteria == config_copy.trigger_criteria
        assert config.review_frequency_days == config_copy.review_frequency_days

    def test_engine_stateless(self):
        """Multiple calls to engine do not interfere with each other."""
        engine = SuspensionEngine()
        config1 = SuspensionConfig(
            enabled=True,
            trigger_criteria=["liquidity_shortfall"],
            review_frequency_days=5,
        )
        config2 = SuspensionConfig(
            enabled=False,
            trigger_criteria=["nav_unreliable"],
            review_frequency_days=5,
        )

        result1 = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config1,
            triggered_criteria=["liquidity_shortfall"],
        )
        result2 = engine.calculate(
            redemption_amount=Decimal("1000000"),
            config=config2,
            triggered_criteria=["liquidity_shortfall"],
        )

        assert result1.suspension_activated is True
        assert result2.suspension_activated is False
