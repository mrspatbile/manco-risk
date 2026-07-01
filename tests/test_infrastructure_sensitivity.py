"""Tests for infrastructure asset sensitivity analytics.

Covers models, engine, and realistic scenarios.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.private_assets import (
    InfrastructureSensitivityEngine,
    InfrastructureSensitivityInput,
    InfrastructureSensitivityResult,
)


class TestInfrastructureSensitivityInput:
    """Test InfrastructureSensitivityInput model."""

    def test_valid_sensitivity_input(self) -> None:
        """Valid infrastructure sensitivity input."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("7.5"),
            inflation_sensitivity=Decimal("0.75"),
        )

        assert asset.valuation_date == date(2024, 6, 30)
        assert asset.duration_years == Decimal("7.5")
        assert asset.inflation_sensitivity == Decimal("0.75")
        assert asset.asset_id is None
        assert asset.interest_rate_sensitivity is None
        assert asset.methodology_version is None

    def test_sensitivity_with_all_fields(self) -> None:
        """Infrastructure sensitivity with all fields supplied."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("5.0"),
            inflation_sensitivity=Decimal("0.65"),
            asset_id="TOLL_ROAD_001",
            interest_rate_sensitivity=Decimal("-2.50"),
            methodology_version="SENSITIVITY_v1.0",
        )

        assert asset.asset_id == "TOLL_ROAD_001"
        assert asset.interest_rate_sensitivity == Decimal("-2.50")
        assert asset.methodology_version == "SENSITIVITY_v1.0"

    def test_zero_duration_allowed(self) -> None:
        """Zero duration is allowed (instantaneous cash flow)."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("0"),
            inflation_sensitivity=Decimal("0.50"),
        )

        assert asset.duration_years == Decimal("0")

    def test_long_duration_allowed(self) -> None:
        """Long-duration asset (30+ years) is allowed."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("30.5"),
            inflation_sensitivity=Decimal("0.80"),
        )

        assert asset.duration_years == Decimal("30.5")

    def test_positive_inflation_sensitivity(self) -> None:
        """Positive inflation sensitivity (asset benefits from inflation)."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("10.0"),
            inflation_sensitivity=Decimal("0.90"),
        )

        assert asset.inflation_sensitivity == Decimal("0.90")
        assert asset.inflation_sensitivity > 0

    def test_negative_inflation_sensitivity(self) -> None:
        """Negative inflation sensitivity (asset hurt by inflation)."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("5.0"),
            inflation_sensitivity=Decimal("-0.30"),
        )

        assert asset.inflation_sensitivity == Decimal("-0.30")
        assert asset.inflation_sensitivity < 0

    def test_zero_inflation_sensitivity(self) -> None:
        """Zero inflation sensitivity (inflation neutral)."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("5.0"),
            inflation_sensitivity=Decimal("0"),
        )

        assert asset.inflation_sensitivity == Decimal("0")

    def test_positive_interest_rate_sensitivity(self) -> None:
        """Positive interest rate sensitivity (asset benefits from rate increases)."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("5.0"),
            inflation_sensitivity=Decimal("0.50"),
            interest_rate_sensitivity=Decimal("1.50"),
        )

        assert asset.interest_rate_sensitivity == Decimal("1.50")

    def test_negative_interest_rate_sensitivity(self) -> None:
        """Negative interest rate sensitivity (asset hurt by rate increases)."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("10.0"),
            inflation_sensitivity=Decimal("0.60"),
            interest_rate_sensitivity=Decimal("-3.25"),
        )

        assert asset.interest_rate_sensitivity == Decimal("-3.25")

    def test_negative_duration_rejected(self) -> None:
        """Negative duration is rejected."""
        with pytest.raises(ValueError, match="duration_years must be non-negative"):
            InfrastructureSensitivityInput(
                valuation_date=date(2024, 6, 30),
                duration_years=Decimal("-5.0"),
                inflation_sensitivity=Decimal("0.50"),
            )

    def test_decimal_precision_preserved(self) -> None:
        """Decimal precision is preserved exactly."""
        duration = Decimal("7.123456")
        inflation = Decimal("0.789123")
        interest_rate = Decimal("-2.456789")

        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=duration,
            inflation_sensitivity=inflation,
            interest_rate_sensitivity=interest_rate,
        )

        assert asset.duration_years == duration
        assert asset.inflation_sensitivity == inflation
        assert asset.interest_rate_sensitivity == interest_rate


class TestInfrastructureSensitivityResult:
    """Test InfrastructureSensitivityResult model."""

    def test_valid_result_with_required_fields(self) -> None:
        """Valid result with required fields."""
        result = InfrastructureSensitivityResult(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("7.5"),
            inflation_sensitivity=Decimal("0.75"),
        )

        assert result.valuation_date == date(2024, 6, 30)
        assert result.duration_years == Decimal("7.5")
        assert result.inflation_sensitivity == Decimal("0.75")

    def test_result_with_all_fields(self) -> None:
        """Result with all fields populated."""
        result = InfrastructureSensitivityResult(
            asset_id="TOLL_ROAD_NORTH",
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("8.0"),
            inflation_sensitivity=Decimal("0.80"),
            interest_rate_sensitivity=Decimal("-2.75"),
            methodology_version="SENSITIVITY_v2.0",
        )

        assert result.asset_id == "TOLL_ROAD_NORTH"
        assert result.interest_rate_sensitivity == Decimal("-2.75")
        assert result.methodology_version == "SENSITIVITY_v2.0"

    def test_negative_duration_rejected(self) -> None:
        """Negative duration is rejected."""
        with pytest.raises(ValueError, match="duration_years must be non-negative"):
            InfrastructureSensitivityResult(
                valuation_date=date(2024, 6, 30),
                duration_years=Decimal("-5.0"),
                inflation_sensitivity=Decimal("0.50"),
            )

    def test_decimal_precision_preserved(self) -> None:
        """Decimal precision is preserved exactly."""
        duration = Decimal("12.345678")
        inflation = Decimal("0.567890")

        result = InfrastructureSensitivityResult(
            valuation_date=date(2024, 6, 30),
            duration_years=duration,
            inflation_sensitivity=inflation,
        )

        assert result.duration_years == duration
        assert result.inflation_sensitivity == inflation


class TestInfrastructureSensitivityEngine:
    """Test InfrastructureSensitivityEngine."""

    def test_analyze_passes_through_values(self) -> None:
        """Engine packages input values into result without modification."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("7.5"),
            inflation_sensitivity=Decimal("0.75"),
        )

        result = InfrastructureSensitivityEngine.analyze(asset)

        assert result.valuation_date == asset.valuation_date
        assert result.duration_years == asset.duration_years
        assert result.inflation_sensitivity == asset.inflation_sensitivity

    def test_analyze_with_all_fields(self) -> None:
        """Engine packages all fields including optional ones."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("6.0"),
            inflation_sensitivity=Decimal("0.65"),
            asset_id="WIND_FARM_WEST",
            interest_rate_sensitivity=Decimal("-1.50"),
            methodology_version="SENSITIVITY_v1.5",
        )

        result = InfrastructureSensitivityEngine.analyze(asset)

        assert result.asset_id == "WIND_FARM_WEST"
        assert result.interest_rate_sensitivity == Decimal("-1.50")
        assert result.methodology_version == "SENSITIVITY_v1.5"

    def test_analyze_with_zero_duration(self) -> None:
        """Engine handles zero duration correctly."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("0"),
            inflation_sensitivity=Decimal("0.50"),
        )

        result = InfrastructureSensitivityEngine.analyze(asset)

        assert result.duration_years == Decimal("0")

    def test_analyze_with_negative_sensitivities(self) -> None:
        """Engine handles negative sensitivity values."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("10.0"),
            inflation_sensitivity=Decimal("-0.40"),
            interest_rate_sensitivity=Decimal("-3.00"),
        )

        result = InfrastructureSensitivityEngine.analyze(asset)

        assert result.inflation_sensitivity == Decimal("-0.40")
        assert result.interest_rate_sensitivity == Decimal("-3.00")

    def test_analyze_preserves_decimal_precision(self) -> None:
        """Engine preserves Decimal precision exactly."""
        duration = Decimal("8.765432")
        inflation = Decimal("0.654321")
        interest_rate = Decimal("-2.345678")

        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=duration,
            inflation_sensitivity=inflation,
            interest_rate_sensitivity=interest_rate,
        )

        result = InfrastructureSensitivityEngine.analyze(asset)

        assert result.duration_years == duration
        assert result.inflation_sensitivity == inflation
        assert result.interest_rate_sensitivity == interest_rate


class TestRealisticExamples:
    """Realistic infrastructure asset sensitivity scenarios."""

    def test_toll_road_typical_sensitivity(self) -> None:
        """Toll road with moderate duration and inflation sensitivity."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("8.5"),
            inflation_sensitivity=Decimal("0.85"),
            asset_id="TOLL_ROAD_REGION_A",
            interest_rate_sensitivity=Decimal("-2.10"),
            methodology_version="DURATION_v1.2",
        )

        result = InfrastructureSensitivityEngine.analyze(asset)

        assert result.duration_years == Decimal("8.5")
        assert result.inflation_sensitivity == Decimal("0.85")
        assert result.interest_rate_sensitivity == Decimal("-2.10")
        assert result.asset_id == "TOLL_ROAD_REGION_A"

    def test_regulated_utility_long_duration(self) -> None:
        """Regulated utility with long duration and moderate inflation sensitivity."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("15.0"),
            inflation_sensitivity=Decimal("0.70"),
            asset_id="UTILITY_WATER_CENTRAL",
            interest_rate_sensitivity=Decimal("-4.50"),
            methodology_version="DURATION_v1.1",
        )

        result = InfrastructureSensitivityEngine.analyze(asset)

        assert result.duration_years == Decimal("15.0")
        assert result.duration_years > Decimal("12.0")
        assert result.inflation_sensitivity == Decimal("0.70")
        assert result.interest_rate_sensitivity == Decimal("-4.50")

    def test_renewable_energy_moderate_sensitivity(self) -> None:
        """Renewable energy project with moderate duration and positive inflation sensitivity."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("12.5"),
            inflation_sensitivity=Decimal("0.95"),
            asset_id="WIND_FARM_NORTH",
            interest_rate_sensitivity=Decimal("-3.25"),
        )

        result = InfrastructureSensitivityEngine.analyze(asset)

        assert result.duration_years == Decimal("12.5")
        assert result.inflation_sensitivity == Decimal("0.95")
        assert result.interest_rate_sensitivity == Decimal("-3.25")

    def test_short_duration_fixed_income_asset(self) -> None:
        """Infrastructure bond with short duration and low inflation sensitivity."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("2.5"),
            inflation_sensitivity=Decimal("0.25"),
            asset_id="BOND_SHORT_TERM",
            interest_rate_sensitivity=Decimal("-2.50"),
        )

        result = InfrastructureSensitivityEngine.analyze(asset)

        assert result.duration_years == Decimal("2.5")
        assert result.duration_years < Decimal("5.0")
        assert result.inflation_sensitivity == Decimal("0.25")

    def test_inflation_hedging_asset(self) -> None:
        """Infrastructure asset designed as inflation hedge (high inflation sensitivity)."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("10.0"),
            inflation_sensitivity=Decimal("1.20"),
            asset_id="INFLATION_HEDGE_INFRA",
            interest_rate_sensitivity=Decimal("-1.50"),
        )

        result = InfrastructureSensitivityEngine.analyze(asset)

        assert result.inflation_sensitivity == Decimal("1.20")
        assert result.inflation_sensitivity > Decimal("1.0")
        assert result.interest_rate_sensitivity == Decimal("-1.50")

    def test_inflation_insensitive_asset(self) -> None:
        """Infrastructure asset with minimal inflation sensitivity (neutral)."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("7.0"),
            inflation_sensitivity=Decimal("0.05"),
            asset_id="INFLATION_NEUTRAL",
            interest_rate_sensitivity=Decimal("-3.75"),
        )

        result = InfrastructureSensitivityEngine.analyze(asset)

        assert result.inflation_sensitivity == Decimal("0.05")
        assert result.inflation_sensitivity < Decimal("0.10")

    def test_negative_inflation_sensitivity_asset(self) -> None:
        """Infrastructure asset hurt by inflation (short contract, fixed cash flows)."""
        asset = InfrastructureSensitivityInput(
            valuation_date=date(2024, 6, 30),
            duration_years=Decimal("3.0"),
            inflation_sensitivity=Decimal("-0.45"),
            asset_id="FIXED_INCOME_INFRA",
            interest_rate_sensitivity=Decimal("-3.00"),
        )

        result = InfrastructureSensitivityEngine.analyze(asset)

        assert result.inflation_sensitivity == Decimal("-0.45")
        assert result.inflation_sensitivity < 0
