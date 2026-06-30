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
    AnnexIVLeverageInput,
    AnnexIVLeverageSection,
    AnnexIVReport,
    AnnexIVRiskMeasuresInput,
    AnnexIVRiskMeasuresSection,
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
    def build_risk_measures(
        input_data: AnnexIVRiskMeasuresInput,
    ) -> AnnexIVRiskMeasuresSection:
        """Build risk measures section from already-computed values.

        Parameters
        ----------
        input_data : AnnexIVRiskMeasuresInput
            Already-computed risk measure values (not calculated by this service).

        Returns
        -------
        AnnexIVRiskMeasuresSection
            Immutable risk measures section.

        Raises
        ------
        ValueError
            If values are invalid.
        """
        return AnnexIVRiskMeasuresSection(
            var_value=input_data.var_value,
            var_method=input_data.var_method,
            var_confidence_level=input_data.var_confidence_level,
            var_horizon_days=input_data.var_horizon_days,
            expected_shortfall=input_data.expected_shortfall,
            es_confidence_level=input_data.es_confidence_level,
            stress_test_reference=input_data.stress_test_reference,
            global_exposure=input_data.global_exposure,
            methodology_version=input_data.methodology_version,
        )

    @staticmethod
    def build_leverage(
        input_data: AnnexIVLeverageInput,
    ) -> AnnexIVLeverageSection:
        """Build leverage section from already-computed values.

        Parameters
        ----------
        input_data : AnnexIVLeverageInput
            Already-computed leverage measures (not calculated by this service).

        Returns
        -------
        AnnexIVLeverageSection
            Immutable leverage section.

        Raises
        ------
        ValueError
            If values are invalid.
        """
        return AnnexIVLeverageSection(
            gross_leverage_ratio=input_data.gross_leverage_ratio,
            commitment_leverage_ratio=input_data.commitment_leverage_ratio,
            gross_exposure=input_data.gross_exposure,
            commitment_exposure=input_data.commitment_exposure,
            nav=input_data.nav,
            leverage_methodology=input_data.leverage_methodology,
            methodology_version=input_data.methodology_version,
        )

    @staticmethod
    def build_report(
        fund_identification: AnnexIVFundIdentificationSection,
        asset_breakdown: Optional[AnnexIVAssetBreakdownSection] = None,
        risk_measures: Optional[AnnexIVRiskMeasuresSection] = None,
        leverage: Optional[AnnexIVLeverageSection] = None,
    ) -> AnnexIVReport:
        """Build Annex IV report from sections.

        Assembles fund identification and optionally asset breakdown, risk measures,
        and leverage into a consolidated report.

        Parameters
        ----------
        fund_identification : AnnexIVFundIdentificationSection
            Fund identification section.
        asset_breakdown : Optional[AnnexIVAssetBreakdownSection], optional
            Asset breakdown section. If supplied, will be included in report.
        risk_measures : Optional[AnnexIVRiskMeasuresSection], optional
            Risk measures section. If supplied, will be included in report.
        leverage : Optional[AnnexIVLeverageSection], optional
            Leverage section. If supplied, will be included in report.

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
        if risk_measures is not None:
            included_sections.append("Risk Measures")
        if leverage is not None:
            included_sections.append("Leverage")

        return AnnexIVReport(
            fund_identification=fund_identification,
            asset_breakdown=asset_breakdown,
            risk_measures=risk_measures,
            leverage=leverage,
            included_sections=included_sections,
        )
