"""Securities financing transaction leverage exposure calculation engine.

Calculates leverage exposure from SFTs by identifying:
- Repo transactions
- Reverse repo transactions
- Securities lending transactions

Tracks whether cash collateral has been reinvested.
Final AIFMD gross and commitment treatment is determined later in aggregation layer.

Does NOT include:
- AIFMD gross or commitment aggregation
- Collateral haircuts or adjustments
- Netting or offsetting rules
- Counterparty risk
- Leverage ratio calculation or limit monitoring
"""

from decimal import Decimal

from manco_risk.risk.leverage.enums import ExposureTreatment, LeverageSource
from manco_risk.risk.leverage.models import LeverageExposureSourceContribution
from manco_risk.risk.leverage.sft_models import SFTRecord, SFTType
from manco_risk.risk.leverage.sft_result import SFTExposureResult


class SFTExposureEngine:
    """Calculate leverage exposure from securities financing transactions.

    Separates repo, reverse repo, and securities lending into distinct
    leverage sources. Leaves final AIFMD treatment (inclusion/exclusion from
    gross or commitment) to later aggregation layer (MRS-163).
    """

    SFT_TYPE_TO_SOURCE = {
        SFTType.REPO: LeverageSource.SFT_REPO,
        SFTType.REVERSE_REPO: LeverageSource.SFT_REVERSE_REPO,
        SFTType.SECURITIES_LENDING: LeverageSource.SECURITIES_LENDING,
    }

    def calculate(self, sft_records: list[SFTRecord]) -> SFTExposureResult:
        """Calculate SFT leverage exposure.

        Parameters
        ----------
        sft_records
            List of SFT records with market values and collateral composition.

        Returns
        -------
        SFTExposureResult
            Source-level exposure contributions for each SFT source type
            present, with warnings if any.
        """
        exposure_by_source: dict[LeverageSource, Decimal] = {}
        warnings: list[str] = []

        for record in sft_records:
            source = self.SFT_TYPE_TO_SOURCE[record.sft_type]
            exposure = self._calculate_source_exposure(record)

            if source not in exposure_by_source:
                exposure_by_source[source] = Decimal("0")
            exposure_by_source[source] += exposure

        source_contributions = [
            LeverageExposureSourceContribution(
                source=source,
                gross_exposure=exposure,
                commitment_exposure=None,
                treatment=ExposureTreatment.PENDING_METHOD_RULE,
            )
            for source, exposure in exposure_by_source.items()
        ]

        return SFTExposureResult(
            sft_records=sft_records,
            source_contributions=source_contributions,
            warnings=warnings,
        )

    def _calculate_source_exposure(self, record: SFTRecord) -> Decimal:
        """Calculate source-layer exposure for an SFT record.

        Phase 1 exposure rule:
        - Base SFT exposure = market_value_base_ccy
        - Add reinvested cash collateral to exposure
        - Securities collateral and non-reinvested cash collateral are
          tracked for reporting but do not increase Phase 1 source-layer exposure

        Parameters
        ----------
        record
            SFT record with market value and collateral amounts.

        Returns
        -------
        Decimal
            Source-layer exposure for this record.
        """
        return record.market_value_base_ccy + record.reinvested_cash_collateral_base_ccy
