"""Reporting layer for manco-risk.

Assembles risk calculations and source data into export-ready reports.

Does not perform risk calculations. Calculations are performed in the risk module.
"""

from manco_risk.reporting.annex_iv import (
    AnnexIVFundIdentificationInput,
    AnnexIVFundIdentificationSection,
    AnnexIVReport,
)
from manco_risk.reporting.annex_iv_service import AnnexIVReportingService

__all__ = [
    "AnnexIVFundIdentificationInput",
    "AnnexIVFundIdentificationSection",
    "AnnexIVReport",
    "AnnexIVReportingService",
]
