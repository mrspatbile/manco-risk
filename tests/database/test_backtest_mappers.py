"""Tests for VaR backtesting result mappers.

Tests conversion of pure backtesting results to ORM objects.
"""

from datetime import date, timedelta
from decimal import Decimal

from manco_risk.database.backtest_mappers import map_backtest_result_to_orm
from manco_risk.risk.models.backtest_result import BacktestObservation, BacktestResult
from manco_risk.risk.models.christoffersen_test import ChristoffersenTestResult, TransitionMatrix
from manco_risk.risk.models.kupiec_test import KupiecTestResult


def create_backtest_result(num_obs: int, breach_count: int) -> BacktestResult:
    """Create a test BacktestResult."""
    start_date = date(2024, 1, 1)
    breach_indices = set(range(breach_count))

    aligned_obs = [
        BacktestObservation(
            observation_date=start_date + timedelta(days=i),
            var_value=Decimal("0.025"),
            realised_pnl=Decimal("-0.030") if i in breach_indices else Decimal("-0.010"),
            is_breach=i in breach_indices,
        )
        for i in range(num_obs)
    ]

    return BacktestResult(
        num_var_forecasts=num_obs,
        num_pnl_observations=num_obs,
        num_valid_aligned=num_obs,
        num_breaches=breach_count,
        num_non_breaches=num_obs - breach_count,
        expected_breach_probability=Decimal("0.05"),
        expected_breach_count=Decimal(num_obs) * Decimal("0.05"),
        breach_ratio=Decimal(breach_count) / Decimal(num_obs) if num_obs > 0 else None,
        backtest_start_date=start_date,
        backtest_end_date=start_date + timedelta(days=num_obs - 1),
        breach_dates=[aligned_obs[i].observation_date for i in breach_indices],
        missing_var_dates=[],
        missing_pnl_dates=[],
        aligned_observations=aligned_obs,
    )


class TestMapBacktestResultToORM:
    """Tests for map_backtest_result_to_orm mapper."""

    def test_map_all_fields(self) -> None:
        """Map all fields from pure results to ORM."""
        backtest_result = create_backtest_result(100, 5)
        kupiec_result = KupiecTestResult(
            num_observations=100,
            num_breaches=5,
            expected_breach_probability=Decimal("0.05"),
            observed_breach_probability=Decimal("0.05"),
            lr_statistic=Decimal("0.1"),
            p_value=Decimal("0.75"),
            alpha=Decimal("0.05"),
            reject_null=False,
        )
        christoffersen_result = ChristoffersenTestResult(
            num_observations=100,
            num_breaches=5,
            expected_breach_probability=Decimal("0.05"),
            transition_matrix=TransitionMatrix(n00=95, n01=5, n10=0, n11=0),
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

        orm = map_backtest_result_to_orm(
            backtest_result,
            kupiec_result,
            christoffersen_result,
            calculation_run_id=123,
            fund_id=456,
        )

        # Check all fields mapped correctly
        assert orm.calculation_run_id == 123
        assert orm.fund_id == 456
        assert orm.window_days == 1
        assert orm.total_observations == 100
        assert orm.num_exceptions == 5
        assert orm.pof == Decimal("0.05")
        assert orm.kupiec_test_statistic == Decimal("0.1")
        assert orm.kupiec_p_value == Decimal("0.75")
        assert orm.kupiec_reject is False
        assert orm.christoffersen_uc_test_statistic == Decimal("0.1")
        assert orm.christoffersen_cc_test_statistic == Decimal("0.6")
        assert orm.christoffersen_reject is False

    def test_map_zero_breaches(self) -> None:
        """Map result with zero breaches."""
        backtest_result = create_backtest_result(100, 0)
        kupiec_result = KupiecTestResult(
            num_observations=100,
            num_breaches=0,
            expected_breach_probability=Decimal("0.05"),
            observed_breach_probability=Decimal("0"),
            lr_statistic=Decimal("5.0"),
            p_value=Decimal("0.025"),
            alpha=Decimal("0.05"),
            reject_null=True,
        )
        christoffersen_result = ChristoffersenTestResult(
            num_observations=100,
            num_breaches=0,
            expected_breach_probability=Decimal("0.05"),
            transition_matrix=TransitionMatrix(n00=99, n01=0, n10=0, n11=0),
            uc_test_statistic=Decimal("5.0"),
            uc_p_value=Decimal("0.025"),
            ind_test_statistic=Decimal("0.0"),
            ind_p_value=Decimal("1.0"),
            cc_test_statistic=Decimal("5.0"),
            cc_p_value=Decimal("0.082"),
            alpha=Decimal("0.05"),
            reject_uc=True,
            reject_ind=False,
            reject_cc=False,
        )

        orm = map_backtest_result_to_orm(
            backtest_result,
            kupiec_result,
            christoffersen_result,
            calculation_run_id=123,
            fund_id=456,
        )

        assert orm.total_observations == 100
        assert orm.num_exceptions == 0
        assert orm.pof == 0  # None converted to 0
        assert orm.kupiec_reject is True

    def test_map_breach_ratio_calculation(self) -> None:
        """Breach ratio (pof) is correctly calculated from breach count."""
        backtest_result = create_backtest_result(200, 10)
        kupiec_result = KupiecTestResult(
            num_observations=200,
            num_breaches=10,
            expected_breach_probability=Decimal("0.05"),
            observed_breach_probability=Decimal("0.05"),
            lr_statistic=Decimal("0.0"),
            p_value=Decimal("1.0"),
            alpha=Decimal("0.05"),
            reject_null=False,
        )
        christoffersen_result = ChristoffersenTestResult(
            num_observations=200,
            num_breaches=10,
            expected_breach_probability=Decimal("0.05"),
            transition_matrix=TransitionMatrix(n00=190, n01=10, n10=0, n11=0),
            uc_test_statistic=Decimal("0.0"),
            uc_p_value=Decimal("1.0"),
            ind_test_statistic=Decimal("0.0"),
            ind_p_value=Decimal("1.0"),
            cc_test_statistic=Decimal("0.0"),
            cc_p_value=Decimal("1.0"),
            alpha=Decimal("0.05"),
            reject_uc=False,
            reject_ind=False,
            reject_cc=False,
        )

        orm = map_backtest_result_to_orm(
            backtest_result,
            kupiec_result,
            christoffersen_result,
            calculation_run_id=123,
            fund_id=456,
        )

        assert orm.pof == Decimal("0.05")  # 10 / 200

    def test_map_kupiec_rejection(self) -> None:
        """Kupiec rejection flag maps correctly."""
        backtest_result = create_backtest_result(100, 20)
        kupiec_result_reject = KupiecTestResult(
            num_observations=100,
            num_breaches=20,
            expected_breach_probability=Decimal("0.05"),
            observed_breach_probability=Decimal("0.20"),
            lr_statistic=Decimal("10.0"),
            p_value=Decimal("0.001"),
            alpha=Decimal("0.05"),
            reject_null=True,
        )

        orm = map_backtest_result_to_orm(
            backtest_result,
            kupiec_result_reject,
            ChristoffersenTestResult(
                num_observations=100,
                num_breaches=20,
                expected_breach_probability=Decimal("0.05"),
                transition_matrix=TransitionMatrix(n00=80, n01=20, n10=0, n11=0),
                uc_test_statistic=Decimal("10.0"),
                uc_p_value=Decimal("0.001"),
                ind_test_statistic=Decimal("0.0"),
                ind_p_value=Decimal("1.0"),
                cc_test_statistic=Decimal("10.0"),
                cc_p_value=Decimal("0.006"),
                alpha=Decimal("0.05"),
                reject_uc=True,
                reject_ind=False,
                reject_cc=True,
            ),
            calculation_run_id=123,
            fund_id=456,
        )

        assert orm.kupiec_reject is True

    def test_map_christoffersen_rejection(self) -> None:
        """Christoffersen rejection flags map correctly."""
        backtest_result = create_backtest_result(100, 5)
        christoffersen_result_reject = ChristoffersenTestResult(
            num_observations=100,
            num_breaches=5,
            expected_breach_probability=Decimal("0.05"),
            transition_matrix=TransitionMatrix(n00=90, n01=5, n10=4, n11=1),
            uc_test_statistic=Decimal("0.0"),
            uc_p_value=Decimal("1.0"),
            ind_test_statistic=Decimal("3.5"),
            ind_p_value=Decimal("0.06"),
            cc_test_statistic=Decimal("3.5"),
            cc_p_value=Decimal("0.17"),
            alpha=Decimal("0.05"),
            reject_uc=False,
            reject_ind=False,
            reject_cc=False,
        )

        orm = map_backtest_result_to_orm(
            backtest_result,
            KupiecTestResult(
                num_observations=100,
                num_breaches=5,
                expected_breach_probability=Decimal("0.05"),
                observed_breach_probability=Decimal("0.05"),
                lr_statistic=Decimal("0.0"),
                p_value=Decimal("1.0"),
                alpha=Decimal("0.05"),
                reject_null=False,
            ),
            christoffersen_result_reject,
            calculation_run_id=123,
            fund_id=456,
        )

        assert orm.christoffersen_reject is False

    def test_map_window_days_fixed_to_one(self) -> None:
        """Window days is always set to 1 (Phase 1 constraint)."""
        backtest_result = create_backtest_result(50, 2)
        kupiec_result = KupiecTestResult(
            num_observations=50,
            num_breaches=2,
            expected_breach_probability=Decimal("0.05"),
            observed_breach_probability=Decimal("0.04"),
            lr_statistic=Decimal("0.05"),
            p_value=Decimal("0.82"),
            alpha=Decimal("0.05"),
            reject_null=False,
        )
        christoffersen_result = ChristoffersenTestResult(
            num_observations=50,
            num_breaches=2,
            expected_breach_probability=Decimal("0.05"),
            transition_matrix=TransitionMatrix(n00=48, n01=2, n10=0, n11=0),
            uc_test_statistic=Decimal("0.05"),
            uc_p_value=Decimal("0.82"),
            ind_test_statistic=Decimal("0.0"),
            ind_p_value=Decimal("1.0"),
            cc_test_statistic=Decimal("0.05"),
            cc_p_value=Decimal("0.97"),
            alpha=Decimal("0.05"),
            reject_uc=False,
            reject_ind=False,
            reject_cc=False,
        )

        orm = map_backtest_result_to_orm(
            backtest_result,
            kupiec_result,
            christoffersen_result,
            calculation_run_id=123,
            fund_id=456,
        )

        assert orm.window_days == 1
