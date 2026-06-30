"""Tests for management reporting layer.

Tests fund summary, management report assembly, and service functionality.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.reporting.management_report import (
    ManagementFundSummaryInput,
    ManagementFundSummarySection,
    ManagementRiskReport,
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
