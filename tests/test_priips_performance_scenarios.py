"""Tests for PRIIPs Performance Scenarios engine.

Tests the PerformanceScenariosEngine against realistic scenario data
and validation requirements from Commission Delegated Regulation
(EU) 2017/653 Annex IV/V.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.priips import (
    RHP_MIN_YEARS,
    PerformanceScenariosEngine,
    PerformanceScenariosInput,
)


class TestPerformanceScenariosEngineBasic:
    """Test basic engine functionality."""

    def test_valid_scenario_output(self):
        """Engine accepts valid scenario input and returns result."""
        input_data = PerformanceScenariosInput(
            product_id="UCITS_BALANCED",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=5,
            stress_return=Decimal("-0.25"),
            unfavourable_return=Decimal("-0.05"),
            moderate_return=Decimal("0.03"),
            favourable_return=Decimal("0.15"),
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        assert result.product_id == "UCITS_BALANCED"
        assert result.valuation_date == date(2026, 6, 30)
        assert result.methodology_version == "2017/653"
        assert result.recommended_holding_period_years == 5

    def test_decimal_preservation_stress(self):
        """Decimal precision preserved for stress return."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=3,
            stress_return=Decimal("-0.2547"),
            unfavourable_return=Decimal("0"),
            moderate_return=Decimal("0"),
            favourable_return=Decimal("0"),
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        assert result.stress_return == Decimal("-0.2547")
        assert isinstance(result.stress_return, Decimal)

    def test_decimal_preservation_all_scenarios(self):
        """Decimal precision preserved for all scenario returns."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            stress_return=Decimal("-0.25000001"),
            unfavourable_return=Decimal("-0.050"),
            moderate_return=Decimal("0.03500"),
            favourable_return=Decimal("0.150999"),
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        assert result.stress_return == Decimal("-0.25000001")
        assert result.unfavourable_return == Decimal("-0.050")
        assert result.moderate_return == Decimal("0.03500")
        assert result.favourable_return == Decimal("0.150999")

    def test_negative_returns_handled(self):
        """Negative returns (losses) are preserved correctly."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=3,
            stress_return=Decimal("-0.50"),
            unfavourable_return=Decimal("-0.10"),
            moderate_return=Decimal("-0.01"),
            favourable_return=Decimal("0.05"),
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        assert result.stress_return == Decimal("-0.50")
        assert result.unfavourable_return == Decimal("-0.10")
        assert result.moderate_return == Decimal("-0.01")

    def test_zero_returns_handled(self):
        """Zero returns are preserved."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            stress_return=Decimal("0"),
            unfavourable_return=Decimal("0"),
            moderate_return=Decimal("0"),
            favourable_return=Decimal("0"),
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        assert result.stress_return == Decimal("0")
        assert result.unfavourable_return == Decimal("0")
        assert result.moderate_return == Decimal("0")
        assert result.favourable_return == Decimal("0")

    def test_positive_returns_handled(self):
        """Positive returns (gains) are preserved correctly."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=3,
            stress_return=Decimal("0.01"),
            unfavourable_return=Decimal("0.05"),
            moderate_return=Decimal("0.10"),
            favourable_return=Decimal("0.30"),
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        assert result.stress_return == Decimal("0.01")
        assert result.unfavourable_return == Decimal("0.05")
        assert result.moderate_return == Decimal("0.10")
        assert result.favourable_return == Decimal("0.30")


class TestInputValidation:
    """Test input validation."""

    def test_product_id_empty_string_rejected(self):
        """Empty product_id is rejected."""
        with pytest.raises(ValueError, match="product_id must be non-empty"):
            PerformanceScenariosInput(
                product_id="",
                valuation_date=date(2026, 6, 30),
                methodology_version="2017/653",
                recommended_holding_period_years=1,
                stress_return=Decimal("0"),
                unfavourable_return=Decimal("0"),
                moderate_return=Decimal("0"),
                favourable_return=Decimal("0"),
            )

    def test_product_id_whitespace_only_rejected(self):
        """Whitespace-only product_id is rejected."""
        with pytest.raises(ValueError, match="product_id must be non-empty"):
            PerformanceScenariosInput(
                product_id="   ",
                valuation_date=date(2026, 6, 30),
                methodology_version="2017/653",
                recommended_holding_period_years=1,
                stress_return=Decimal("0"),
                unfavourable_return=Decimal("0"),
                moderate_return=Decimal("0"),
                favourable_return=Decimal("0"),
            )

    def test_methodology_version_empty_string_rejected(self):
        """Empty methodology_version is rejected."""
        with pytest.raises(ValueError, match="methodology_version must be non-empty"):
            PerformanceScenariosInput(
                product_id="TEST",
                valuation_date=date(2026, 6, 30),
                methodology_version="",
                recommended_holding_period_years=1,
                stress_return=Decimal("0"),
                unfavourable_return=Decimal("0"),
                moderate_return=Decimal("0"),
                favourable_return=Decimal("0"),
            )

    def test_methodology_version_whitespace_only_rejected(self):
        """Whitespace-only methodology_version is rejected."""
        with pytest.raises(ValueError, match="methodology_version must be non-empty"):
            PerformanceScenariosInput(
                product_id="TEST",
                valuation_date=date(2026, 6, 30),
                methodology_version="   ",
                recommended_holding_period_years=1,
                stress_return=Decimal("0"),
                unfavourable_return=Decimal("0"),
                moderate_return=Decimal("0"),
                favourable_return=Decimal("0"),
            )

    def test_recommended_holding_period_zero_rejected(self):
        """RHP = 0 is rejected."""
        with pytest.raises(ValueError, match="recommended_holding_period_years must be positive"):
            PerformanceScenariosInput(
                product_id="TEST",
                valuation_date=date(2026, 6, 30),
                methodology_version="2017/653",
                recommended_holding_period_years=0,
                stress_return=Decimal("0"),
                unfavourable_return=Decimal("0"),
                moderate_return=Decimal("0"),
                favourable_return=Decimal("0"),
            )

    def test_recommended_holding_period_negative_rejected(self):
        """Negative RHP is rejected."""
        with pytest.raises(ValueError, match="recommended_holding_period_years must be positive"):
            PerformanceScenariosInput(
                product_id="TEST",
                valuation_date=date(2026, 6, 30),
                methodology_version="2017/653",
                recommended_holding_period_years=-1,
                stress_return=Decimal("0"),
                unfavourable_return=Decimal("0"),
                moderate_return=Decimal("0"),
                favourable_return=Decimal("0"),
            )

    def test_recommended_holding_period_positive_accepted(self):
        """Positive RHP is accepted (1 year minimum)."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=RHP_MIN_YEARS,
            stress_return=Decimal("0"),
            unfavourable_return=Decimal("0"),
            moderate_return=Decimal("0"),
            favourable_return=Decimal("0"),
        )
        assert input_data.recommended_holding_period_years == RHP_MIN_YEARS

    def test_recommended_holding_period_large_value_accepted(self):
        """Large RHP values are accepted (no maximum enforced)."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=100,
            stress_return=Decimal("0"),
            unfavourable_return=Decimal("0"),
            moderate_return=Decimal("0"),
            favourable_return=Decimal("0"),
        )
        assert input_data.recommended_holding_period_years == 100


class TestMethodologyVersionHandling:
    """Test methodology version preservation and flexibility."""

    def test_methodology_version_2017_653_accepted(self):
        """Delegated Regulation 2017/653 methodology accepted."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=5,
            stress_return=Decimal("0"),
            unfavourable_return=Decimal("0"),
            moderate_return=Decimal("0"),
            favourable_return=Decimal("0"),
        )
        result = PerformanceScenariosEngine.calculate(input_data)
        assert result.methodology_version == "2017/653"

    def test_methodology_version_2021_2268_accepted(self):
        """Delegated Regulation 2021/2268 methodology accepted."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2021/2268",
            recommended_holding_period_years=5,
            stress_return=Decimal("0"),
            unfavourable_return=Decimal("0"),
            moderate_return=Decimal("0"),
            favourable_return=Decimal("0"),
        )
        result = PerformanceScenariosEngine.calculate(input_data)
        assert result.methodology_version == "2021/2268"

    def test_future_methodology_version_accepted(self):
        """Future methodology versions accepted (no hardcoded validation)."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2030/9999",
            recommended_holding_period_years=5,
            stress_return=Decimal("0"),
            unfavourable_return=Decimal("0"),
            moderate_return=Decimal("0"),
            favourable_return=Decimal("0"),
        )
        result = PerformanceScenariosEngine.calculate(input_data)
        assert result.methodology_version == "2030/9999"


class TestResultImmutability:
    """Test that PerformanceScenariosResult is immutable."""

    def test_result_is_frozen(self):
        """PerformanceScenariosResult cannot be mutated after creation."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=3,
            stress_return=Decimal("-0.25"),
            unfavourable_return=Decimal("-0.05"),
            moderate_return=Decimal("0.03"),
            favourable_return=Decimal("0.15"),
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        with pytest.raises(Exception):  # Pydantic frozen models raise ValidationError
            result.stress_return = Decimal("0")

    def test_result_is_frozen_product_id(self):
        """PerformanceScenariosResult product_id cannot be mutated."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=3,
            stress_return=Decimal("-0.25"),
            unfavourable_return=Decimal("-0.05"),
            moderate_return=Decimal("0.03"),
            favourable_return=Decimal("0.15"),
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        with pytest.raises(Exception):
            result.product_id = "NEW_PRODUCT"

    def test_result_is_frozen_methodology_version(self):
        """PerformanceScenariosResult methodology_version cannot be mutated."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=3,
            stress_return=Decimal("-0.25"),
            unfavourable_return=Decimal("-0.05"),
            moderate_return=Decimal("0.03"),
            favourable_return=Decimal("0.15"),
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        with pytest.raises(Exception):
            result.methodology_version = "2021/2268"


class TestRealisticExample:
    """Test realistic PRIIPs scenario example."""

    def test_realistic_balanced_fund_scenario(self):
        """Realistic UCITS balanced fund scenario."""
        input_data = PerformanceScenariosInput(
            product_id="UCITS_BALANCED_EUR",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=5,
            stress_return=Decimal("-0.247"),  # -24.7%
            unfavourable_return=Decimal("-0.052"),  # -5.2%
            moderate_return=Decimal("0.033"),  # 3.3%
            favourable_return=Decimal("0.162"),  # 16.2%
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        assert result.product_id == "UCITS_BALANCED_EUR"
        assert result.recommended_holding_period_years == 5
        assert result.stress_return == Decimal("-0.247")
        assert result.favourable_return == Decimal("0.162")

    def test_realistic_equity_fund_scenario(self):
        """Realistic equity fund scenario with higher volatility."""
        input_data = PerformanceScenariosInput(
            product_id="EQUITY_WORLD",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=7,
            stress_return=Decimal("-0.486"),  # -48.6% (equity stress)
            unfavourable_return=Decimal("-0.156"),  # -15.6%
            moderate_return=Decimal("0.071"),  # 7.1%
            favourable_return=Decimal("0.347"),  # 34.7%
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        assert result.product_id == "EQUITY_WORLD"
        assert result.stress_return == Decimal("-0.486")
        assert result.moderate_return == Decimal("0.071")

    def test_realistic_bond_fund_scenario(self):
        """Realistic bond fund scenario with lower volatility."""
        input_data = PerformanceScenariosInput(
            product_id="BOND_AGGREGATE",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=3,
            stress_return=Decimal("-0.085"),  # -8.5%
            unfavourable_return=Decimal("-0.021"),  # -2.1%
            moderate_return=Decimal("0.018"),  # 1.8%
            favourable_return=Decimal("0.052"),  # 5.2%
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        assert result.product_id == "BOND_AGGREGATE"
        assert result.stress_return == Decimal("-0.085")
        assert result.favourable_return == Decimal("0.052")


class TestDeterminism:
    """Test engine determinism."""

    def test_same_input_produces_same_output(self):
        """Same input always produces same output (deterministic)."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=5,
            stress_return=Decimal("-0.25"),
            unfavourable_return=Decimal("-0.05"),
            moderate_return=Decimal("0.03"),
            favourable_return=Decimal("0.15"),
        )
        result1 = PerformanceScenariosEngine.calculate(input_data)
        result2 = PerformanceScenariosEngine.calculate(input_data)

        assert result1.product_id == result2.product_id
        assert result1.stress_return == result2.stress_return
        assert result1.unfavourable_return == result2.unfavourable_return
        assert result1.moderate_return == result2.moderate_return
        assert result1.favourable_return == result2.favourable_return


class TestDecimalCoercion:
    """Test that numeric inputs are coerced to Decimal."""

    def test_float_input_coerced_to_decimal(self):
        """Float input is coerced to Decimal in input model."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            stress_return=-0.25,  # float
            unfavourable_return=-0.05,  # float
            moderate_return=0.03,  # float
            favourable_return=0.15,  # float
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        assert isinstance(result.stress_return, Decimal)
        assert isinstance(result.unfavourable_return, Decimal)
        assert isinstance(result.moderate_return, Decimal)
        assert isinstance(result.favourable_return, Decimal)

    def test_integer_input_coerced_to_decimal(self):
        """Integer input is coerced to Decimal in input model."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            stress_return=0,  # int
            unfavourable_return=-1,  # int
            moderate_return=1,  # int
            favourable_return=2,  # int
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        assert result.stress_return == Decimal("0")
        assert result.unfavourable_return == Decimal("-1")
        assert result.moderate_return == Decimal("1")
        assert result.favourable_return == Decimal("2")

    def test_string_decimal_coerced(self):
        """String decimal input is coerced to Decimal in input model."""
        input_data = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            stress_return="-0.25",  # string
            unfavourable_return="-0.05",  # string
            moderate_return="0.03",  # string
            favourable_return="0.15",  # string
        )
        result = PerformanceScenariosEngine.calculate(input_data)

        assert result.stress_return == Decimal("-0.25")
        assert result.unfavourable_return == Decimal("-0.05")
        assert result.moderate_return == Decimal("0.03")
        assert result.favourable_return == Decimal("0.15")
