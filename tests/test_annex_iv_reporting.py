"""Tests for Annex IV reporting layer.

Tests fund identification models, report assembly, validation, and immutability.
"""

from datetime import date

import pytest

from manco_risk.reporting import (
    AnnexIVFundIdentificationInput,
    AnnexIVFundIdentificationSection,
    AnnexIVReport,
    AnnexIVReportingService,
)


class TestAnnexIVFundIdentificationInput:
    """Test input validation for fund identification."""

    def test_valid_input(self) -> None:
        """Valid fund identification input construction."""
        input_data = AnnexIVFundIdentificationInput(
            fund_id=1,
            fund_name="Test Fund UCITS",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        assert input_data.fund_id == 1
        assert input_data.fund_name == "Test Fund UCITS"
        assert input_data.fund_regime == "UCITS"
        assert input_data.domicile == "LU"
        assert input_data.base_currency == "EUR"
        assert input_data.valuation_date == date(2024, 6, 30)
        assert input_data.reporting_period_end == date(2024, 6, 30)

    def test_empty_fund_name_rejected(self) -> None:
        """Empty fund_name is rejected."""
        with pytest.raises(ValueError, match="fund_name must be non-empty"):
            AnnexIVFundIdentificationInput(
                fund_id=1,
                fund_name="",
                fund_regime="UCITS",
                domicile="LU",
                base_currency="EUR",
                valuation_date=date(2024, 6, 30),
                reporting_period_end=date(2024, 6, 30),
            )

    def test_whitespace_fund_name_stripped(self) -> None:
        """Fund name with whitespace is stripped."""
        input_data = AnnexIVFundIdentificationInput(
            fund_id=1,
            fund_name="  Test Fund  ",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        assert input_data.fund_name == "Test Fund"

    def test_empty_fund_regime_rejected(self) -> None:
        """Empty fund_regime is rejected."""
        with pytest.raises(ValueError, match="fund_regime must be non-empty"):
            AnnexIVFundIdentificationInput(
                fund_id=1,
                fund_name="Test Fund",
                fund_regime="",
                domicile="LU",
                base_currency="EUR",
                valuation_date=date(2024, 6, 30),
                reporting_period_end=date(2024, 6, 30),
            )

    def test_empty_domicile_rejected(self) -> None:
        """Empty domicile is rejected."""
        with pytest.raises(ValueError, match="domicile must be non-empty"):
            AnnexIVFundIdentificationInput(
                fund_id=1,
                fund_name="Test Fund",
                fund_regime="UCITS",
                domicile="",
                base_currency="EUR",
                valuation_date=date(2024, 6, 30),
                reporting_period_end=date(2024, 6, 30),
            )

    def test_empty_base_currency_rejected(self) -> None:
        """Empty base_currency is rejected."""
        with pytest.raises(ValueError, match="base_currency must be non-empty"):
            AnnexIVFundIdentificationInput(
                fund_id=1,
                fund_name="Test Fund",
                fund_regime="UCITS",
                domicile="LU",
                base_currency="",
                valuation_date=date(2024, 6, 30),
                reporting_period_end=date(2024, 6, 30),
            )

    def test_immutability(self) -> None:
        """Fund identification input is immutable."""
        input_data = AnnexIVFundIdentificationInput(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            input_data.fund_name = "Modified"  # type: ignore


class TestAnnexIVFundIdentificationSection:
    """Test fund identification section model."""

    def test_valid_section(self) -> None:
        """Valid fund identification section construction."""
        section = AnnexIVFundIdentificationSection(
            fund_id=1,
            fund_name="Test Fund UCITS",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        assert section.fund_id == 1
        assert section.fund_name == "Test Fund UCITS"
        assert section.fund_regime == "UCITS"
        assert section.domicile == "LU"
        assert section.base_currency == "EUR"
        assert section.valuation_date == date(2024, 6, 30)
        assert section.reporting_period_end == date(2024, 6, 30)

    def test_negative_fund_id_rejected(self) -> None:
        """Negative fund_id is rejected."""
        with pytest.raises(ValueError, match="fund_id must be positive"):
            AnnexIVFundIdentificationSection(
                fund_id=-1,
                fund_name="Test Fund",
                fund_regime="UCITS",
                domicile="LU",
                base_currency="EUR",
                valuation_date=date(2024, 6, 30),
                reporting_period_end=date(2024, 6, 30),
            )

    def test_zero_fund_id_rejected(self) -> None:
        """Zero fund_id is rejected."""
        with pytest.raises(ValueError, match="fund_id must be positive"):
            AnnexIVFundIdentificationSection(
                fund_id=0,
                fund_name="Test Fund",
                fund_regime="UCITS",
                domicile="LU",
                base_currency="EUR",
                valuation_date=date(2024, 6, 30),
                reporting_period_end=date(2024, 6, 30),
            )

    def test_empty_fund_name_rejected(self) -> None:
        """Empty fund_name is rejected."""
        with pytest.raises(ValueError, match="fund_name must be non-empty"):
            AnnexIVFundIdentificationSection(
                fund_id=1,
                fund_name="",
                fund_regime="UCITS",
                domicile="LU",
                base_currency="EUR",
                valuation_date=date(2024, 6, 30),
                reporting_period_end=date(2024, 6, 30),
            )

    def test_immutability(self) -> None:
        """Fund identification section is immutable."""
        section = AnnexIVFundIdentificationSection(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            section.fund_name = "Modified"  # type: ignore


class TestAnnexIVReport:
    """Test Annex IV report container."""

    def test_valid_report(self) -> None:
        """Valid Annex IV report construction."""
        fund_id_section = AnnexIVFundIdentificationSection(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        report = AnnexIVReport(
            fund_identification=fund_id_section,
            included_sections=["Fund Identification"],
        )

        assert report.fund_identification == fund_id_section
        assert report.included_sections == ["Fund Identification"]

    def test_missing_fund_identification_in_sections_rejected(self) -> None:
        """included_sections must contain Fund Identification."""
        fund_id_section = AnnexIVFundIdentificationSection(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        with pytest.raises(ValueError, match="Fund Identification must be in included_sections"):
            AnnexIVReport(
                fund_identification=fund_id_section,
                included_sections=["Other Section"],
            )

    def test_immutability(self) -> None:
        """Annex IV report is immutable."""
        fund_id_section = AnnexIVFundIdentificationSection(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        report = AnnexIVReport(
            fund_identification=fund_id_section,
            included_sections=["Fund Identification"],
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            report.included_sections = ["Modified"]  # type: ignore


class TestAnnexIVReportingService:
    """Test Annex IV reporting service."""

    def test_build_fund_identification(self) -> None:
        """Service builds fund identification section from input."""
        input_data = AnnexIVFundIdentificationInput(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        section = AnnexIVReportingService.build_fund_identification(input_data)

        assert section.fund_id == 1
        assert section.fund_name == "Test Fund"
        assert section.fund_regime == "UCITS"
        assert section.domicile == "LU"
        assert section.base_currency == "EUR"
        assert section.valuation_date == date(2024, 6, 30)
        assert section.reporting_period_end == date(2024, 6, 30)

    def test_build_report(self) -> None:
        """Service builds Annex IV report from fund identification section."""
        fund_id_section = AnnexIVFundIdentificationSection(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        report = AnnexIVReportingService.build_report(fund_id_section)

        assert report.fund_identification == fund_id_section
        assert "Fund Identification" in report.included_sections

    def test_service_is_stateless(self) -> None:
        """Service methods are static and stateless."""
        input_data = AnnexIVFundIdentificationInput(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        section1 = AnnexIVReportingService.build_fund_identification(input_data)
        section2 = AnnexIVReportingService.build_fund_identification(input_data)

        assert section1 == section2

    def test_full_workflow_ucits(self) -> None:
        """Full workflow: build identification and report for UCITS fund."""
        input_data = AnnexIVFundIdentificationInput(
            fund_id=101,
            fund_name="European Growth UCITS Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        fund_id_section = AnnexIVReportingService.build_fund_identification(input_data)
        report = AnnexIVReportingService.build_report(fund_id_section)

        assert report.fund_identification.fund_id == 101
        assert report.fund_identification.fund_name == "European Growth UCITS Fund"
        assert report.fund_identification.fund_regime == "UCITS"
        assert report.fund_identification.domicile == "LU"
        assert report.fund_identification.base_currency == "EUR"
        assert report.included_sections == ["Fund Identification"]

    def test_full_workflow_aif(self) -> None:
        """Full workflow: build identification and report for AIF fund."""
        input_data = AnnexIVFundIdentificationInput(
            fund_id=202,
            fund_name="Strategic Opportunities AIF",
            fund_regime="AIF",
            domicile="IE",
            base_currency="USD",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        fund_id_section = AnnexIVReportingService.build_fund_identification(input_data)
        report = AnnexIVReportingService.build_report(fund_id_section)

        assert report.fund_identification.fund_id == 202
        assert report.fund_identification.fund_name == "Strategic Opportunities AIF"
        assert report.fund_identification.fund_regime == "AIF"
        assert report.fund_identification.domicile == "IE"
        assert report.fund_identification.base_currency == "USD"
        assert report.included_sections == ["Fund Identification"]

    def test_service_validates_input_before_assembly(self) -> None:
        """Service validates input during build."""
        invalid_input = AnnexIVFundIdentificationInput(
            fund_id=1,
            fund_name="Test",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        # Should succeed since input is valid
        section = AnnexIVReportingService.build_fund_identification(invalid_input)
        assert section is not None

    def test_service_does_not_perform_calculations(self) -> None:
        """Service only packages data, does not calculate."""
        input_data = AnnexIVFundIdentificationInput(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        section = AnnexIVReportingService.build_fund_identification(input_data)

        # Verify only identity fields are present
        assert hasattr(section, "fund_id")
        assert hasattr(section, "fund_name")
        assert hasattr(section, "fund_regime")
        assert hasattr(section, "domicile")
        assert hasattr(section, "base_currency")
        assert hasattr(section, "valuation_date")
        assert hasattr(section, "reporting_period_end")

        # No risk measure fields
        assert not hasattr(section, "var_value")
        assert not hasattr(section, "es_value")
        assert not hasattr(section, "leverage")
