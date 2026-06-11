"""Tests for equity stress testing engine.

Comprehensive test suite covering:
- Pure model validation
- Engine calculation correctness
- Edge cases and error handling
- Sign conventions and decimal precision
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.engines.equity_stress import EquityStressEngine
from manco_risk.risk.exceptions import UnsupportedAssetClassError
from manco_risk.risk.models.stress_portfolio_result import StressPortfolioResult
from manco_risk.risk.models.stress_position_result import StressPositionResult
from manco_risk.risk.models.stress_scenario import StressScenario
from manco_risk.risk.models.stress_test_input import StressTestInput


@pytest.fixture
def single_equity_position() -> RiskReadyPortfolio:
    """Single equity position, 100 base currency."""
    position = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=101,
        isin="US0378331005",
        valuation_date="2026-06-10",
        quantity=Decimal("10"),
        market_value=Decimal("1000"),
        position_currency="USD",
        asset_class="EQUITY",
        instrument_currency="USD",
        market_value_base_ccy=Decimal("100"),
        fund_base_currency="USD",
        weight=Decimal("1.0"),
    )
    return RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2026-06-10",
        fund_base_currency="USD",
        nav=Decimal("100"),
        positions=[position],
    )


@pytest.fixture
def mixed_equity_cash_portfolio() -> RiskReadyPortfolio:
    """Portfolio with 80 equity and 20 cash."""
    equity = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=101,
        isin="US0378331005",
        valuation_date="2026-06-10",
        quantity=Decimal("8"),
        market_value=Decimal("800"),
        position_currency="USD",
        asset_class="EQUITY",
        instrument_currency="USD",
        market_value_base_ccy=Decimal("80"),
        fund_base_currency="USD",
        weight=Decimal("0.8"),
    )
    cash = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=102,
        isin="CASH_USD",
        valuation_date="2026-06-10",
        quantity=Decimal("20"),
        market_value=Decimal("20"),
        position_currency="USD",
        asset_class="CASH",
        instrument_currency="USD",
        market_value_base_ccy=Decimal("20"),
        fund_base_currency="USD",
        weight=Decimal("0.2"),
    )
    return RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2026-06-10",
        fund_base_currency="USD",
        nav=Decimal("100"),
        positions=[equity, cash],
    )


@pytest.fixture
def all_cash_portfolio() -> RiskReadyPortfolio:
    """Portfolio with only cash."""
    cash = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=101,
        isin="CASH_USD",
        valuation_date="2026-06-10",
        quantity=Decimal("100"),
        market_value=Decimal("100"),
        position_currency="USD",
        asset_class="CASH",
        instrument_currency="USD",
        market_value_base_ccy=Decimal("100"),
        fund_base_currency="USD",
        weight=Decimal("1.0"),
    )
    return RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2026-06-10",
        fund_base_currency="USD",
        nav=Decimal("100"),
        positions=[cash],
    )


@pytest.fixture
def foreign_currency_cash_portfolio() -> RiskReadyPortfolio:
    """Portfolio with foreign-currency cash (unsupported)."""
    eur_cash = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=101,
        isin="CASH_EUR",
        valuation_date="2026-06-10",
        quantity=Decimal("100"),
        market_value=Decimal("100"),
        position_currency="EUR",
        asset_class="CASH",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("100"),
        fund_base_currency="USD",
        weight=Decimal("1.0"),
    )
    return RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2026-06-10",
        fund_base_currency="USD",
        nav=Decimal("100"),
        positions=[eur_cash],
    )


@pytest.fixture
def bond_position_portfolio() -> RiskReadyPortfolio:
    """Portfolio with an unsupported bond position."""
    bond = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=101,
        isin="XS0000000000",
        valuation_date="2026-06-10",
        quantity=Decimal("100"),
        market_value=Decimal("100"),
        position_currency="USD",
        asset_class="BOND",
        instrument_currency="USD",
        market_value_base_ccy=Decimal("100"),
        fund_base_currency="USD",
        weight=Decimal("1.0"),
        modified_duration=Decimal("5"),
    )
    return RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2026-06-10",
        fund_base_currency="USD",
        nav=Decimal("100"),
        positions=[bond],
    )


@pytest.fixture
def scenario_20pct_down() -> StressScenario:
    """20% equity shock down."""
    return StressScenario(
        scenario_id="EQ_PARALLEL_20",
        scenario_name="Equity parallel shock -20%",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="PARALLEL_EQUITY",
        shock_rate=Decimal("-0.20"),
        description="Hypothetical 20% parallel equity market shock",
    )


@pytest.fixture
def scenario_10pct_up() -> StressScenario:
    """10% equity shock up."""
    return StressScenario(
        scenario_id="EQ_PARALLEL_UP_10",
        scenario_name="Equity parallel shock +10%",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type="PARALLEL_EQUITY",
        shock_rate=Decimal("0.10"),
        description="Hypothetical 10% parallel equity market gain",
    )


@pytest.fixture
def engine() -> EquityStressEngine:
    """Equity stress engine."""
    return EquityStressEngine()


# ============================================================================
# Model validation tests
# ============================================================================


class TestStressScenarioModel:
    """Tests for StressScenario model."""

    def test_valid_scenario(self, scenario_20pct_down: StressScenario) -> None:
        """Valid scenario can be created."""
        assert scenario_20pct_down.scenario_id == "EQ_PARALLEL_20"
        assert scenario_20pct_down.shock_rate == Decimal("-0.20")
        assert scenario_20pct_down.scenario_type == "HYPOTHETICAL"
        assert scenario_20pct_down.scenario_source == "MANAGER_DEFINED"

    def test_scenario_immutable(self, scenario_20pct_down: StressScenario) -> None:
        """Scenario is immutable."""
        with pytest.raises(Exception):  # FrozenInstanceError or similar
            scenario_20pct_down.shock_rate = Decimal("-0.30")

    def test_scenario_requires_non_empty_strings(self) -> None:
        """Scenario rejects empty string fields."""
        with pytest.raises(ValueError):
            StressScenario(
                scenario_id="",  # Empty
                scenario_name="Test",
                scenario_type="HYPOTHETICAL",
                scenario_source="MANAGER_DEFINED",
                shock_type="PARALLEL_EQUITY",
                shock_rate=Decimal("-0.20"),
                description="Test",
            )

    def test_scenario_shock_rate_converts_from_string(self) -> None:
        """Shock rate can be passed as string and is converted to Decimal."""
        scenario = StressScenario(
            scenario_id="TEST",
            scenario_name="Test",
            scenario_type="HYPOTHETICAL",
            scenario_source="MANAGER_DEFINED",
            shock_type="PARALLEL_EQUITY",
            shock_rate="-0.25",  # String
            description="Test",
        )
        assert scenario.shock_rate == Decimal("-0.25")


class TestStressTestInputModel:
    """Tests for StressTestInput model."""

    def test_valid_input(self, single_equity_position, scenario_20pct_down) -> None:
        """Valid input can be created."""
        input = StressTestInput(
            portfolio=single_equity_position,
            scenarios=[scenario_20pct_down],
        )
        assert input.portfolio.fund_id == 1
        assert len(input.scenarios) == 1

    def test_input_requires_non_empty_scenarios(self, single_equity_position) -> None:
        """Input requires at least one scenario."""
        with pytest.raises(ValueError):
            StressTestInput(
                portfolio=single_equity_position,
                scenarios=[],  # Empty
            )

    def test_input_multiple_scenarios(
        self, single_equity_position, scenario_20pct_down, scenario_10pct_up
    ) -> None:
        """Input can contain multiple scenarios."""
        input = StressTestInput(
            portfolio=single_equity_position,
            scenarios=[scenario_20pct_down, scenario_10pct_up],
        )
        assert len(input.scenarios) == 2


class TestStressPositionResultModel:
    """Tests for StressPositionResult model."""

    def test_valid_position_result(self) -> None:
        """Valid position result can be created."""
        result = StressPositionResult(
            position_id=101,
            isin="US0378331005",
            position_name="Apple Inc",
            asset_class="EQUITY",
            shock_type="PARALLEL_EQUITY",
            current_market_value_base_ccy=Decimal("100"),
            shock_rate=Decimal("-0.20"),
            stressed_market_value_base_ccy=Decimal("80"),
            position_pnl=Decimal("-20"),
        )
        assert result.current_market_value_base_ccy == Decimal("100")
        assert result.position_pnl == Decimal("-20")

    def test_position_result_immutable(self) -> None:
        """Position result is immutable."""
        result = StressPositionResult(
            position_id=101,
            isin="US0378331005",
            position_name="Apple Inc",
            asset_class="EQUITY",
            shock_type="PARALLEL_EQUITY",
            current_market_value_base_ccy=Decimal("100"),
            shock_rate=Decimal("-0.20"),
            stressed_market_value_base_ccy=Decimal("80"),
            position_pnl=Decimal("-20"),
        )
        with pytest.raises(Exception):
            result.position_pnl = Decimal("-30")

    def test_position_result_optional_position_name(self) -> None:
        """Position name is optional."""
        result = StressPositionResult(
            position_id=101,
            isin="US0378331005",
            position_name=None,  # Optional
            asset_class="EQUITY",
            shock_type="PARALLEL_EQUITY",
            current_market_value_base_ccy=Decimal("100"),
            shock_rate=Decimal("-0.20"),
            stressed_market_value_base_ccy=Decimal("80"),
            position_pnl=Decimal("-20"),
        )
        assert result.position_name is None

    def test_position_result_rejects_negative_market_values(self) -> None:
        """Market values must be non-negative."""
        with pytest.raises(ValueError):
            StressPositionResult(
                position_id=101,
                isin="US0378331005",
                position_name="Apple Inc",
                asset_class="EQUITY",
                shock_type="PARALLEL_EQUITY",
                current_market_value_base_ccy=Decimal("-100"),  # Invalid
                shock_rate=Decimal("-0.20"),
                stressed_market_value_base_ccy=Decimal("80"),
                position_pnl=Decimal("-20"),
            )


class TestStressPortfolioResultModel:
    """Tests for StressPortfolioResult model."""

    def test_valid_portfolio_result(self) -> None:
        """Valid portfolio result can be created."""
        result = StressPortfolioResult(
            fund_id=1,
            valuation_date=date(2026, 6, 10),
            scenario_id="EQ_PARALLEL_20",
            scenario_name="Equity parallel shock -20%",
            scenario_type="HYPOTHETICAL",
            scenario_source="MANAGER_DEFINED",
            shock_type="PARALLEL_EQUITY",
            shock_rate=Decimal("-0.20"),
            current_nav=Decimal("100"),
            stressed_nav=Decimal("80"),
            total_pnl=Decimal("-20"),
            loss_pct_nav=Decimal("0.20"),
            stressed_positions=[],
            num_positions_stressed=1,
            num_cash_positions=0,
        )
        assert result.current_nav == Decimal("100")
        assert result.stressed_nav == Decimal("80")

    def test_portfolio_result_loss_pct_nav_non_negative(self) -> None:
        """Loss percentage must be non-negative."""
        with pytest.raises(ValueError):
            StressPortfolioResult(
                fund_id=1,
                valuation_date=date(2026, 6, 10),
                scenario_id="EQ_PARALLEL_20",
                scenario_name="Test",
                scenario_type="HYPOTHETICAL",
                scenario_source="MANAGER_DEFINED",
                shock_type="PARALLEL_EQUITY",
                shock_rate=Decimal("-0.20"),
                current_nav=Decimal("100"),
                stressed_nav=Decimal("80"),
                total_pnl=Decimal("-20"),
                loss_pct_nav=Decimal("-0.10"),  # Invalid: negative
                stressed_positions=[],
                num_positions_stressed=1,
                num_cash_positions=0,
            )


# ============================================================================
# Engine calculation tests
# ============================================================================


class TestEquityStressEngine:
    """Tests for EquityStressEngine."""

    def test_single_equity_20pct_down(
        self, engine, single_equity_position, scenario_20pct_down
    ) -> None:
        """Single equity position with 20% shock down."""
        input = StressTestInput(
            portfolio=single_equity_position,
            scenarios=[scenario_20pct_down],
        )
        results = engine.stress(input)

        assert len(results) == 1
        result = results[0]
        assert result.scenario_id == "EQ_PARALLEL_20"
        assert result.current_nav == Decimal("100")
        assert result.stressed_nav == Decimal("80")
        assert result.total_pnl == Decimal("-20")
        assert result.loss_pct_nav == Decimal("0.20")
        assert len(result.stressed_positions) == 1

        position_result = result.stressed_positions[0]
        assert position_result.current_market_value_base_ccy == Decimal("100")
        assert position_result.stressed_market_value_base_ccy == Decimal("80")
        assert position_result.position_pnl == Decimal("-20")
        assert position_result.asset_class == "EQUITY"

    def test_mixed_equity_cash_20pct_down(
        self, engine, mixed_equity_cash_portfolio, scenario_20pct_down
    ) -> None:
        """Mixed equity/cash portfolio with 20% equity shock."""
        input = StressTestInput(
            portfolio=mixed_equity_cash_portfolio,
            scenarios=[scenario_20pct_down],
        )
        results = engine.stress(input)

        assert len(results) == 1
        result = results[0]

        # Equity 80 * -20% = -16; Cash 20 * 0% = 0; Total = -16
        assert result.total_pnl == Decimal("-16")
        assert result.current_nav == Decimal("100")
        assert result.stressed_nav == Decimal("84")
        assert result.loss_pct_nav == Decimal("0.16")

        # Check position results
        assert len(result.stressed_positions) == 2
        assert result.num_positions_stressed == 1
        assert result.num_cash_positions == 1

        # Equity position
        equity_result = result.stressed_positions[0]
        assert equity_result.asset_class == "EQUITY"
        assert equity_result.position_pnl == Decimal("-16")

        # Cash position
        cash_result = result.stressed_positions[1]
        assert cash_result.asset_class == "CASH"
        assert cash_result.position_pnl == Decimal("0")

    def test_all_cash_portfolio_20pct_shock(
        self, engine, all_cash_portfolio, scenario_20pct_down
    ) -> None:
        """All-cash portfolio returns zero P&L and zero loss percentage."""
        input = StressTestInput(
            portfolio=all_cash_portfolio,
            scenarios=[scenario_20pct_down],
        )
        results = engine.stress(input)

        assert len(results) == 1
        result = results[0]

        assert result.total_pnl == Decimal("0")
        assert result.current_nav == Decimal("100")
        assert result.stressed_nav == Decimal("100")
        assert result.loss_pct_nav == Decimal("0")
        assert result.num_positions_stressed == 0
        assert result.num_cash_positions == 1

    def test_cash_unchanged(self, engine, mixed_equity_cash_portfolio, scenario_20pct_down) -> None:
        """Cash positions are unchanged under any equity shock."""
        input = StressTestInput(
            portfolio=mixed_equity_cash_portfolio,
            scenarios=[scenario_20pct_down],
        )
        results = engine.stress(input)

        result = results[0]
        cash_result = result.stressed_positions[1]

        assert cash_result.current_market_value_base_ccy == Decimal("20")
        assert cash_result.stressed_market_value_base_ccy == Decimal("20")
        assert cash_result.position_pnl == Decimal("0")

    def test_positive_shock_gain(self, engine, single_equity_position, scenario_10pct_up) -> None:
        """Positive shock produces gain and zero loss percentage."""
        input = StressTestInput(
            portfolio=single_equity_position,
            scenarios=[scenario_10pct_up],
        )
        results = engine.stress(input)

        result = results[0]
        assert result.total_pnl == Decimal("10")
        assert result.loss_pct_nav == Decimal("0")  # max(0, -10/100) = 0
        assert result.stressed_nav == Decimal("110")

    def test_multiple_scenarios(
        self, engine, single_equity_position, scenario_20pct_down, scenario_10pct_up
    ) -> None:
        """Multiple scenarios are applied in order."""
        input = StressTestInput(
            portfolio=single_equity_position,
            scenarios=[scenario_20pct_down, scenario_10pct_up],
        )
        results = engine.stress(input)

        assert len(results) == 2

        # First result: -20% shock
        assert results[0].scenario_id == "EQ_PARALLEL_20"
        assert results[0].total_pnl == Decimal("-20")

        # Second result: +10% shock
        assert results[1].scenario_id == "EQ_PARALLEL_UP_10"
        assert results[1].total_pnl == Decimal("10")

    def test_scenario_metadata_copied_to_result(
        self, engine, single_equity_position, scenario_20pct_down
    ) -> None:
        """Scenario metadata is copied to portfolio result."""
        input = StressTestInput(
            portfolio=single_equity_position,
            scenarios=[scenario_20pct_down],
        )
        results = engine.stress(input)

        result = results[0]
        assert result.scenario_id == scenario_20pct_down.scenario_id
        assert result.scenario_name == scenario_20pct_down.scenario_name
        assert result.scenario_type == scenario_20pct_down.scenario_type
        assert result.scenario_source == scenario_20pct_down.scenario_source
        assert result.shock_type == scenario_20pct_down.shock_type
        assert result.shock_rate == scenario_20pct_down.shock_rate

    def test_position_result_includes_asset_class_shock_type_and_position_name(
        self, engine, single_equity_position, scenario_20pct_down
    ) -> None:
        """StressPositionResult includes asset_class, shock_type, and position_name for audit."""
        input = StressTestInput(
            portfolio=single_equity_position,
            scenarios=[scenario_20pct_down],
        )
        results = engine.stress(input)

        result = results[0]
        position_result = result.stressed_positions[0]

        assert position_result.asset_class == "EQUITY"
        assert position_result.shock_type == "PARALLEL_EQUITY"
        assert position_result.position_name is None  # Not available in enriched position

    def test_unsupported_asset_class_bond_raises_error(
        self, engine, bond_position_portfolio, scenario_20pct_down
    ) -> None:
        """Unsupported asset class (BOND) raises UnsupportedAssetClassError."""
        input = StressTestInput(
            portfolio=bond_position_portfolio,
            scenarios=[scenario_20pct_down],
        )
        with pytest.raises(UnsupportedAssetClassError) as exc_info:
            engine.stress(input)

        assert exc_info.value.asset_class == "BOND"
        assert exc_info.value.isin == "XS0000000000"

    def test_foreign_currency_cash_raises_error(
        self, engine, foreign_currency_cash_portfolio, scenario_20pct_down
    ) -> None:
        """Foreign-currency cash raises UnsupportedAssetClassError."""
        input = StressTestInput(
            portfolio=foreign_currency_cash_portfolio,
            scenarios=[scenario_20pct_down],
        )
        with pytest.raises(UnsupportedAssetClassError) as exc_info:
            engine.stress(input)

        assert exc_info.value.asset_class == "CASH"
        assert "Foreign-currency" in exc_info.value.reason

    def test_decimal_precision_preserved(self, engine) -> None:
        """Decimal precision is preserved through calculations."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=101,
            isin="US0378331005",
            valuation_date="2026-06-10",
            quantity=Decimal("1"),
            market_value=Decimal("123.456"),
            position_currency="USD",
            asset_class="EQUITY",
            instrument_currency="USD",
            market_value_base_ccy=Decimal("123.456"),
            fund_base_currency="USD",
            weight=Decimal("1.0"),
        )
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="USD",
            nav=Decimal("123.456"),
            positions=[position],
        )
        scenario = StressScenario(
            scenario_id="TEST",
            scenario_name="Test",
            scenario_type="HYPOTHETICAL",
            scenario_source="MANAGER_DEFINED",
            shock_type="PARALLEL_EQUITY",
            shock_rate=Decimal("-0.123456"),
            description="Test",
        )
        input = StressTestInput(portfolio=portfolio, scenarios=[scenario])

        results = engine.stress(input)
        result = results[0]

        # Verify decimal calculations are precise
        expected_shocked = Decimal("123.456") * (Decimal("1") + Decimal("-0.123456"))
        expected_pnl = expected_shocked - Decimal("123.456")

        assert result.stressed_positions[0].stressed_market_value_base_ccy == expected_shocked
        assert result.stressed_positions[0].position_pnl == expected_pnl
        assert result.total_pnl == expected_pnl

    def test_loss_pct_nav_formula_max_zero(self, engine, single_equity_position) -> None:
        """Loss percentage uses max(0, -total_pnl / current_nav)."""
        # Positive shock: total_pnl = 50, so -50/100 = -0.5, max(0, -0.5) = 0
        scenario = StressScenario(
            scenario_id="TEST_UP",
            scenario_name="Test Up",
            scenario_type="HYPOTHETICAL",
            scenario_source="MANAGER_DEFINED",
            shock_type="PARALLEL_EQUITY",
            shock_rate=Decimal("0.5"),  # +50%
            description="Test",
        )
        input = StressTestInput(
            portfolio=single_equity_position,
            scenarios=[scenario],
        )

        results = engine.stress(input)
        result = results[0]

        assert result.total_pnl == Decimal("50")
        assert result.loss_pct_nav == Decimal("0")  # max(0, -50/100) = 0

    def test_stressed_nav_formula(
        self, engine, single_equity_position, scenario_20pct_down
    ) -> None:
        """Stressed NAV = current NAV + total P&L."""
        input = StressTestInput(
            portfolio=single_equity_position,
            scenarios=[scenario_20pct_down],
        )

        results = engine.stress(input)
        result = results[0]

        assert result.stressed_nav == result.current_nav + result.total_pnl
        assert result.stressed_nav == Decimal("100") + Decimal("-20")
        assert result.stressed_nav == Decimal("80")
