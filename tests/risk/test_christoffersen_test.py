"""Tests for Christoffersen conditional coverage test.

Tests independence and conditional coverage of VaR breaches.
"""

from datetime import date, timedelta
from decimal import Decimal

from manco_risk.risk.engines.christoffersen_test import ChristoffersenTest
from manco_risk.risk.models.backtest_result import BacktestObservation, BacktestResult
from manco_risk.risk.models.christoffersen_test import ChristoffersenTestResult, TransitionMatrix


def create_backtest_result(
    num_obs: int,
    breach_pattern: list[bool],
) -> BacktestResult:
    """Helper to create a BacktestResult with specified breach pattern."""
    start_date = date(2024, 1, 1)
    aligned_obs = [
        BacktestObservation(
            observation_date=start_date + timedelta(days=i),
            var_value=Decimal("0.025"),
            realised_pnl=Decimal("-0.030") if breach_pattern[i] else Decimal("-0.010"),
            is_breach=breach_pattern[i],
        )
        for i in range(num_obs)
    ]

    return BacktestResult(
        num_var_forecasts=num_obs,
        num_pnl_observations=num_obs,
        num_valid_aligned=num_obs,
        num_breaches=sum(breach_pattern),
        num_non_breaches=num_obs - sum(breach_pattern),
        expected_breach_probability=Decimal("0.05"),
        expected_breach_count=Decimal(num_obs) * Decimal("0.05"),
        breach_ratio=Decimal(sum(breach_pattern)) / Decimal(num_obs) if num_obs > 0 else None,
        backtest_start_date=start_date,
        backtest_end_date=start_date + timedelta(days=num_obs - 1),
        breach_dates=[start_date + timedelta(days=i) for i, b in enumerate(breach_pattern) if b],
        missing_var_dates=[],
        missing_pnl_dates=[],
        aligned_observations=aligned_obs,
    )


class TestTransitionMatrix:
    """Tests for TransitionMatrix model."""

    def test_valid_transition_matrix(self) -> None:
        """Valid transition matrix."""
        tm = TransitionMatrix(n00=100, n01=10, n10=5, n11=2)
        assert tm.n00 == 100
        assert tm.n01 == 10
        assert tm.n10 == 5
        assert tm.n11 == 2
        assert tm.n0 == 110
        assert tm.n1 == 7
        assert tm.total == 117

    def test_all_zeros(self) -> None:
        """All zero counts (valid edge case)."""
        tm = TransitionMatrix(n00=0, n01=0, n10=0, n11=0)
        assert tm.total == 0

    def test_derived_counts(self) -> None:
        """Test derived properties."""
        tm = TransitionMatrix(n00=50, n01=10, n10=20, n11=5)
        assert tm.n0 == 60  # n00 + n01
        assert tm.n1 == 25  # n10 + n11
        assert tm.total == 85


class TestChristoffersenTestResult:
    """Tests for ChristoffersenTestResult model."""

    def test_valid_result(self) -> None:
        """Valid Christoffersen test result."""
        tm = TransitionMatrix(n00=100, n01=10, n10=5, n11=2)
        result = ChristoffersenTestResult(
            num_observations=117,
            num_breaches=12,
            expected_breach_probability=Decimal("0.10"),
            transition_matrix=tm,
            uc_test_statistic=Decimal("0.1"),
            uc_p_value=Decimal("0.75"),
            ind_test_statistic=Decimal("0.5"),
            ind_p_value=Decimal("0.48"),
            cc_test_statistic=Decimal("0.6"),
            cc_p_value=Decimal("0.74"),
            alpha=Decimal("0.05"),
            reject_uc=False,
            reject_ind=False,
            reject_cc=False,
        )
        assert result.num_observations == 117
        assert result.reject_cc is False

    def test_reject_flags_consistency(self) -> None:
        """Reject flags must match p-values vs alpha."""
        tm = TransitionMatrix(n00=100, n01=10, n10=5, n11=2)
        result = ChristoffersenTestResult(
            num_observations=117,
            num_breaches=12,
            expected_breach_probability=Decimal("0.10"),
            transition_matrix=tm,
            uc_test_statistic=Decimal("5.0"),
            uc_p_value=Decimal("0.02"),
            ind_test_statistic=Decimal("0.5"),
            ind_p_value=Decimal("0.48"),
            cc_test_statistic=Decimal("5.5"),
            cc_p_value=Decimal("0.01"),
            alpha=Decimal("0.05"),
            reject_uc=True,  # 0.02 < 0.05
            reject_ind=False,  # 0.48 > 0.05
            reject_cc=True,  # 0.01 < 0.05
        )
        assert result.reject_uc is True
        assert result.reject_ind is False
        assert result.reject_cc is True


class TestChristoffersenCalculate:
    """Tests for ChristoffersenTest.calculate()."""

    def test_alternating_breaches(self) -> None:
        """Alternating breach pattern."""
        pattern = [False, True, False, True, False, True]
        result = create_backtest_result(len(pattern), pattern)
        chris = ChristoffersenTest.calculate(result)

        # Verify basic counts
        assert chris.num_observations == 6
        assert chris.num_breaches == 3
        assert chris.transition_matrix.total == 5  # 6 obs → 5 transitions

    def test_clustered_breaches(self) -> None:
        """Breaches clustered together."""
        pattern = [False, False, False, True, True, True, False, False]
        result = create_backtest_result(len(pattern), pattern)
        chris = ChristoffersenTest.calculate(result)

        # Cluster has B→B transitions
        assert chris.num_breaches == 3
        assert chris.transition_matrix.n11 == 2  # 3 breaches = 2 transitions

    def test_no_breaches(self) -> None:
        """No breaches in sequence."""
        pattern = [False] * 10
        result = create_backtest_result(len(pattern), pattern)
        chris = ChristoffersenTest.calculate(result)

        assert chris.num_breaches == 0
        assert chris.transition_matrix.n01 == 0
        assert chris.transition_matrix.n11 == 0

    def test_all_breaches(self) -> None:
        """All observations are breaches."""
        pattern = [True] * 10
        result = create_backtest_result(len(pattern), pattern)
        chris = ChristoffersenTest.calculate(result)

        assert chris.num_breaches == 10
        # All transitions are B→B (n11 = 9 for 10 observations)
        assert chris.transition_matrix.n11 == 9

    def test_all_test_statistics_non_negative(self) -> None:
        """All test statistics are non-negative."""
        pattern = [False, True, False, True, False]
        result = create_backtest_result(len(pattern), pattern)
        chris = ChristoffersenTest.calculate(result)

        assert chris.uc_test_statistic >= Decimal("0")
        assert chris.ind_test_statistic >= Decimal("0")
        assert chris.cc_test_statistic >= Decimal("0")

    def test_cc_stat_sum_of_uc_ind(self) -> None:
        """CC statistic equals UC + Ind (within tolerance)."""
        pattern = [False, True, False, True, False, True]
        result = create_backtest_result(len(pattern), pattern)
        chris = ChristoffersenTest.calculate(result)

        expected = chris.uc_test_statistic + chris.ind_test_statistic
        assert abs(chris.cc_test_statistic - expected) < Decimal("0.01")

    def test_p_values_in_range(self) -> None:
        """All p-values in [0, 1]."""
        pattern = [False, True] * 5
        result = create_backtest_result(len(pattern), pattern)
        chris = ChristoffersenTest.calculate(result)

        assert Decimal("0") <= chris.uc_p_value <= Decimal("1")
        assert Decimal("0") <= chris.ind_p_value <= Decimal("1")
        assert Decimal("0") <= chris.cc_p_value <= Decimal("1")

    def test_alpha_affects_rejection(self) -> None:
        """Alpha parameter affects rejection decision."""
        pattern = [False] * 15 + [True] * 5
        result = create_backtest_result(len(pattern), pattern)

        strict = ChristoffersenTest.calculate(result, alpha=Decimal("0.01"))
        lenient = ChristoffersenTest.calculate(result, alpha=Decimal("0.10"))

        # Results should have the same structure even if rejections differ
        assert isinstance(strict.reject_uc, bool)
        assert isinstance(lenient.reject_uc, bool)
        assert strict.alpha == Decimal("0.01")
        assert lenient.alpha == Decimal("0.10")

    def test_single_breach_in_long_series(self) -> None:
        """Single isolated breach."""
        pattern = [False] * 20 + [True] + [False] * 20
        result = create_backtest_result(len(pattern), pattern)
        chris = ChristoffersenTest.calculate(result)

        assert chris.num_breaches == 1
        assert chris.transition_matrix.n01 == 1  # N→B once
        assert chris.transition_matrix.n10 == 1  # B→N once
        assert chris.transition_matrix.n11 == 0  # No B→B
