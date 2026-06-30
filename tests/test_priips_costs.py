"""Tests for PRIIPs Costs engine.

Tests the PRIIPSCostsEngine against realistic cost data and validation
requirements from Commission Delegated Regulation (EU) 2017/653 Annex VI/VII.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.priips import (
    COST_TYPES,
    RHP_MIN_YEARS,
    PRIIPSCostsEngine,
    PRIIPSCostsInput,
)


class TestPRIIPSCostsEngineBasic:
    """Test basic engine functionality."""

    def test_valid_cost_output(self):
        """Engine accepts valid cost input and returns result."""
        input_data = PRIIPSCostsInput(
            product_id="UCITS_BALANCED",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=5,
            entry_cost=Decimal("0.01"),
            exit_cost=Decimal("0.005"),
            ongoing_cost=Decimal("0.005"),
            transaction_cost=Decimal("0.001"),
            incidental_cost=Decimal("0.0"),
        )
        result = PRIIPSCostsEngine.calculate(input_data)

        assert result.product_id == "UCITS_BALANCED"
        assert result.valuation_date == date(2026, 7, 1)
        assert result.methodology_version == "2017/653"
        assert result.recommended_holding_period_years == 5

    def test_decimal_preservation_all_costs(self):
        """Decimal precision preserved for all cost values."""
        input_data = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            entry_cost=Decimal("0.00125"),
            exit_cost=Decimal("0.00250"),
            ongoing_cost=Decimal("0.00750"),
            transaction_cost=Decimal("0.00033"),
            incidental_cost=Decimal("0.00001"),
        )
        result = PRIIPSCostsEngine.calculate(input_data)

        assert result.entry_cost == Decimal("0.00125")
        assert result.exit_cost == Decimal("0.00250")
        assert result.ongoing_cost == Decimal("0.00750")
        assert result.transaction_cost == Decimal("0.00033")
        assert result.incidental_cost == Decimal("0.00001")

    def test_zero_costs_handled(self):
        """Zero costs are preserved."""
        input_data = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            entry_cost=Decimal("0"),
            exit_cost=Decimal("0"),
            ongoing_cost=Decimal("0"),
            transaction_cost=Decimal("0"),
            incidental_cost=Decimal("0"),
        )
        result = PRIIPSCostsEngine.calculate(input_data)

        assert result.entry_cost == Decimal("0")
        assert result.exit_cost == Decimal("0")
        assert result.ongoing_cost == Decimal("0")
        assert result.transaction_cost == Decimal("0")
        assert result.incidental_cost == Decimal("0")

    def test_positive_costs_handled(self):
        """Positive costs are preserved correctly."""
        input_data = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=3,
            entry_cost=Decimal("0.02"),
            exit_cost=Decimal("0.01"),
            ongoing_cost=Decimal("0.01"),
            transaction_cost=Decimal("0.002"),
            incidental_cost=Decimal("0.0005"),
        )
        result = PRIIPSCostsEngine.calculate(input_data)

        assert result.entry_cost == Decimal("0.02")
        assert result.exit_cost == Decimal("0.01")
        assert result.ongoing_cost == Decimal("0.01")
        assert result.transaction_cost == Decimal("0.002")
        assert result.incidental_cost == Decimal("0.0005")


class TestInputValidation:
    """Test input validation."""

    def test_product_id_empty_string_rejected(self):
        """Empty product_id is rejected."""
        with pytest.raises(ValueError, match="product_id must be non-empty"):
            PRIIPSCostsInput(
                product_id="",
                valuation_date=date(2026, 7, 1),
                methodology_version="2017/653",
                recommended_holding_period_years=1,
                entry_cost=Decimal("0"),
                exit_cost=Decimal("0"),
                ongoing_cost=Decimal("0"),
                transaction_cost=Decimal("0"),
                incidental_cost=Decimal("0"),
            )

    def test_product_id_whitespace_only_rejected(self):
        """Whitespace-only product_id is rejected."""
        with pytest.raises(ValueError, match="product_id must be non-empty"):
            PRIIPSCostsInput(
                product_id="   ",
                valuation_date=date(2026, 7, 1),
                methodology_version="2017/653",
                recommended_holding_period_years=1,
                entry_cost=Decimal("0"),
                exit_cost=Decimal("0"),
                ongoing_cost=Decimal("0"),
                transaction_cost=Decimal("0"),
                incidental_cost=Decimal("0"),
            )

    def test_methodology_version_empty_string_rejected(self):
        """Empty methodology_version is rejected."""
        with pytest.raises(ValueError, match="methodology_version must be non-empty"):
            PRIIPSCostsInput(
                product_id="TEST",
                valuation_date=date(2026, 7, 1),
                methodology_version="",
                recommended_holding_period_years=1,
                entry_cost=Decimal("0"),
                exit_cost=Decimal("0"),
                ongoing_cost=Decimal("0"),
                transaction_cost=Decimal("0"),
                incidental_cost=Decimal("0"),
            )

    def test_methodology_version_whitespace_only_rejected(self):
        """Whitespace-only methodology_version is rejected."""
        with pytest.raises(ValueError, match="methodology_version must be non-empty"):
            PRIIPSCostsInput(
                product_id="TEST",
                valuation_date=date(2026, 7, 1),
                methodology_version="   ",
                recommended_holding_period_years=1,
                entry_cost=Decimal("0"),
                exit_cost=Decimal("0"),
                ongoing_cost=Decimal("0"),
                transaction_cost=Decimal("0"),
                incidental_cost=Decimal("0"),
            )

    def test_recommended_holding_period_zero_rejected(self):
        """RHP = 0 is rejected."""
        with pytest.raises(ValueError, match="recommended_holding_period_years must be positive"):
            PRIIPSCostsInput(
                product_id="TEST",
                valuation_date=date(2026, 7, 1),
                methodology_version="2017/653",
                recommended_holding_period_years=0,
                entry_cost=Decimal("0"),
                exit_cost=Decimal("0"),
                ongoing_cost=Decimal("0"),
                transaction_cost=Decimal("0"),
                incidental_cost=Decimal("0"),
            )

    def test_recommended_holding_period_negative_rejected(self):
        """Negative RHP is rejected."""
        with pytest.raises(ValueError, match="recommended_holding_period_years must be positive"):
            PRIIPSCostsInput(
                product_id="TEST",
                valuation_date=date(2026, 7, 1),
                methodology_version="2017/653",
                recommended_holding_period_years=-1,
                entry_cost=Decimal("0"),
                exit_cost=Decimal("0"),
                ongoing_cost=Decimal("0"),
                transaction_cost=Decimal("0"),
                incidental_cost=Decimal("0"),
            )

    def test_recommended_holding_period_positive_accepted(self):
        """Positive RHP is accepted (1 year minimum)."""
        input_data = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=RHP_MIN_YEARS,
            entry_cost=Decimal("0"),
            exit_cost=Decimal("0"),
            ongoing_cost=Decimal("0"),
            transaction_cost=Decimal("0"),
            incidental_cost=Decimal("0"),
        )
        assert input_data.recommended_holding_period_years == RHP_MIN_YEARS


class TestMethodologyVersionHandling:
    """Test methodology version preservation and flexibility."""

    def test_methodology_version_2017_653_accepted(self):
        """Delegated Regulation 2017/653 methodology accepted."""
        input_data = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=5,
            entry_cost=Decimal("0"),
            exit_cost=Decimal("0"),
            ongoing_cost=Decimal("0"),
            transaction_cost=Decimal("0"),
            incidental_cost=Decimal("0"),
        )
        result = PRIIPSCostsEngine.calculate(input_data)
        assert result.methodology_version == "2017/653"

    def test_methodology_version_2021_2268_accepted(self):
        """Delegated Regulation 2021/2268 methodology accepted."""
        input_data = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2021/2268",
            recommended_holding_period_years=5,
            entry_cost=Decimal("0"),
            exit_cost=Decimal("0"),
            ongoing_cost=Decimal("0"),
            transaction_cost=Decimal("0"),
            incidental_cost=Decimal("0"),
        )
        result = PRIIPSCostsEngine.calculate(input_data)
        assert result.methodology_version == "2021/2268"

    def test_future_methodology_version_accepted(self):
        """Future methodology versions accepted (no hardcoded validation)."""
        input_data = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2030/9999",
            recommended_holding_period_years=5,
            entry_cost=Decimal("0"),
            exit_cost=Decimal("0"),
            ongoing_cost=Decimal("0"),
            transaction_cost=Decimal("0"),
            incidental_cost=Decimal("0"),
        )
        result = PRIIPSCostsEngine.calculate(input_data)
        assert result.methodology_version == "2030/9999"


class TestResultImmutability:
    """Test that PRIIPSCostsResult is immutable."""

    def test_result_is_frozen(self):
        """PRIIPSCostsResult cannot be mutated after creation."""
        input_data = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=3,
            entry_cost=Decimal("0.01"),
            exit_cost=Decimal("0.005"),
            ongoing_cost=Decimal("0.005"),
            transaction_cost=Decimal("0.001"),
            incidental_cost=Decimal("0"),
        )
        result = PRIIPSCostsEngine.calculate(input_data)

        with pytest.raises(Exception):  # Pydantic frozen models raise ValidationError
            result.entry_cost = Decimal("0.02")

    def test_result_is_frozen_product_id(self):
        """PRIIPSCostsResult product_id cannot be mutated."""
        input_data = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=3,
            entry_cost=Decimal("0.01"),
            exit_cost=Decimal("0.005"),
            ongoing_cost=Decimal("0.005"),
            transaction_cost=Decimal("0.001"),
            incidental_cost=Decimal("0"),
        )
        result = PRIIPSCostsEngine.calculate(input_data)

        with pytest.raises(Exception):
            result.product_id = "NEW_PRODUCT"


class TestRealisticExample:
    """Test realistic PRIIPs cost examples."""

    def test_realistic_ucits_balanced_costs(self):
        """Realistic UCITS balanced fund cost breakdown."""
        input_data = PRIIPSCostsInput(
            product_id="UCITS_BALANCED_EUR",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=5,
            entry_cost=Decimal("0.01"),  # 1% entry
            exit_cost=Decimal("0.005"),  # 0.5% exit
            ongoing_cost=Decimal("0.005"),  # 0.5% per year
            transaction_cost=Decimal("0.001"),  # 0.1% transactions
            incidental_cost=Decimal("0.0005"),  # 0.05% incidental
        )
        result = PRIIPSCostsEngine.calculate(input_data)

        assert result.product_id == "UCITS_BALANCED_EUR"
        assert result.entry_cost == Decimal("0.01")
        assert result.ongoing_cost == Decimal("0.005")

    def test_realistic_equity_fund_costs(self):
        """Realistic equity fund cost breakdown."""
        input_data = PRIIPSCostsInput(
            product_id="EQUITY_WORLD",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=7,
            entry_cost=Decimal("0.015"),  # 1.5% entry
            exit_cost=Decimal("0.01"),  # 1% exit
            ongoing_cost=Decimal("0.007"),  # 0.7% per year
            transaction_cost=Decimal("0.002"),  # 0.2% transactions
            incidental_cost=Decimal("0.001"),  # 0.1% incidental
        )
        result = PRIIPSCostsEngine.calculate(input_data)

        assert result.product_id == "EQUITY_WORLD"
        assert result.entry_cost == Decimal("0.015")
        assert result.transaction_cost == Decimal("0.002")

    def test_realistic_bond_fund_costs(self):
        """Realistic bond fund cost breakdown."""
        input_data = PRIIPSCostsInput(
            product_id="BOND_AGGREGATE",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=3,
            entry_cost=Decimal("0.003"),  # 0.3% entry
            exit_cost=Decimal("0.001"),  # 0.1% exit
            ongoing_cost=Decimal("0.0025"),  # 0.25% per year
            transaction_cost=Decimal("0.0005"),  # 0.05% transactions
            incidental_cost=Decimal("0.0001"),  # 0.01% incidental
        )
        result = PRIIPSCostsEngine.calculate(input_data)

        assert result.product_id == "BOND_AGGREGATE"
        assert result.entry_cost == Decimal("0.003")
        assert result.ongoing_cost == Decimal("0.0025")

    def test_zero_cost_product(self):
        """Product with no costs (e.g., passive index fund)."""
        input_data = PRIIPSCostsInput(
            product_id="INDEX_PASSIVE",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=10,
            entry_cost=Decimal("0"),
            exit_cost=Decimal("0"),
            ongoing_cost=Decimal("0.0001"),  # 0.01% per year (minimal)
            transaction_cost=Decimal("0"),
            incidental_cost=Decimal("0"),
        )
        result = PRIIPSCostsEngine.calculate(input_data)

        assert result.entry_cost == Decimal("0")
        assert result.ongoing_cost == Decimal("0.0001")


class TestDeterminism:
    """Test engine determinism."""

    def test_same_input_produces_same_output(self):
        """Same input always produces same output (deterministic)."""
        input_data = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=5,
            entry_cost=Decimal("0.01"),
            exit_cost=Decimal("0.005"),
            ongoing_cost=Decimal("0.005"),
            transaction_cost=Decimal("0.001"),
            incidental_cost=Decimal("0.0005"),
        )
        result1 = PRIIPSCostsEngine.calculate(input_data)
        result2 = PRIIPSCostsEngine.calculate(input_data)

        assert result1.product_id == result2.product_id
        assert result1.entry_cost == result2.entry_cost
        assert result1.exit_cost == result2.exit_cost
        assert result1.ongoing_cost == result2.ongoing_cost
        assert result1.transaction_cost == result2.transaction_cost
        assert result1.incidental_cost == result2.incidental_cost


class TestDecimalCoercion:
    """Test that numeric inputs are coerced to Decimal."""

    def test_float_input_coerced_to_decimal(self):
        """Float input is coerced to Decimal in input model."""
        input_data = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            entry_cost=0.01,  # float
            exit_cost=0.005,  # float
            ongoing_cost=0.005,  # float
            transaction_cost=0.001,  # float
            incidental_cost=0.0,  # float
        )
        result = PRIIPSCostsEngine.calculate(input_data)

        assert isinstance(result.entry_cost, Decimal)
        assert isinstance(result.exit_cost, Decimal)
        assert isinstance(result.ongoing_cost, Decimal)
        assert isinstance(result.transaction_cost, Decimal)
        assert isinstance(result.incidental_cost, Decimal)

    def test_integer_input_coerced_to_decimal(self):
        """Integer input is coerced to Decimal in input model."""
        input_data = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            entry_cost=0,  # int
            exit_cost=0,  # int
            ongoing_cost=1,  # int
            transaction_cost=0,  # int
            incidental_cost=0,  # int
        )
        result = PRIIPSCostsEngine.calculate(input_data)

        assert result.entry_cost == Decimal("0")
        assert result.exit_cost == Decimal("0")
        assert result.ongoing_cost == Decimal("1")
        assert result.transaction_cost == Decimal("0")
        assert result.incidental_cost == Decimal("0")

    def test_string_decimal_coerced(self):
        """String decimal input is coerced to Decimal in input model."""
        input_data = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            entry_cost="0.01",  # string
            exit_cost="0.005",  # string
            ongoing_cost="0.005",  # string
            transaction_cost="0.001",  # string
            incidental_cost="0.0",  # string
        )
        result = PRIIPSCostsEngine.calculate(input_data)

        assert result.entry_cost == Decimal("0.01")
        assert result.exit_cost == Decimal("0.005")
        assert result.ongoing_cost == Decimal("0.005")
        assert result.transaction_cost == Decimal("0.001")
        assert result.incidental_cost == Decimal("0.0")


class TestCostTypes:
    """Test cost type constants."""

    def test_cost_types_enumeration(self):
        """Cost types constant includes all components."""
        assert "entry" in COST_TYPES
        assert "exit" in COST_TYPES
        assert "ongoing" in COST_TYPES
        assert "transaction" in COST_TYPES
        assert "incidental" in COST_TYPES
