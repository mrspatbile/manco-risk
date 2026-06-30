"""Annex IV reporting service.

Orchestration layer that assembles fund identification, asset breakdown,
and report data from typed inputs.

The service performs NO calculations. It only validates consistency
and packages supplied data into immutable report objects.
"""

from typing import Optional

from manco_risk.reporting.annex_iv import (
    AnnexIVAssetBreakdownInput,
    AnnexIVAssetBreakdownSection,
    AnnexIVFundIdentificationInput,
    AnnexIVFundIdentificationSection,
    AnnexIVReport,
)


class AnnexIVReportingService:
    """Annex IV reporting orchestration service.

    Assembles fund identification and other sections into a consolidated
    Annex IV-style report.

    The service:
    1. Receives typed input objects with source data and risk outputs.
    2. Validates consistency and required fields.
    3. Builds immutable result objects.

    The service performs NO calculations, only validation and assembly.

    Reference:
    - AIFMD Annex IV: AIF risk disclosures and reporting requirements.
    - UCITS Directive Annex IV: Fund identification and risk reporting.
    """

    @staticmethod
    def build_fund_identification(
        input_data: AnnexIVFundIdentificationInput,
    ) -> AnnexIVFundIdentificationSection:
        """Build fund identification section from source data.

        Parameters
        ----------
        input_data : AnnexIVFundIdentificationInput
            Source fund data (fund_id, fund_name, fund_regime, domicile,
            base_currency, valuation_date, reporting_period_end).

        Returns
        -------
        AnnexIVFundIdentificationSection
            Immutable fund identification section.

        Raises
        ------
        ValueError
            If required fields are empty or invalid.
        """
        return AnnexIVFundIdentificationSection(
            fund_id=input_data.fund_id,
            fund_name=input_data.fund_name,
            fund_regime=input_data.fund_regime,
            domicile=input_data.domicile,
            base_currency=input_data.base_currency,
            valuation_date=input_data.valuation_date,
            reporting_period_end=input_data.reporting_period_end,
        )

    @staticmethod
    def build_asset_breakdown(
        input_data: AnnexIVAssetBreakdownInput,
    ) -> AnnexIVAssetBreakdownSection:
        """Build asset breakdown section from pre-aggregated rows.

        Parameters
        ----------
        input_data : AnnexIVAssetBreakdownInput
            Pre-aggregated asset breakdown rows (not calculated or aggregated
            by this service).

        Returns
        -------
        AnnexIVAssetBreakdownSection
            Immutable asset breakdown section.

        Raises
        ------
        ValueError
            If rows are empty or invalid.
        """
        return AnnexIVAssetBreakdownSection(rows=input_data.rows)

    @staticmethod
    def build_report(
        fund_identification: AnnexIVFundIdentificationSection,
        asset_breakdown: Optional[AnnexIVAssetBreakdownSection] = None,
    ) -> AnnexIVReport:
        """Build Annex IV report from sections.

        Assembles fund identification and optionally asset breakdown
        into a consolidated report.

        Parameters
        ----------
        fund_identification : AnnexIVFundIdentificationSection
            Fund identification section.
        asset_breakdown : Optional[AnnexIVAssetBreakdownSection], optional
            Asset breakdown section. If supplied, will be included in report.

        Returns
        -------
        AnnexIVReport
            Immutable Annex IV report.

        Raises
        ------
        ValueError
            If sections are invalid.
        """
        included_sections = ["Fund Identification"]
        if asset_breakdown is not None:
            included_sections.append("Asset Breakdown")

        return AnnexIVReport(
            fund_identification=fund_identification,
            asset_breakdown=asset_breakdown,
            included_sections=included_sections,
        )
