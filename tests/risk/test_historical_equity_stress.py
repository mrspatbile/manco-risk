"""Tests for historical equity stress engine.

Comprehensive test suite covering:
- Pure model validation
- Engine selection logic
- Window handling and metadata
- Edge cases and error handling
- Sign conventions and decimal precision
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.engines.historical_equity_stress import HistoricalEquityStressEngine
from manco_risk.risk.exceptions import UnsupportedAssetClassError
from manco_risk.risk.models.historical_stress_input import HistoricalStressInput
from manco_risk.risk.models.historical_stress_result import HistoricalStressResult
from manco_risk.risk.models.scenario_pnl import ScenarioPnL


@pytest.fixture
def single_equity_portfolio() -> RiskReadyPortfolio:
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
def engine() -> HistoricalEquityStressEngine:
    """Historical equity stress engine."""
    return HistoricalEquityStressEngine()


# ============================================================================
# Model validation tests
# ============================================================================


class TestHistoricalStressInputModel:
    """Tests for HistoricalStressInput model."""

    def test_valid_input(self, single_equity_portfolio) -> None:
        """Valid input can be created."""
        scenarios = [
            ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("-20")),
            ScenarioPnL(scenario_date=date(2008, 10, 15), total_pnl=Decimal("-30")),
        ]
        input = HistoricalStressInput(
            portfolio=single_equity_portfolio,
            scenario_pnls=scenarios,
            scenario_id="HIST_GFC",
            scenario_name="Global financial crisis",
            scenario_type="HISTORICAL",
            scenario_source="HISTORICAL_WINDOW",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            description="September 2008 - March 2009",
        )
        assert input.scenario_id == "HIST_GFC"
        assert len(input.scenario_pnls) == 2

    def test_input_rejects_empty_scenario_pnls(self, single_equity_portfolio) -> None:
        """Input requires non-empty scenario P&Ls."""
        with pytest.raises(ValueError):
            HistoricalStressInput(
                portfolio=single_equity_portfolio,
                scenario_pnls=[],  # Empty
                scenario_id="HIST_TEST",
                scenario_name="Test",
                scenario_type="HISTORICAL",
                scenario_source="HISTORICAL_WINDOW",
                shock_type="HISTORICAL_EQUITY",
                window_start_date=date(2008, 9, 1),
                window_end_date=date(2009, 3, 31),
                description="Test",
            )

    def test_input_rejects_invalid_window_dates(self, single_equity_portfolio) -> None:
        """Input rejects end date before start date."""
        scenarios = [ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("-20"))]
        with pytest.raises(ValueError):
            HistoricalStressInput(
                portfolio=single_equity_portfolio,
                scenario_pnls=scenarios,
                scenario_id="HIST_TEST",
                scenario_name="Test",
                scenario_type="HISTORICAL",
                scenario_source="HISTORICAL_WINDOW",
                shock_type="HISTORICAL_EQUITY",
                window_start_date=date(2009, 3, 31),
                window_end_date=date(2008, 9, 1),  # Before start date
                description="Test",
            )


class TestHistoricalStressResultModel:
    """Tests for HistoricalStressResult model."""

    def test_valid_result(self) -> None:
        """Valid result can be created."""
        result = HistoricalStressResult(
            fund_id=1,
            valuation_date=date(2026, 6, 10),
            scenario_id="HIST_GFC",
            scenario_name="Global financial crisis",
            scenario_type="HISTORICAL",
            scenario_source="HISTORICAL_WINDOW",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            worst_scenario_date=date(2008, 10, 15),
            worst_scenario_pnl=Decimal("-30"),
            loss_pct_nav=Decimal("0.30"),
            num_scenarios=5,
            description="Test",
        )
        assert result.num_scenarios == 5
        assert result.worst_scenario_pnl == Decimal("-30")

    def test_result_rejects_negative_loss_pct(self) -> None:
        """Loss percentage must be non-negative."""
        with pytest.raises(ValueError):
            HistoricalStressResult(
                fund_id=1,
                valuation_date=date(2026, 6, 10),
                scenario_id="HIST_TEST",
                scenario_name="Test",
                scenario_type="HISTORICAL",
                scenario_source="HISTORICAL_WINDOW",
                shock_type="HISTORICAL_EQUITY",
                window_start_date=date(2008, 9, 1),
                window_end_date=date(2009, 3, 31),
                worst_scenario_date=date(2008, 10, 15),
                worst_scenario_pnl=Decimal("-30"),
                loss_pct_nav=Decimal("-0.10"),  # Invalid
                num_scenarios=5,
                description="Test",
            )


# ============================================================================
# Engine selection tests
# ============================================================================


class TestHistoricalEquityStressEngine:
    """Tests for HistoricalEquityStressEngine."""

    def test_selects_worst_scenario_by_signed_pnl(self, engine, single_equity_portfolio) -> None:
        """Engine selects scenario with minimum (worst) signed P&L."""
        scenarios = [
            ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("-20")),
            ScenarioPnL(scenario_date=date(2008, 10, 15), total_pnl=Decimal("-50")),  # Worst
            ScenarioPnL(scenario_date=date(2008, 11, 15), total_pnl=Decimal("-30")),
        ]
        input = HistoricalStressInput(
            portfolio=single_equity_portfolio,
            scenario_pnls=scenarios,
            scenario_id="HIST_GFC",
            scenario_name="Global financial crisis",
            scenario_type="HISTORICAL",
            scenario_source="HISTORICAL_WINDOW",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            description="Test worst selection",
        )

        result = engine.calculate(input)

        assert result.worst_scenario_date == date(2008, 10, 15)
        assert result.worst_scenario_pnl == Decimal("-50")

    def test_loss_percentage_is_positive_magnitude(self, engine, single_equity_portfolio) -> None:
        """Loss percentage is always non-negative."""
        scenarios = [ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("-20"))]
        input = HistoricalStressInput(
            portfolio=single_equity_portfolio,
            scenario_pnls=scenarios,
            scenario_id="HIST_TEST",
            scenario_name="Test",
            scenario_type="HISTORICAL",
            scenario_source="HISTORICAL_WINDOW",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            description="Test loss percentage",
        )

        result = engine.calculate(input)

        # P&L = -20, NAV = 100, loss% = max(0, 20/100) = 0.20
        assert result.loss_pct_nav == Decimal("0.20")
        assert result.loss_pct_nav >= Decimal("0")

    def test_positive_worst_pnl_gives_zero_loss_percentage(
        self, engine, single_equity_portfolio
    ) -> None:
        """Positive worst P&L gives zero loss percentage."""
        scenarios = [ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("10"))]
        input = HistoricalStressInput(
            portfolio=single_equity_portfolio,
            scenario_pnls=scenarios,
            scenario_id="HIST_GAIN",
            scenario_name="Gain scenario",
            scenario_type="HISTORICAL",
            scenario_source="HISTORICAL_WINDOW",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            description="Test positive gain",
        )

        result = engine.calculate(input)

        assert result.worst_scenario_pnl == Decimal("10")
        assert result.loss_pct_nav == Decimal("0")

    def test_zero_worst_pnl_gives_zero_loss_percentage(
        self, engine, single_equity_portfolio
    ) -> None:
        """Zero worst P&L gives zero loss percentage."""
        scenarios = [ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("0"))]
        input = HistoricalStressInput(
            portfolio=single_equity_portfolio,
            scenario_pnls=scenarios,
            scenario_id="HIST_ZERO",
            scenario_name="Zero change scenario",
            scenario_type="HISTORICAL",
            scenario_source="HISTORICAL_WINDOW",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            description="Test zero P&L",
        )

        result = engine.calculate(input)

        assert result.worst_scenario_pnl == Decimal("0")
        assert result.loss_pct_nav == Decimal("0")

    def test_all_cash_portfolio_with_zero_pnls(self, engine, all_cash_portfolio) -> None:
        """All-cash portfolio with zero scenario P&Ls is valid."""
        scenarios = [
            ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("0")),
            ScenarioPnL(scenario_date=date(2008, 10, 15), total_pnl=Decimal("0")),
        ]
        input = HistoricalStressInput(
            portfolio=all_cash_portfolio,
            scenario_pnls=scenarios,
            scenario_id="HIST_CASH",
            scenario_name="All-cash historical",
            scenario_type="HISTORICAL",
            scenario_source="HISTORICAL_WINDOW",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            description="Test all-cash",
        )

        result = engine.calculate(input)

        assert isinstance(result, HistoricalStressResult)
        assert result.num_scenarios == 2
        assert result.loss_pct_nav == Decimal("0")

    def test_scenario_metadata_copied_to_result(self, engine, single_equity_portfolio) -> None:
        """Scenario metadata is copied to result."""
        scenarios = [ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("-20"))]
        input = HistoricalStressInput(
            portfolio=single_equity_portfolio,
            scenario_pnls=scenarios,
            scenario_id="HIST_GFC",
            scenario_name="Global financial crisis",
            scenario_type="HISTORICAL",
            scenario_source="MANAGER_ANALYSIS",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            description="GFC window",
        )

        result = engine.calculate(input)

        assert result.scenario_id == input.scenario_id
        assert result.scenario_name == input.scenario_name
        assert result.scenario_type == "HISTORICAL"
        assert result.scenario_source == "MANAGER_ANALYSIS"
        assert result.shock_type == "HISTORICAL_EQUITY"

    def test_historical_window_metadata_copied_to_result(
        self, engine, single_equity_portfolio
    ) -> None:
        """Historical window metadata is copied to result."""
        scenarios = [ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("-20"))]
        input = HistoricalStressInput(
            portfolio=single_equity_portfolio,
            scenario_pnls=scenarios,
            scenario_id="HIST_TEST",
            scenario_name="Test window",
            scenario_type="HISTORICAL",
            scenario_source="HISTORICAL_WINDOW",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            description="Test",
        )

        result = engine.calculate(input)

        assert result.window_start_date == date(2008, 9, 1)
        assert result.window_end_date == date(2009, 3, 31)

    def test_num_scenarios_reported_correctly(self, engine, single_equity_portfolio) -> None:
        """Number of scenarios is reported correctly."""
        scenarios = [
            ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("-20")),
            ScenarioPnL(scenario_date=date(2008, 10, 15), total_pnl=Decimal("-30")),
            ScenarioPnL(scenario_date=date(2008, 11, 15), total_pnl=Decimal("-25")),
            ScenarioPnL(scenario_date=date(2008, 12, 15), total_pnl=Decimal("-40")),
        ]
        input = HistoricalStressInput(
            portfolio=single_equity_portfolio,
            scenario_pnls=scenarios,
            scenario_id="HIST_COUNT",
            scenario_name="Test count",
            scenario_type="HISTORICAL",
            scenario_source="HISTORICAL_WINDOW",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            description="Test",
        )

        result = engine.calculate(input)

        assert result.num_scenarios == 4

    def test_current_portfolio_nav_used_for_loss_percentage(
        self, engine, mixed_equity_cash_portfolio
    ) -> None:
        """Current portfolio NAV is used for loss percentage calculation."""
        # NAV = 100, P&L = -25
        scenarios = [ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("-25"))]
        input = HistoricalStressInput(
            portfolio=mixed_equity_cash_portfolio,
            scenario_pnls=scenarios,
            scenario_id="HIST_NAV",
            scenario_name="NAV test",
            scenario_type="HISTORICAL",
            scenario_source="HISTORICAL_WINDOW",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            description="Test",
        )

        result = engine.calculate(input)

        # loss_pct = 25 / 100 = 0.25
        assert result.loss_pct_nav == Decimal("0.25")

    def test_unsupported_asset_class_raises_error(self, engine, bond_position_portfolio) -> None:
        """Unsupported asset class raises UnsupportedAssetClassError."""
        scenarios = [ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("-20"))]
        input = HistoricalStressInput(
            portfolio=bond_position_portfolio,
            scenario_pnls=scenarios,
            scenario_id="HIST_BOND",
            scenario_name="Bond test",
            scenario_type="HISTORICAL",
            scenario_source="HISTORICAL_WINDOW",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            description="Test",
        )

        with pytest.raises(UnsupportedAssetClassError):
            engine.calculate(input)

    def test_foreign_currency_cash_raises_error(
        self, engine, foreign_currency_cash_portfolio
    ) -> None:
        """Foreign-currency cash raises UnsupportedAssetClassError."""
        scenarios = [ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("-20"))]
        input = HistoricalStressInput(
            portfolio=foreign_currency_cash_portfolio,
            scenario_pnls=scenarios,
            scenario_id="HIST_FX",
            scenario_name="FX cash test",
            scenario_type="HISTORICAL",
            scenario_source="HISTORICAL_WINDOW",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            description="Test",
        )

        with pytest.raises(UnsupportedAssetClassError):
            engine.calculate(input)

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
        scenarios = [ScenarioPnL(scenario_date=date(2008, 9, 15), total_pnl=Decimal("-12.3456"))]
        input = HistoricalStressInput(
            portfolio=portfolio,
            scenario_pnls=scenarios,
            scenario_id="HIST_PRECISION",
            scenario_name="Precision test",
            scenario_type="HISTORICAL",
            scenario_source="HISTORICAL_WINDOW",
            shock_type="HISTORICAL_EQUITY",
            window_start_date=date(2008, 9, 1),
            window_end_date=date(2009, 3, 31),
            description="Test",
        )

        result = engine.calculate(input)

        # Verify precise calculation
        expected_loss_pct = Decimal("12.3456") / Decimal("123.456")
        assert result.loss_pct_nav == expected_loss_pct
