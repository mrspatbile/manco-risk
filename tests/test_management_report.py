"""Tests for management reporting layer.

Tests fund summary, market risk, management report assembly, and service functionality.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.reporting.management_report import (
    ManagementFundSummaryInput,
    ManagementFundSummarySection,
    ManagementMarketRiskInput,
    ManagementMarketRiskSection,
    ManagementRiskReport,
    ManagementStressTestingInput,
    ManagementStressTestingSection,
)
from manco_risk.reporting.management_report_service import ManagementReportService


class TestManagementFundSummaryInput:
    """Test input validation for fund summary."""

    def test_valid_input_required_fields_only(self) -> None:
        """Valid fund summary input with required fields only."""
        input_data = ManagementFundSummaryInput(
            fund_id="FUND001",
            fund_name="Test UCITS Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        assert input_data.fund_id == "FUND001"
        assert input_data.fund_name == "Test UCITS Fund"
        assert input_data.fund_regime == "UCITS"
        assert input_data.base_currency == "EUR"
        assert input_data.valuation_date == date(2024, 6, 30)
        assert input_data.nav == Decimal("1000000.00")
        assert input_data.aum is None
        assert input_data.inception_date is None
        assert input_data.reporting_period_end is None
        assert input_data.methodology_version is None

    def test_valid_input_with_optional_fields(self) -> None:
        """Valid fund summary input with all optional fields."""
        input_data = ManagementFundSummaryInput(
            fund_id="FUND002",
            fund_name="Test AIF Fund",
            fund_regime="AIF",
            base_currency="USD",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("5000000.00"),
            aum=Decimal("5000000.00"),
            inception_date=date(2020, 1, 15),
            reporting_period_end=date(2024, 6, 30),
            methodology_version="v1.0",
        )

        assert input_data.fund_id == "FUND002"
        assert input_data.fund_name == "Test AIF Fund"
        assert input_data.fund_regime == "AIF"
        assert input_data.base_currency == "USD"
        assert input_data.valuation_date == date(2024, 6, 30)
        assert input_data.nav == Decimal("5000000.00")
        assert input_data.aum == Decimal("5000000.00")
        assert input_data.inception_date == date(2020, 1, 15)
        assert input_data.reporting_period_end == date(2024, 6, 30)
        assert input_data.methodology_version == "v1.0"

    def test_empty_fund_id_rejected(self) -> None:
        """Empty fund_id is rejected."""
        with pytest.raises(ValueError, match="fund_id must be non-empty"):
            ManagementFundSummaryInput(
                fund_id="",
                fund_name="Test Fund",
                fund_regime="UCITS",
                base_currency="EUR",
                valuation_date=date(2024, 6, 30),
                nav=Decimal("1000000.00"),
            )

    def test_whitespace_fund_id_stripped(self) -> None:
        """Fund ID with whitespace is stripped."""
        input_data = ManagementFundSummaryInput(
            fund_id="  FUND001  ",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        assert input_data.fund_id == "FUND001"

    def test_empty_fund_name_rejected(self) -> None:
        """Empty fund_name is rejected."""
        with pytest.raises(ValueError, match="fund_name must be non-empty"):
            ManagementFundSummaryInput(
                fund_id="FUND001",
                fund_name="",
                fund_regime="UCITS",
                base_currency="EUR",
                valuation_date=date(2024, 6, 30),
                nav=Decimal("1000000.00"),
            )

    def test_whitespace_fund_name_stripped(self) -> None:
        """Fund name with whitespace is stripped."""
        input_data = ManagementFundSummaryInput(
            fund_id="FUND001",
            fund_name="  Test Fund  ",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        assert input_data.fund_name == "Test Fund"

    def test_empty_fund_regime_rejected(self) -> None:
        """Empty fund_regime is rejected."""
        with pytest.raises(ValueError, match="fund_regime must be non-empty"):
            ManagementFundSummaryInput(
                fund_id="FUND001",
                fund_name="Test Fund",
                fund_regime="",
                base_currency="EUR",
                valuation_date=date(2024, 6, 30),
                nav=Decimal("1000000.00"),
            )

    def test_empty_base_currency_rejected(self) -> None:
        """Empty base_currency is rejected."""
        with pytest.raises(ValueError, match="base_currency must be non-empty"):
            ManagementFundSummaryInput(
                fund_id="FUND001",
                fund_name="Test Fund",
                fund_regime="UCITS",
                base_currency="",
                valuation_date=date(2024, 6, 30),
                nav=Decimal("1000000.00"),
            )

    def test_negative_nav_rejected(self) -> None:
        """Negative NAV is rejected."""
        with pytest.raises(ValueError, match="nav must be non-negative"):
            ManagementFundSummaryInput(
                fund_id="FUND001",
                fund_name="Test Fund",
                fund_regime="UCITS",
                base_currency="EUR",
                valuation_date=date(2024, 6, 30),
                nav=Decimal("-1000000.00"),
            )

    def test_zero_nav_accepted(self) -> None:
        """Zero NAV is accepted."""
        input_data = ManagementFundSummaryInput(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("0.00"),
        )

        assert input_data.nav == Decimal("0.00")

    def test_negative_aum_rejected(self) -> None:
        """Negative AUM is rejected."""
        with pytest.raises(ValueError, match="aum must be non-negative"):
            ManagementFundSummaryInput(
                fund_id="FUND001",
                fund_name="Test Fund",
                fund_regime="UCITS",
                base_currency="EUR",
                valuation_date=date(2024, 6, 30),
                nav=Decimal("1000000.00"),
                aum=Decimal("-500000.00"),
            )

    def test_zero_aum_accepted(self) -> None:
        """Zero AUM is accepted."""
        input_data = ManagementFundSummaryInput(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
            aum=Decimal("0.00"),
        )

        assert input_data.aum == Decimal("0.00")

    def test_empty_methodology_version_rejected(self) -> None:
        """Empty methodology_version is rejected."""
        with pytest.raises(ValueError, match="methodology_version must be non-empty when supplied"):
            ManagementFundSummaryInput(
                fund_id="FUND001",
                fund_name="Test Fund",
                fund_regime="UCITS",
                base_currency="EUR",
                valuation_date=date(2024, 6, 30),
                nav=Decimal("1000000.00"),
                methodology_version="",
            )

    def test_whitespace_methodology_version_stripped(self) -> None:
        """Methodology version with whitespace is stripped."""
        input_data = ManagementFundSummaryInput(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
            methodology_version="  v1.0  ",
        )

        assert input_data.methodology_version == "v1.0"

    def test_immutability(self) -> None:
        """Fund summary input is immutable."""
        input_data = ManagementFundSummaryInput(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            input_data.fund_name = "Modified"  # type: ignore

    def test_decimal_preservation_in_input(self) -> None:
        """Decimal values are preserved exactly in input."""
        input_data = ManagementFundSummaryInput(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.123"),
            aum=Decimal("2000000.456"),
        )

        assert input_data.nav == Decimal("1000000.123")
        assert input_data.aum == Decimal("2000000.456")


class TestManagementFundSummarySection:
    """Test fund summary section model."""

    def test_valid_section_required_fields_only(self) -> None:
        """Valid fund summary section with required fields only."""
        section = ManagementFundSummarySection(
            fund_id="FUND001",
            fund_name="Test UCITS Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        assert section.fund_id == "FUND001"
        assert section.fund_name == "Test UCITS Fund"
        assert section.fund_regime == "UCITS"
        assert section.base_currency == "EUR"
        assert section.valuation_date == date(2024, 6, 30)
        assert section.nav == Decimal("1000000.00")
        assert section.aum is None

    def test_valid_section_with_optional_fields(self) -> None:
        """Valid fund summary section with all optional fields."""
        section = ManagementFundSummarySection(
            fund_id="FUND002",
            fund_name="Test AIF Fund",
            fund_regime="AIF",
            base_currency="USD",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("5000000.00"),
            aum=Decimal("5000000.00"),
            inception_date=date(2020, 1, 15),
            reporting_period_end=date(2024, 6, 30),
            methodology_version="v1.0",
        )

        assert section.fund_id == "FUND002"
        assert section.aum == Decimal("5000000.00")
        assert section.inception_date == date(2020, 1, 15)
        assert section.methodology_version == "v1.0"

    def test_immutability(self) -> None:
        """Fund summary section is immutable."""
        section = ManagementFundSummarySection(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            section.fund_name = "Modified"  # type: ignore

    def test_decimal_preservation_in_section(self) -> None:
        """Decimal values are preserved exactly in section."""
        section = ManagementFundSummarySection(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1234567.89"),
            aum=Decimal("9876543.21"),
        )

        assert section.nav == Decimal("1234567.89")
        assert section.aum == Decimal("9876543.21")


class TestManagementRiskReport:
    """Test management risk report model."""

    def test_valid_report_with_fund_summary(self) -> None:
        """Valid management risk report with fund summary."""
        fund_summary = ManagementFundSummarySection(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        report = ManagementRiskReport(
            fund_summary=fund_summary,
            included_sections=["Fund Summary"],
        )

        assert report.fund_summary.fund_id == "FUND001"
        assert report.included_sections == ["Fund Summary"]

    def test_immutability(self) -> None:
        """Management risk report is immutable."""
        fund_summary = ManagementFundSummarySection(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        report = ManagementRiskReport(
            fund_summary=fund_summary,
            included_sections=["Fund Summary"],
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            report.included_sections = ["Fund Summary", "Market Risk"]  # type: ignore


class TestManagementReportService:
    """Test management reporting service."""

    def test_build_fund_summary_from_input(self) -> None:
        """Build fund summary section from input."""
        input_data = ManagementFundSummaryInput(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        section = ManagementReportService.build_fund_summary(input_data)

        assert isinstance(section, ManagementFundSummarySection)
        assert section.fund_id == "FUND001"
        assert section.fund_name == "Test Fund"
        assert section.fund_regime == "UCITS"
        assert section.base_currency == "EUR"
        assert section.valuation_date == date(2024, 6, 30)
        assert section.nav == Decimal("1000000.00")

    def test_build_fund_summary_preserves_optional_fields(self) -> None:
        """Build fund summary preserves optional fields."""
        input_data = ManagementFundSummaryInput(
            fund_id="FUND002",
            fund_name="Test AIF",
            fund_regime="AIF",
            base_currency="USD",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("5000000.00"),
            aum=Decimal("5000000.00"),
            inception_date=date(2020, 1, 15),
            reporting_period_end=date(2024, 6, 30),
            methodology_version="v1.0",
        )

        section = ManagementReportService.build_fund_summary(input_data)

        assert section.aum == Decimal("5000000.00")
        assert section.inception_date == date(2020, 1, 15)
        assert section.reporting_period_end == date(2024, 6, 30)
        assert section.methodology_version == "v1.0"

    def test_build_fund_summary_immutable_result(self) -> None:
        """Build fund summary returns immutable section."""
        input_data = ManagementFundSummaryInput(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        section = ManagementReportService.build_fund_summary(input_data)

        with pytest.raises(Exception):  # Pydantic frozen model raises
            section.fund_name = "Modified"  # type: ignore

    def test_build_report_with_fund_summary(self) -> None:
        """Build report with fund summary section."""
        fund_summary = ManagementFundSummarySection(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        report = ManagementReportService.build_report(fund_summary)

        assert isinstance(report, ManagementRiskReport)
        assert report.fund_summary.fund_id == "FUND001"
        assert "Fund Summary" in report.included_sections

    def test_build_report_included_sections_correct(self) -> None:
        """Build report sets included_sections correctly."""
        fund_summary = ManagementFundSummarySection(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        report = ManagementReportService.build_report(fund_summary)

        assert report.included_sections == ["Fund Summary"]

    def test_build_report_immutable_result(self) -> None:
        """Build report returns immutable report object."""
        fund_summary = ManagementFundSummarySection(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        report = ManagementReportService.build_report(fund_summary)

        with pytest.raises(Exception):  # Pydantic frozen model raises
            report.included_sections = []  # type: ignore

    def test_build_report_with_market_risk(self) -> None:
        """Build report with fund summary and market risk sections."""
        fund_summary = ManagementFundSummarySection(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        market_risk = ManagementMarketRiskSection(
            var_value=Decimal("0.025"),
            var_method="Historical Simulation",
        )

        report = ManagementReportService.build_report(fund_summary, market_risk)

        assert report.fund_summary.fund_id == "FUND001"
        assert report.market_risk is not None
        assert report.market_risk.var_value == Decimal("0.025")
        assert "Fund Summary" in report.included_sections
        assert "Market Risk" in report.included_sections

    def test_build_report_without_market_risk(self) -> None:
        """Build report without market risk section."""
        fund_summary = ManagementFundSummarySection(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        report = ManagementReportService.build_report(fund_summary)

        assert report.market_risk is None
        assert report.included_sections == ["Fund Summary"]


class TestManagementMarketRiskInput:
    """Test input validation for market risk."""

    def test_valid_input_required_fields_only(self) -> None:
        """Valid market risk input with required fields only."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.025"),
            var_method="Historical Simulation",
        )

        assert input_data.var_value == Decimal("0.025")
        assert input_data.var_method == "Historical Simulation"
        assert input_data.expected_shortfall is None
        assert input_data.srri_class is None
        assert input_data.global_exposure is None
        assert input_data.stress_summary_reference is None
        assert input_data.methodology_version is None

    def test_valid_input_with_optional_fields(self) -> None:
        """Valid market risk input with all optional fields."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.025"),
            var_method="Parametric",
            expected_shortfall=Decimal("0.040"),
            srri_class="5",
            global_exposure=Decimal("1.5"),
            stress_summary_reference="Stress Test Results 2024-06-30",
            methodology_version="VaR_Parametric_v1.0",
        )

        assert input_data.var_value == Decimal("0.025")
        assert input_data.var_method == "Parametric"
        assert input_data.expected_shortfall == Decimal("0.040")
        assert input_data.srri_class == "5"
        assert input_data.global_exposure == Decimal("1.5")
        assert input_data.stress_summary_reference == "Stress Test Results 2024-06-30"
        assert input_data.methodology_version == "VaR_Parametric_v1.0"

    def test_empty_var_method_rejected(self) -> None:
        """Empty var_method is rejected."""
        with pytest.raises(ValueError, match="var_method must be non-empty"):
            ManagementMarketRiskInput(
                var_value=Decimal("0.025"),
                var_method="",
            )

    def test_whitespace_var_method_stripped(self) -> None:
        """Var method with whitespace is stripped."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.025"),
            var_method="  Historical Simulation  ",
        )

        assert input_data.var_method == "Historical Simulation"

    def test_negative_var_value_rejected(self) -> None:
        """Negative var_value is rejected."""
        with pytest.raises(ValueError, match="var_value must be non-negative"):
            ManagementMarketRiskInput(
                var_value=Decimal("-0.025"),
                var_method="Historical Simulation",
            )

    def test_zero_var_value_accepted(self) -> None:
        """Zero var_value is accepted."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.00"),
            var_method="Historical Simulation",
        )

        assert input_data.var_value == Decimal("0.00")

    def test_negative_expected_shortfall_rejected(self) -> None:
        """Negative expected_shortfall is rejected."""
        with pytest.raises(ValueError, match="expected_shortfall must be non-negative"):
            ManagementMarketRiskInput(
                var_value=Decimal("0.025"),
                var_method="Historical Simulation",
                expected_shortfall=Decimal("-0.040"),
            )

    def test_zero_expected_shortfall_accepted(self) -> None:
        """Zero expected_shortfall is accepted."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.025"),
            var_method="Historical Simulation",
            expected_shortfall=Decimal("0.00"),
        )

        assert input_data.expected_shortfall == Decimal("0.00")

    def test_negative_global_exposure_rejected(self) -> None:
        """Negative global_exposure is rejected."""
        with pytest.raises(ValueError, match="global_exposure must be non-negative"):
            ManagementMarketRiskInput(
                var_value=Decimal("0.025"),
                var_method="Historical Simulation",
                global_exposure=Decimal("-1.5"),
            )

    def test_zero_global_exposure_accepted(self) -> None:
        """Zero global_exposure is accepted."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.025"),
            var_method="Historical Simulation",
            global_exposure=Decimal("0.00"),
        )

        assert input_data.global_exposure == Decimal("0.00")

    def test_empty_srri_class_rejected(self) -> None:
        """Empty srri_class is rejected."""
        with pytest.raises(ValueError, match="srri_class must be non-empty when supplied"):
            ManagementMarketRiskInput(
                var_value=Decimal("0.025"),
                var_method="Historical Simulation",
                srri_class="",
            )

    def test_whitespace_srri_class_stripped(self) -> None:
        """SRRI class with whitespace is stripped."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.025"),
            var_method="Historical Simulation",
            srri_class="  5  ",
        )

        assert input_data.srri_class == "5"

    def test_empty_stress_summary_reference_rejected(self) -> None:
        """Empty stress_summary_reference is rejected."""
        with pytest.raises(
            ValueError, match="stress_summary_reference must be non-empty when supplied"
        ):
            ManagementMarketRiskInput(
                var_value=Decimal("0.025"),
                var_method="Historical Simulation",
                stress_summary_reference="",
            )

    def test_whitespace_stress_summary_reference_stripped(self) -> None:
        """Stress summary reference with whitespace is stripped."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.025"),
            var_method="Historical Simulation",
            stress_summary_reference="  Stress Results  ",
        )

        assert input_data.stress_summary_reference == "Stress Results"

    def test_empty_methodology_version_rejected(self) -> None:
        """Empty methodology_version is rejected."""
        with pytest.raises(ValueError, match="methodology_version must be non-empty when supplied"):
            ManagementMarketRiskInput(
                var_value=Decimal("0.025"),
                var_method="Historical Simulation",
                methodology_version="",
            )

    def test_whitespace_methodology_version_stripped(self) -> None:
        """Methodology version with whitespace is stripped."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.025"),
            var_method="Historical Simulation",
            methodology_version="  v1.0  ",
        )

        assert input_data.methodology_version == "v1.0"

    def test_immutability(self) -> None:
        """Market risk input is immutable."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.025"),
            var_method="Historical Simulation",
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            input_data.var_method = "Modified"  # type: ignore

    def test_decimal_preservation_in_input(self) -> None:
        """Decimal values are preserved exactly in input."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.025123"),
            var_method="Historical Simulation",
            expected_shortfall=Decimal("0.040567"),
            global_exposure=Decimal("1.555555"),
        )

        assert input_data.var_value == Decimal("0.025123")
        assert input_data.expected_shortfall == Decimal("0.040567")
        assert input_data.global_exposure == Decimal("1.555555")


class TestManagementMarketRiskSection:
    """Test market risk section model."""

    def test_valid_section_required_fields_only(self) -> None:
        """Valid market risk section with required fields only."""
        section = ManagementMarketRiskSection(
            var_value=Decimal("0.025"),
            var_method="Historical Simulation",
        )

        assert section.var_value == Decimal("0.025")
        assert section.var_method == "Historical Simulation"
        assert section.expected_shortfall is None

    def test_valid_section_with_optional_fields(self) -> None:
        """Valid market risk section with all optional fields."""
        section = ManagementMarketRiskSection(
            var_value=Decimal("0.025"),
            var_method="Parametric",
            expected_shortfall=Decimal("0.040"),
            srri_class="5",
            global_exposure=Decimal("1.5"),
            stress_summary_reference="Stress Test Results 2024-06-30",
            methodology_version="VaR_Parametric_v1.0",
        )

        assert section.var_value == Decimal("0.025")
        assert section.expected_shortfall == Decimal("0.040")
        assert section.srri_class == "5"
        assert section.global_exposure == Decimal("1.5")

    def test_immutability(self) -> None:
        """Market risk section is immutable."""
        section = ManagementMarketRiskSection(
            var_value=Decimal("0.025"),
            var_method="Historical Simulation",
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            section.var_method = "Modified"  # type: ignore

    def test_decimal_preservation_in_section(self) -> None:
        """Decimal values are preserved exactly in section."""
        section = ManagementMarketRiskSection(
            var_value=Decimal("0.025123"),
            var_method="Historical Simulation",
            expected_shortfall=Decimal("0.040567"),
            global_exposure=Decimal("1.555555"),
        )

        assert section.var_value == Decimal("0.025123")
        assert section.expected_shortfall == Decimal("0.040567")
        assert section.global_exposure == Decimal("1.555555")


class TestManagementReportServiceMarketRisk:
    """Test market risk service methods."""

    def test_build_market_risk_from_input(self) -> None:
        """Build market risk section from input."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.025"),
            var_method="Historical Simulation",
        )

        section = ManagementReportService.build_market_risk(input_data)

        assert isinstance(section, ManagementMarketRiskSection)
        assert section.var_value == Decimal("0.025")
        assert section.var_method == "Historical Simulation"

    def test_build_market_risk_preserves_optional_fields(self) -> None:
        """Build market risk preserves optional fields."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.025"),
            var_method="Parametric",
            expected_shortfall=Decimal("0.040"),
            srri_class="5",
            global_exposure=Decimal("1.5"),
            stress_summary_reference="Stress Test Results 2024-06-30",
            methodology_version="VaR_Parametric_v1.0",
        )

        section = ManagementReportService.build_market_risk(input_data)

        assert section.expected_shortfall == Decimal("0.040")
        assert section.srri_class == "5"
        assert section.global_exposure == Decimal("1.5")
        assert section.stress_summary_reference == "Stress Test Results 2024-06-30"
        assert section.methodology_version == "VaR_Parametric_v1.0"

    def test_build_market_risk_immutable_result(self) -> None:
        """Build market risk returns immutable section."""
        input_data = ManagementMarketRiskInput(
            var_value=Decimal("0.025"),
            var_method="Historical Simulation",
        )

        section = ManagementReportService.build_market_risk(input_data)

        with pytest.raises(Exception):  # Pydantic frozen model raises
            section.var_method = "Modified"  # type: ignore

    def test_build_report_with_stress_testing(self) -> None:
        """Build report with fund summary and stress testing sections."""
        fund_summary = ManagementFundSummarySection(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        stress_testing = ManagementStressTestingSection(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
        )

        report = ManagementReportService.build_report(fund_summary, stress_testing=stress_testing)

        assert report.fund_summary.fund_id == "FUND001"
        assert report.stress_testing is not None
        assert report.stress_testing.scenario_name == "Lehman Crisis 2008"
        assert "Fund Summary" in report.included_sections
        assert "Stress Testing" in report.included_sections

    def test_build_report_with_market_risk_and_stress_testing(self) -> None:
        """Build report with all sections."""
        fund_summary = ManagementFundSummarySection(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        market_risk = ManagementMarketRiskSection(
            var_value=Decimal("0.025"),
            var_method="Historical Simulation",
        )

        stress_testing = ManagementStressTestingSection(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
        )

        report = ManagementReportService.build_report(fund_summary, market_risk, stress_testing)

        assert report.fund_summary.fund_id == "FUND001"
        assert report.market_risk is not None
        assert report.stress_testing is not None
        assert len(report.included_sections) == 3
        assert "Fund Summary" in report.included_sections
        assert "Market Risk" in report.included_sections
        assert "Stress Testing" in report.included_sections

    def test_build_report_without_stress_testing(self) -> None:
        """Build report without stress testing section."""
        fund_summary = ManagementFundSummarySection(
            fund_id="FUND001",
            fund_name="Test Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1000000.00"),
        )

        report = ManagementReportService.build_report(fund_summary)

        assert report.stress_testing is None
        assert report.included_sections == ["Fund Summary"]


class TestManagementStressTestingInput:
    """Test input validation for stress testing."""

    def test_valid_input_required_fields_only(self) -> None:
        """Valid stress testing input with required fields only."""
        input_data = ManagementStressTestingInput(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
        )

        assert input_data.scenario_name == "Lehman Crisis 2008"
        assert input_data.scenario_type == "Historical"
        assert input_data.portfolio_impact == Decimal("-0.125")
        assert input_data.nav_impact is None
        assert input_data.worst_position is None
        assert input_data.worst_sector is None
        assert input_data.stress_date is None
        assert input_data.methodology_version is None

    def test_valid_input_with_optional_fields(self) -> None:
        """Valid stress testing input with all optional fields."""
        input_data = ManagementStressTestingInput(
            scenario_name="Rates +100bps",
            scenario_type="Hypothetical",
            portfolio_impact=Decimal("-0.045"),
            nav_impact=Decimal("-0.045"),
            worst_position="DE0005140008",
            worst_sector="Fixed Income",
            stress_date=date(2024, 6, 30),
            methodology_version="Stress_v1.0",
        )

        assert input_data.scenario_name == "Rates +100bps"
        assert input_data.scenario_type == "Hypothetical"
        assert input_data.portfolio_impact == Decimal("-0.045")
        assert input_data.nav_impact == Decimal("-0.045")
        assert input_data.worst_position == "DE0005140008"
        assert input_data.worst_sector == "Fixed Income"
        assert input_data.stress_date == date(2024, 6, 30)
        assert input_data.methodology_version == "Stress_v1.0"

    def test_empty_scenario_name_rejected(self) -> None:
        """Empty scenario_name is rejected."""
        with pytest.raises(ValueError, match="scenario_name must be non-empty"):
            ManagementStressTestingInput(
                scenario_name="",
                scenario_type="Historical",
                portfolio_impact=Decimal("-0.125"),
            )

    def test_whitespace_scenario_name_stripped(self) -> None:
        """Scenario name with whitespace is stripped."""
        input_data = ManagementStressTestingInput(
            scenario_name="  Lehman Crisis 2008  ",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
        )

        assert input_data.scenario_name == "Lehman Crisis 2008"

    def test_empty_scenario_type_rejected(self) -> None:
        """Empty scenario_type is rejected."""
        with pytest.raises(ValueError, match="scenario_type must be non-empty"):
            ManagementStressTestingInput(
                scenario_name="Lehman Crisis 2008",
                scenario_type="",
                portfolio_impact=Decimal("-0.125"),
            )

    def test_whitespace_scenario_type_stripped(self) -> None:
        """Scenario type with whitespace is stripped."""
        input_data = ManagementStressTestingInput(
            scenario_name="Lehman Crisis 2008",
            scenario_type="  Historical  ",
            portfolio_impact=Decimal("-0.125"),
        )

        assert input_data.scenario_type == "Historical"

    def test_negative_portfolio_impact_accepted(self) -> None:
        """Negative portfolio_impact (loss) is accepted."""
        input_data = ManagementStressTestingInput(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
        )

        assert input_data.portfolio_impact == Decimal("-0.125")

    def test_positive_portfolio_impact_accepted(self) -> None:
        """Positive portfolio_impact (gain) is accepted."""
        input_data = ManagementStressTestingInput(
            scenario_name="Gold Rally 2020",
            scenario_type="Historical",
            portfolio_impact=Decimal("0.085"),
        )

        assert input_data.portfolio_impact == Decimal("0.085")

    def test_zero_portfolio_impact_accepted(self) -> None:
        """Zero portfolio_impact is accepted."""
        input_data = ManagementStressTestingInput(
            scenario_name="Neutral Scenario",
            scenario_type="Hypothetical",
            portfolio_impact=Decimal("0.00"),
        )

        assert input_data.portfolio_impact == Decimal("0.00")

    def test_negative_nav_impact_accepted(self) -> None:
        """Negative nav_impact (loss) is accepted."""
        input_data = ManagementStressTestingInput(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
            nav_impact=Decimal("-0.125"),
        )

        assert input_data.nav_impact == Decimal("-0.125")

    def test_positive_nav_impact_accepted(self) -> None:
        """Positive nav_impact (gain) is accepted."""
        input_data = ManagementStressTestingInput(
            scenario_name="Gold Rally 2020",
            scenario_type="Historical",
            portfolio_impact=Decimal("0.085"),
            nav_impact=Decimal("0.085"),
        )

        assert input_data.nav_impact == Decimal("0.085")

    def test_empty_worst_position_rejected(self) -> None:
        """Empty worst_position is rejected."""
        with pytest.raises(ValueError, match="worst_position must be non-empty when supplied"):
            ManagementStressTestingInput(
                scenario_name="Lehman Crisis 2008",
                scenario_type="Historical",
                portfolio_impact=Decimal("-0.125"),
                worst_position="",
            )

    def test_whitespace_worst_position_stripped(self) -> None:
        """Worst position with whitespace is stripped."""
        input_data = ManagementStressTestingInput(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
            worst_position="  DE0005140008  ",
        )

        assert input_data.worst_position == "DE0005140008"

    def test_empty_worst_sector_rejected(self) -> None:
        """Empty worst_sector is rejected."""
        with pytest.raises(ValueError, match="worst_sector must be non-empty when supplied"):
            ManagementStressTestingInput(
                scenario_name="Lehman Crisis 2008",
                scenario_type="Historical",
                portfolio_impact=Decimal("-0.125"),
                worst_sector="",
            )

    def test_whitespace_worst_sector_stripped(self) -> None:
        """Worst sector with whitespace is stripped."""
        input_data = ManagementStressTestingInput(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
            worst_sector="  Financial Services  ",
        )

        assert input_data.worst_sector == "Financial Services"

    def test_empty_methodology_version_rejected(self) -> None:
        """Empty methodology_version is rejected."""
        with pytest.raises(ValueError, match="methodology_version must be non-empty when supplied"):
            ManagementStressTestingInput(
                scenario_name="Lehman Crisis 2008",
                scenario_type="Historical",
                portfolio_impact=Decimal("-0.125"),
                methodology_version="",
            )

    def test_whitespace_methodology_version_stripped(self) -> None:
        """Methodology version with whitespace is stripped."""
        input_data = ManagementStressTestingInput(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
            methodology_version="  Stress_v1.0  ",
        )

        assert input_data.methodology_version == "Stress_v1.0"

    def test_immutability(self) -> None:
        """Stress testing input is immutable."""
        input_data = ManagementStressTestingInput(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            input_data.scenario_name = "Modified"  # type: ignore

    def test_decimal_preservation_in_input(self) -> None:
        """Decimal values are preserved exactly in input."""
        input_data = ManagementStressTestingInput(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125678"),
            nav_impact=Decimal("-0.125678"),
        )

        assert input_data.portfolio_impact == Decimal("-0.125678")
        assert input_data.nav_impact == Decimal("-0.125678")


class TestManagementStressTestingSection:
    """Test stress testing section model."""

    def test_valid_section_required_fields_only(self) -> None:
        """Valid stress testing section with required fields only."""
        section = ManagementStressTestingSection(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
        )

        assert section.scenario_name == "Lehman Crisis 2008"
        assert section.scenario_type == "Historical"
        assert section.portfolio_impact == Decimal("-0.125")
        assert section.nav_impact is None

    def test_valid_section_with_optional_fields(self) -> None:
        """Valid stress testing section with all optional fields."""
        section = ManagementStressTestingSection(
            scenario_name="Rates +100bps",
            scenario_type="Hypothetical",
            portfolio_impact=Decimal("-0.045"),
            nav_impact=Decimal("-0.045"),
            worst_position="DE0005140008",
            worst_sector="Fixed Income",
            stress_date=date(2024, 6, 30),
            methodology_version="Stress_v1.0",
        )

        assert section.scenario_name == "Rates +100bps"
        assert section.nav_impact == Decimal("-0.045")
        assert section.worst_position == "DE0005140008"
        assert section.worst_sector == "Fixed Income"

    def test_immutability(self) -> None:
        """Stress testing section is immutable."""
        section = ManagementStressTestingSection(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            section.scenario_name = "Modified"  # type: ignore

    def test_decimal_preservation_in_section(self) -> None:
        """Decimal values are preserved exactly in section."""
        section = ManagementStressTestingSection(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125678"),
            nav_impact=Decimal("-0.125678"),
        )

        assert section.portfolio_impact == Decimal("-0.125678")
        assert section.nav_impact == Decimal("-0.125678")


class TestManagementReportServiceStressTesting:
    """Test stress testing service methods."""

    def test_build_stress_testing_from_input(self) -> None:
        """Build stress testing section from input."""
        input_data = ManagementStressTestingInput(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
        )

        section = ManagementReportService.build_stress_testing(input_data)

        assert isinstance(section, ManagementStressTestingSection)
        assert section.scenario_name == "Lehman Crisis 2008"
        assert section.scenario_type == "Historical"
        assert section.portfolio_impact == Decimal("-0.125")

    def test_build_stress_testing_preserves_optional_fields(self) -> None:
        """Build stress testing preserves optional fields."""
        input_data = ManagementStressTestingInput(
            scenario_name="Rates +100bps",
            scenario_type="Hypothetical",
            portfolio_impact=Decimal("-0.045"),
            nav_impact=Decimal("-0.045"),
            worst_position="DE0005140008",
            worst_sector="Fixed Income",
            stress_date=date(2024, 6, 30),
            methodology_version="Stress_v1.0",
        )

        section = ManagementReportService.build_stress_testing(input_data)

        assert section.nav_impact == Decimal("-0.045")
        assert section.worst_position == "DE0005140008"
        assert section.worst_sector == "Fixed Income"
        assert section.stress_date == date(2024, 6, 30)
        assert section.methodology_version == "Stress_v1.0"

    def test_build_stress_testing_immutable_result(self) -> None:
        """Build stress testing returns immutable section."""
        input_data = ManagementStressTestingInput(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
        )

        section = ManagementReportService.build_stress_testing(input_data)

        with pytest.raises(Exception):  # Pydantic frozen model raises
            section.scenario_name = "Modified"  # type: ignore


class TestRealisticExamples:
    """Test realistic fund examples."""

    def test_ucits_fund_example(self) -> None:
        """Realistic UCITS fund example."""
        input_data = ManagementFundSummaryInput(
            fund_id="LU001234567890",
            fund_name="Global Equity UCITS Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("250000000.00"),
            aum=Decimal("250000000.00"),
            inception_date=date(2010, 3, 15),
            reporting_period_end=date(2024, 6, 30),
            methodology_version="VaR_HistoricalSimulation_v1.0",
        )

        section = ManagementReportService.build_fund_summary(input_data)
        report = ManagementReportService.build_report(section)

        assert report.fund_summary.fund_regime == "UCITS"
        assert report.fund_summary.nav == Decimal("250000000.00")
        assert "Fund Summary" in report.included_sections

    def test_aif_fund_example(self) -> None:
        """Realistic AIF fund example."""
        input_data = ManagementFundSummaryInput(
            fund_id="IE0087654321234",
            fund_name="Alternative Strategies AIF",
            fund_regime="AIF",
            base_currency="USD",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1500000000.50"),
            aum=Decimal("1500000000.50"),
            inception_date=date(2015, 6, 1),
            reporting_period_end=date(2024, 6, 30),
            methodology_version="VaR_HistoricalSimulation_v2.0",
        )

        section = ManagementReportService.build_fund_summary(input_data)
        report = ManagementReportService.build_report(section)

        assert report.fund_summary.fund_regime == "AIF"
        assert report.fund_summary.nav == Decimal("1500000000.50")
        assert report.fund_summary.aum == Decimal("1500000000.50")

    def test_ucits_fund_with_market_risk_example(self) -> None:
        """Realistic UCITS fund with market risk example."""
        fund_summary_input = ManagementFundSummaryInput(
            fund_id="LU001234567890",
            fund_name="Global Equity UCITS Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("250000000.00"),
            aum=Decimal("250000000.00"),
            inception_date=date(2010, 3, 15),
            reporting_period_end=date(2024, 6, 30),
            methodology_version="VaR_HistoricalSimulation_v1.0",
        )

        market_risk_input = ManagementMarketRiskInput(
            var_value=Decimal("0.0275"),
            var_method="Historical Simulation",
            expected_shortfall=Decimal("0.0425"),
            srri_class="5",
            global_exposure=Decimal("1.2"),
            stress_summary_reference="Stress Scenarios Q2 2024",
            methodology_version="VaR_HistoricalSimulation_v1.0",
        )

        fund_summary = ManagementReportService.build_fund_summary(fund_summary_input)
        market_risk = ManagementReportService.build_market_risk(market_risk_input)
        report = ManagementReportService.build_report(fund_summary, market_risk)

        assert report.fund_summary.fund_regime == "UCITS"
        assert report.market_risk is not None
        assert report.market_risk.var_value == Decimal("0.0275")
        assert report.market_risk.srri_class == "5"
        assert len(report.included_sections) == 2
        assert "Fund Summary" in report.included_sections
        assert "Market Risk" in report.included_sections

    def test_aif_fund_with_market_risk_example(self) -> None:
        """Realistic AIF fund with market risk example."""
        fund_summary_input = ManagementFundSummaryInput(
            fund_id="IE0087654321234",
            fund_name="Alternative Strategies AIF",
            fund_regime="AIF",
            base_currency="USD",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1500000000.50"),
            aum=Decimal("1500000000.50"),
            inception_date=date(2015, 6, 1),
            reporting_period_end=date(2024, 6, 30),
            methodology_version="VaR_Parametric_v2.0",
        )

        market_risk_input = ManagementMarketRiskInput(
            var_value=Decimal("0.0350"),
            var_method="Parametric (Normal)",
            expected_shortfall=Decimal("0.0550"),
            srri_class="6",
            global_exposure=Decimal("2.5"),
            stress_summary_reference="Stress Scenarios Q2 2024",
            methodology_version="VaR_Parametric_v2.0",
        )

        fund_summary = ManagementReportService.build_fund_summary(fund_summary_input)
        market_risk = ManagementReportService.build_market_risk(market_risk_input)
        report = ManagementReportService.build_report(fund_summary, market_risk)

        assert report.fund_summary.fund_regime == "AIF"
        assert report.market_risk is not None
        assert report.market_risk.var_value == Decimal("0.0350")
        assert report.market_risk.global_exposure == Decimal("2.5")
        assert "Market Risk" in report.included_sections

    def test_ucits_fund_with_stress_testing_example(self) -> None:
        """Realistic UCITS fund with stress testing example."""
        fund_summary_input = ManagementFundSummaryInput(
            fund_id="LU001234567890",
            fund_name="Global Equity UCITS Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("250000000.00"),
            aum=Decimal("250000000.00"),
            inception_date=date(2010, 3, 15),
            reporting_period_end=date(2024, 6, 30),
            methodology_version="VaR_HistoricalSimulation_v1.0",
        )

        stress_testing_input = ManagementStressTestingInput(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
            nav_impact=Decimal("-0.125"),
            worst_position="US0378331005",
            worst_sector="Financial Services",
            stress_date=date(2008, 9, 15),
            methodology_version="Stress_HistoricalSimulation_v1.0",
        )

        fund_summary = ManagementReportService.build_fund_summary(fund_summary_input)
        stress_testing = ManagementReportService.build_stress_testing(stress_testing_input)
        report = ManagementReportService.build_report(fund_summary, stress_testing=stress_testing)

        assert report.fund_summary.fund_regime == "UCITS"
        assert report.stress_testing is not None
        assert report.stress_testing.scenario_name == "Lehman Crisis 2008"
        assert report.stress_testing.portfolio_impact == Decimal("-0.125")
        assert report.stress_testing.worst_sector == "Financial Services"
        assert "Fund Summary" in report.included_sections
        assert "Stress Testing" in report.included_sections

    def test_aif_fund_with_hypothetical_stress_example(self) -> None:
        """Realistic AIF fund with hypothetical stress scenario example."""
        fund_summary_input = ManagementFundSummaryInput(
            fund_id="IE0087654321234",
            fund_name="Alternative Strategies AIF",
            fund_regime="AIF",
            base_currency="USD",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("1500000000.50"),
            aum=Decimal("1500000000.50"),
            inception_date=date(2015, 6, 1),
            reporting_period_end=date(2024, 6, 30),
            methodology_version="VaR_Parametric_v2.0",
        )

        stress_testing_input = ManagementStressTestingInput(
            scenario_name="US Interest Rates +100bps",
            scenario_type="Hypothetical",
            portfolio_impact=Decimal("-0.045"),
            nav_impact=Decimal("-0.045"),
            worst_position="BOND_CUSIP_123",
            worst_sector="Fixed Income",
            stress_date=date(2024, 6, 30),
            methodology_version="Stress_Parametric_v2.0",
        )

        fund_summary = ManagementReportService.build_fund_summary(fund_summary_input)
        stress_testing = ManagementReportService.build_stress_testing(stress_testing_input)
        report = ManagementReportService.build_report(fund_summary, stress_testing=stress_testing)

        assert report.fund_summary.fund_regime == "AIF"
        assert report.stress_testing is not None
        assert report.stress_testing.scenario_type == "Hypothetical"
        assert report.stress_testing.portfolio_impact == Decimal("-0.045")
        assert report.stress_testing.worst_sector == "Fixed Income"
        assert "Stress Testing" in report.included_sections

    def test_comprehensive_fund_report_example(self) -> None:
        """Comprehensive fund report with all sections."""
        fund_summary_input = ManagementFundSummaryInput(
            fund_id="LU001234567890",
            fund_name="Global Equity UCITS Fund",
            fund_regime="UCITS",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            nav=Decimal("250000000.00"),
            aum=Decimal("250000000.00"),
            inception_date=date(2010, 3, 15),
            reporting_period_end=date(2024, 6, 30),
            methodology_version="VaR_HistoricalSimulation_v1.0",
        )

        market_risk_input = ManagementMarketRiskInput(
            var_value=Decimal("0.0275"),
            var_method="Historical Simulation",
            expected_shortfall=Decimal("0.0425"),
            srri_class="5",
            global_exposure=Decimal("1.2"),
            stress_summary_reference="Stress Scenarios Q2 2024",
            methodology_version="VaR_HistoricalSimulation_v1.0",
        )

        stress_testing_input = ManagementStressTestingInput(
            scenario_name="Lehman Crisis 2008",
            scenario_type="Historical",
            portfolio_impact=Decimal("-0.125"),
            nav_impact=Decimal("-0.125"),
            worst_position="US0378331005",
            worst_sector="Financial Services",
            stress_date=date(2008, 9, 15),
            methodology_version="Stress_HistoricalSimulation_v1.0",
        )

        fund_summary = ManagementReportService.build_fund_summary(fund_summary_input)
        market_risk = ManagementReportService.build_market_risk(market_risk_input)
        stress_testing = ManagementReportService.build_stress_testing(stress_testing_input)
        report = ManagementReportService.build_report(fund_summary, market_risk, stress_testing)

        assert report.fund_summary.fund_name == "Global Equity UCITS Fund"
        assert report.fund_summary.nav == Decimal("250000000.00")
        assert report.market_risk is not None
        assert report.market_risk.var_value == Decimal("0.0275")
        assert report.stress_testing is not None
        assert report.stress_testing.scenario_name == "Lehman Crisis 2008"
        assert len(report.included_sections) == 3
        assert "Fund Summary" in report.included_sections
        assert "Market Risk" in report.included_sections
        assert "Stress Testing" in report.included_sections
