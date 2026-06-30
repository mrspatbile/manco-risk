"""Annex IV reporting service.

Orchestration layer that assembles fund identification and report data
from typed inputs.

The service performs NO calculations. It only validates consistency
and packages supplied data into immutable report objects.
"""

from manco_risk.reporting.annex_iv import (
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
    def build_report(
        fund_identification: AnnexIVFundIdentificationSection,
    ) -> AnnexIVReport:
        """Build Annex IV report from sections.

        For this slice, the report contains only fund identification.
        Future slices will add asset breakdown, risk measures, leverage, liquidity.

        Parameters
        ----------
        fund_identification : AnnexIVFundIdentificationSection
            Fund identification section.

        Returns
        -------
        AnnexIVReport
            Immutable Annex IV report.

        Raises
        ------
        ValueError
            If fund_identification is invalid.
        """
        return AnnexIVReport(
            fund_identification=fund_identification,
            included_sections=["Fund Identification"],
        )
