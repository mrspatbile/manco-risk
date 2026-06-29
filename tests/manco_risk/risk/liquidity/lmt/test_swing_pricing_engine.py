"""Tests for swing pricing engine."""

from decimal import Decimal

import pytest

from manco_risk.risk.liquidity.lmt.models import SwingPricingConfig
from manco_risk.risk.liquidity.lmt.swing_pricing_engine import (
    SwingPricingEngine,
    SwingPricingResult,
)


class TestSwingPricingResult:
    """Tests for SwingPricingResult model validation."""

    def test_valid_swing_activated_nav_basis(self):
        """Create valid swing result when activated with NAV basis."""
        result = SwingPricingResult(
            swing_pricing_activated=True,
            raw_swing_factor=Decimal("0.025"),
            applied_swing_factor=Decimal("0.020"),
            exceeded_maximum_factor=True,
            swing_cost_amount=Decimal("100000"),
            redemption_rate=Decimal("0.15"),
            cost_basis="nav",
        )
        assert result.swing_pricing_activated is True
        assert result.raw_swing_factor == Decimal("0.025")
        assert result.cost_basis == "nav"

    def test_valid_swing_activated_flow_basis(self):
        """Create valid swing result when activated with flow basis."""
        result = SwingPricingResult(
            swing_pricing_activated=True,
            raw_swing_factor=Decimal("0.030"),
            applied_swing_factor=Decimal("0.020"),
            exceeded_maximum_factor=True,
            swing_cost_amount=Decimal("50000"),
            redemption_rate=Decimal("0.20"),
            cost_basis="flow",
        )
        assert result.swing_pricing_activated is True
        assert result.cost_basis == "flow"

    def test_valid_swing_not_activated(self):
        """Create valid swing result when not activated."""
        result = SwingPricingResult(
            swing_pricing_activated=False,
            raw_swing_factor=Decimal("0"),
            applied_swing_factor=Decimal("0"),
            exceeded_maximum_factor=False,
            swing_cost_amount=Decimal("0"),
            redemption_rate=Decimal("0.05"),
            cost_basis="nav",
        )
        assert result.swing_pricing_activated is False
        assert result.applied_swing_factor == Decimal("0")

    def test_activated_requires_positive_applied_factor(self):
        """If activated, applied_swing_factor must be > 0."""
        with pytest.raises(
            ValueError, match="swing_pricing_activated=True requires applied_swing_factor"
        ):
            SwingPricingResult(
                swing_pricing_activated=True,
                raw_swing_factor=Decimal("0.010"),
                applied_swing_factor=Decimal("0"),  # Invalid for activated
                exceeded_maximum_factor=False,
                swing_cost_amount=Decimal("0"),
                redemption_rate=Decimal("0.15"),
                cost_basis="nav",
            )

    def test_not_activated_requires_zero_applied_factor(self):
        """If not activated, applied_swing_factor must be 0."""
        with pytest.raises(
            ValueError, match="swing_pricing_activated=False requires applied_swing_factor"
        ):
            SwingPricingResult(
                swing_pricing_activated=False,
                raw_swing_factor=Decimal("0"),
                applied_swing_factor=Decimal("0.010"),  # Invalid for not activated
                exceeded_maximum_factor=False,
                swing_cost_amount=Decimal("50000"),
                redemption_rate=Decimal("0.15"),
                cost_basis="nav",
            )

    def test_non_negative_factors(self):
        """All factors must be non-negative."""
        with pytest.raises(ValueError, match="must be non-negative"):
            SwingPricingResult(
                swing_pricing_activated=False,
                raw_swing_factor=Decimal("-0.010"),
                applied_swing_factor=Decimal("0"),
                exceeded_maximum_factor=False,
                swing_cost_amount=Decimal("0"),
                redemption_rate=Decimal("0.05"),
                cost_basis="nav",
            )

    def test_applied_factor_not_exceeding_one(self):
        """Applied factor cannot exceed 1.0."""
        with pytest.raises(ValueError, match="cannot exceed 1.0"):
            SwingPricingResult(
                swing_pricing_activated=True,
                raw_swing_factor=Decimal("1.5"),
                applied_swing_factor=Decimal("1.1"),
                exceeded_maximum_factor=True,
                swing_cost_amount=Decimal("100000"),
                redemption_rate=Decimal("0.20"),
                cost_basis="nav",
            )

    def test_valid_cost_basis(self):
        """Cost basis must be 'nav' or 'flow'."""
        with pytest.raises(ValueError, match="cost_basis must be"):
            SwingPricingResult(
                swing_pricing_activated=False,
                raw_swing_factor=Decimal("0"),
                applied_swing_factor=Decimal("0"),
                exceeded_maximum_factor=False,
                swing_cost_amount=Decimal("0"),
                redemption_rate=Decimal("0.05"),
                cost_basis="invalid",
            )

    def test_frozen_model(self):
        """SwingPricingResult is immutable."""
        result = SwingPricingResult(
            swing_pricing_activated=False,
            raw_swing_factor=Decimal("0"),
            applied_swing_factor=Decimal("0"),
            exceeded_maximum_factor=False,
            swing_cost_amount=Decimal("0"),
            redemption_rate=Decimal("0.05"),
            cost_basis="nav",
        )
        with pytest.raises(Exception):
            result.swing_pricing_activated = True


class TestSwingPricingEngineDisabled:
    """Tests for swing pricing engine with disabled config."""

    def test_disabled_config_no_swing(self):
        """If swing pricing is disabled, no activation regardless of redemption."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=False,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("2000000"),
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("100000"),
            config=config,
        )

        assert result.swing_pricing_activated is False
        assert result.applied_swing_factor == Decimal("0")
        assert result.swing_cost_amount == Decimal("0")
        assert result.cost_basis == "nav"


class TestSwingPricingEngineZeroRedemption:
    """Tests for swing pricing engine with zero redemption."""

    def test_zero_redemption_no_swing(self):
        """If redemption_amount is zero, no swing even if cost exists."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("0"),
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("500000"),
            config=config,
        )

        assert result.swing_pricing_activated is False
        assert result.applied_swing_factor == Decimal("0")
        assert result.swing_cost_amount == Decimal("0")
        assert result.redemption_rate == Decimal("0")


class TestSwingPricingEngineThreshold:
    """Tests for swing pricing threshold logic."""

    def test_redemption_rate_below_threshold(self):
        """If redemption_rate < threshold, no swing."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("500000"),  # 5% of NAV
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("50000"),
            config=config,
        )

        assert result.swing_pricing_activated is False
        assert result.redemption_rate == Decimal("0.05")

    def test_redemption_rate_at_threshold(self):
        """If redemption_rate == threshold, no swing (boundary case)."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),  # Exactly 10% of NAV
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("100000"),
            config=config,
        )

        assert result.swing_pricing_activated is False
        assert result.redemption_rate == Decimal("0.10")

    def test_redemption_rate_above_threshold(self):
        """If redemption_rate > threshold, swing is triggered."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("1500000"),  # 15% of NAV
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("150000"),
            config=config,
        )

        assert result.swing_pricing_activated is True
        assert result.redemption_rate == Decimal("0.15")


class TestSwingPricingEngineNavBasis:
    """Tests for NAV cost basis calculation."""

    def test_nav_basis_raw_factor_calculation(self):
        """NAV basis: raw_swing_factor = estimated_liquidity_cost / fund_nav."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.05"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("2000000"),  # 20% of NAV
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("200000"),  # 2% of NAV
            config=config,
        )

        assert result.swing_pricing_activated is True
        assert result.raw_swing_factor == Decimal("0.02")  # 200000 / 10000000
        assert result.applied_swing_factor == Decimal("0.02")
        assert result.exceeded_maximum_factor is False
        assert result.swing_cost_amount == Decimal("200000")  # 0.02 * 10000000
        assert result.cost_basis == "nav"

    def test_nav_basis_swing_cost_calculation(self):
        """NAV basis: swing_cost = applied_swing_factor * fund_nav."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.05"),
            max_swing_factor=Decimal("0.015"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("1500000"),  # 15% of NAV
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("300000"),  # Would be 3% raw
            config=config,
        )

        assert result.swing_pricing_activated is True
        assert result.raw_swing_factor == Decimal("0.03")
        assert result.applied_swing_factor == Decimal("0.015")  # Capped at max
        assert result.swing_cost_amount == Decimal("150000")  # 0.015 * 10000000
        assert result.cost_basis == "nav"

    def test_nav_basis_zero_cost_with_trigger(self):
        """NAV basis with zero estimated cost and threshold exceeded.

        Even though threshold is exceeded, if cost is zero, no swing applies.
        Swing pricing only applies if there's cost to transfer.
        """
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("2000000"),  # 20% of NAV
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("0"),
            config=config,
        )

        # Threshold is exceeded, but zero cost means no swing to apply
        assert result.swing_pricing_activated is False
        assert result.raw_swing_factor == Decimal("0")
        assert result.applied_swing_factor == Decimal("0")
        assert result.swing_cost_amount == Decimal("0")


class TestSwingPricingEngineFlowBasis:
    """Tests for flow cost basis calculation."""

    def test_flow_basis_raw_factor_calculation(self):
        """Flow basis: raw_swing_factor = estimated_liquidity_cost / redemption_amount."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.05"),
            cost_basis="flow",
        )

        result = engine.calculate(
            redemption_amount=Decimal("2000000"),  # 20% of NAV
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("100000"),  # 5% of redemption flow
            config=config,
        )

        assert result.swing_pricing_activated is True
        assert result.raw_swing_factor == Decimal("0.05")  # 100000 / 2000000
        assert result.applied_swing_factor == Decimal("0.05")
        assert result.exceeded_maximum_factor is False
        assert result.swing_cost_amount == Decimal("100000")  # 0.05 * 2000000
        assert result.cost_basis == "flow"

    def test_flow_basis_swing_cost_calculation(self):
        """Flow basis: swing_cost = applied_swing_factor * redemption_amount."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.05"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="flow",
        )

        result = engine.calculate(
            redemption_amount=Decimal("1500000"),  # 15% of NAV
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("60000"),  # Would be 4% raw
            config=config,
        )

        assert result.swing_pricing_activated is True
        assert result.raw_swing_factor == Decimal("0.04")  # 60000 / 1500000
        assert result.applied_swing_factor == Decimal("0.02")  # Capped at max
        assert result.swing_cost_amount == Decimal("30000")  # 0.02 * 1500000
        assert result.cost_basis == "flow"

    def test_flow_basis_zero_cost(self):
        """Flow basis with zero estimated cost and threshold exceeded.

        Even though threshold is exceeded, if cost is zero, no swing applies.
        """
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="flow",
        )

        result = engine.calculate(
            redemption_amount=Decimal("2000000"),  # 20% of NAV
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("0"),
            config=config,
        )

        # Threshold is exceeded, but zero cost means no swing to apply
        assert result.swing_pricing_activated is False
        assert result.raw_swing_factor == Decimal("0")
        assert result.applied_swing_factor == Decimal("0")
        assert result.swing_cost_amount == Decimal("0")


class TestSwingPricingEngineMaxFactorCapping:
    """Tests for max factor capping logic."""

    def test_raw_factor_below_max_no_cap(self):
        """If raw factor < max, apply raw (no capping)."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.03"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("2000000"),  # 20% of NAV
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("150000"),  # 1.5% of NAV
            config=config,
        )

        assert result.swing_pricing_activated is True
        assert result.raw_swing_factor == Decimal("0.015")
        assert result.applied_swing_factor == Decimal("0.015")
        assert result.exceeded_maximum_factor is False

    def test_raw_factor_above_max_capped(self):
        """If raw factor > max, cap at max and flag it."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("2000000"),  # 20% of NAV
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("500000"),  # 5% of NAV
            config=config,
        )

        assert result.swing_pricing_activated is True
        assert result.raw_swing_factor == Decimal("0.05")
        assert result.applied_swing_factor == Decimal("0.02")  # Capped
        assert result.exceeded_maximum_factor is True

    def test_raw_factor_equals_max_no_flag(self):
        """If raw factor == max, no exceeding flag."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("2000000"),  # 20% of NAV
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("200000"),  # Exactly 2% of NAV
            config=config,
        )

        assert result.swing_pricing_activated is True
        assert result.raw_swing_factor == Decimal("0.02")
        assert result.applied_swing_factor == Decimal("0.02")
        assert result.exceeded_maximum_factor is False

    def test_max_factor_boundary_flow_basis(self):
        """Max factor capping with flow basis."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.05"),
            max_swing_factor=Decimal("0.025"),
            cost_basis="flow",
        )

        result = engine.calculate(
            redemption_amount=Decimal("1000000"),  # 10% of NAV
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("50000"),  # 5% of flow
            config=config,
        )

        assert result.swing_pricing_activated is True
        assert result.raw_swing_factor == Decimal("0.05")
        assert result.applied_swing_factor == Decimal("0.025")
        assert result.exceeded_maximum_factor is True
        assert result.swing_cost_amount == Decimal("25000")  # 0.025 * 1000000


class TestSwingPricingEngineValidation:
    """Tests for input validation."""

    def test_negative_redemption_amount(self):
        """Negative redemption amount raises ValueError."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        with pytest.raises(ValueError, match="redemption_amount must be non-negative"):
            engine.calculate(
                redemption_amount=Decimal("-1000000"),
                fund_nav=Decimal("10000000"),
                estimated_liquidity_cost=Decimal("100000"),
                config=config,
            )

    def test_zero_nav_invalid(self):
        """Zero NAV raises ValueError."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        with pytest.raises(ValueError, match="fund_nav must be positive"):
            engine.calculate(
                redemption_amount=Decimal("1000000"),
                fund_nav=Decimal("0"),
                estimated_liquidity_cost=Decimal("100000"),
                config=config,
            )

    def test_negative_nav_invalid(self):
        """Negative NAV raises ValueError."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        with pytest.raises(ValueError, match="fund_nav must be positive"):
            engine.calculate(
                redemption_amount=Decimal("1000000"),
                fund_nav=Decimal("-10000000"),
                estimated_liquidity_cost=Decimal("100000"),
                config=config,
            )

    def test_negative_liquidity_cost(self):
        """Negative estimated liquidity cost raises ValueError."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        with pytest.raises(ValueError, match="estimated_liquidity_cost must be non-negative"):
            engine.calculate(
                redemption_amount=Decimal("1000000"),
                fund_nav=Decimal("10000000"),
                estimated_liquidity_cost=Decimal("-100000"),
                config=config,
            )

    def test_large_amounts_precision_preserved(self):
        """Large amounts preserve Decimal precision."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("999999999999.99"),
            fund_nav=Decimal("5000000000000"),
            estimated_liquidity_cost=Decimal("12345678.99"),
            config=config,
        )

        assert result.swing_pricing_activated is True


class TestSwingPricingEngineMetadata:
    """Tests for metadata preservation."""

    def test_cost_basis_preserved_nav(self):
        """NAV cost basis is preserved in result."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("2000000"),
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("200000"),
            config=config,
        )

        assert result.cost_basis == "nav"

    def test_cost_basis_preserved_flow(self):
        """Flow cost basis is preserved in result."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="flow",
        )

        result = engine.calculate(
            redemption_amount=Decimal("2000000"),
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("200000"),
            config=config,
        )

        assert result.cost_basis == "flow"

    def test_config_description_not_in_result(self):
        """Config description is not copied to result (governance metadata)."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
            description="Custom swing pricing policy",
        )

        result = engine.calculate(
            redemption_amount=Decimal("2000000"),
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("200000"),
            config=config,
        )

        # Result should have cost_basis for traceability but not description
        assert result.cost_basis == "nav"
        assert not hasattr(result, "description")


class TestSwingPricingEngineStateless:
    """Tests for stateless and deterministic behavior."""

    def test_identical_inputs_identical_outputs(self):
        """Identical inputs always produce identical outputs."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        result1 = engine.calculate(
            redemption_amount=Decimal("2000000"),
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("200000"),
            config=config,
        )
        result2 = engine.calculate(
            redemption_amount=Decimal("2000000"),
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("200000"),
            config=config,
        )

        assert result1.swing_pricing_activated == result2.swing_pricing_activated
        assert result1.raw_swing_factor == result2.raw_swing_factor
        assert result1.applied_swing_factor == result2.applied_swing_factor
        assert result1.swing_cost_amount == result2.swing_cost_amount

    def test_no_side_effects_on_config(self):
        """Engine does not modify config."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )
        config_copy = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )

        engine.calculate(
            redemption_amount=Decimal("2000000"),
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("200000"),
            config=config,
        )

        assert config.enabled == config_copy.enabled
        assert config.trigger_threshold == config_copy.trigger_threshold
        assert config.max_swing_factor == config_copy.max_swing_factor

    def test_engine_stateless(self):
        """Multiple calls with different configs do not interfere."""
        engine = SwingPricingEngine()
        config1 = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="nav",
        )
        config2 = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.05"),
            max_swing_factor=Decimal("0.01"),
            cost_basis="flow",
        )

        result1 = engine.calculate(
            redemption_amount=Decimal("2000000"),
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("200000"),
            config=config1,
        )
        result2 = engine.calculate(
            redemption_amount=Decimal("2000000"),
            fund_nav=Decimal("10000000"),
            estimated_liquidity_cost=Decimal("200000"),
            config=config2,
        )

        assert result1.cost_basis == "nav"
        assert result2.cost_basis == "flow"


class TestSwingPricingEngineRealWorldScenarios:
    """Tests for realistic fund scenarios."""

    def test_large_redemption_nav_basis(self):
        """Large redemption with NAV cost basis."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.15"),
            max_swing_factor=Decimal("0.01"),
            cost_basis="nav",
        )

        # 30M redemption on 100M fund = 30%, threshold 15%
        result = engine.calculate(
            redemption_amount=Decimal("30000000"),
            fund_nav=Decimal("100000000"),
            estimated_liquidity_cost=Decimal("1500000"),  # 1.5% of NAV
            config=config,
        )

        assert result.swing_pricing_activated is True
        assert result.redemption_rate == Decimal("0.30")
        assert result.raw_swing_factor == Decimal("0.015")
        assert result.applied_swing_factor == Decimal("0.01")
        assert result.exceeded_maximum_factor is True
        assert result.swing_cost_amount == Decimal("1000000")

    def test_small_redemption_below_threshold(self):
        """Small redemption below threshold."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.05"),
            max_swing_factor=Decimal("0.02"),
            cost_basis="flow",
        )

        # 2M redemption on 100M fund = 2%, threshold 5%
        result = engine.calculate(
            redemption_amount=Decimal("2000000"),
            fund_nav=Decimal("100000000"),
            estimated_liquidity_cost=Decimal("100000"),
            config=config,
        )

        assert result.swing_pricing_activated is False
        assert result.redemption_rate == Decimal("0.02")

    def test_exactly_at_max_factor(self):
        """Swing factor exactly at maximum."""
        engine = SwingPricingEngine()
        config = SwingPricingConfig(
            enabled=True,
            trigger_threshold=Decimal("0.10"),
            max_swing_factor=Decimal("0.015"),
            cost_basis="nav",
        )

        result = engine.calculate(
            redemption_amount=Decimal("15000000"),  # 15% of NAV
            fund_nav=Decimal("100000000"),
            estimated_liquidity_cost=Decimal("1500000"),  # Exactly 1.5% of NAV
            config=config,
        )

        assert result.swing_pricing_activated is True
        assert result.raw_swing_factor == Decimal("0.015")
        assert result.applied_swing_factor == Decimal("0.015")
        assert result.exceeded_maximum_factor is False
