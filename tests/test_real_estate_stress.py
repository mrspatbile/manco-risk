"""Tests for real estate stress analysis.

Covers models, engine, and realistic scenarios.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.private_assets import (
    RealEstateStressEngine,
    RealEstateStressInput,
    RealEstateStressResult,
)


class TestRealEstateStressInput:
    """Test RealEstateStressInput model."""

    def test_valid_stress_input(self) -> None:
        """Valid real estate stress input."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("5000000"),
            debt_outstanding=Decimal("3000000"),
            rental_income=Decimal("500000"),
            operating_expenses=Decimal("150000"),
            value_shock=Decimal("-0.20"),
            rental_income_shock=Decimal("-0.15"),
        )

        assert property_data.valuation_date == date(2024, 6, 30)
        assert property_data.property_value == Decimal("5000000")
        assert property_data.debt_outstanding == Decimal("3000000")
        assert property_data.rental_income == Decimal("500000")
        assert property_data.operating_expenses == Decimal("150000")
        assert property_data.value_shock == Decimal("-0.20")
        assert property_data.rental_income_shock == Decimal("-0.15")
        assert property_data.expense_shock == Decimal("0")

    def test_stress_input_with_all_fields(self) -> None:
        """Stress input with all fields including optional ones."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("2000000"),
            debt_outstanding=Decimal("1000000"),
            rental_income=Decimal("300000"),
            operating_expenses=Decimal("100000"),
            value_shock=Decimal("-0.15"),
            rental_income_shock=Decimal("-0.10"),
            expense_shock=Decimal("0.05"),
            property_id="OFFICE_BUILDING_001",
            methodology_version="STRESS_v1.0",
        )

        assert property_data.property_id == "OFFICE_BUILDING_001"
        assert property_data.expense_shock == Decimal("0.05")
        assert property_data.methodology_version == "STRESS_v1.0"

    def test_positive_value_shock(self) -> None:
        """Positive property value shock allowed."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("1000000"),
            debt_outstanding=Decimal("500000"),
            rental_income=Decimal("100000"),
            operating_expenses=Decimal("30000"),
            value_shock=Decimal("0.10"),
            rental_income_shock=Decimal("0.05"),
        )

        assert property_data.value_shock == Decimal("0.10")

    def test_negative_rental_income_shock(self) -> None:
        """Negative rental income shock allowed."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("1000000"),
            debt_outstanding=Decimal("500000"),
            rental_income=Decimal("100000"),
            operating_expenses=Decimal("30000"),
            value_shock=Decimal("0"),
            rental_income_shock=Decimal("-0.25"),
        )

        assert property_data.rental_income_shock == Decimal("-0.25")

    def test_negative_property_value_rejected(self) -> None:
        """Negative property value is rejected."""
        with pytest.raises(ValueError, match="property_value must be non-negative"):
            RealEstateStressInput(
                valuation_date=date(2024, 6, 30),
                property_value=Decimal("-1000000"),
                debt_outstanding=Decimal("500000"),
                rental_income=Decimal("100000"),
                operating_expenses=Decimal("30000"),
                value_shock=Decimal("0"),
                rental_income_shock=Decimal("0"),
            )

    def test_negative_debt_rejected(self) -> None:
        """Negative debt outstanding is rejected."""
        with pytest.raises(ValueError, match="debt_outstanding must be non-negative"):
            RealEstateStressInput(
                valuation_date=date(2024, 6, 30),
                property_value=Decimal("1000000"),
                debt_outstanding=Decimal("-500000"),
                rental_income=Decimal("100000"),
                operating_expenses=Decimal("30000"),
                value_shock=Decimal("0"),
                rental_income_shock=Decimal("0"),
            )

    def test_negative_rental_income_rejected(self) -> None:
        """Negative rental income is rejected."""
        with pytest.raises(ValueError, match="rental_income must be non-negative"):
            RealEstateStressInput(
                valuation_date=date(2024, 6, 30),
                property_value=Decimal("1000000"),
                debt_outstanding=Decimal("500000"),
                rental_income=Decimal("-100000"),
                operating_expenses=Decimal("30000"),
                value_shock=Decimal("0"),
                rental_income_shock=Decimal("0"),
            )

    def test_negative_operating_expenses_rejected(self) -> None:
        """Negative operating expenses are rejected."""
        with pytest.raises(ValueError, match="operating_expenses must be non-negative"):
            RealEstateStressInput(
                valuation_date=date(2024, 6, 30),
                property_value=Decimal("1000000"),
                debt_outstanding=Decimal("500000"),
                rental_income=Decimal("100000"),
                operating_expenses=Decimal("-30000"),
                value_shock=Decimal("0"),
                rental_income_shock=Decimal("0"),
            )

    def test_zero_values_allowed(self) -> None:
        """Zero values for property value, debt, rental income, expenses allowed."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("0"),
            debt_outstanding=Decimal("0"),
            rental_income=Decimal("0"),
            operating_expenses=Decimal("0"),
            value_shock=Decimal("0"),
            rental_income_shock=Decimal("0"),
        )

        assert property_data.property_value == Decimal("0")
        assert property_data.debt_outstanding == Decimal("0")

    def test_decimal_precision_preserved(self) -> None:
        """Decimal precision is preserved exactly."""
        prop_value = Decimal("1234567.89")
        debt = Decimal("987654.32")
        rental = Decimal("123456.78")
        expenses = Decimal("45678.90")
        shock = Decimal("-0.123456")

        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=prop_value,
            debt_outstanding=debt,
            rental_income=rental,
            operating_expenses=expenses,
            value_shock=shock,
            rental_income_shock=Decimal("0.05"),
        )

        assert property_data.property_value == prop_value
        assert property_data.debt_outstanding == debt
        assert property_data.value_shock == shock


class TestRealEstateStressResult:
    """Test RealEstateStressResult model."""

    def test_valid_stress_result(self) -> None:
        """Valid real estate stress result."""
        result = RealEstateStressResult(
            valuation_date=date(2024, 6, 30),
            stressed_property_value=Decimal("4000000"),
            stressed_rental_income=Decimal("425000"),
            stressed_operating_expenses=Decimal("150000"),
            stressed_noi=Decimal("275000"),
            stressed_ltv=Decimal("0.75"),
            debt_outstanding=Decimal("3000000"),
        )

        assert result.stressed_property_value == Decimal("4000000")
        assert result.stressed_noi == Decimal("275000")
        assert result.stressed_ltv == Decimal("0.75")

    def test_result_with_none_ltv(self) -> None:
        """Result with None stressed LTV (zero property value)."""
        result = RealEstateStressResult(
            valuation_date=date(2024, 6, 30),
            stressed_property_value=Decimal("0"),
            stressed_rental_income=Decimal("0"),
            stressed_operating_expenses=Decimal("100000"),
            stressed_noi=Decimal("-100000"),
            stressed_ltv=None,
            debt_outstanding=Decimal("1000000"),
        )

        assert result.stressed_property_value == Decimal("0")
        assert result.stressed_ltv is None

    def test_negative_stressed_values_rejected(self) -> None:
        """Negative stressed values rejected."""
        with pytest.raises(ValueError, match="stressed_property_value must be non-negative"):
            RealEstateStressResult(
                valuation_date=date(2024, 6, 30),
                stressed_property_value=Decimal("-1000000"),
                stressed_rental_income=Decimal("100000"),
                stressed_operating_expenses=Decimal("30000"),
                stressed_noi=Decimal("70000"),
                stressed_ltv=None,
                debt_outstanding=Decimal("500000"),
            )

    def test_decimal_precision_preserved(self) -> None:
        """Decimal precision is preserved exactly."""
        prop_val = Decimal("1234567.89")
        rental = Decimal("234567.89")
        expenses = Decimal("123456.78")
        noi = Decimal("111111.11")
        ltv = Decimal("0.456789")

        result = RealEstateStressResult(
            valuation_date=date(2024, 6, 30),
            stressed_property_value=prop_val,
            stressed_rental_income=rental,
            stressed_operating_expenses=expenses,
            stressed_noi=noi,
            stressed_ltv=ltv,
            debt_outstanding=Decimal("500000"),
        )

        assert result.stressed_property_value == prop_val
        assert result.stressed_noi == noi
        assert result.stressed_ltv == ltv


class TestRealEstateStressEngine:
    """Test RealEstateStressEngine calculation logic."""

    def test_typical_property_stress(self) -> None:
        """Typical property stress with negative shocks."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("5000000"),
            debt_outstanding=Decimal("3000000"),
            rental_income=Decimal("500000"),
            operating_expenses=Decimal("150000"),
            value_shock=Decimal("-0.20"),
            rental_income_shock=Decimal("-0.15"),
            property_id="OFFICE_TOWER_001",
        )

        result = RealEstateStressEngine.analyze(property_data)

        assert result.stressed_property_value == Decimal("4000000")
        assert result.stressed_rental_income == Decimal("425000")
        assert result.stressed_operating_expenses == Decimal("150000")
        assert result.stressed_noi == Decimal("275000")
        assert result.stressed_ltv == Decimal("0.75")
        assert result.property_id == "OFFICE_TOWER_001"

    def test_positive_value_shock(self) -> None:
        """Property appreciation scenario (positive value shock)."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("2000000"),
            debt_outstanding=Decimal("1000000"),
            rental_income=Decimal("200000"),
            operating_expenses=Decimal("60000"),
            value_shock=Decimal("0.10"),
            rental_income_shock=Decimal("0.05"),
        )

        result = RealEstateStressEngine.analyze(property_data)

        assert result.stressed_property_value == Decimal("2200000")
        assert result.stressed_rental_income == Decimal("210000")
        assert result.stressed_ltv == Decimal("1000000") / Decimal("2200000")
        assert result.stressed_ltv < Decimal("0.50")

    def test_zero_stressed_property_value(self) -> None:
        """Severe property value shock resulting in zero value."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("1000000"),
            debt_outstanding=Decimal("500000"),
            rental_income=Decimal("100000"),
            operating_expenses=Decimal("30000"),
            value_shock=Decimal("-1.0"),
            rental_income_shock=Decimal("0"),
        )

        result = RealEstateStressEngine.analyze(property_data)

        assert result.stressed_property_value == Decimal("0")
        assert result.stressed_ltv is None

    def test_negative_stressed_noi(self) -> None:
        """Operating loss scenario (expenses exceed stressed rental income)."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("1000000"),
            debt_outstanding=Decimal("500000"),
            rental_income=Decimal("100000"),
            operating_expenses=Decimal("80000"),
            value_shock=Decimal("-0.10"),
            rental_income_shock=Decimal("-0.50"),
            expense_shock=Decimal("0.20"),
        )

        result = RealEstateStressEngine.analyze(property_data)

        assert result.stressed_rental_income == Decimal("50000")
        assert result.stressed_operating_expenses == Decimal("96000")
        assert result.stressed_noi == Decimal("-46000")
        assert result.stressed_noi < 0

    def test_zero_debt_outstanding(self) -> None:
        """Unlevered property (zero debt)."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("2000000"),
            debt_outstanding=Decimal("0"),
            rental_income=Decimal("200000"),
            operating_expenses=Decimal("60000"),
            value_shock=Decimal("-0.15"),
            rental_income_shock=Decimal("-0.10"),
        )

        result = RealEstateStressEngine.analyze(property_data)

        assert result.stressed_ltv == Decimal("0")

    def test_default_expense_shock(self) -> None:
        """Default expense shock of zero used when not supplied."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("1000000"),
            debt_outstanding=Decimal("500000"),
            rental_income=Decimal("100000"),
            operating_expenses=Decimal("30000"),
            value_shock=Decimal("0"),
            rental_income_shock=Decimal("0"),
        )

        result = RealEstateStressEngine.analyze(property_data)

        assert result.stressed_operating_expenses == Decimal("30000")

    def test_decimal_precision_in_calculations(self) -> None:
        """Decimal precision is preserved in all calculations."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("3"),
            debt_outstanding=Decimal("1"),
            rental_income=Decimal("1"),
            operating_expenses=Decimal("0"),
            value_shock=Decimal("-0.5"),
            rental_income_shock=Decimal("0"),
        )

        result = RealEstateStressEngine.analyze(property_data)

        assert result.stressed_property_value == Decimal("1.5")
        assert result.stressed_ltv == Decimal("1") / Decimal("1.5")
        assert result.stressed_ltv == Decimal("2") / Decimal("3")


class TestRealisticExamples:
    """Realistic real estate stress scenarios."""

    def test_office_building_downturn(self) -> None:
        """Office building in market downturn."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("10000000"),
            debt_outstanding=Decimal("6000000"),
            rental_income=Decimal("800000"),
            operating_expenses=Decimal("240000"),
            value_shock=Decimal("-0.25"),
            rental_income_shock=Decimal("-0.20"),
            expense_shock=Decimal("0.10"),
            property_id="OFFICE_TOWER_MID_CITY",
            methodology_version="STRESS_v1.0",
        )

        result = RealEstateStressEngine.analyze(property_data)

        assert result.stressed_property_value == Decimal("7500000")
        assert result.stressed_rental_income == Decimal("640000")
        assert result.stressed_operating_expenses == Decimal("264000")
        assert result.stressed_noi == Decimal("376000")
        assert result.stressed_ltv == Decimal("0.8")

    def test_retail_property_stress(self) -> None:
        """Retail property under e-commerce pressure."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("5000000"),
            debt_outstanding=Decimal("3500000"),
            rental_income=Decimal("400000"),
            operating_expenses=Decimal("120000"),
            value_shock=Decimal("-0.30"),
            rental_income_shock=Decimal("-0.35"),
            expense_shock=Decimal("0.15"),
            property_id="SHOPPING_CENTER_SUBURBAN",
        )

        result = RealEstateStressEngine.analyze(property_data)

        assert result.stressed_property_value == Decimal("3500000")
        assert result.stressed_rental_income == Decimal("260000")
        assert result.stressed_operating_expenses == Decimal("138000")
        assert result.stressed_noi == Decimal("122000")
        assert result.stressed_ltv == Decimal("1.0")

    def test_residential_property_appreciation(self) -> None:
        """Residential property in appreciating market."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("1500000"),
            debt_outstanding=Decimal("800000"),
            rental_income=Decimal("120000"),
            operating_expenses=Decimal("36000"),
            value_shock=Decimal("0.15"),
            rental_income_shock=Decimal("0.05"),
            property_id="APARTMENT_COMPLEX_URBAN",
        )

        result = RealEstateStressEngine.analyze(property_data)

        assert result.stressed_property_value == Decimal("1725000")
        assert result.stressed_rental_income == Decimal("126000")
        assert result.stressed_operating_expenses == Decimal("36000")
        assert result.stressed_noi == Decimal("90000")
        assert result.stressed_ltv == Decimal("800000") / Decimal("1725000")
        assert result.stressed_ltv < Decimal("0.50")

    def test_industrial_property_moderate_stress(self) -> None:
        """Industrial property with moderate stress."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("8000000"),
            debt_outstanding=Decimal("4000000"),
            rental_income=Decimal("600000"),
            operating_expenses=Decimal("150000"),
            value_shock=Decimal("-0.10"),
            rental_income_shock=Decimal("-0.08"),
            property_id="WAREHOUSE_DISTRIBUTION_CENTER",
        )

        result = RealEstateStressEngine.analyze(property_data)

        assert result.stressed_property_value == Decimal("7200000")
        assert result.stressed_rental_income == Decimal("552000")
        assert result.stressed_operating_expenses == Decimal("150000")
        assert result.stressed_noi == Decimal("402000")
        assert result.stressed_ltv == Decimal("4000000") / Decimal("7200000")
        assert result.stressed_ltv < Decimal("0.60")

    def test_hotel_stress_scenario(self) -> None:
        """Hotel property under demand shock."""
        property_data = RealEstateStressInput(
            valuation_date=date(2024, 6, 30),
            property_value=Decimal("6000000"),
            debt_outstanding=Decimal("4000000"),
            rental_income=Decimal("900000"),
            operating_expenses=Decimal("400000"),
            value_shock=Decimal("-0.20"),
            rental_income_shock=Decimal("-0.40"),
            expense_shock=Decimal("-0.10"),
            property_id="BOUTIQUE_HOTEL_DOWNTOWN",
        )

        result = RealEstateStressEngine.analyze(property_data)

        assert result.stressed_property_value == Decimal("4800000")
        assert result.stressed_rental_income == Decimal("540000")
        assert result.stressed_operating_expenses == Decimal("360000")
        assert result.stressed_noi == Decimal("180000")
        assert result.stressed_ltv == Decimal("4000000") / Decimal("4800000")
        assert result.stressed_ltv == Decimal("5") / Decimal("6")
