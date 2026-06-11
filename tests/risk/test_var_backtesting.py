"""Tests for VaR backtesting engine.

Tests alignment, regulatory counting, and diagnostic outputs.
Phase 1: counting and alignment only. No statistical tests.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.engines.var_backtesting import VaRBacktestingEngine
from manco_risk.risk.models.backtest_input import (
    BacktestInput,
    RealisedPnLObservation,
    VaRForecastObservation,
)


class TestVaRForecastObservation:
    """Tests for VaRForecastObservation input model."""

    def test_valid_observation(self) -> None:
        """Valid VaR forecast observation."""
        obs = VaRForecastObservation(
            forecast_date=date(2024, 1, 1),
            var_value=Decimal("0.025"),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        assert obs.forecast_date == date(2024, 1, 1)
        assert obs.var_value == Decimal("0.025")
        assert obs.confidence_level == Decimal("0.95")
        assert obs.horizon_days == 1

    def test_var_value_zero(self) -> None:
        """Zero VaR is valid (edge case: no loss forecast)."""
        obs = VaRForecastObservation(
            forecast_date=date(2024, 1, 1),
            var_value=Decimal("0"),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        assert obs.var_value == Decimal("0")

    def test_var_value_negative_rejected(self) -> None:
        """Negative VaR value is rejected."""
        with pytest.raises(ValueError, match="VaR value must be non-negative"):
            VaRForecastObservation(
                forecast_date=date(2024, 1, 1),
                var_value=Decimal("-0.025"),
                confidence_level=Decimal("0.95"),
                horizon_days=1,
            )

    def test_confidence_level_boundary_lower(self) -> None:
        """Confidence level must be strictly > 0."""
        with pytest.raises(ValueError, match="Confidence level must be in \\(0, 1\\)"):
            VaRForecastObservation(
                forecast_date=date(2024, 1, 1),
                var_value=Decimal("0.025"),
                confidence_level=Decimal("0"),
                horizon_days=1,
            )

    def test_confidence_level_boundary_upper(self) -> None:
        """Confidence level must be strictly < 1."""
        with pytest.raises(ValueError, match="Confidence level must be in \\(0, 1\\)"):
            VaRForecastObservation(
                forecast_date=date(2024, 1, 1),
                var_value=Decimal("0.025"),
                confidence_level=Decimal("1"),
                horizon_days=1,
            )

    def test_horizon_days_not_one_rejected(self) -> None:
        """Horizon days must be 1 for Phase 1."""
        with pytest.raises(ValueError, match="Phase 1 supports only horizon_days=1"):
            VaRForecastObservation(
                forecast_date=date(2024, 1, 1),
                var_value=Decimal("0.025"),
                confidence_level=Decimal("0.95"),
                horizon_days=10,
            )

    def test_frozen_model(self) -> None:
        """Model is frozen (immutable)."""
        obs = VaRForecastObservation(
            forecast_date=date(2024, 1, 1),
            var_value=Decimal("0.025"),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            obs.var_value = Decimal("0.030")  # type: ignore


class TestRealisedPnLObservation:
    """Tests for RealisedPnLObservation input model."""

    def test_valid_loss(self) -> None:
        """Valid realised loss (negative P&L)."""
        obs = RealisedPnLObservation(
            pnl_date=date(2024, 1, 1),
            realised_pnl=Decimal("-0.010"),
        )
        assert obs.pnl_date == date(2024, 1, 1)
        assert obs.realised_pnl == Decimal("-0.010")

    def test_valid_gain(self) -> None:
        """Valid realised gain (positive P&L)."""
        obs = RealisedPnLObservation(
            pnl_date=date(2024, 1, 1),
            realised_pnl=Decimal("0.015"),
        )
        assert obs.realised_pnl == Decimal("0.015")

    def test_zero_pnl(self) -> None:
        """Zero P&L is valid."""
        obs = RealisedPnLObservation(
            pnl_date=date(2024, 1, 1),
            realised_pnl=Decimal("0"),
        )
        assert obs.realised_pnl == Decimal("0")

    def test_frozen_model(self) -> None:
        """Model is frozen (immutable)."""
        obs = RealisedPnLObservation(
            pnl_date=date(2024, 1, 1),
            realised_pnl=Decimal("-0.010"),
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            obs.realised_pnl = Decimal("0.005")  # type: ignore


class TestBacktestInputValidation:
    """Tests for BacktestInput validation."""

    def test_valid_input(self) -> None:
        """Valid input with matching VaR and P&L."""
        var_forecasts = [
            VaRForecastObservation(
                forecast_date=date(2024, 1, 1),
                var_value=Decimal("0.025"),
                confidence_level=Decimal("0.95"),
                horizon_days=1,
            ),
        ]
        realised_pnls = [
            RealisedPnLObservation(
                pnl_date=date(2024, 1, 1),
                realised_pnl=Decimal("-0.010"),
            ),
        ]
        input = BacktestInput(
            var_forecasts=var_forecasts,
            realised_pnls=realised_pnls,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        assert len(input.var_forecasts) == 1
        assert len(input.realised_pnls) == 1

    def test_empty_var_forecasts_rejected(self) -> None:
        """Empty VaR forecast list rejected."""
        with pytest.raises(ValueError, match="At least one VaR forecast required"):
            BacktestInput(
                var_forecasts=[],
                realised_pnls=[
                    RealisedPnLObservation(
                        pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.010")
                    ),
                ],
                confidence_level=Decimal("0.95"),
                horizon_days=1,
            )

    def test_empty_realised_pnls_rejected(self) -> None:
        """Empty realised P&L list rejected."""
        with pytest.raises(ValueError, match="At least one realised P&L observation required"):
            BacktestInput(
                var_forecasts=[
                    VaRForecastObservation(
                        forecast_date=date(2024, 1, 1),
                        var_value=Decimal("0.025"),
                        confidence_level=Decimal("0.95"),
                        horizon_days=1,
                    ),
                ],
                realised_pnls=[],
                confidence_level=Decimal("0.95"),
                horizon_days=1,
            )

    def test_duplicate_var_forecast_dates_rejected(self) -> None:
        """Duplicate forecast dates rejected."""
        with pytest.raises(ValueError, match="Duplicate forecast dates detected"):
            BacktestInput(
                var_forecasts=[
                    VaRForecastObservation(
                        forecast_date=date(2024, 1, 1),
                        var_value=Decimal("0.025"),
                        confidence_level=Decimal("0.95"),
                        horizon_days=1,
                    ),
                    VaRForecastObservation(
                        forecast_date=date(2024, 1, 1),
                        var_value=Decimal("0.030"),
                        confidence_level=Decimal("0.95"),
                        horizon_days=1,
                    ),
                ],
                realised_pnls=[
                    RealisedPnLObservation(
                        pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.010")
                    ),
                ],
                confidence_level=Decimal("0.95"),
                horizon_days=1,
            )

    def test_duplicate_pnl_dates_rejected(self) -> None:
        """Duplicate realised P&L dates rejected."""
        with pytest.raises(ValueError, match="Duplicate realised P&L dates detected"):
            BacktestInput(
                var_forecasts=[
                    VaRForecastObservation(
                        forecast_date=date(2024, 1, 1),
                        var_value=Decimal("0.025"),
                        confidence_level=Decimal("0.95"),
                        horizon_days=1,
                    ),
                ],
                realised_pnls=[
                    RealisedPnLObservation(
                        pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.010")
                    ),
                    RealisedPnLObservation(
                        pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.015")
                    ),
                ],
                confidence_level=Decimal("0.95"),
                horizon_days=1,
            )

    def test_inconsistent_var_confidence_level_rejected(self) -> None:
        """VaR forecast confidence level must match input."""
        with pytest.raises(ValueError, match="does not match input confidence level"):
            BacktestInput(
                var_forecasts=[
                    VaRForecastObservation(
                        forecast_date=date(2024, 1, 1),
                        var_value=Decimal("0.025"),
                        confidence_level=Decimal("0.99"),  # Mismatch
                        horizon_days=1,
                    ),
                ],
                realised_pnls=[
                    RealisedPnLObservation(
                        pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.010")
                    ),
                ],
                confidence_level=Decimal("0.95"),  # Different
                horizon_days=1,
            )


class TestBacktestingCounting:
    """Tests for VaR backtesting alignment and counting."""

    def test_perfect_alignment(self) -> None:
        """Perfect alignment: all dates match."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 2),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.010")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 2), realised_pnl=Decimal("0.005")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert result.num_var_forecasts == 2
        assert result.num_pnl_observations == 2
        assert result.num_valid_aligned == 2
        assert result.missing_var_dates == []
        assert result.missing_pnl_dates == []
        assert len(result.aligned_observations) == 2

    def test_missing_var_date(self) -> None:
        """P&L exists but VaR is missing for one date."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.010")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 2), realised_pnl=Decimal("0.005")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert result.num_var_forecasts == 1
        assert result.num_pnl_observations == 2
        assert result.num_valid_aligned == 1
        assert result.missing_var_dates == [date(2024, 1, 2)]
        assert result.missing_pnl_dates == []

    def test_missing_pnl_date(self) -> None:
        """VaR exists but P&L is missing for one date."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 2),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.010")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert result.num_var_forecasts == 2
        assert result.num_pnl_observations == 1
        assert result.num_valid_aligned == 1
        assert result.missing_var_dates == []
        assert result.missing_pnl_dates == [date(2024, 1, 2)]

    def test_no_common_dates(self) -> None:
        """No dates in common: alignment produces zero valid observations."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 2), realised_pnl=Decimal("-0.010")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert result.num_var_forecasts == 1
        assert result.num_pnl_observations == 1
        assert result.num_valid_aligned == 0
        assert result.num_breaches == 0
        assert result.num_non_breaches == 0
        assert result.breach_ratio is None
        assert result.backtest_start_date is None
        assert result.backtest_end_date is None


class TestBreachDetection:
    """Tests for breach detection logic."""

    def test_no_breaches(self) -> None:
        """All P&L observations exceed negative VaR (no breaches)."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 2),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.010")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 2), realised_pnl=Decimal("0.005")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert result.num_breaches == 0
        assert result.num_non_breaches == 2
        assert result.breach_dates == []

    def test_one_breach(self) -> None:
        """One observation is a breach."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.030")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert result.num_breaches == 1
        assert result.num_non_breaches == 0
        assert result.breach_dates == [date(2024, 1, 1)]

    def test_multiple_breaches(self) -> None:
        """Multiple observations are breaches."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 2),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 3),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.030")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 2), realised_pnl=Decimal("-0.040")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 3), realised_pnl=Decimal("-0.010")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert result.num_breaches == 2
        assert result.num_non_breaches == 1
        assert result.breach_dates == [date(2024, 1, 1), date(2024, 1, 2)]

    def test_exact_threshold_is_not_breach(self) -> None:
        """Exact threshold hit (realised_pnl == -var_value) is NOT a breach."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.025")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert result.num_breaches == 0
        assert result.num_non_breaches == 1
        assert result.breach_dates == []

    def test_positive_pnl_is_not_breach(self) -> None:
        """Positive realised P&L is never a breach."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("0.050")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert result.num_breaches == 0
        assert result.num_non_breaches == 1


class TestRegulatoryCountingFormulas:
    """Tests for regulatory counting formulas."""

    def test_expected_breach_count_formula(self) -> None:
        """Expected breach count = num_valid_aligned * (1 - confidence_level)."""
        from datetime import timedelta

        engine = VaRBacktestingEngine()
        start_date = date(2024, 1, 1)
        # Create 100 observations spanning multiple months
        var_forecasts = [
            VaRForecastObservation(
                forecast_date=start_date + timedelta(days=i),
                var_value=Decimal("0.025"),
                confidence_level=Decimal("0.95"),
                horizon_days=1,
            )
            for i in range(100)
        ]
        realised_pnls = [
            RealisedPnLObservation(
                pnl_date=start_date + timedelta(days=i),
                realised_pnl=Decimal("0.000"),
            )
            for i in range(100)
        ]
        input = BacktestInput(
            var_forecasts=var_forecasts,
            realised_pnls=realised_pnls,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        # Expected breaches at 95% confidence = 100 * (1 - 0.95) = 5
        assert result.expected_breach_count == Decimal("5")

    def test_breach_ratio_formula(self) -> None:
        """Breach ratio = num_breaches / num_valid_aligned."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 2),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 3),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 4),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.030")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 2), realised_pnl=Decimal("-0.010")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 3), realised_pnl=Decimal("-0.040")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 4), realised_pnl=Decimal("0.005")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        # 2 breaches out of 4 valid aligned = 2/4 = 0.5
        assert result.breach_ratio == Decimal("0.5")

    def test_expected_breach_probability(self) -> None:
        """Expected breach probability = 1 - confidence_level."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("0.000")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        # 1 - 0.95 = 0.05
        assert result.expected_breach_probability == Decimal("0.05")

    def test_breach_count_plus_non_breach_equals_aligned(self) -> None:
        """num_breaches + num_non_breaches == num_valid_aligned."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, i),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                )
                for i in range(1, 11)
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, i), realised_pnl=Decimal("-0.030"))
                if i % 3 == 0
                else RealisedPnLObservation(
                    pnl_date=date(2024, 1, i), realised_pnl=Decimal("0.000")
                )
                for i in range(1, 11)
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert result.num_breaches + result.num_non_breaches == result.num_valid_aligned


class TestBacktestDates:
    """Tests for backtest date range and breach dates."""

    def test_start_end_dates_from_aligned_observations(self) -> None:
        """Start and end dates come from aligned observations only."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 5),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.010")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 5), realised_pnl=Decimal("0.005")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert result.backtest_start_date == date(2024, 1, 1)
        assert result.backtest_end_date == date(2024, 1, 5)

    def test_breach_dates_captured(self) -> None:
        """Breach dates are captured correctly."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 2),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 3),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.030")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 2), realised_pnl=Decimal("-0.010")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 3), realised_pnl=Decimal("-0.040")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert set(result.breach_dates) == {date(2024, 1, 1), date(2024, 1, 3)}
        assert len(result.breach_dates) == 2


class TestBacktestObservations:
    """Tests for aligned observation details."""

    def test_aligned_observations_contain_correct_fields(self) -> None:
        """Aligned observations have correct observation_date, var_value, realised_pnl, is_breach."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.030")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert len(result.aligned_observations) == 1
        obs = result.aligned_observations[0]
        assert obs.observation_date == date(2024, 1, 1)
        assert obs.var_value == Decimal("0.025")
        assert obs.realised_pnl == Decimal("-0.030")
        assert obs.is_breach is True

    def test_aligned_observations_sorted_by_date(self) -> None:
        """Aligned observations are sorted by date."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 3),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 2),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 3), realised_pnl=Decimal("0.005")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("-0.010")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 2), realised_pnl=Decimal("0.000")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        dates = [obs.observation_date for obs in result.aligned_observations]
        assert dates == sorted(dates)


class TestResultValidation:
    """Tests for BacktestResult model validation."""

    def test_result_is_frozen(self) -> None:
        """BacktestResult is frozen (immutable)."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("0.000")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        with pytest.raises(Exception):  # FrozenInstanceError
            result.num_breaches = 999  # type: ignore

    def test_result_aligned_observations_count_matches(self) -> None:
        """Result.aligned_observations.count must match num_valid_aligned."""
        engine = VaRBacktestingEngine()
        input = BacktestInput(
            var_forecasts=[
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 1),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
                VaRForecastObservation(
                    forecast_date=date(2024, 1, 2),
                    var_value=Decimal("0.025"),
                    confidence_level=Decimal("0.95"),
                    horizon_days=1,
                ),
            ],
            realised_pnls=[
                RealisedPnLObservation(pnl_date=date(2024, 1, 1), realised_pnl=Decimal("0.000")),
                RealisedPnLObservation(pnl_date=date(2024, 1, 2), realised_pnl=Decimal("0.000")),
            ],
            confidence_level=Decimal("0.95"),
            horizon_days=1,
        )
        result = engine.calculate(input)
        assert len(result.aligned_observations) == result.num_valid_aligned
