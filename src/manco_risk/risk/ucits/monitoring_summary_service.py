"""UCITS monitoring summary service.

Orchestration layer that assembles monitoring results into a summary.
"""

from manco_risk.risk.ucits.absolute_var import UCITSAbsoluteVaRResult, UCITSAbsoluteVaRStatus
from manco_risk.risk.ucits.borrowing import UCITSBorrowingResult, UCITSBorrowingStatus
from manco_risk.risk.ucits.concentration import UCITSConcentrationResult, UCITSConcentrationStatus
from manco_risk.risk.ucits.monitoring_summary import UCITSMonitoringSummary
from manco_risk.risk.ucits.otc_counterparty import (
    UCITSOTCCounterpartyResult,
    UCITSOTCCounterpartyStatus,
)
from manco_risk.risk.ucits.relative_var import UCITSRelativeVaRResult, UCITSRelativeVaRStatus
from manco_risk.risk.ucits.srri import SRRIResult


class UCITSMonitoringSummaryService:
    """UCITS monitoring orchestration service.

    Assembles individual monitoring results into a consolidated summary.

    The service:
    1. Receives monitoring results from all engines.
    2. Validates fund ID consistency.
    3. Determines overall compliance status.
    4. Counts breaches.
    5. Identifies breached monitoring areas.
    6. Returns an immutable summary.

    The service performs NO calculations, only orchestration.
    """

    @staticmethod
    def build(
        absolute_var_result: UCITSAbsoluteVaRResult,
        relative_var_result: UCITSRelativeVaRResult,
        srri_result: SRRIResult,
        borrowing_result: UCITSBorrowingResult,
        concentration_result: UCITSConcentrationResult,
        otc_counterparty_result: UCITSOTCCounterpartyResult,
    ) -> UCITSMonitoringSummary:
        """Build consolidated UCITS monitoring summary.

        Parameters
        ----------
        absolute_var_result : UCITSAbsoluteVaRResult
            Absolute VaR monitoring result.
        relative_var_result : UCITSRelativeVaRResult
            Relative VaR monitoring result.
        srri_result : SRRIResult
            SRRI calculation result.
        borrowing_result : UCITSBorrowingResult
            Direct borrowing limit result.
        concentration_result : UCITSConcentrationResult
            Single-issuer concentration result.
        otc_counterparty_result : UCITSOTCCounterpartyResult
            OTC counterparty exposure result.

        Returns
        -------
        UCITSMonitoringSummary
            Consolidated monitoring summary.

        Raises
        ------
        ValueError
            If fund IDs are not consistent across all results.
        """
        # Validate fund ID consistency
        fund_ids = {
            absolute_var_result.fund_id,
            relative_var_result.fund_id,
            srri_result.fund_id,
            borrowing_result.fund_id,
            concentration_result.fund_id,
            otc_counterparty_result.fund_id,
        }

        if len(fund_ids) > 1:
            raise ValueError(f"Fund IDs are not consistent across monitoring results: {fund_ids}")

        fund_id = absolute_var_result.fund_id

        # Determine breaches
        breached_checks = []

        if absolute_var_result.status == UCITSAbsoluteVaRStatus.BREACH:
            breached_checks.append("Absolute VaR")

        if relative_var_result.status == UCITSRelativeVaRStatus.BREACH:
            breached_checks.append("Relative VaR")

        # SRRI is not a monitoring check (it's informational), so no breach status

        if borrowing_result.status == UCITSBorrowingStatus.BREACH:
            breached_checks.append("Direct Borrowing")

        if concentration_result.status == UCITSConcentrationStatus.BREACH:
            breached_checks.append("Issuer Concentration")

        if otc_counterparty_result.status == UCITSOTCCounterpartyStatus.BREACH:
            breached_checks.append("OTC Counterparty")

        breach_count = len(breached_checks)
        overall_compliance = breach_count == 0

        return UCITSMonitoringSummary(
            fund_id=fund_id,
            valuation_date=absolute_var_result.valuation_date,
            overall_compliance=overall_compliance,
            breach_count=breach_count,
            breached_checks=breached_checks,
            absolute_var_result=absolute_var_result,
            relative_var_result=relative_var_result,
            srri_result=srri_result,
            borrowing_result=borrowing_result,
            concentration_result=concentration_result,
            otc_counterparty_result=otc_counterparty_result,
        )
