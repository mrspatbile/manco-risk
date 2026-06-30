"""Tests for Annex IV reporting layer.

Tests fund identification, asset breakdown, and report assembly.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.reporting import (
    AnnexIVAssetBreakdownInput,
    AnnexIVAssetBreakdownRow,
    AnnexIVAssetBreakdownSection,
    AnnexIVFundIdentificationInput,
    AnnexIVFundIdentificationSection,
    AnnexIVReport,
    AnnexIVReportingService,
    AnnexIVRiskMeasuresInput,
    AnnexIVRiskMeasuresSection,
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


class TestAnnexIVAssetBreakdownRow:
    """Test asset breakdown row model."""

    def test_valid_row(self) -> None:
        """Valid asset breakdown row construction."""
        row = AnnexIVAssetBreakdownRow(
            asset_class="Equities",
            market_value=Decimal("500000.00"),
            nav_percentage=Decimal("0.50"),
        )

        assert row.asset_class == "Equities"
        assert row.market_value == Decimal("500000.00")
        assert row.nav_percentage == Decimal("0.50")
        assert row.currency is None
        assert row.exposure_basis is None

    def test_row_with_optional_fields(self) -> None:
        """Asset breakdown row with optional fields."""
        row = AnnexIVAssetBreakdownRow(
            asset_class="Bonds",
            market_value=Decimal("300000.00"),
            nav_percentage=Decimal("0.30"),
            currency="EUR",
            exposure_basis="Long",
        )

        assert row.asset_class == "Bonds"
        assert row.currency == "EUR"
        assert row.exposure_basis == "Long"

    def test_empty_asset_class_rejected(self) -> None:
        """Empty asset_class is rejected."""
        with pytest.raises(ValueError, match="asset_class must be non-empty"):
            AnnexIVAssetBreakdownRow(
                asset_class="",
                market_value=Decimal("100000.00"),
                nav_percentage=Decimal("0.10"),
            )

    def test_negative_market_value_rejected(self) -> None:
        """Negative market_value is rejected."""
        with pytest.raises(ValueError, match="market_value must be non-negative"):
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("-100000.00"),
                nav_percentage=Decimal("0.10"),
            )

    def test_negative_nav_percentage_rejected(self) -> None:
        """Negative nav_percentage is rejected."""
        with pytest.raises(ValueError, match="nav_percentage must be non-negative"):
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("100000.00"),
                nav_percentage=Decimal("-0.10"),
            )

    def test_zero_values_allowed(self) -> None:
        """Zero market_value and nav_percentage are allowed."""
        row = AnnexIVAssetBreakdownRow(
            asset_class="Cash",
            market_value=Decimal("0.00"),
            nav_percentage=Decimal("0.00"),
        )

        assert row.market_value == Decimal("0.00")
        assert row.nav_percentage == Decimal("0.00")

    def test_decimal_preservation(self) -> None:
        """Decimal type is preserved."""
        row = AnnexIVAssetBreakdownRow(
            asset_class="Equities",
            market_value=Decimal("123456.789"),
            nav_percentage=Decimal("0.234567"),
        )

        assert isinstance(row.market_value, Decimal)
        assert isinstance(row.nav_percentage, Decimal)
        assert row.market_value == Decimal("123456.789")
        assert row.nav_percentage == Decimal("0.234567")

    def test_immutability(self) -> None:
        """Asset breakdown row is immutable."""
        row = AnnexIVAssetBreakdownRow(
            asset_class="Equities",
            market_value=Decimal("100000.00"),
            nav_percentage=Decimal("0.10"),
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            row.asset_class = "Bonds"  # type: ignore


class TestAnnexIVAssetBreakdownInput:
    """Test asset breakdown input validation."""

    def test_valid_input(self) -> None:
        """Valid asset breakdown input construction."""
        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("500000.00"),
                nav_percentage=Decimal("0.50"),
            ),
            AnnexIVAssetBreakdownRow(
                asset_class="Bonds",
                market_value=Decimal("300000.00"),
                nav_percentage=Decimal("0.30"),
            ),
        ]

        input_data = AnnexIVAssetBreakdownInput(rows=rows)

        assert len(input_data.rows) == 2
        assert input_data.rows[0].asset_class == "Equities"
        assert input_data.rows[1].asset_class == "Bonds"

    def test_single_row_allowed(self) -> None:
        """Single row asset breakdown is allowed."""
        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("1000000.00"),
                nav_percentage=Decimal("1.00"),
            )
        ]

        input_data = AnnexIVAssetBreakdownInput(rows=rows)

        assert len(input_data.rows) == 1

    def test_empty_rows_rejected(self) -> None:
        """Empty rows list is rejected."""
        with pytest.raises(ValueError, match="Asset breakdown must contain at least one row"):
            AnnexIVAssetBreakdownInput(rows=[])

    def test_immutability(self) -> None:
        """Asset breakdown input is immutable."""
        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("100000.00"),
                nav_percentage=Decimal("0.10"),
            )
        ]

        input_data = AnnexIVAssetBreakdownInput(rows=rows)

        with pytest.raises(Exception):  # Pydantic frozen model raises
            input_data.rows = []  # type: ignore


class TestAnnexIVAssetBreakdownSection:
    """Test asset breakdown section model."""

    def test_valid_section(self) -> None:
        """Valid asset breakdown section construction."""
        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("500000.00"),
                nav_percentage=Decimal("0.50"),
            ),
            AnnexIVAssetBreakdownRow(
                asset_class="Bonds",
                market_value=Decimal("300000.00"),
                nav_percentage=Decimal("0.30"),
            ),
            AnnexIVAssetBreakdownRow(
                asset_class="Cash",
                market_value=Decimal("200000.00"),
                nav_percentage=Decimal("0.20"),
            ),
        ]

        section = AnnexIVAssetBreakdownSection(rows=rows)

        assert len(section.rows) == 3
        assert section.rows[0].asset_class == "Equities"
        assert section.rows[2].asset_class == "Cash"

    def test_empty_rows_rejected(self) -> None:
        """Empty rows list is rejected."""
        with pytest.raises(ValueError, match="Asset breakdown must contain at least one row"):
            AnnexIVAssetBreakdownSection(rows=[])

    def test_immutability(self) -> None:
        """Asset breakdown section is immutable."""
        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("100000.00"),
                nav_percentage=Decimal("0.10"),
            )
        ]

        section = AnnexIVAssetBreakdownSection(rows=rows)

        with pytest.raises(Exception):  # Pydantic frozen model raises
            section.rows = []  # type: ignore


class TestAnnexIVReportWithAssetBreakdown:
    """Test Annex IV report with asset breakdown."""

    def test_report_with_fund_identification_only(self) -> None:
        """Report with only fund identification."""
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
            asset_breakdown=None,
            included_sections=["Fund Identification"],
        )

        assert report.fund_identification is not None
        assert report.asset_breakdown is None
        assert "Fund Identification" in report.included_sections
        assert "Asset Breakdown" not in report.included_sections

    def test_report_with_fund_identification_and_asset_breakdown(self) -> None:
        """Report with both fund identification and asset breakdown."""
        fund_id_section = AnnexIVFundIdentificationSection(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("500000.00"),
                nav_percentage=Decimal("0.50"),
            ),
            AnnexIVAssetBreakdownRow(
                asset_class="Bonds",
                market_value=Decimal("500000.00"),
                nav_percentage=Decimal("0.50"),
            ),
        ]

        asset_breakdown_section = AnnexIVAssetBreakdownSection(rows=rows)

        report = AnnexIVReport(
            fund_identification=fund_id_section,
            asset_breakdown=asset_breakdown_section,
            included_sections=["Fund Identification", "Asset Breakdown"],
        )

        assert report.fund_identification is not None
        assert report.asset_breakdown is not None
        assert len(report.asset_breakdown.rows) == 2
        assert "Fund Identification" in report.included_sections
        assert "Asset Breakdown" in report.included_sections

    def test_report_immutability(self) -> None:
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
            report.asset_breakdown = None  # type: ignore


class TestAnnexIVReportingServiceAssetBreakdown:
    """Test asset breakdown service methods."""

    def test_build_asset_breakdown(self) -> None:
        """Service builds asset breakdown section from input."""
        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("500000.00"),
                nav_percentage=Decimal("0.50"),
            ),
            AnnexIVAssetBreakdownRow(
                asset_class="Bonds",
                market_value=Decimal("300000.00"),
                nav_percentage=Decimal("0.30"),
            ),
        ]

        input_data = AnnexIVAssetBreakdownInput(rows=rows)
        section = AnnexIVReportingService.build_asset_breakdown(input_data)

        assert len(section.rows) == 2
        assert section.rows[0].asset_class == "Equities"
        assert section.rows[1].asset_class == "Bonds"

    def test_build_report_fund_identification_only(self) -> None:
        """Service builds report with fund identification only."""
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

        assert report.fund_identification is not None
        assert report.asset_breakdown is None
        assert report.included_sections == ["Fund Identification"]

    def test_build_report_with_asset_breakdown(self) -> None:
        """Service builds report with fund identification and asset breakdown."""
        fund_id_section = AnnexIVFundIdentificationSection(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("500000.00"),
                nav_percentage=Decimal("0.50"),
            ),
        ]

        asset_breakdown_section = AnnexIVAssetBreakdownSection(rows=rows)

        report = AnnexIVReportingService.build_report(
            fund_id_section,
            asset_breakdown_section,
        )

        assert report.fund_identification is not None
        assert report.asset_breakdown is not None
        assert "Fund Identification" in report.included_sections
        assert "Asset Breakdown" in report.included_sections

    def test_full_workflow_ucits_with_asset_breakdown(self) -> None:
        """Full workflow: UCITS fund with asset breakdown."""
        # Fund identification
        fund_id_input = AnnexIVFundIdentificationInput(
            fund_id=101,
            fund_name="European Growth UCITS Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        fund_id_section = AnnexIVReportingService.build_fund_identification(fund_id_input)

        # Asset breakdown
        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("600000.00"),
                nav_percentage=Decimal("0.60"),
                currency="EUR",
                exposure_basis="Long",
            ),
            AnnexIVAssetBreakdownRow(
                asset_class="Bonds",
                market_value=Decimal("300000.00"),
                nav_percentage=Decimal("0.30"),
                currency="EUR",
                exposure_basis="Long",
            ),
            AnnexIVAssetBreakdownRow(
                asset_class="Cash",
                market_value=Decimal("100000.00"),
                nav_percentage=Decimal("0.10"),
                currency="EUR",
            ),
        ]

        asset_breakdown_input = AnnexIVAssetBreakdownInput(rows=rows)
        asset_breakdown_section = AnnexIVReportingService.build_asset_breakdown(
            asset_breakdown_input
        )

        # Build report
        report = AnnexIVReportingService.build_report(
            fund_id_section,
            asset_breakdown_section,
        )

        assert report.fund_identification.fund_name == "European Growth UCITS Fund"
        assert report.fund_identification.fund_regime == "UCITS"
        assert len(report.asset_breakdown.rows) == 3
        assert report.asset_breakdown.rows[0].asset_class == "Equities"
        assert report.asset_breakdown.rows[0].nav_percentage == Decimal("0.60")

    def test_full_workflow_aif_with_asset_breakdown(self) -> None:
        """Full workflow: AIF fund with asset breakdown."""
        fund_id_input = AnnexIVFundIdentificationInput(
            fund_id=202,
            fund_name="Strategic Opportunities AIF",
            fund_regime="AIF",
            domicile="IE",
            base_currency="USD",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        fund_id_section = AnnexIVReportingService.build_fund_identification(fund_id_input)

        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("400000.00"),
                nav_percentage=Decimal("0.40"),
                exposure_basis="Long",
            ),
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("100000.00"),
                nav_percentage=Decimal("0.10"),
                exposure_basis="Short",
            ),
            AnnexIVAssetBreakdownRow(
                asset_class="Derivatives",
                market_value=Decimal("500000.00"),
                nav_percentage=Decimal("0.50"),
                exposure_basis="Notional",
            ),
        ]

        asset_breakdown_input = AnnexIVAssetBreakdownInput(rows=rows)
        asset_breakdown_section = AnnexIVReportingService.build_asset_breakdown(
            asset_breakdown_input
        )

        report = AnnexIVReportingService.build_report(
            fund_id_section,
            asset_breakdown_section,
        )

        assert report.fund_identification.fund_regime == "AIF"
        assert len(report.asset_breakdown.rows) == 3
        assert report.asset_breakdown.rows[1].exposure_basis == "Short"
        assert report.asset_breakdown.rows[2].asset_class == "Derivatives"

    def test_service_does_not_aggregate_positions(self) -> None:
        """Service does not aggregate positions."""
        # Service accepts pre-aggregated rows as-is
        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("250000.00"),
                nav_percentage=Decimal("0.25"),
            ),
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("250000.00"),
                nav_percentage=Decimal("0.25"),
            ),
        ]

        # Service accepts two separate Equities rows without combining them
        input_data = AnnexIVAssetBreakdownInput(rows=rows)
        section = AnnexIVReportingService.build_asset_breakdown(input_data)

        assert len(section.rows) == 2
        assert section.rows[0].asset_class == "Equities"
        assert section.rows[1].asset_class == "Equities"
        # Not aggregated to single Equities row with 500000


class TestAnnexIVRiskMeasuresInput:
    """Test risk measures input validation."""

    def test_valid_input_var_only(self) -> None:
        """Valid risk measures input with VaR only."""
        input_data = AnnexIVRiskMeasuresInput(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
        )

        assert input_data.var_value == Decimal("0.025")
        assert input_data.var_method == "Historical"
        assert input_data.var_confidence_level == Decimal("0.95")
        assert input_data.var_horizon_days == 1
        assert input_data.expected_shortfall is None

    def test_valid_input_with_es(self) -> None:
        """Valid risk measures input with VaR and ES."""
        input_data = AnnexIVRiskMeasuresInput(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
            expected_shortfall=Decimal("0.040"),
            es_confidence_level=Decimal("0.95"),
        )

        assert input_data.var_value == Decimal("0.025")
        assert input_data.expected_shortfall == Decimal("0.040")
        assert input_data.es_confidence_level == Decimal("0.95")

    def test_valid_input_with_all_fields(self) -> None:
        """Valid risk measures input with all optional fields."""
        input_data = AnnexIVRiskMeasuresInput(
            var_value=Decimal("0.025"),
            var_method="Parametric",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
            expected_shortfall=Decimal("0.040"),
            es_confidence_level=Decimal("0.95"),
            stress_test_reference="Market Stress 2020",
            global_exposure=Decimal("1.5"),
            methodology_version="1.2",
        )

        assert input_data.var_method == "Parametric"
        assert input_data.stress_test_reference == "Market Stress 2020"
        assert input_data.global_exposure == Decimal("1.5")
        assert input_data.methodology_version == "1.2"

    def test_empty_var_method_rejected(self) -> None:
        """Empty var_method is rejected."""
        with pytest.raises(ValueError, match="var_method must be non-empty"):
            AnnexIVRiskMeasuresInput(
                var_value=Decimal("0.025"),
                var_method="",
                var_confidence_level=Decimal("0.95"),
                var_horizon_days=1,
            )

    def test_negative_var_value_rejected(self) -> None:
        """Negative var_value is rejected."""
        with pytest.raises(ValueError, match="var_value must be non-negative"):
            AnnexIVRiskMeasuresInput(
                var_value=Decimal("-0.025"),
                var_method="Historical",
                var_confidence_level=Decimal("0.95"),
                var_horizon_days=1,
            )

    def test_negative_var_confidence_level_rejected(self) -> None:
        """Negative var_confidence_level is rejected."""
        with pytest.raises(ValueError, match="var_confidence_level must be non-negative"):
            AnnexIVRiskMeasuresInput(
                var_value=Decimal("0.025"),
                var_method="Historical",
                var_confidence_level=Decimal("-0.95"),
                var_horizon_days=1,
            )

    def test_non_positive_var_horizon_days_rejected(self) -> None:
        """Non-positive var_horizon_days is rejected."""
        with pytest.raises(ValueError, match="var_horizon_days must be positive"):
            AnnexIVRiskMeasuresInput(
                var_value=Decimal("0.025"),
                var_method="Historical",
                var_confidence_level=Decimal("0.95"),
                var_horizon_days=0,
            )

    def test_negative_expected_shortfall_rejected(self) -> None:
        """Negative expected_shortfall is rejected."""
        with pytest.raises(ValueError, match="expected_shortfall must be non-negative"):
            AnnexIVRiskMeasuresInput(
                var_value=Decimal("0.025"),
                var_method="Historical",
                var_confidence_level=Decimal("0.95"),
                var_horizon_days=1,
                expected_shortfall=Decimal("-0.040"),
            )

    def test_negative_global_exposure_rejected(self) -> None:
        """Negative global_exposure is rejected."""
        with pytest.raises(ValueError, match="global_exposure must be non-negative"):
            AnnexIVRiskMeasuresInput(
                var_value=Decimal("0.025"),
                var_method="Historical",
                var_confidence_level=Decimal("0.95"),
                var_horizon_days=1,
                global_exposure=Decimal("-0.5"),
            )

    def test_zero_values_allowed(self) -> None:
        """Zero values are allowed."""
        input_data = AnnexIVRiskMeasuresInput(
            var_value=Decimal("0.0"),
            var_method="Historical",
            var_confidence_level=Decimal("0.0"),
            var_horizon_days=1,
        )

        assert input_data.var_value == Decimal("0.0")
        assert input_data.var_confidence_level == Decimal("0.0")

    def test_decimal_preservation(self) -> None:
        """Decimal type is preserved."""
        input_data = AnnexIVRiskMeasuresInput(
            var_value=Decimal("0.0251234567"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
        )

        assert isinstance(input_data.var_value, Decimal)
        assert input_data.var_value == Decimal("0.0251234567")

    def test_immutability(self) -> None:
        """Risk measures input is immutable."""
        input_data = AnnexIVRiskMeasuresInput(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            input_data.var_method = "Parametric"  # type: ignore


class TestAnnexIVRiskMeasuresSection:
    """Test risk measures section model."""

    def test_valid_section_var_only(self) -> None:
        """Valid risk measures section with VaR only."""
        section = AnnexIVRiskMeasuresSection(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
        )

        assert section.var_value == Decimal("0.025")
        assert section.var_method == "Historical"
        assert section.var_confidence_level == Decimal("0.95")
        assert section.var_horizon_days == 1

    def test_valid_section_with_es(self) -> None:
        """Valid risk measures section with VaR and ES."""
        section = AnnexIVRiskMeasuresSection(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
            expected_shortfall=Decimal("0.040"),
            es_confidence_level=Decimal("0.95"),
        )

        assert section.expected_shortfall == Decimal("0.040")
        assert section.es_confidence_level == Decimal("0.95")

    def test_valid_section_with_all_fields(self) -> None:
        """Valid risk measures section with all fields."""
        section = AnnexIVRiskMeasuresSection(
            var_value=Decimal("0.025"),
            var_method="Student-t",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
            expected_shortfall=Decimal("0.040"),
            es_confidence_level=Decimal("0.95"),
            stress_test_reference="Scenario A",
            global_exposure=Decimal("2.0"),
            methodology_version="2.1",
        )

        assert section.var_method == "Student-t"
        assert section.global_exposure == Decimal("2.0")
        assert section.methodology_version == "2.1"

    def test_empty_var_method_rejected(self) -> None:
        """Empty var_method is rejected."""
        with pytest.raises(ValueError, match="var_method must be non-empty"):
            AnnexIVRiskMeasuresSection(
                var_value=Decimal("0.025"),
                var_method="",
                var_confidence_level=Decimal("0.95"),
                var_horizon_days=1,
            )

    def test_negative_var_value_rejected(self) -> None:
        """Negative var_value is rejected."""
        with pytest.raises(ValueError, match="var_value must be non-negative"):
            AnnexIVRiskMeasuresSection(
                var_value=Decimal("-0.025"),
                var_method="Historical",
                var_confidence_level=Decimal("0.95"),
                var_horizon_days=1,
            )

    def test_immutability(self) -> None:
        """Risk measures section is immutable."""
        section = AnnexIVRiskMeasuresSection(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            section.var_method = "Parametric"  # type: ignore


class TestAnnexIVReportWithRiskMeasures:
    """Test Annex IV report with risk measures."""

    def test_report_with_all_sections(self) -> None:
        """Report with fund identification, asset breakdown, and risk measures."""
        fund_id_section = AnnexIVFundIdentificationSection(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("500000.00"),
                nav_percentage=Decimal("0.50"),
            ),
        ]
        asset_breakdown_section = AnnexIVAssetBreakdownSection(rows=rows)

        risk_measures_section = AnnexIVRiskMeasuresSection(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
            expected_shortfall=Decimal("0.040"),
        )

        report = AnnexIVReport(
            fund_identification=fund_id_section,
            asset_breakdown=asset_breakdown_section,
            risk_measures=risk_measures_section,
            included_sections=["Fund Identification", "Asset Breakdown", "Risk Measures"],
        )

        assert report.fund_identification is not None
        assert report.asset_breakdown is not None
        assert report.risk_measures is not None
        assert "Fund Identification" in report.included_sections
        assert "Asset Breakdown" in report.included_sections
        assert "Risk Measures" in report.included_sections

    def test_report_with_fund_id_and_risk_measures(self) -> None:
        """Report with fund identification and risk measures (no asset breakdown)."""
        fund_id_section = AnnexIVFundIdentificationSection(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        risk_measures_section = AnnexIVRiskMeasuresSection(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
        )

        report = AnnexIVReport(
            fund_identification=fund_id_section,
            risk_measures=risk_measures_section,
            included_sections=["Fund Identification", "Risk Measures"],
        )

        assert report.asset_breakdown is None
        assert report.risk_measures is not None
        assert "Asset Breakdown" not in report.included_sections
        assert "Risk Measures" in report.included_sections

    def test_report_immutability_with_risk_measures(self) -> None:
        """Annex IV report with risk measures is immutable."""
        fund_id_section = AnnexIVFundIdentificationSection(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        risk_measures_section = AnnexIVRiskMeasuresSection(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
        )

        report = AnnexIVReport(
            fund_identification=fund_id_section,
            risk_measures=risk_measures_section,
            included_sections=["Fund Identification", "Risk Measures"],
        )

        with pytest.raises(Exception):  # Pydantic frozen model raises
            report.risk_measures = None  # type: ignore


class TestAnnexIVReportingServiceRiskMeasures:
    """Test risk measures service methods."""

    def test_build_risk_measures(self) -> None:
        """Service builds risk measures section from input."""
        input_data = AnnexIVRiskMeasuresInput(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
            expected_shortfall=Decimal("0.040"),
        )

        section = AnnexIVReportingService.build_risk_measures(input_data)

        assert section.var_value == Decimal("0.025")
        assert section.var_method == "Historical"
        assert section.expected_shortfall == Decimal("0.040")

    def test_build_report_with_all_sections(self) -> None:
        """Service builds report with all sections."""
        fund_id_section = AnnexIVFundIdentificationSection(
            fund_id=1,
            fund_name="Test Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )

        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("500000.00"),
                nav_percentage=Decimal("0.50"),
            ),
        ]
        asset_breakdown_section = AnnexIVAssetBreakdownSection(rows=rows)

        risk_measures_section = AnnexIVRiskMeasuresSection(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
        )

        report = AnnexIVReportingService.build_report(
            fund_id_section,
            asset_breakdown_section,
            risk_measures_section,
        )

        assert report.fund_identification is not None
        assert report.asset_breakdown is not None
        assert report.risk_measures is not None
        assert "Fund Identification" in report.included_sections
        assert "Asset Breakdown" in report.included_sections
        assert "Risk Measures" in report.included_sections

    def test_full_workflow_ucits_with_risk_measures(self) -> None:
        """Full workflow: UCITS fund with all sections."""
        # Fund identification
        fund_id_input = AnnexIVFundIdentificationInput(
            fund_id=101,
            fund_name="European Growth UCITS Fund",
            fund_regime="UCITS",
            domicile="LU",
            base_currency="EUR",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )
        fund_id_section = AnnexIVReportingService.build_fund_identification(fund_id_input)

        # Asset breakdown
        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("600000.00"),
                nav_percentage=Decimal("0.60"),
            ),
            AnnexIVAssetBreakdownRow(
                asset_class="Bonds",
                market_value=Decimal("400000.00"),
                nav_percentage=Decimal("0.40"),
            ),
        ]
        asset_breakdown_input = AnnexIVAssetBreakdownInput(rows=rows)
        asset_breakdown_section = AnnexIVReportingService.build_asset_breakdown(
            asset_breakdown_input
        )

        # Risk measures
        risk_measures_input = AnnexIVRiskMeasuresInput(
            var_value=Decimal("0.0250"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
            expected_shortfall=Decimal("0.0400"),
            es_confidence_level=Decimal("0.95"),
            global_exposure=Decimal("1.0"),
            methodology_version="1.0",
        )
        risk_measures_section = AnnexIVReportingService.build_risk_measures(risk_measures_input)

        # Build report
        report = AnnexIVReportingService.build_report(
            fund_id_section,
            asset_breakdown_section,
            risk_measures_section,
        )

        assert report.fund_identification.fund_name == "European Growth UCITS Fund"
        assert report.asset_breakdown.rows[0].asset_class == "Equities"
        assert report.risk_measures.var_value == Decimal("0.0250")
        assert report.risk_measures.var_method == "Historical"
        assert len(report.included_sections) == 3

    def test_full_workflow_aif_with_risk_measures(self) -> None:
        """Full workflow: AIF fund with risk measures."""
        fund_id_input = AnnexIVFundIdentificationInput(
            fund_id=202,
            fund_name="Strategic Opportunities AIF",
            fund_regime="AIF",
            domicile="IE",
            base_currency="USD",
            valuation_date=date(2024, 6, 30),
            reporting_period_end=date(2024, 6, 30),
        )
        fund_id_section = AnnexIVReportingService.build_fund_identification(fund_id_input)

        rows = [
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("400000.00"),
                nav_percentage=Decimal("0.40"),
                exposure_basis="Long",
            ),
            AnnexIVAssetBreakdownRow(
                asset_class="Equities",
                market_value=Decimal("100000.00"),
                nav_percentage=Decimal("0.10"),
                exposure_basis="Short",
            ),
        ]
        asset_breakdown_input = AnnexIVAssetBreakdownInput(rows=rows)
        asset_breakdown_section = AnnexIVReportingService.build_asset_breakdown(
            asset_breakdown_input
        )

        risk_measures_input = AnnexIVRiskMeasuresInput(
            var_value=Decimal("0.0350"),
            var_method="Parametric",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
            expected_shortfall=Decimal("0.0550"),
            stress_test_reference="Market Stress 2022",
            global_exposure=Decimal("1.5"),
            methodology_version="2.0",
        )
        risk_measures_section = AnnexIVReportingService.build_risk_measures(risk_measures_input)

        report = AnnexIVReportingService.build_report(
            fund_id_section,
            asset_breakdown_section,
            risk_measures_section,
        )

        assert report.fund_identification.fund_regime == "AIF"
        assert report.risk_measures.var_method == "Parametric"
        assert report.risk_measures.global_exposure == Decimal("1.5")
        assert report.risk_measures.stress_test_reference == "Market Stress 2022"

    def test_service_does_not_calculate_var(self) -> None:
        """Service accepts VaR values as-is, does not calculate."""
        # Service accepts pre-computed VaR
        input_data = AnnexIVRiskMeasuresInput(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
        )

        section = AnnexIVReportingService.build_risk_measures(input_data)

        # Value is passed through unchanged
        assert section.var_value == Decimal("0.025")
        # No calculation fields
        assert not hasattr(section, "num_scenarios")
        assert not hasattr(section, "quantile_index")

    def test_service_does_not_calculate_es(self) -> None:
        """Service accepts ES values as-is, does not calculate."""
        input_data = AnnexIVRiskMeasuresInput(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
            expected_shortfall=Decimal("0.040"),
        )

        section = AnnexIVReportingService.build_risk_measures(input_data)

        # Value is passed through unchanged
        assert section.expected_shortfall == Decimal("0.040")

    def test_service_is_stateless(self) -> None:
        """Service is stateless."""
        input_data = AnnexIVRiskMeasuresInput(
            var_value=Decimal("0.025"),
            var_method="Historical",
            var_confidence_level=Decimal("0.95"),
            var_horizon_days=1,
        )

        section1 = AnnexIVReportingService.build_risk_measures(input_data)
        section2 = AnnexIVReportingService.build_risk_measures(input_data)

        assert section1 == section2
