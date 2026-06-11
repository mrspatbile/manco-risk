"""Direct borrowing leverage exposure calculation engine.

Calculates leverage exposure from direct borrowing by separating:
- Unreinvested borrowing (cash that is not yet invested)
- Reinvested borrowing (borrowed cash that has been deployed)

Final AIFMD gross and commitment treatment is determined later in aggregation layer.

Does NOT include:
- AIFMD gross or commitment aggregation
- Borrowing limits or caps
- SFTs or securities lending
- Leverage ratio calculation or limit monitoring
- Loan-originating AIF regulatory limits
"""

from decimal import Decimal

from manco_risk.risk.leverage.borrowing_models import BorrowingRecord
from manco_risk.risk.leverage.direct_borrowing_result import DirectBorrowingExposureResult
from manco_risk.risk.leverage.enums import ExposureTreatment, LeverageSource
from manco_risk.risk.leverage.models import LeverageExposureSourceContribution


class DirectBorrowingExposureEngine:
    """Calculate leverage exposure from direct borrowing.

    Separates unreinvested and reinvested borrowing into distinct leverage sources.
    Leaves final AIFMD treatment (inclusion/exclusion from gross or commitment) to
    later aggregation layer (MRS-163).
    """

    def calculate(self, borrowing_records: list[BorrowingRecord]) -> DirectBorrowingExposureResult:
        """Calculate direct borrowing leverage exposure.

        Parameters
        ----------
        borrowing_records
            List of borrowing records with amounts and deployment status.

        Returns
        -------
        DirectBorrowingExposureResult
            Source-level exposure contributions for DIRECT_BORROWING
            and/or REINVESTED_BORROWING, with warnings if any.
        """
        total_unreinvested_exposure = Decimal("0")
        total_reinvested_exposure = Decimal("0")
        warnings: list[str] = []

        for record in borrowing_records:
            unreinvested_amount = record.amount_base_ccy - record.reinvested_amount_base_ccy
            total_unreinvested_exposure += unreinvested_amount
            total_reinvested_exposure += record.reinvested_amount_base_ccy

        source_contributions: list[LeverageExposureSourceContribution] = []

        if total_unreinvested_exposure > Decimal("0"):
            source_contributions.append(
                self._direct_borrowing_contribution(total_unreinvested_exposure)
            )

        if total_reinvested_exposure > Decimal("0"):
            source_contributions.append(
                self._reinvested_borrowing_contribution(total_reinvested_exposure)
            )

        return DirectBorrowingExposureResult(
            borrowing_records=borrowing_records,
            source_contributions=source_contributions,
            warnings=warnings,
        )

    def _direct_borrowing_contribution(
        self, unreinvested_amount: Decimal
    ) -> LeverageExposureSourceContribution:
        """Create source contribution for unreinvested borrowing.

        Unreinvested borrowing is cash that has not yet been invested.
        Final AIFMD treatment (inclusion in gross/commitment) is pending.

        Parameters
        ----------
        unreinvested_amount
            Total unreinvested borrowed amount in base currency.

        Returns
        -------
        LeverageExposureSourceContribution
            Source contribution with DIRECT_BORROWING source.
        """
        return LeverageExposureSourceContribution(
            source=LeverageSource.DIRECT_BORROWING,
            gross_exposure=unreinvested_amount,
            commitment_exposure=None,
            treatment=ExposureTreatment.PENDING_METHOD_RULE,
        )

    def _reinvested_borrowing_contribution(
        self, reinvested_amount: Decimal
    ) -> LeverageExposureSourceContribution:
        """Create source contribution for reinvested borrowing.

        Reinvested borrowing is borrowed cash that has been deployed as exposure.
        Final AIFMD treatment (inclusion in gross/commitment) is pending.

        Parameters
        ----------
        reinvested_amount
            Total reinvested borrowed amount in base currency.

        Returns
        -------
        LeverageExposureSourceContribution
            Source contribution with REINVESTED_BORROWING source.
        """
        return LeverageExposureSourceContribution(
            source=LeverageSource.REINVESTED_BORROWING,
            gross_exposure=reinvested_amount,
            commitment_exposure=None,
            treatment=ExposureTreatment.PENDING_METHOD_RULE,
        )
