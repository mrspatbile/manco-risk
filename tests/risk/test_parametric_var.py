"""Tests for parametric normal VaR engine."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.engines.parametric_var import ParametricNormalVaR
from manco_risk.risk.models.parametric_var_input import ParametricNormalVaRInput
from manco_risk.risk.models.parametric_var_result import ParametricNormalVaRResult
from manco_risk.risk.models.scenario_pnl import ScenarioPnL


class TestParametricNormalVaRInput:
    """Test ParametricNormalVaRInput model validation."""

    def test_valid_input(self) -> None:
        """Create valid parametric VaR input."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("1000"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-100")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("200")),
        ]

        input = ParametricNormalVaRInput(
            portfolio=portfolio,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            scenario_pnls=pnls,
        )

        assert input.confidence_level == Decimal("0.95")
        assert input.horizon_days == 1
        assert len(input.scenario_pnls) == 2

    def test_confidence_level_must_be_between_0_and_1(self) -> None:
        """Confidence level must be strictly between 0 and 1."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("1000"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-100")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("200")),
        ]

        # Test 0.0 (invalid)
        with pytest.raises(ValidationError):
            ParametricNormalVaRInput(
                portfolio=portfolio,
                confidence_level=Decimal("0.0"),
                horizon_days=1,
                scenario_pnls=pnls,
            )

        # Test 1.0 (invalid)
        with pytest.raises(ValidationError):
            ParametricNormalVaRInput(
                portfolio=portfolio,
                confidence_level=Decimal("1.0"),
                horizon_days=1,
                scenario_pnls=pnls,
            )

        # Test > 1.0 (invalid)
        with pytest.raises(ValidationError):
            ParametricNormalVaRInput(
                portfolio=portfolio,
                confidence_level=Decimal("1.5"),
                horizon_days=1,
                scenario_pnls=pnls,
            )

    def test_horizon_days_must_be_1(self) -> None:
        """Horizon days must be 1 for Phase 1."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("1000"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-100")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("200")),
        ]

        with pytest.raises(ValidationError):
            ParametricNormalVaRInput(
                portfolio=portfolio,
                confidence_level=Decimal("0.95"),
                horizon_days=10,
                scenario_pnls=pnls,
            )

    def test_minimum_2_observations_required(self) -> None:
        """At least 2 scenario P&Ls required for std dev calculation."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("1000"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        # Only 1 observation
        pnls = [ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-100"))]

        with pytest.raises(ValidationError):
            ParametricNormalVaRInput(
                portfolio=portfolio,
                confidence_level=Decimal("0.95"),
                horizon_days=1,
                scenario_pnls=pnls,
            )


class TestParametricNormalVaRResult:
    """Test ParametricNormalVaRResult model validation."""

    def test_valid_result(self) -> None:
        """Create valid parametric VaR result."""
        result = ParametricNormalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("2500.00"),
            var_pct_nav=Decimal("0.025"),
            mean_return=Decimal("0.001"),
            std_dev=Decimal("0.015"),
            num_observations=250,
            z_score=Decimal("-1.645"),
        )

        assert result.fund_id == 1
        assert result.var_value >= Decimal("0")
        assert result.var_pct_nav >= Decimal("0")

    def test_var_value_must_be_non_negative(self) -> None:
        """VaR value must be non-negative."""
        with pytest.raises(ValidationError):
            ParametricNormalVaRResult(
                fund_id=1,
                valuation_date=date(2024, 1, 1),
                confidence_level=Decimal("0.95"),
                horizon_days=1,
                var_value=Decimal("-100.00"),
                var_pct_nav=Decimal("0.025"),
                mean_return=Decimal("0.001"),
                std_dev=Decimal("0.015"),
                num_observations=250,
                z_score=Decimal("-1.645"),
            )

    def test_std_dev_must_be_non_negative(self) -> None:
        """Standard deviation must be non-negative."""
        with pytest.raises(ValidationError):
            ParametricNormalVaRResult(
                fund_id=1,
                valuation_date=date(2024, 1, 1),
                confidence_level=Decimal("0.95"),
                horizon_days=1,
                var_value=Decimal("2500.00"),
                var_pct_nav=Decimal("0.025"),
                mean_return=Decimal("0.001"),
                std_dev=Decimal("-0.015"),
                num_observations=250,
                z_score=Decimal("-1.645"),
            )

    def test_num_observations_must_be_at_least_2(self) -> None:
        """Number of observations must be at least 2."""
        with pytest.raises(ValidationError):
            ParametricNormalVaRResult(
                fund_id=1,
                valuation_date=date(2024, 1, 1),
                confidence_level=Decimal("0.95"),
                horizon_days=1,
                var_value=Decimal("2500.00"),
                var_pct_nav=Decimal("0.025"),
                mean_return=Decimal("0.001"),
                std_dev=Decimal("0.015"),
                num_observations=1,
                z_score=Decimal("-1.645"),
            )


class TestParametricNormalVaR:
    """Test ParametricNormalVaR engine calculation."""

    def test_deterministic_known_returns(self) -> None:
        """Calculate parametric normal VaR with known P&Ls."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("1000"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        # Symmetric returns: [-0.02, -0.01, 0.00, 0.01, 0.02]
        # mean = 0, std_dev ≈ 0.01581 (sample std dev with n-1)
        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-2000")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("-1000")),
            ScenarioPnL(scenario_date=date(2024, 1, 3), total_pnl=Decimal("0")),
            ScenarioPnL(scenario_date=date(2024, 1, 4), total_pnl=Decimal("1000")),
            ScenarioPnL(scenario_date=date(2024, 1, 5), total_pnl=Decimal("2000")),
        ]

        input = ParametricNormalVaRInput(
            portfolio=portfolio,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            scenario_pnls=pnls,
        )

        engine = ParametricNormalVaR()
        result = engine.calculate(input)

        # Verify result structure
        assert result.fund_id == 1
        assert result.valuation_date == date(2024, 1, 1)
        assert result.confidence_level == Decimal("0.95")
        assert result.horizon_days == 1
        assert result.num_observations == 5

        # Verify mean is close to 0
        assert abs(result.mean_return) < Decimal("0.001")

        # Verify std_dev is positive
        assert result.std_dev > Decimal("0")

        # Verify z-score is negative (left tail for 95% VaR)
        assert result.z_score < Decimal("0")

        # Verify VaR is positive (loss magnitude)
        assert result.var_value >= Decimal("0")
        assert result.var_pct_nav >= Decimal("0")

    def test_mean_return_calculation(self) -> None:
        """Verify mean return calculation."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("1000"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        # Returns: 1%, 2%, 3% (mean = 2%)
        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("1000")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("2000")),
            ScenarioPnL(scenario_date=date(2024, 1, 3), total_pnl=Decimal("3000")),
        ]

        input = ParametricNormalVaRInput(
            portfolio=portfolio,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            scenario_pnls=pnls,
        )

        engine = ParametricNormalVaR()
        result = engine.calculate(input)

        # Expected mean return: (0.01 + 0.02 + 0.03) / 3 = 0.02
        assert abs(result.mean_return - Decimal("0.02")) < Decimal("0.0001")

    def test_std_dev_calculation_uses_n_minus_1(self) -> None:
        """Standard deviation uses sample formula (n - 1)."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("1000"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        # Returns: 0%, 0%, 1% (mean = 1/3%, std_dev = sqrt(2/9 / 2) ≈ 0.2357)
        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("0")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("0")),
            ScenarioPnL(scenario_date=date(2024, 1, 3), total_pnl=Decimal("1000")),
        ]

        input = ParametricNormalVaRInput(
            portfolio=portfolio,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            scenario_pnls=pnls,
        )

        engine = ParametricNormalVaR()
        result = engine.calculate(input)

        # Verify std dev is positive (uses n-1)
        assert result.std_dev > Decimal("0")
        assert result.num_observations == 3

    def test_z_score_is_negative_for_left_tail(self) -> None:
        """Z-score is negative for left-tail quantile (95% VaR)."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("1000"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-100")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("200")),
        ]

        input = ParametricNormalVaRInput(
            portfolio=portfolio,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            scenario_pnls=pnls,
        )

        engine = ParametricNormalVaR()
        result = engine.calculate(input)

        # Z-score for 95% VaR should be approximately -1.645
        assert result.z_score < Decimal("0")
        assert result.z_score > Decimal("-2.0")
        assert result.z_score < Decimal("-1.5")

    def test_var_is_positive_loss_magnitude(self) -> None:
        """VaR is reported as positive loss magnitude."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("1000"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, i), total_pnl=Decimal(str(-1000 + i * 100)))
            for i in range(1, 11)
        ]

        input = ParametricNormalVaRInput(
            portfolio=portfolio,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            scenario_pnls=pnls,
        )

        engine = ParametricNormalVaR()
        result = engine.calculate(input)

        # Both should be non-negative
        assert result.var_value >= Decimal("0")
        assert result.var_pct_nav >= Decimal("0")

    def test_higher_confidence_gives_higher_or_equal_var(self) -> None:
        """Higher confidence level produces higher or equal VaR."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("1000"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, i), total_pnl=Decimal(str(-1000 + i * 100)))
            for i in range(1, 21)
        ]

        # Calculate VaR at 90% confidence
        input_90 = ParametricNormalVaRInput(
            portfolio=portfolio,
            confidence_level=Decimal("0.90"),
            horizon_days=1,
            scenario_pnls=pnls,
        )

        # Calculate VaR at 95% confidence
        input_95 = ParametricNormalVaRInput(
            portfolio=portfolio,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            scenario_pnls=pnls,
        )

        # Calculate VaR at 99% confidence
        input_99 = ParametricNormalVaRInput(
            portfolio=portfolio,
            confidence_level=Decimal("0.99"),
            horizon_days=1,
            scenario_pnls=pnls,
        )

        engine = ParametricNormalVaR()
        result_90 = engine.calculate(input_90)
        result_95 = engine.calculate(input_95)
        result_99 = engine.calculate(input_99)

        # Higher confidence should give higher or equal VaR (more conservative)
        assert result_99.var_pct_nav >= result_95.var_pct_nav
        assert result_95.var_pct_nav >= result_90.var_pct_nav
