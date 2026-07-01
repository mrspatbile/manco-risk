"""Management reporting service.

Orchestration layer that assembles fund summary and management report data
from typed inputs.

The service performs NO calculations. It only validates consistency
and packages supplied data into immutable report objects.
"""

from typing import Optional

from manco_risk.reporting.management_report import (
    ManagementFundSummaryInput,
    ManagementFundSummarySection,
    ManagementMarketRiskInput,
    ManagementMarketRiskSection,
    ManagementRiskReport,
    ManagementStressTestingInput,
    ManagementStressTestingSection,
)


class ManagementReportService:
    """Management reporting orchestration service.

    Assembles fund summary into a consolidated management report.

    The service:
    1. Receives typed input objects with source data.
    2. Validates consistency and required fields.
    3. Builds immutable result objects.

    The service performs NO calculations, only validation and assembly.

    Reference:
    - Management reporting for fund governance and review.
    - Board risk reporting outputs.
    """

    @staticmethod
    def build_fund_summary(
        input_data: ManagementFundSummaryInput,
    ) -> ManagementFundSummarySection:
        """Build fund summary section from source data.

        Parameters
        ----------
        input_data : ManagementFundSummaryInput
            Source fund data (fund_id, fund_name, fund_regime, base_currency,
            valuation_date, nav, optional aum, inception_date, reporting_period_end,
            methodology_version).

        Returns
        -------
        ManagementFundSummarySection
            Immutable fund summary section.

        Raises
        ------
        ValueError
            If required fields are empty or invalid.
        """
        return ManagementFundSummarySection(
            fund_id=input_data.fund_id,
            fund_name=input_data.fund_name,
            fund_regime=input_data.fund_regime,
            base_currency=input_data.base_currency,
            valuation_date=input_data.valuation_date,
            nav=input_data.nav,
            aum=input_data.aum,
            inception_date=input_data.inception_date,
            reporting_period_end=input_data.reporting_period_end,
            methodology_version=input_data.methodology_version,
        )

    @staticmethod
    def build_market_risk(
        input_data: ManagementMarketRiskInput,
    ) -> ManagementMarketRiskSection:
        """Build market risk section from already-computed outputs.

        Parameters
        ----------
        input_data : ManagementMarketRiskInput
            Already-computed market risk data (var_value, var_method,
            optional expected_shortfall, srri_class, global_exposure,
            stress_summary_reference, methodology_version).

        Returns
        -------
        ManagementMarketRiskSection
            Immutable market risk section.

        Raises
        ------
        ValueError
            If required fields are empty or invalid.
        """
        return ManagementMarketRiskSection(
            var_value=input_data.var_value,
            var_method=input_data.var_method,
            expected_shortfall=input_data.expected_shortfall,
            srri_class=input_data.srri_class,
            global_exposure=input_data.global_exposure,
            stress_summary_reference=input_data.stress_summary_reference,
            methodology_version=input_data.methodology_version,
        )

    @staticmethod
    def build_stress_testing(
        input_data: ManagementStressTestingInput,
    ) -> ManagementStressTestingSection:
        """Build stress testing section from already-computed outputs.

        Parameters
        ----------
        input_data : ManagementStressTestingInput
            Already-computed stress testing data (scenario_name, scenario_type,
            portfolio_impact, optional nav_impact, worst_position, worst_sector,
            stress_date, methodology_version).

        Returns
        -------
        ManagementStressTestingSection
            Immutable stress testing section.

        Raises
        ------
        ValueError
            If required fields are empty or invalid.
        """
        return ManagementStressTestingSection(
            scenario_name=input_data.scenario_name,
            scenario_type=input_data.scenario_type,
            portfolio_impact=input_data.portfolio_impact,
            nav_impact=input_data.nav_impact,
            worst_position=input_data.worst_position,
            worst_sector=input_data.worst_sector,
            stress_date=input_data.stress_date,
            methodology_version=input_data.methodology_version,
        )

    @staticmethod
    def build_report(
        fund_summary: ManagementFundSummarySection,
        market_risk: Optional[ManagementMarketRiskSection] = None,
        stress_testing: Optional[ManagementStressTestingSection] = None,
    ) -> ManagementRiskReport:
        """Build management report from sections.

        For Slice 1, includes fund summary section only.
        For Slice 2+, optionally includes market risk and stress testing.

        Parameters
        ----------
        fund_summary : ManagementFundSummarySection
            Fund summary section (required).
        market_risk : Optional[ManagementMarketRiskSection], optional
            Market risk section. If supplied, will be included in report.
        stress_testing : Optional[ManagementStressTestingSection], optional
            Stress testing section. If supplied, will be included in report.

        Returns
        -------
        ManagementRiskReport
            Immutable management risk report.

        Raises
        ------
        ValueError
            If sections are invalid.
        """
        included_sections = ["Fund Summary"]
        if market_risk is not None:
            included_sections.append("Market Risk")
        if stress_testing is not None:
            included_sections.append("Stress Testing")

        return ManagementRiskReport(
            fund_summary=fund_summary,
            market_risk=market_risk,
            stress_testing=stress_testing,
            included_sections=included_sections,
        )
