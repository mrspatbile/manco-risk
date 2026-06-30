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
    AnnexIVReport,
    AnnexIVRiskMeasuresInput,
    AnnexIVRiskMeasuresSection,
)
from manco_risk.reporting.annex_iv_service import AnnexIVReportingService

__all__ = [
    "AnnexIVFundIdentificationInput",
    "AnnexIVFundIdentificationSection",
    "AnnexIVAssetBreakdownRow",
    "AnnexIVAssetBreakdownInput",
    "AnnexIVAssetBreakdownSection",
    "AnnexIVRiskMeasuresInput",
    "AnnexIVRiskMeasuresSection",
    "AnnexIVReport",
    "AnnexIVReportingService",
]
