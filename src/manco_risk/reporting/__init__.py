"""Reporting layer for manco-risk.

Assembles risk calculations and source data into export-ready reports.

Does not perform risk calculations. Calculations are performed in the risk module.
"""

from manco_risk.reporting.annex_iv import (
    AnnexIVAssetBreakdownInput,
    AnnexIVAssetBreakdownRow,
    AnnexIVAssetBreakdownSection,
    AnnexIVFundIdentificationInput,
    AnnexIVFundIdentificationSection,
    AnnexIVLeverageInput,
    AnnexIVLeverageSection,
    AnnexIVLiquidityProfileInput,
    AnnexIVLiquidityProfileSection,
    AnnexIVReport,
    AnnexIVRiskMeasuresInput,
    AnnexIVRiskMeasuresSection,
)
from manco_risk.reporting.annex_iv_service import AnnexIVReportingService
from manco_risk.reporting.management_report import (
    ManagementExceptionItem,
    ManagementExceptionSummaryInput,
    ManagementExceptionSummarySection,
    ManagementFundSummaryInput,
    ManagementFundSummarySection,
    ManagementLeverageInput,
    ManagementLeverageSection,
    ManagementLiquidityInput,
    ManagementLiquiditySection,
    ManagementMarketRiskInput,
    ManagementMarketRiskSection,
    ManagementRiskReport,
    ManagementStressTestingInput,
    ManagementStressTestingSection,
)
from manco_risk.reporting.management_report_service import ManagementReportService

__all__ = [
    "AnnexIVFundIdentificationInput",
    "AnnexIVFundIdentificationSection",
    "AnnexIVAssetBreakdownRow",
    "AnnexIVAssetBreakdownInput",
    "AnnexIVAssetBreakdownSection",
    "AnnexIVRiskMeasuresInput",
    "AnnexIVRiskMeasuresSection",
    "AnnexIVLeverageInput",
    "AnnexIVLeverageSection",
    "AnnexIVLiquidityProfileInput",
    "AnnexIVLiquidityProfileSection",
    "AnnexIVReport",
    "AnnexIVReportingService",
    "ManagementExceptionItem",
    "ManagementExceptionSummaryInput",
    "ManagementExceptionSummarySection",
    "ManagementFundSummaryInput",
    "ManagementFundSummarySection",
    "ManagementLeverageInput",
    "ManagementLeverageSection",
    "ManagementLiquidityInput",
    "ManagementLiquiditySection",
    "ManagementMarketRiskInput",
    "ManagementMarketRiskSection",
    "ManagementStressTestingInput",
    "ManagementStressTestingSection",
    "ManagementRiskReport",
    "ManagementReportService",
]
