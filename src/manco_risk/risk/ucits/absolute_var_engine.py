"""UCITS Absolute VaR monitoring engine.

Evaluates a VaR observation against a regulatory threshold.
"""

from decimal import Decimal

from manco_risk.risk.ucits.absolute_var import (
    UCITSAbsoluteVaRInput,
    UCITSAbsoluteVaRResult,
    UCITSAbsoluteVaRStatus,
)
from manco_risk.risk.ucits.constants import UCITS_ABSOLUTE_VAR_LIMIT_RATIO


class UCITSAbsoluteVaREngine:
    """UCITS Absolute VaR monitoring engine.

    Evaluates a pre-calculated VaR observation against a regulatory threshold.

    The engine:
    1. Receives a VaR observation (fund, date, NAV, VaR amount, confidence, horizon).
    2. Calculates var_ratio from var_amount and NAV.
    3. Calculates threshold amount from NAV and threshold ratio.
    4. Determines compliance status.
    5. Calculates excess amount and ratio.
    6. Returns a typed result.

    The engine does NOT:
    - Calculate VaR (reuses pre-calculated observation).
    - Fetch market data.
    - Access databases.
    - Validate cross-object consistency beyond the input/output models.

    The engine is the single source of truth for derived calculations.
    """

    def calculate(self, observation: UCITSAbsoluteVaRInput) -> UCITSAbsoluteVaRResult:
        """Calculate absolute VaR monitoring status.

        Parameters
        ----------
        observation : UCITSAbsoluteVaRInput
            VaR observation (fund, date, NAV, var_amount, confidence, horizon).

        Returns
        -------
        UCITSAbsoluteVaRResult
            Monitoring result with status, threshold, excess, and audit fields.
        """
        threshold_ratio = UCITS_ABSOLUTE_VAR_LIMIT_RATIO

        # Calculate var_ratio
        var_ratio = observation.var_amount / observation.nav

        # Calculate threshold amount
        threshold_amount = observation.nav * threshold_ratio

        # Determine status and calculate excess
        if var_ratio <= threshold_ratio:
            status = UCITSAbsoluteVaRStatus.WITHIN_LIMIT
            excess_amount = Decimal("0")
            excess_ratio = Decimal("0")
        else:
            status = UCITSAbsoluteVaRStatus.BREACH
            excess_amount = observation.var_amount - threshold_amount
            excess_ratio = var_ratio - threshold_ratio

        return UCITSAbsoluteVaRResult(
            fund_id=observation.fund_id,
            valuation_date=observation.valuation_date,
            nav=observation.nav,
            var_amount=observation.var_amount,
            var_ratio=var_ratio,
            threshold_ratio=threshold_ratio,
            threshold_amount=threshold_amount,
            status=status,
            excess_amount=excess_amount,
            excess_ratio=excess_ratio,
            confidence_level=observation.confidence_level,
            holding_period_days=observation.holding_period_days,
        )
