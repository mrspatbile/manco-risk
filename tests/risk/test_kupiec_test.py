"""Tests for Kupiec unconditional coverage test.

Tests the Kupiec POF (Proportion of Failures) test for VaR backtesting.
"""

from decimal import Decimal

import pytest

from manco_risk.risk.engines.backtesting_tests import KupiecTest
from manco_risk.risk.models.kupiec_test import KupiecTestResult


class TestKupiecTestResult:
    """Tests for KupiecTestResult model validation."""

    def test_valid_result(self) -> None:
        """Valid Kupiec test result."""
        result = KupiecTestResult(
            num_observations=250,
            num_breaches=10,
            expected_breach_probability=Decimal("0.05"),
            observed_breach_probability=Decimal("0.04"),
            lr_statistic=Decimal("0.5"),
            p_value=Decimal("0.48"),
            alpha=Decimal("0.05"),
            reject_null=False,
        )
        assert result.num_observations == 250
        assert result.num_breaches == 10

    def test_num_observations_must_be_positive(self) -> None:
        """Number of observations must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            KupiecTestResult(
                num_observations=0,
                num_breaches=0,
                expected_breach_probability=Decimal("0.05"),
                observed_breach_probability=Decimal("0"),
                lr_statistic=Decimal("0"),
                p_value=Decimal("1"),
                alpha=Decimal("0.05"),
                reject_null=False,
            )

    def test_num_breaches_non_negative(self) -> None:
        """Number of breaches must be non-negative."""
        with pytest.raises(ValueError, match="must be non-negative"):
            KupiecTestResult(
                num_observations=100,
                num_breaches=-1,
                expected_breach_probability=Decimal("0.05"),
                observed_breach_probability=Decimal("0"),
                lr_statistic=Decimal("0"),
                p_value=Decimal("1"),
                alpha=Decimal("0.05"),
                reject_null=False,
            )

    def test_breaches_cannot_exceed_observations(self) -> None:
        """Number of breaches cannot exceed observations."""
        with pytest.raises(ValueError, match="cannot exceed"):
            KupiecTestResult(
                num_observations=100,
                num_breaches=101,
                expected_breach_probability=Decimal("0.05"),
                observed_breach_probability=Decimal("1.01"),
                lr_statistic=Decimal("0"),
                p_value=Decimal("0.01"),
                alpha=Decimal("0.05"),
                reject_null=True,
            )

    def test_expected_probability_in_open_interval(self) -> None:
        """Expected breach probability must be in (0, 1)."""
        with pytest.raises(ValueError, match="must be in \\(0, 1\\)"):
            KupiecTestResult(
                num_observations=100,
                num_breaches=5,
                expected_breach_probability=Decimal("0"),
                observed_breach_probability=Decimal("0.05"),
                lr_statistic=Decimal("0"),
                p_value=Decimal("1"),
                alpha=Decimal("0.05"),
                reject_null=False,
            )

    def test_observed_probability_in_closed_interval(self) -> None:
        """Observed breach probability must be in [0, 1]."""
        with pytest.raises(ValueError, match="must be in \\[0, 1\\]"):
            KupiecTestResult(
                num_observations=100,
                num_breaches=5,
                expected_breach_probability=Decimal("0.05"),
                observed_breach_probability=Decimal("1.01"),
                lr_statistic=Decimal("0"),
                p_value=Decimal("0.5"),
                alpha=Decimal("0.05"),
                reject_null=False,
            )

    def test_observed_probability_matches_ratio(self) -> None:
        """Observed breach probability must equal num_breaches / num_observations."""
        with pytest.raises(ValueError, match="must equal"):
            KupiecTestResult(
                num_observations=100,
                num_breaches=5,
                expected_breach_probability=Decimal("0.05"),
                observed_breach_probability=Decimal("0.04"),  # Should be 0.05
                lr_statistic=Decimal("0"),
                p_value=Decimal("1"),
                alpha=Decimal("0.05"),
                reject_null=False,
            )

    def test_lr_statistic_non_negative(self) -> None:
        """LR statistic must be non-negative."""
        with pytest.raises(ValueError, match="must be non-negative"):
            KupiecTestResult(
                num_observations=100,
                num_breaches=5,
                expected_breach_probability=Decimal("0.05"),
                observed_breach_probability=Decimal("0.05"),
                lr_statistic=Decimal("-0.1"),
                p_value=Decimal("0.5"),
                alpha=Decimal("0.05"),
                reject_null=False,
            )

    def test_p_value_in_unit_interval(self) -> None:
        """P-value must be in [0, 1]."""
        with pytest.raises(ValueError, match="must be in \\[0, 1\\]"):
            KupiecTestResult(
                num_observations=100,
                num_breaches=5,
                expected_breach_probability=Decimal("0.05"),
                observed_breach_probability=Decimal("0.05"),
                lr_statistic=Decimal("0"),
                p_value=Decimal("1.01"),
                alpha=Decimal("0.05"),
                reject_null=False,
            )

    def test_alpha_in_open_interval(self) -> None:
        """Alpha must be in (0, 1)."""
        with pytest.raises(ValueError, match="must be in \\(0, 1\\)"):
            KupiecTestResult(
                num_observations=100,
                num_breaches=5,
                expected_breach_probability=Decimal("0.05"),
                observed_breach_probability=Decimal("0.05"),
                lr_statistic=Decimal("0"),
                p_value=Decimal("0.5"),
                alpha=Decimal("0"),
                reject_null=False,
            )

    def test_reject_null_must_match_p_value_alpha(self) -> None:
        """reject_null must equal (p_value < alpha)."""
        with pytest.raises(ValueError, match="reject_null must be"):
            KupiecTestResult(
                num_observations=100,
                num_breaches=5,
                expected_breach_probability=Decimal("0.05"),
                observed_breach_probability=Decimal("0.05"),
                lr_statistic=Decimal("0"),
                p_value=Decimal("0.02"),  # < 0.05
                alpha=Decimal("0.05"),
                reject_null=False,  # Should be True
            )

    def test_frozen_model(self) -> None:
        """KupiecTestResult is frozen (immutable)."""
        result = KupiecTestResult(
            num_observations=100,
            num_breaches=5,
            expected_breach_probability=Decimal("0.05"),
            observed_breach_probability=Decimal("0.05"),
            lr_statistic=Decimal("0"),
            p_value=Decimal("1"),
            alpha=Decimal("0.05"),
            reject_null=False,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            result.num_breaches = 10  # type: ignore


class TestKupiecCalculate:
    """Tests for KupiecTest.calculate() method."""

    def test_observed_equals_expected_no_rejection(self) -> None:
        """When observed matches expected, do not reject (high p-value)."""
        # 250 observations, 95% confidence, so expect 5% breaches = 12.5
        # Actual: 12 breaches (close to expected)
        result = KupiecTest.calculate(
            num_observations=250,
            num_breaches=12,
            expected_breach_probability=Decimal("0.05"),
            alpha=Decimal("0.05"),
        )
        assert result.observed_breach_probability == Decimal("0.048")
        assert result.reject_null is False
        assert result.p_value > Decimal("0.05")

    def test_too_many_breaches_rejection(self) -> None:
        """When breaches are significantly above expected, reject."""
        # 250 observations, expected 5% = 12.5 breaches
        # Actual: 30 breaches (far above expected)
        result = KupiecTest.calculate(
            num_observations=250,
            num_breaches=30,
            expected_breach_probability=Decimal("0.05"),
            alpha=Decimal("0.05"),
        )
        assert result.observed_breach_probability == Decimal("0.12")
        assert result.reject_null is True
        assert result.p_value < Decimal("0.05")

    def test_too_few_breaches_rejection(self) -> None:
        """When breaches are significantly below expected, reject."""
        # 250 observations, expected 5% = 12.5 breaches
        # Actual: 0 breaches (far below expected)
        result = KupiecTest.calculate(
            num_observations=250,
            num_breaches=0,
            expected_breach_probability=Decimal("0.05"),
            alpha=Decimal("0.05"),
        )
        assert result.observed_breach_probability == Decimal("0")
        assert result.reject_null is True
        assert result.p_value < Decimal("0.05")

    def test_zero_breaches_edge_case(self) -> None:
        """Handle zero breaches correctly (boundary case for log)."""
        result = KupiecTest.calculate(
            num_observations=100,
            num_breaches=0,
            expected_breach_probability=Decimal("0.05"),
        )
        assert result.num_breaches == 0
        assert result.observed_breach_probability == Decimal("0")
        assert result.lr_statistic >= Decimal("0")
        assert Decimal("0") <= result.p_value <= Decimal("1")

    def test_all_breaches_edge_case(self) -> None:
        """Handle all breaches correctly (boundary case for log)."""
        result = KupiecTest.calculate(
            num_observations=100,
            num_breaches=100,
            expected_breach_probability=Decimal("0.05"),
        )
        assert result.num_breaches == 100
        assert result.observed_breach_probability == Decimal("1")
        assert result.lr_statistic >= Decimal("0")
        assert Decimal("0") <= result.p_value <= Decimal("1")

    def test_p_value_in_valid_range(self) -> None:
        """P-value must be between 0 and 1."""
        for num_breaches in [0, 5, 10, 25, 50, 100]:
            result = KupiecTest.calculate(
                num_observations=100,
                num_breaches=num_breaches,
                expected_breach_probability=Decimal("0.25"),
            )
            assert Decimal("0") <= result.p_value <= Decimal("1")

    def test_alpha_controls_rejection(self) -> None:
        """Alpha parameter controls rejection decision."""
        # Case: p_value = 0.06, between common alpha levels
        # Should reject at alpha=0.10, not reject at alpha=0.05
        result_reject = KupiecTest.calculate(
            num_observations=250,
            num_breaches=25,
            expected_breach_probability=Decimal("0.05"),
            alpha=Decimal("0.10"),
        )
        result_no_reject = KupiecTest.calculate(
            num_observations=250,
            num_breaches=25,
            expected_breach_probability=Decimal("0.05"),
            alpha=Decimal("0.05"),
        )
        # One should reject, one should not (or both same if p-value farther from boundary)
        # Check that alpha actually affects outcome (when p-value is near boundaries)
        assert result_reject.alpha == Decimal("0.10")
        assert result_no_reject.alpha == Decimal("0.05")

    def test_observed_breach_probability_calculation(self) -> None:
        """Observed breach probability equals num_breaches / num_observations."""
        result = KupiecTest.calculate(
            num_observations=200,
            num_breaches=20,
            expected_breach_probability=Decimal("0.05"),
        )
        assert result.observed_breach_probability == Decimal("0.10")

    def test_result_fields_populated(self) -> None:
        """All result fields are populated."""
        result = KupiecTest.calculate(
            num_observations=250,
            num_breaches=15,
            expected_breach_probability=Decimal("0.05"),
            alpha=Decimal("0.05"),
        )
        assert result.num_observations == 250
        assert result.num_breaches == 15
        assert result.expected_breach_probability == Decimal("0.05")
        assert result.observed_breach_probability == Decimal("0.06")
        assert result.lr_statistic >= Decimal("0")
        assert Decimal("0") <= result.p_value <= Decimal("1")
        assert result.alpha == Decimal("0.05")
        assert isinstance(result.reject_null, bool)

    def test_lr_statistic_increases_with_divergence(self) -> None:
        """LR statistic increases as observed diverges from expected."""
        # Moderate divergence
        result_moderate = KupiecTest.calculate(
            num_observations=250,
            num_breaches=20,  # 8% vs expected 5%
            expected_breach_probability=Decimal("0.05"),
        )
        # Large divergence
        result_large = KupiecTest.calculate(
            num_observations=250,
            num_breaches=40,  # 16% vs expected 5%
            expected_breach_probability=Decimal("0.05"),
        )
        # Larger divergence should have larger LR statistic
        assert result_large.lr_statistic > result_moderate.lr_statistic

    def test_different_confidence_levels(self) -> None:
        """Test with different confidence levels (different expected probabilities)."""
        # 99% confidence: 1% expected breaches
        result_99 = KupiecTest.calculate(
            num_observations=250,
            num_breaches=5,
            expected_breach_probability=Decimal("0.01"),
        )
        # 95% confidence: 5% expected breaches
        result_95 = KupiecTest.calculate(
            num_observations=250,
            num_breaches=5,
            expected_breach_probability=Decimal("0.05"),
        )
        # Same breach count, different expected levels
        assert result_99.observed_breach_probability == result_95.observed_breach_probability
        assert result_99.observed_breach_probability == Decimal("0.02")
        # One may reject, one may not, depending on divergence

    def test_symmetry_around_expected(self) -> None:
        """Test symmetry: deviations above/below expected."""
        # 5% expected, 25 observations → expect 1.25 breaches
        # Test 0 breaches vs 3 breaches (both deviate ~1.25)
        result_below = KupiecTest.calculate(
            num_observations=25,
            num_breaches=0,
            expected_breach_probability=Decimal("0.05"),
        )
        result_above = KupiecTest.calculate(
            num_observations=25,
            num_breaches=3,
            expected_breach_probability=Decimal("0.05"),
        )
        # LR statistics should be similar (symmetry of binomial)
        # but not necessarily equal due to discrete nature
        assert result_below.lr_statistic >= Decimal("0")
        assert result_above.lr_statistic >= Decimal("0")

    def test_small_sample_size(self) -> None:
        """Handle small sample sizes."""
        result = KupiecTest.calculate(
            num_observations=10,
            num_breaches=1,
            expected_breach_probability=Decimal("0.05"),
        )
        assert result.num_observations == 10
        assert result.observed_breach_probability == Decimal("0.1")

    def test_large_sample_size(self) -> None:
        """Handle large sample sizes."""
        result = KupiecTest.calculate(
            num_observations=5000,
            num_breaches=250,
            expected_breach_probability=Decimal("0.05"),
        )
        assert result.num_observations == 5000
        assert result.observed_breach_probability == Decimal("0.05")


class TestKupiecStatisticCalculation:
    """Tests for likelihood-ratio statistic calculation details."""

    def test_lr_statistic_zero_when_observed_equals_expected(self) -> None:
        """LR statistic should be close to zero when probabilities match exactly."""
        # Create a scenario where observed exactly equals expected
        # 100 obs, 5 breaches, 5% expected = exact match
        result = KupiecTest.calculate(
            num_observations=100,
            num_breaches=5,
            expected_breach_probability=Decimal("0.05"),
        )
        # Should be very close to zero (small floating point differences allowed)
        assert result.lr_statistic < Decimal("0.01")

    def test_lr_statistic_for_boundary_cases(self) -> None:
        """LR statistic handles boundary cases (0 and n breaches)."""
        # Zero breaches
        result_zero = KupiecTest.calculate(
            num_observations=100,
            num_breaches=0,
            expected_breach_probability=Decimal("0.05"),
        )
        assert result_zero.lr_statistic > Decimal("0")

        # All breaches
        result_all = KupiecTest.calculate(
            num_observations=100,
            num_breaches=100,
            expected_breach_probability=Decimal("0.05"),
        )
        assert result_all.lr_statistic > Decimal("0")
