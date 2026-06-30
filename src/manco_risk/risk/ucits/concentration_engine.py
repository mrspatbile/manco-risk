"""UCITS single-issuer concentration monitoring engine.

Evaluates single-issuer exposure observation against a regulatory threshold.
"""

from decimal import Decimal

from manco_risk.risk.ucits.concentration import (
    UCITSConcentrationInput,
    UCITSConcentrationResult,
    UCITSConcentrationStatus,
)
from manco_risk.risk.ucits.constants import UCITS_ISSUER_CONCENTRATION_LIMIT_RATIO


class UCITSConcentrationEngine:
    """UCITS single-issuer concentration monitoring engine.

    Evaluates a single-issuer exposure observation against a regulatory threshold.

    The engine:
    1. Receives an issuer exposure observation (fund, date, NAV, issuer, exposure amount).
    2. Calculates exposure_ratio from issuer_exposure_amount and NAV.
    3. Calculates limit amount from NAV and limit ratio (10%).
    4. Determines compliance status.
    5. Calculates excess amount and ratio.
    6. Returns a typed result.

    The engine monitors only single-issuer concentration and does NOT:
    - Aggregate issuer exposure from positions.
    - Perform group issuer logic or look-through.
    - Apply exemptions (government securities, index replication, etc.) — exemptions
      are deliberately out of scope for this slice.
    - Fetch market data or prices.
    - Access databases.
    - Validate cross-object consistency beyond the input/output models.

    The engine is the single source of truth for derived calculations.
    """

    def calculate(self, observation: UCITSConcentrationInput) -> UCITSConcentrationResult:
        """Calculate single-issuer concentration monitoring status.

        Parameters
        ----------
        observation : UCITSConcentrationInput
            Issuer concentration observation (fund, date, NAV, issuer, exposure amount).

        Returns
        -------
        UCITSConcentrationResult
            Monitoring result with status, threshold, excess, and audit fields.
        """
        limit_ratio = UCITS_ISSUER_CONCENTRATION_LIMIT_RATIO

        # Calculate exposure_ratio
        exposure_ratio = observation.issuer_exposure_amount / observation.nav

        # Calculate limit amount
        limit_amount = observation.nav * limit_ratio

        # Determine status and calculate excess
        if exposure_ratio <= limit_ratio:
            status = UCITSConcentrationStatus.WITHIN_LIMIT
            excess_amount = Decimal("0")
            excess_ratio = Decimal("0")
        else:
            status = UCITSConcentrationStatus.BREACH
            excess_amount = observation.issuer_exposure_amount - limit_amount
            excess_ratio = exposure_ratio - limit_ratio

        return UCITSConcentrationResult(
            fund_id=observation.fund_id,
            valuation_date=observation.valuation_date,
            nav=observation.nav,
            issuer_id=observation.issuer_id,
            issuer_name=observation.issuer_name,
            issuer_exposure_amount=observation.issuer_exposure_amount,
            exposure_ratio=exposure_ratio,
            limit_ratio=limit_ratio,
            limit_amount=limit_amount,
            status=status,
            excess_amount=excess_amount,
            excess_ratio=excess_ratio,
        )
