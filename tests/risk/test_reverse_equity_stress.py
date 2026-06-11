"""Tests for reverse equity stress engine.

Comprehensive test suite covering:
- Pure model validation
- Engine calculation correctness
- Feasibility and infeasibility handling
- Edge cases and error handling
- Sign conventions and decimal precision
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.engines.reverse_equity_stress import ReverseEquityStressEngine
from manco_risk.risk.exceptions import UnsupportedAssetClassError
from manco_risk.risk.models.reverse_stress_input import ReverseStressInput
from manco_risk.risk.models.reverse_stress_result import ReverseStressResult


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
def engine() -> ReverseEquityStressEngine:
    """Reverse equity stress engine."""
    return ReverseEquityStressEngine()


# ============================================================================
# Model validation tests
# ============================================================================


class TestReverseStressInputModel:
    """Tests for ReverseStressInput model."""

    def test_valid_input(self, single_equity_portfolio) -> None:
        """Valid input can be created."""
        input = ReverseStressInput(
            portfolio=single_equity_portfolio,
            target_loss_pct=Decimal("0.20"),
            scenario_id="REV_TARGET_20",
            scenario_name="Reverse: 20% NAV loss",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test reverse stress to 20% loss",
        )
        assert input.target_loss_pct == Decimal("0.20")
        assert input.scenario_type == "REVERSE"

    def test_input_zero_target_loss_is_valid(self, single_equity_portfolio) -> None:
        """Target loss of 0% is valid and feasible."""
        input = ReverseStressInput(
            portfolio=single_equity_portfolio,
            target_loss_pct=Decimal("0"),
            scenario_id="REV_TARGET_0",
            scenario_name="Reverse: 0% NAV loss",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test reverse stress to 0% loss",
        )
        assert input.target_loss_pct == Decimal("0")

    def test_input_rejects_negative_target_loss(self, single_equity_portfolio) -> None:
        """Target loss must be >= 0."""
        with pytest.raises(ValueError):
            ReverseStressInput(
                portfolio=single_equity_portfolio,
                target_loss_pct=Decimal("-0.10"),
                scenario_id="REV_NEG",
                scenario_name="Test",
                scenario_type="REVERSE",
                scenario_source="MANAGER_DEFINED",
                description="Test",
            )

    def test_input_rejects_target_loss_100_pct(self, single_equity_portfolio) -> None:
        """Target loss must be < 1."""
        with pytest.raises(ValueError):
            ReverseStressInput(
                portfolio=single_equity_portfolio,
                target_loss_pct=Decimal("1.0"),
                scenario_id="REV_100",
                scenario_name="Test",
                scenario_type="REVERSE",
                scenario_source="MANAGER_DEFINED",
                description="Test",
            )


class TestReverseStressResultModel:
    """Tests for ReverseStressResult model."""

    def test_valid_feasible_result_requires_stress_result(self) -> None:
        """Valid feasible result requires stress_result to be populated."""
        # Feasible results must have stress_result populated; this is validated by the model
        # The engine tests verify that feasible results are created correctly with stress_result
        # This test just verifies that the consistency constraint is enforced
        with pytest.raises(ValueError):
            ReverseStressResult(
                fund_id=1,
                valuation_date=date(2026, 6, 10),
                scenario_id="REV_TEST",
                scenario_name="Test",
                scenario_type="REVERSE",
                scenario_source="MANAGER_DEFINED",
                target_loss_pct=Decimal("0.20"),
                target_loss_amount=Decimal("20"),
                equity_like_market_value=Decimal("100"),
                required_shock=Decimal("-0.20"),
                is_feasible=True,
                infeasibility_reason=None,
                stress_result=None,  # Invalid for feasible result
                current_nav=Decimal("100"),
                stressed_nav=Decimal("80"),
                total_pnl=Decimal("-20"),
                loss_pct_nav=Decimal("0.20"),
            )

    def test_valid_infeasible_result(self) -> None:
        """Valid infeasible result can be created."""
        result = ReverseStressResult(
            fund_id=1,
            valuation_date=date(2026, 6, 10),
            scenario_id="REV_TEST",
            scenario_name="Test",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            target_loss_pct=Decimal("0.50"),
            target_loss_amount=Decimal("50"),
            equity_like_market_value=Decimal("0"),
            required_shock=None,
            is_feasible=False,
            infeasibility_reason="No equity-like exposure",
            stress_result=None,
            current_nav=Decimal("100"),
            stressed_nav=None,
            total_pnl=None,
            loss_pct_nav=None,
        )
        assert result.is_feasible is False
        assert result.required_shock is None
        assert result.current_nav == Decimal("100")
        assert result.stressed_nav is None


# ============================================================================
# Engine calculation tests
# ============================================================================


class TestReverseEquityStressEngine:
    """Tests for ReverseEquityStressEngine."""

    def test_zero_percent_target_loss_is_feasible(self, engine, single_equity_portfolio) -> None:
        """Target loss of 0% is feasible with required shock of 0."""
        input = ReverseStressInput(
            portfolio=single_equity_portfolio,
            target_loss_pct=Decimal("0"),
            scenario_id="REV_0PCT",
            scenario_name="Reverse: 0% loss",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test zero loss",
        )
        result = engine.calculate(input)

        assert result.is_feasible is True
        assert result.required_shock == Decimal("0")
        assert result.target_loss_amount == Decimal("0")
        assert result.stress_result is not None
        assert result.stress_result.loss_pct_nav == Decimal("0")

    def test_10pct_target_loss_single_equity(self, engine, single_equity_portfolio) -> None:
        """10% target NAV loss on single equity portfolio."""
        input = ReverseStressInput(
            portfolio=single_equity_portfolio,
            target_loss_pct=Decimal("0.10"),
            scenario_id="REV_10PCT",
            scenario_name="Reverse: 10% loss",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test 10% loss",
        )
        result = engine.calculate(input)

        assert result.is_feasible is True
        assert result.target_loss_pct == Decimal("0.10")
        assert result.target_loss_amount == Decimal("10")
        assert result.equity_like_market_value == Decimal("100")
        # required_shock = -10 / 100 = -0.10
        assert result.required_shock == Decimal("-0.10")
        assert result.stress_result is not None
        assert result.stress_result.total_pnl == Decimal("-10")
        assert result.stress_result.loss_pct_nav == Decimal("0.10")

    def test_20pct_target_loss_mixed_equity_cash(self, engine, mixed_equity_cash_portfolio) -> None:
        """20% target NAV loss on mixed equity/cash portfolio."""
        # NAV = 100, Equity = 80, Cash = 20, Target = 20%
        # Target loss amount = 20
        # Required shock = -20 / 80 = -0.25
        input = ReverseStressInput(
            portfolio=mixed_equity_cash_portfolio,
            target_loss_pct=Decimal("0.20"),
            scenario_id="REV_20PCT_MIX",
            scenario_name="Reverse: 20% loss mixed",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test 20% loss with cash",
        )
        result = engine.calculate(input)

        assert result.is_feasible is True
        assert result.target_loss_amount == Decimal("20")
        assert result.equity_like_market_value == Decimal("80")
        assert result.required_shock == Decimal("-0.25")
        assert result.stress_result is not None
        assert result.stress_result.total_pnl == Decimal("-20")
        assert result.stress_result.loss_pct_nav == Decimal("0.20")

    def test_applied_shock_produces_target_loss(self, engine, single_equity_portfolio) -> None:
        """Applied shock produces the target loss."""
        input = ReverseStressInput(
            portfolio=single_equity_portfolio,
            target_loss_pct=Decimal("0.15"),
            scenario_id="REV_15PCT",
            scenario_name="Reverse: 15% loss",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Verify shock produces loss",
        )
        result = engine.calculate(input)

        assert result.is_feasible is True
        stress_result = result.stress_result
        assert stress_result is not None
        # Loss percentage should match target
        assert stress_result.loss_pct_nav == result.target_loss_pct

    def test_cash_remains_unchanged(self, engine, mixed_equity_cash_portfolio) -> None:
        """Cash remains unchanged in reverse stress."""
        input = ReverseStressInput(
            portfolio=mixed_equity_cash_portfolio,
            target_loss_pct=Decimal("0.20"),
            scenario_id="REV_CASH_CHECK",
            scenario_name="Check cash unchanged",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Verify cash unchanged",
        )
        result = engine.calculate(input)

        assert result.is_feasible is True
        stress_result = result.stress_result
        assert stress_result is not None

        # Find cash position in stress result
        cash_results = [p for p in stress_result.stressed_positions if p.asset_class == "CASH"]
        assert len(cash_results) == 1
        cash_result = cash_results[0]

        assert cash_result.current_market_value_base_ccy == Decimal("20")
        assert cash_result.stressed_market_value_base_ccy == Decimal("20")
        assert cash_result.position_pnl == Decimal("0")

    def test_all_cash_portfolio_infeasible(self, engine, all_cash_portfolio) -> None:
        """All-cash portfolio is infeasible with required_shock=None."""
        input = ReverseStressInput(
            portfolio=all_cash_portfolio,
            target_loss_pct=Decimal("0.10"),
            scenario_id="REV_ALLCASH",
            scenario_name="All-cash infeasible",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test all-cash infeasibility",
        )
        result = engine.calculate(input)

        assert result.is_feasible is False
        assert result.required_shock is None
        assert result.stress_result is None
        assert "No equity-like exposure" in result.infeasibility_reason

    def test_zero_equity_exposure_infeasible(self, engine, all_cash_portfolio) -> None:
        """Zero equity-like exposure is infeasible."""
        input = ReverseStressInput(
            portfolio=all_cash_portfolio,
            target_loss_pct=Decimal("0.05"),
            scenario_id="REV_ZERO_EQ",
            scenario_name="Zero equity infeasible",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test zero equity infeasibility",
        )
        result = engine.calculate(input)

        assert result.is_feasible is False
        assert result.required_shock is None
        assert result.equity_like_market_value == Decimal("0")

    def test_shock_below_minus_100pct_infeasible_keeps_shock(
        self, engine, mixed_equity_cash_portfolio
    ) -> None:
        """Required shock < -100% is infeasible but keeps calculated shock."""
        # NAV = 100, Equity = 80, target = 95%
        # Target loss = 95, required shock = -95 / 80 = -1.1875
        input = ReverseStressInput(
            portfolio=mixed_equity_cash_portfolio,
            target_loss_pct=Decimal("0.95"),
            scenario_id="REV_EXTREME",
            scenario_name="Extreme loss target",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test shock > 100%",
        )
        result = engine.calculate(input)

        assert result.is_feasible is False
        assert result.required_shock is not None
        assert result.required_shock < Decimal("-1.0")
        assert result.stress_result is None
        assert "exceeds -100%" in result.infeasibility_reason

    def test_unsupported_asset_class_raises_error(self, engine, bond_position_portfolio) -> None:
        """Unsupported asset class raises UnsupportedAssetClassError."""
        input = ReverseStressInput(
            portfolio=bond_position_portfolio,
            target_loss_pct=Decimal("0.10"),
            scenario_id="REV_BOND",
            scenario_name="Bond unsupported",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test bond rejection",
        )
        with pytest.raises(UnsupportedAssetClassError):
            engine.calculate(input)

    def test_foreign_currency_cash_raises_error(
        self, engine, foreign_currency_cash_portfolio
    ) -> None:
        """Foreign-currency cash raises UnsupportedAssetClassError."""
        input = ReverseStressInput(
            portfolio=foreign_currency_cash_portfolio,
            target_loss_pct=Decimal("0.10"),
            scenario_id="REV_FX",
            scenario_name="Foreign cash unsupported",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test foreign cash rejection",
        )
        with pytest.raises(UnsupportedAssetClassError):
            engine.calculate(input)

    def test_scenario_metadata_carried_to_result(self, engine, single_equity_portfolio) -> None:
        """Scenario metadata is carried to result."""
        input = ReverseStressInput(
            portfolio=single_equity_portfolio,
            target_loss_pct=Decimal("0.10"),
            scenario_id="REV_META",
            scenario_name="Metadata test",
            scenario_type="REVERSE",
            scenario_source="INTERNAL_POLICY",
            description="Test metadata transfer",
        )
        result = engine.calculate(input)

        assert result.scenario_id == input.scenario_id
        assert result.scenario_name == input.scenario_name
        assert result.scenario_type == "REVERSE"
        assert result.scenario_source == "INTERNAL_POLICY"

    def test_scenario_metadata_in_stress_result(self, engine, single_equity_portfolio) -> None:
        """Scenario metadata is also in underlying StressPortfolioResult."""
        input = ReverseStressInput(
            portfolio=single_equity_portfolio,
            target_loss_pct=Decimal("0.10"),
            scenario_id="REV_STRESS_META",
            scenario_name="Stress metadata test",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test stress result metadata",
        )
        result = engine.calculate(input)

        assert result.is_feasible is True
        stress_result = result.stress_result
        assert stress_result is not None
        assert stress_result.scenario_id == input.scenario_id
        assert stress_result.shock_type == "PARALLEL_EQUITY_REVERSE"

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
        input = ReverseStressInput(
            portfolio=portfolio,
            target_loss_pct=Decimal("0.123456"),
            scenario_id="REV_PRECISION",
            scenario_name="Precision test",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test decimal precision",
        )

        result = engine.calculate(input)

        assert result.is_feasible is True
        # Verify precise calculation
        expected_loss_amount = Decimal("123.456") * Decimal("0.123456")
        assert result.target_loss_amount == expected_loss_amount

        expected_shock = -expected_loss_amount / Decimal("123.456")
        assert result.required_shock == expected_shock

    def test_infeasible_result_consistency(self, engine, all_cash_portfolio) -> None:
        """Infeasible result validates consistency constraints."""
        input = ReverseStressInput(
            portfolio=all_cash_portfolio,
            target_loss_pct=Decimal("0.10"),
            scenario_id="REV_CONSISTENCY",
            scenario_name="Consistency check",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test consistency",
        )
        result = engine.calculate(input)

        # Infeasible: stress_result must be None
        assert result.is_feasible is False
        assert result.stress_result is None

    def test_feasible_result_consistency(self, engine, single_equity_portfolio) -> None:
        """Feasible result validates consistency constraints."""
        input = ReverseStressInput(
            portfolio=single_equity_portfolio,
            target_loss_pct=Decimal("0.10"),
            scenario_id="REV_FEASIBLE_CONSISTENT",
            scenario_name="Feasible consistency",
            scenario_type="REVERSE",
            scenario_source="MANAGER_DEFINED",
            description="Test feasible consistency",
        )
        result = engine.calculate(input)

        # Feasible: stress_result must be populated
        assert result.is_feasible is True
        assert result.stress_result is not None

    def test_target_loss_greater_than_nav_infeasible(self, engine) -> None:
        """Target loss >= NAV is infeasible."""
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
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="USD",
            nav=Decimal("100"),
            positions=[position],
        )
        # Input validation should reject target_loss_pct >= 1.0
        with pytest.raises(ValueError):
            ReverseStressInput(
                portfolio=portfolio,
                target_loss_pct=Decimal("1.0"),
                scenario_id="REV_100PCT",
                scenario_name="Test",
                scenario_type="REVERSE",
                scenario_source="MANAGER_DEFINED",
                description="Test",
            )
