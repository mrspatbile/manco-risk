"""Tests for infrastructure asset analytics.

Covers models, engine, and realistic scenarios.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.private_assets import (
    InfrastructureAnalyticsResult,
    InfrastructureAssetInput,
    InfrastructureEngine,
)


class TestInfrastructureAssetInput:
    """Test InfrastructureAssetInput model."""

    def test_valid_asset_input(self) -> None:
        """Valid infrastructure asset input."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("500000"),
            debt_service_amount=Decimal("400000"),
            asset_value=Decimal("5000000"),
            debt_outstanding=Decimal("3000000"),
        )

        assert asset.valuation_date == date(2024, 6, 30)
        assert asset.cash_available_for_debt_service == Decimal("500000")
        assert asset.debt_service_amount == Decimal("400000")
        assert asset.asset_value == Decimal("5000000")
        assert asset.debt_outstanding == Decimal("3000000")
        assert asset.asset_id is None

    def test_asset_with_id(self) -> None:
        """Infrastructure asset with optional ID."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("100000"),
            debt_service_amount=Decimal("100000"),
            asset_value=Decimal("1000000"),
            debt_outstanding=Decimal("500000"),
            asset_id="TOLL_ROAD_001",
        )

        assert asset.asset_id == "TOLL_ROAD_001"

    def test_zero_cash_allowed(self) -> None:
        """Zero cash available for debt service is allowed."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("0"),
            debt_service_amount=Decimal("100000"),
            asset_value=Decimal("1000000"),
            debt_outstanding=Decimal("500000"),
        )

        assert asset.cash_available_for_debt_service == Decimal("0")

    def test_zero_debt_service_allowed(self) -> None:
        """Zero debt service amount is allowed."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("100000"),
            debt_service_amount=Decimal("0"),
            asset_value=Decimal("1000000"),
            debt_outstanding=Decimal("500000"),
        )

        assert asset.debt_service_amount == Decimal("0")

    def test_zero_asset_value_allowed(self) -> None:
        """Zero asset value is allowed."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("100000"),
            debt_service_amount=Decimal("100000"),
            asset_value=Decimal("0"),
            debt_outstanding=Decimal("0"),
        )

        assert asset.asset_value == Decimal("0")

    def test_zero_debt_outstanding_allowed(self) -> None:
        """Zero debt outstanding is allowed."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("100000"),
            debt_service_amount=Decimal("100000"),
            asset_value=Decimal("1000000"),
            debt_outstanding=Decimal("0"),
        )

        assert asset.debt_outstanding == Decimal("0")

    def test_negative_cash_rejected(self) -> None:
        """Negative cash available for debt service is rejected."""
        with pytest.raises(
            ValueError, match="cash_available_for_debt_service must be non-negative"
        ):
            InfrastructureAssetInput(
                valuation_date=date(2024, 6, 30),
                cash_available_for_debt_service=Decimal("-100000"),
                debt_service_amount=Decimal("100000"),
                asset_value=Decimal("1000000"),
                debt_outstanding=Decimal("500000"),
            )

    def test_negative_debt_service_rejected(self) -> None:
        """Negative debt service amount is rejected."""
        with pytest.raises(ValueError, match="debt_service_amount must be non-negative"):
            InfrastructureAssetInput(
                valuation_date=date(2024, 6, 30),
                cash_available_for_debt_service=Decimal("100000"),
                debt_service_amount=Decimal("-100000"),
                asset_value=Decimal("1000000"),
                debt_outstanding=Decimal("500000"),
            )

    def test_negative_asset_value_rejected(self) -> None:
        """Negative asset value is rejected."""
        with pytest.raises(ValueError, match="asset_value must be non-negative"):
            InfrastructureAssetInput(
                valuation_date=date(2024, 6, 30),
                cash_available_for_debt_service=Decimal("100000"),
                debt_service_amount=Decimal("100000"),
                asset_value=Decimal("-1000000"),
                debt_outstanding=Decimal("500000"),
            )

    def test_negative_debt_outstanding_rejected(self) -> None:
        """Negative debt outstanding is rejected."""
        with pytest.raises(ValueError, match="debt_outstanding must be non-negative"):
            InfrastructureAssetInput(
                valuation_date=date(2024, 6, 30),
                cash_available_for_debt_service=Decimal("100000"),
                debt_service_amount=Decimal("100000"),
                asset_value=Decimal("1000000"),
                debt_outstanding=Decimal("-500000"),
            )

    def test_decimal_precision_preserved(self) -> None:
        """Decimal precision is preserved exactly."""
        cash = Decimal("123456.789")
        debt_service = Decimal("100000.123")
        asset_value = Decimal("9876543.21")
        debt_out = Decimal("4567890.456")

        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=cash,
            debt_service_amount=debt_service,
            asset_value=asset_value,
            debt_outstanding=debt_out,
        )

        assert asset.cash_available_for_debt_service == cash
        assert asset.debt_service_amount == debt_service
        assert asset.asset_value == asset_value
        assert asset.debt_outstanding == debt_out


class TestInfrastructureAnalyticsResult:
    """Test InfrastructureAnalyticsResult model."""

    def test_valid_result_with_all_metrics(self) -> None:
        """Valid result with all metrics populated."""
        result = InfrastructureAnalyticsResult(
            valuation_date=date(2024, 6, 30),
            dscr=Decimal("1.25"),
            ltv=Decimal("0.60"),
            cash_available_for_debt_service=Decimal("500000"),
            debt_service_amount=Decimal("400000"),
            asset_value=Decimal("5000000"),
            debt_outstanding=Decimal("3000000"),
        )

        assert result.dscr == Decimal("1.25")
        assert result.ltv == Decimal("0.60")

    def test_result_with_none_dscr(self) -> None:
        """Result with None DSCR (zero debt service)."""
        result = InfrastructureAnalyticsResult(
            valuation_date=date(2024, 6, 30),
            dscr=None,
            ltv=Decimal("0.50"),
            cash_available_for_debt_service=Decimal("100000"),
            debt_service_amount=Decimal("0"),
            asset_value=Decimal("5000000"),
            debt_outstanding=Decimal("2500000"),
        )

        assert result.dscr is None
        assert result.ltv == Decimal("0.50")

    def test_result_with_none_ltv(self) -> None:
        """Result with None LTV (zero asset value)."""
        result = InfrastructureAnalyticsResult(
            valuation_date=date(2024, 6, 30),
            dscr=Decimal("1.50"),
            ltv=None,
            cash_available_for_debt_service=Decimal("500000"),
            debt_service_amount=Decimal("333333"),
            asset_value=Decimal("0"),
            debt_outstanding=Decimal("0"),
        )

        assert result.dscr == Decimal("1.50")
        assert result.ltv is None

    def test_result_with_both_none(self) -> None:
        """Result with both DSCR and LTV as None."""
        result = InfrastructureAnalyticsResult(
            valuation_date=date(2024, 6, 30),
            dscr=None,
            ltv=None,
            cash_available_for_debt_service=Decimal("100000"),
            debt_service_amount=Decimal("0"),
            asset_value=Decimal("0"),
            debt_outstanding=Decimal("0"),
        )

        assert result.dscr is None
        assert result.ltv is None

    def test_negative_dscr_rejected(self) -> None:
        """Negative DSCR is rejected."""
        with pytest.raises(ValueError, match="dscr must be non-negative"):
            InfrastructureAnalyticsResult(
                valuation_date=date(2024, 6, 30),
                dscr=Decimal("-0.50"),
                ltv=None,
                cash_available_for_debt_service=Decimal("100000"),
                debt_service_amount=Decimal("100000"),
                asset_value=Decimal("1000000"),
                debt_outstanding=Decimal("500000"),
            )

    def test_negative_ltv_rejected(self) -> None:
        """Negative LTV is rejected."""
        with pytest.raises(ValueError, match="ltv must be non-negative"):
            InfrastructureAnalyticsResult(
                valuation_date=date(2024, 6, 30),
                dscr=None,
                ltv=Decimal("-0.50"),
                cash_available_for_debt_service=Decimal("100000"),
                debt_service_amount=Decimal("100000"),
                asset_value=Decimal("1000000"),
                debt_outstanding=Decimal("500000"),
            )

    def test_decimal_precision_preserved(self) -> None:
        """Decimal precision in ratios is preserved."""
        dscr = Decimal("1.234567")
        ltv = Decimal("0.456789")

        result = InfrastructureAnalyticsResult(
            valuation_date=date(2024, 6, 30),
            dscr=dscr,
            ltv=ltv,
            cash_available_for_debt_service=Decimal("1234567.89"),
            debt_service_amount=Decimal("1000000"),
            asset_value=Decimal("5000000"),
            debt_outstanding=Decimal("2283945"),
        )

        assert result.dscr == dscr
        assert result.ltv == ltv


class TestInfrastructureEngine:
    """Test InfrastructureEngine calculation logic."""

    def test_typical_infrastructure_asset(self) -> None:
        """Typical infrastructure asset with healthy DSCR and LTV."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("500000"),
            debt_service_amount=Decimal("400000"),
            asset_value=Decimal("5000000"),
            debt_outstanding=Decimal("3000000"),
            asset_id="HIGHWAY_001",
        )

        result = InfrastructureEngine.analyze(asset)

        assert result.dscr == Decimal("500000") / Decimal("400000")
        assert result.dscr == Decimal("1.25")
        assert result.ltv == Decimal("3000000") / Decimal("5000000")
        assert result.ltv == Decimal("0.6")
        assert result.asset_id == "HIGHWAY_001"

    def test_zero_debt_service(self) -> None:
        """Zero debt service results in None DSCR."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("100000"),
            debt_service_amount=Decimal("0"),
            asset_value=Decimal("5000000"),
            debt_outstanding=Decimal("2500000"),
        )

        result = InfrastructureEngine.analyze(asset)

        assert result.dscr is None
        assert result.ltv == Decimal("0.5")

    def test_zero_asset_value(self) -> None:
        """Zero asset value results in None LTV."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("500000"),
            debt_service_amount=Decimal("400000"),
            asset_value=Decimal("0"),
            debt_outstanding=Decimal("0"),
        )

        result = InfrastructureEngine.analyze(asset)

        assert result.dscr == Decimal("1.25")
        assert result.ltv is None

    def test_zero_debt_outstanding(self) -> None:
        """Zero debt outstanding results in zero LTV."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("500000"),
            debt_service_amount=Decimal("400000"),
            asset_value=Decimal("5000000"),
            debt_outstanding=Decimal("0"),
        )

        result = InfrastructureEngine.analyze(asset)

        assert result.dscr == Decimal("1.25")
        assert result.ltv == Decimal("0")

    def test_zero_cash_available(self) -> None:
        """Zero cash available for debt service results in zero DSCR."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("0"),
            debt_service_amount=Decimal("400000"),
            asset_value=Decimal("5000000"),
            debt_outstanding=Decimal("3000000"),
        )

        result = InfrastructureEngine.analyze(asset)

        assert result.dscr == Decimal("0")
        assert result.ltv == Decimal("0.6")

    def test_decimal_precision_in_calculations(self) -> None:
        """Decimal precision is preserved in calculations."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("1"),
            debt_service_amount=Decimal("3"),
            asset_value=Decimal("5"),
            debt_outstanding=Decimal("2"),
        )

        result = InfrastructureEngine.analyze(asset)

        # 1/3 = 0.333... (repeating)
        assert result.dscr == Decimal("1") / Decimal("3")
        # 2/5 = 0.4
        assert result.ltv == Decimal("2") / Decimal("5")
        assert result.ltv == Decimal("0.4")

    def test_high_leverage_asset(self) -> None:
        """Asset with high leverage (high LTV)."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("200000"),
            debt_service_amount=Decimal("200000"),
            asset_value=Decimal("1000000"),
            debt_outstanding=Decimal("850000"),
        )

        result = InfrastructureEngine.analyze(asset)

        assert result.dscr == Decimal("1.0")
        assert result.ltv == Decimal("0.85")
        assert result.ltv > Decimal("0.80")

    def test_stressed_dscr(self) -> None:
        """Asset with stressed DSCR (below 1.0)."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("300000"),
            debt_service_amount=Decimal("400000"),
            asset_value=Decimal("5000000"),
            debt_outstanding=Decimal("2500000"),
        )

        result = InfrastructureEngine.analyze(asset)

        assert result.dscr == Decimal("0.75")
        assert result.dscr < Decimal("1.0")
        assert result.ltv == Decimal("0.5")


class TestRealisticExamples:
    """Realistic infrastructure asset scenarios."""

    def test_toll_road_healthy_state(self) -> None:
        """Healthy toll road with strong DSCR and moderate LTV."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("2000000"),
            debt_service_amount=Decimal("1500000"),
            asset_value=Decimal("25000000"),
            debt_outstanding=Decimal("12000000"),
            asset_id="TOLL_ROAD_REGION_A",
        )

        result = InfrastructureEngine.analyze(asset)

        assert result.dscr == Decimal("2000000") / Decimal("1500000")
        assert result.dscr > Decimal("1.3")
        assert result.ltv == Decimal("12000000") / Decimal("25000000")
        assert result.ltv == Decimal("0.48")

    def test_wind_farm_high_leverage(self) -> None:
        """Wind farm with high leverage (high LTV) and modest DSCR."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("800000"),
            debt_service_amount=Decimal("750000"),
            asset_value=Decimal("5000000"),
            debt_outstanding=Decimal("4000000"),
            asset_id="WIND_FARM_NORTH",
        )

        result = InfrastructureEngine.analyze(asset)

        assert result.dscr == Decimal("800000") / Decimal("750000")
        assert result.dscr > Decimal("1.0")
        assert result.ltv == Decimal("4000000") / Decimal("5000000")
        assert result.ltv == Decimal("0.80")

    def test_water_utility_recently_financed(self) -> None:
        """Water utility with recent refinancing, stressed cash flow."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("400000"),
            debt_service_amount=Decimal("500000"),
            asset_value=Decimal("10000000"),
            debt_outstanding=Decimal("7000000"),
            asset_id="WATER_UTILITY_CENTRAL",
        )

        result = InfrastructureEngine.analyze(asset)

        assert result.dscr == Decimal("400000") / Decimal("500000")
        assert result.dscr == Decimal("0.8")
        assert result.dscr < Decimal("1.0")
        assert result.ltv == Decimal("7000000") / Decimal("10000000")
        assert result.ltv == Decimal("0.70")

    def test_mature_airport_unlevered(self) -> None:
        """Mature airport with no debt (zero LTV)."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("5000000"),
            debt_service_amount=Decimal("0"),
            asset_value=Decimal("100000000"),
            debt_outstanding=Decimal("0"),
            asset_id="AIRPORT_MAJOR",
        )

        result = InfrastructureEngine.analyze(asset)

        assert result.dscr is None
        assert result.ltv == Decimal("0")

    def test_district_heating_moderate_metrics(self) -> None:
        """District heating system with moderate DSCR and LTV."""
        asset = InfrastructureAssetInput(
            valuation_date=date(2024, 6, 30),
            cash_available_for_debt_service=Decimal("1200000"),
            debt_service_amount=Decimal("1000000"),
            asset_value=Decimal("8000000"),
            debt_outstanding=Decimal("4000000"),
            asset_id="DISTRICT_HEAT_CITY",
        )

        result = InfrastructureEngine.analyze(asset)

        assert result.dscr == Decimal("1.2")
        assert result.ltv == Decimal("0.5")
