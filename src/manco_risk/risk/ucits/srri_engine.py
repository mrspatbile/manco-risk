"""UCITS SRRI calculation engine.

Maps annualised volatility to SRRI class (1-7).
"""

from decimal import Decimal

from manco_risk.risk.ucits.constants import SRRI_VOLATILITY_BANDS
from manco_risk.risk.ucits.srri import SRRIInput, SRRIResult


class SRRIEngine:
    """UCITS SRRI (Synthetic Risk and Reward Indicator) calculation engine.

    Maps an annualised volatility observation to SRRI class (1-7).

    The engine:
    1. Receives an annualised volatility observation (fund, date, volatility).
    2. Matches volatility against SRRI volatility bands.
    3. Determines SRRI class.
    4. Returns a typed result.

    The engine does NOT:
    - Calculate volatility (reuses pre-calculated observation).
    - Fetch market data or prices.
    - Access databases.
    - Validate cross-object consistency beyond the input/output models.

    The engine is the single source of truth for SRRI class determination.
    """

    def calculate(self, observation: SRRIInput) -> SRRIResult:
        """Calculate SRRI class from annualised volatility.

        Parameters
        ----------
        observation : SRRIInput
            Volatility observation (fund, date, annualised_volatility).

        Returns
        -------
        SRRIResult
            SRRI result with class and audit fields.
        """
        # Determine SRRI class by matching volatility against bands
        srri_class = self._determine_srri_class(observation.annualised_volatility)

        return SRRIResult(
            fund_id=observation.fund_id,
            valuation_date=observation.valuation_date,
            annualised_volatility=observation.annualised_volatility,
            srri_class=srri_class,
        )

    def _determine_srri_class(self, volatility: Decimal) -> int:
        """Determine SRRI class from annualised volatility.

        Parameters
        ----------
        volatility : Decimal
            Annualised volatility as decimal (e.g., 0.15 = 15%).

        Returns
        -------
        int
            SRRI class (1-7).
        """
        for lower_bound, upper_bound, srri_class in SRRI_VOLATILITY_BANDS:
            if lower_bound <= volatility < upper_bound:
                return srri_class

        # Fallback to highest class (should not reach if bands are correct)
        return 7
