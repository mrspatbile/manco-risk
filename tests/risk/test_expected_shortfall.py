"""Tests for Historical Expected Shortfall engine.

Tests input validation, output validation, and calculation logic.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.engines.expected_shortfall import HistoricalExpectedShortfall
from manco_risk.risk.engines.var import HistoricalVaR
from manco_risk.risk.models.expected_shortfall_input import HistoricalExpectedShortfallInput
from manco_risk.risk.models.expected_shortfall_result import HistoricalExpectedShortfallResult
from manco_risk.risk.models.scenario_pnl import ScenarioPnL
from manco_risk.risk.models.var_input import HistoricalVaRInput
from manco_risk.risk.models.var_result import HistoricalVaRResult


class TestHistoricalExpectedShortfallInput:
    """Test input validation for HistoricalExpectedShortfall."""

    def test_valid_input(self) -> None:
        """Valid ES input construction."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1000")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("500")),
        ]

        var_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("1000.00"),
            var_pct_nav=Decimal("0.01"),
            num_scenarios=2,
            quantile_index=0,
        )

        input = HistoricalExpectedShortfallInput(
            portfolio=portfolio,
            scenario_pnls=pnls,
            var_result=var_result,
        )

        assert input.portfolio.fund_id == 1
        assert len(input.scenario_pnls) == 2
        assert input.var_result.confidence_level == Decimal("0.95")

    def test_minimum_two_observations_required(self) -> None:
        """Scenario P&Ls must contain at least 2 observations."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[],
        )

        pnls = [ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1000"))]

        var_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("1000.00"),
            var_pct_nav=Decimal("0.01"),
            num_scenarios=1,
            quantile_index=0,
        )

        with pytest.raises(ValueError, match="At least 2 scenario P&Ls required"):
            HistoricalExpectedShortfallInput(
                portfolio=portfolio,
                scenario_pnls=pnls,
                var_result=var_result,
            )

    def test_var_result_num_scenarios_must_match(self) -> None:
        """VaR result num_scenarios must match scenario count."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1000")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("500")),
        ]

        var_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("1000.00"),
            var_pct_nav=Decimal("0.01"),
            num_scenarios=100,  # Mismatch: 100 vs 2
            quantile_index=0,
        )

        with pytest.raises(ValueError, match="does not match"):
            HistoricalExpectedShortfallInput(
                portfolio=portfolio,
                scenario_pnls=pnls,
                var_result=var_result,
            )

    def test_var_result_fund_id_must_match(self) -> None:
        """VaR result fund_id must match portfolio."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1000")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("500")),
        ]

        var_result = HistoricalVaRResult(
            fund_id=2,  # Mismatch
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("1000.00"),
            var_pct_nav=Decimal("0.01"),
            num_scenarios=2,
            quantile_index=0,
        )

        with pytest.raises(ValueError, match="fund_id"):
            HistoricalExpectedShortfallInput(
                portfolio=portfolio,
                scenario_pnls=pnls,
                var_result=var_result,
            )

    def test_var_result_valuation_date_must_match(self) -> None:
        """VaR result valuation_date must match portfolio."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1000")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("500")),
        ]

        var_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 2),  # Mismatch
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("1000.00"),
            var_pct_nav=Decimal("0.01"),
            num_scenarios=2,
            quantile_index=0,
        )

        with pytest.raises(ValueError, match="valuation_date"):
            HistoricalExpectedShortfallInput(
                portfolio=portfolio,
                scenario_pnls=pnls,
                var_result=var_result,
            )


class TestHistoricalExpectedShortfallResult:
    """Test output validation for HistoricalExpectedShortfall."""

    def test_valid_result(self) -> None:
        """Valid ES result construction."""
        result = HistoricalExpectedShortfallResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            es_value=Decimal("1500.00"),
            es_pct_nav=Decimal("0.015"),
            num_tail_observations=5,
            num_observations=100,
            quantile_index=4,
            linked_var_value=Decimal("1000.00"),
            linked_var_pct_nav=Decimal("0.01"),
        )

        assert result.es_value == Decimal("1500.00")
        assert result.num_tail_observations == 5

    def test_es_value_must_be_non_negative(self) -> None:
        """ES value must be non-negative."""
        with pytest.raises(ValueError, match="non-negative"):
            HistoricalExpectedShortfallResult(
                fund_id=1,
                valuation_date=date(2024, 1, 1),
                confidence_level=Decimal("0.95"),
                horizon_days=1,
                es_value=Decimal("-1500.00"),
                es_pct_nav=Decimal("0.015"),
                num_tail_observations=5,
                num_observations=100,
                quantile_index=4,
                linked_var_value=Decimal("1000.00"),
                linked_var_pct_nav=Decimal("0.01"),
            )

    def test_es_pct_nav_must_be_non_negative(self) -> None:
        """ES % NAV must be non-negative."""
        with pytest.raises(ValueError, match="non-negative"):
            HistoricalExpectedShortfallResult(
                fund_id=1,
                valuation_date=date(2024, 1, 1),
                confidence_level=Decimal("0.95"),
                horizon_days=1,
                es_value=Decimal("1500.00"),
                es_pct_nav=Decimal("-0.015"),
                num_tail_observations=5,
                num_observations=100,
                quantile_index=4,
                linked_var_value=Decimal("1000.00"),
                linked_var_pct_nav=Decimal("0.01"),
            )

    def test_horizon_days_must_be_1(self) -> None:
        """Horizon days must be 1 for Phase 1."""
        with pytest.raises(ValueError, match="horizon_days=1"):
            HistoricalExpectedShortfallResult(
                fund_id=1,
                valuation_date=date(2024, 1, 1),
                confidence_level=Decimal("0.95"),
                horizon_days=5,
                es_value=Decimal("1500.00"),
                es_pct_nav=Decimal("0.015"),
                num_tail_observations=5,
                num_observations=100,
                quantile_index=4,
                linked_var_value=Decimal("1000.00"),
                linked_var_pct_nav=Decimal("0.01"),
            )

    def test_num_tail_observations_must_be_positive(self) -> None:
        """Number of tail observations must be positive."""
        with pytest.raises(ValueError, match="positive"):
            HistoricalExpectedShortfallResult(
                fund_id=1,
                valuation_date=date(2024, 1, 1),
                confidence_level=Decimal("0.95"),
                horizon_days=1,
                es_value=Decimal("1500.00"),
                es_pct_nav=Decimal("0.015"),
                num_tail_observations=0,
                num_observations=100,
                quantile_index=4,
                linked_var_value=Decimal("1000.00"),
                linked_var_pct_nav=Decimal("0.01"),
            )


class TestHistoricalExpectedShortfall:
    """Test HistoricalExpectedShortfall calculation engine."""

    def test_deterministic_known_pnls(self) -> None:
        """Deterministic ES calculation with known P&Ls."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1000")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("-800")),
            ScenarioPnL(scenario_date=date(2024, 1, 3), total_pnl=Decimal("-600")),
            ScenarioPnL(scenario_date=date(2024, 1, 4), total_pnl=Decimal("-400")),
            ScenarioPnL(scenario_date=date(2024, 1, 5), total_pnl=Decimal("-200")),
            ScenarioPnL(scenario_date=date(2024, 1, 6), total_pnl=Decimal("0")),
        ]

        var_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("800.00"),
            var_pct_nav=Decimal("0.008"),
            num_scenarios=6,
            quantile_index=1,  # 95% VaR at index 1
        )

        input = HistoricalExpectedShortfallInput(
            portfolio=portfolio,
            scenario_pnls=pnls,
            var_result=var_result,
        )

        engine = HistoricalExpectedShortfall()
        result = engine.calculate(input)

        # Tail: indices 0 and 1 → [-1000, -800] → mean = -900
        # ES as magnitude: 900
        assert result.es_value == Decimal("900.00")
        assert result.es_pct_nav == Decimal("0.009")
        assert result.num_tail_observations == 2

    def test_tail_includes_var_observation(self) -> None:
        """Tail includes the VaR observation (quantile_index + 1 elements)."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, i), total_pnl=Decimal(str(-100 * (6 - i))))
            for i in range(1, 7)
        ]

        var_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("500.00"),
            var_pct_nav=Decimal("0.005"),
            num_scenarios=6,
            quantile_index=2,  # Third element (0-indexed)
        )

        input = HistoricalExpectedShortfallInput(
            portfolio=portfolio,
            scenario_pnls=pnls,
            var_result=var_result,
        )

        engine = HistoricalExpectedShortfall()
        result = engine.calculate(input)

        # Tail: quantile_index + 1 = 3 elements
        assert result.num_tail_observations == 3

    def test_result_copies_confidence_and_horizon_from_var(self) -> None:
        """Result copies confidence level and horizon from VaR result."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1000")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("500")),
        ]

        var_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.99"),
            horizon_days=1,
            var_value=Decimal("1000.00"),
            var_pct_nav=Decimal("0.01"),
            num_scenarios=2,
            quantile_index=0,
        )

        input = HistoricalExpectedShortfallInput(
            portfolio=portfolio,
            scenario_pnls=pnls,
            var_result=var_result,
        )

        engine = HistoricalExpectedShortfall()
        result = engine.calculate(input)

        assert result.confidence_level == Decimal("0.99")
        assert result.horizon_days == 1

    def test_result_links_var_values(self) -> None:
        """Result includes linked_var_value and linked_var_pct_nav."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1000")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("500")),
        ]

        var_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("1000.00"),
            var_pct_nav=Decimal("0.01"),
            num_scenarios=2,
            quantile_index=0,
        )

        input = HistoricalExpectedShortfallInput(
            portfolio=portfolio,
            scenario_pnls=pnls,
            var_result=var_result,
        )

        engine = HistoricalExpectedShortfall()
        result = engine.calculate(input)

        assert result.linked_var_value == Decimal("1000.00")
        assert result.linked_var_pct_nav == Decimal("0.01")

    def test_es_greater_than_or_equal_to_var_invariant(self) -> None:
        """ES >= VaR invariant: conditional mean >= quantile (general invariant).

        Expected Shortfall is the conditional mean of losses at or beyond the
        VaR threshold, so ES must always be >= VaR.

        This invariant applies to all ES calculation methods:
        - Historical ES >= Historical VaR (this test)
        - Parametric normal ES >= Parametric normal VaR (future)
        - Parametric Student-t ES >= Parametric Student-t VaR (future, if implemented)
        - Variance-covariance ES >= Variance-covariance VaR (future, if implemented)

        Each new ES method must include an analogous consistency test against
        its matching VaR method to ensure this invariant holds.
        """
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[
                EnrichedPosition(
                    fund_id=1,
                    position_snapshot_id=1,
                    position_id=1,
                    isin="US0378331005",
                    valuation_date="2024-01-01",
                    quantity=Decimal("100"),
                    market_value=Decimal("100000.00"),
                    position_currency="EUR",
                    asset_class="EQUITY",
                    instrument_currency="EUR",
                    market_value_base_ccy=Decimal("100000.00"),
                    fund_base_currency="EUR",
                    weight=Decimal("1.0"),
                )
            ],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1 + i), total_pnl=Decimal(str(-100 * (20 - i))))
            for i in range(20)
        ]

        # Calculate historical VaR
        var_input = HistoricalVaRInput(
            portfolio=portfolio,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            scenario_pnls=pnls,
        )
        var_engine = HistoricalVaR()
        var_result = var_engine.calculate(var_input)

        # Calculate historical ES using same distribution
        es_input = HistoricalExpectedShortfallInput(
            portfolio=portfolio,
            scenario_pnls=pnls,
            var_result=var_result,
        )
        es_engine = HistoricalExpectedShortfall()
        es_result = es_engine.calculate(es_input)

        # Verify ES >= VaR invariant
        assert es_result.es_value >= var_result.var_value
        assert es_result.es_pct_nav >= var_result.var_pct_nav

    def test_all_positive_pnls_produce_zero_es(self) -> None:
        """All-positive P&Ls produce ES of zero (no tail losses)."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("100")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("200")),
            ScenarioPnL(scenario_date=date(2024, 1, 3), total_pnl=Decimal("300")),
        ]

        var_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("0"),
            var_pct_nav=Decimal("0"),
            num_scenarios=3,
            quantile_index=0,
        )

        input = HistoricalExpectedShortfallInput(
            portfolio=portfolio,
            scenario_pnls=pnls,
            var_result=var_result,
        )

        engine = HistoricalExpectedShortfall()
        result = engine.calculate(input)

        assert result.es_value == Decimal("0")
        assert result.es_pct_nav == Decimal("0")

    def test_decimal_precision_preserved(self) -> None:
        """Decimal precision is preserved through calculation."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("123456.789"),
            positions=[],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-1234.56789")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("-2345.6789")),
        ]

        var_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("1234.56789"),
            var_pct_nav=Decimal("0.010000000"),
            num_scenarios=2,
            quantile_index=0,
        )

        input = HistoricalExpectedShortfallInput(
            portfolio=portfolio,
            scenario_pnls=pnls,
            var_result=var_result,
        )

        engine = HistoricalExpectedShortfall()
        result = engine.calculate(input)

        # Mean of tail: (-1234.56789 - 2345.6789) / 2 = -1790.123395
        # ES magnitude: 1790.123395
        assert result.es_value > Decimal("0")
        assert isinstance(result.es_pct_nav, Decimal)

    def test_single_breach_edge_case(self) -> None:
        """Single breach (quantile_index=0) produces tail of size 1."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, 1), total_pnl=Decimal("-500")),
            ScenarioPnL(scenario_date=date(2024, 1, 2), total_pnl=Decimal("100")),
        ]

        var_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("500.00"),
            var_pct_nav=Decimal("0.005"),
            num_scenarios=2,
            quantile_index=0,
        )

        input = HistoricalExpectedShortfallInput(
            portfolio=portfolio,
            scenario_pnls=pnls,
            var_result=var_result,
        )

        engine = HistoricalExpectedShortfall()
        result = engine.calculate(input)

        # Tail: indices [0:1] = [-500] → mean = -500 → ES = 500
        assert result.num_tail_observations == 1
        assert result.es_value == Decimal("500.00")

    def test_all_pnls_in_tail_edge_case(self) -> None:
        """All P&Ls in tail (high confidence level) produces large tail."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[],
        )

        pnls = [
            ScenarioPnL(scenario_date=date(2024, 1, i), total_pnl=Decimal(str(-100 * i)))
            for i in range(1, 6)
        ]

        var_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.99"),
            horizon_days=1,
            var_value=Decimal("500.00"),
            var_pct_nav=Decimal("0.005"),
            num_scenarios=5,
            quantile_index=4,  # All observations in tail
        )

        input = HistoricalExpectedShortfallInput(
            portfolio=portfolio,
            scenario_pnls=pnls,
            var_result=var_result,
        )

        engine = HistoricalExpectedShortfall()
        result = engine.calculate(input)

        # Tail includes all 5 observations
        assert result.num_tail_observations == 5
        assert result.num_observations == 5
