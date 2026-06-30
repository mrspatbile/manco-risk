"""UCITS OTC counterparty exposure monitoring engine.

Evaluates OTC counterparty exposure observation against a regulatory threshold.
"""

from decimal import Decimal

from manco_risk.risk.ucits.constants import (
    UCITS_OTC_COUNTERPARTY_LIMIT_RATIO,
    UCITS_OTC_CREDIT_INSTITUTION_LIMIT_RATIO,
)
from manco_risk.risk.ucits.otc_counterparty import (
    UCITSCounterpartyCategory,
    UCITSOTCCounterpartyInput,
    UCITSOTCCounterpartyResult,
    UCITSOTCCounterpartyStatus,
)


class UCITSOTCCounterpartyEngine:
    """UCITS OTC counterparty exposure monitoring engine.

    Evaluates an OTC counterparty exposure observation against a regulatory threshold.

    The engine:
    1. Receives an OTC counterparty observation (fund, date, NAV, counterparty, exposure, category).
    2. Calculates exposure_ratio from exposure_amount and NAV.
    3. Determines limit_ratio based on counterparty category.
    4. Calculates limit amount from NAV and limit ratio.
    5. Determines compliance status.
    6. Calculates excess amount and ratio.
    7. Returns a typed result.

    The engine monitors OTC counterparty exposure under the UCITS framework and does NOT:
    - Value derivatives (reuses pre-computed exposure observation).
    - Aggregate OTC counterparty positions.
    - Apply collateral netting or look-through logic.
    - Fetch market data or prices.
    - Access databases.
    - Validate cross-object consistency beyond the input/output models.

    The engine is the single source of truth for derived calculations.
    """

    def calculate(self, observation: UCITSOTCCounterpartyInput) -> UCITSOTCCounterpartyResult:
        """Calculate OTC counterparty exposure monitoring status.

        Parameters
        ----------
        observation : UCITSOTCCounterpartyInput
            OTC counterparty observation (fund, date, NAV, counterparty, exposure, category).

        Returns
        -------
        UCITSOTCCounterpartyResult
            Monitoring result with status, threshold, excess, and audit fields.
        """
        # Determine limit_ratio based on counterparty category
        if (
            observation.counterparty_category
            == UCITSCounterpartyCategory.ELIGIBLE_CREDIT_INSTITUTION
        ):
            limit_ratio = UCITS_OTC_CREDIT_INSTITUTION_LIMIT_RATIO
        else:
            limit_ratio = UCITS_OTC_COUNTERPARTY_LIMIT_RATIO

        # Calculate exposure_ratio
        exposure_ratio = observation.exposure_amount / observation.nav

        # Calculate limit amount
        limit_amount = observation.nav * limit_ratio

        # Determine status and calculate excess
        if exposure_ratio <= limit_ratio:
            status = UCITSOTCCounterpartyStatus.WITHIN_LIMIT
            excess_amount = Decimal("0")
            excess_ratio = Decimal("0")
        else:
            status = UCITSOTCCounterpartyStatus.BREACH
            excess_amount = observation.exposure_amount - limit_amount
            excess_ratio = exposure_ratio - limit_ratio

        return UCITSOTCCounterpartyResult(
            fund_id=observation.fund_id,
            valuation_date=observation.valuation_date,
            counterparty_id=observation.counterparty_id,
            counterparty_name=observation.counterparty_name,
            nav=observation.nav,
            exposure_amount=observation.exposure_amount,
            exposure_ratio=exposure_ratio,
            limit_ratio=limit_ratio,
            limit_amount=limit_amount,
            status=status,
            excess_amount=excess_amount,
            excess_ratio=excess_ratio,
            counterparty_category=observation.counterparty_category,
        )
