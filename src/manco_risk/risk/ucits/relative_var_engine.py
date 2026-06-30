"""UCITS Relative VaR monitoring engine.

Evaluates fund VaR observation against reference portfolio VaR threshold.
"""

from decimal import Decimal

from manco_risk.risk.ucits.constants import UCITS_RELATIVE_VAR_LIMIT_RATIO
from manco_risk.risk.ucits.relative_var import (
    UCITSRelativeVaRInput,
    UCITSRelativeVaRResult,
    UCITSRelativeVaRStatus,
)


class UCITSRelativeVaREngine:
    """UCITS Relative VaR monitoring engine.

    Evaluates fund VaR against a reference portfolio VaR threshold.

    The engine:
    1. Receives VaR observations (fund, date, fund VaR, reference portfolio VaR, confidence, horizon).
    2. Calculates relative_var_ratio from fund_var and reference_portfolio_var.
    3. Determines compliance status against the 1.0x limit.
    4. Calculates excess ratio.
    5. Returns a typed result.

    The engine monitors relative VaR under UCITS framework and does NOT:
    - Calculate VaR (reuses pre-calculated observations).
    - Construct or select reference portfolios.
    - Fetch market data or prices.
    - Access databases.
    - Validate cross-object consistency beyond the input/output models.

    The engine is the single source of truth for derived calculations.
    """

    def calculate(self, observation: UCITSRelativeVaRInput) -> UCITSRelativeVaRResult:
        """Calculate relative VaR monitoring status.

        Parameters
        ----------
        observation : UCITSRelativeVaRInput
            VaR observation (fund, date, fund_var, reference_portfolio_var, confidence, horizon).

        Returns
        -------
        UCITSRelativeVaRResult
            Monitoring result with status, ratio, excess, and audit fields.
        """
        limit_ratio = UCITS_RELATIVE_VAR_LIMIT_RATIO

        # Calculate relative_var_ratio
        relative_var_ratio = observation.fund_var / observation.reference_portfolio_var

        # Determine status and calculate excess
        if relative_var_ratio <= limit_ratio:
            status = UCITSRelativeVaRStatus.WITHIN_LIMIT
            excess_ratio = Decimal("0")
        else:
            status = UCITSRelativeVaRStatus.BREACH
            excess_ratio = relative_var_ratio - limit_ratio

        return UCITSRelativeVaRResult(
            fund_id=observation.fund_id,
            valuation_date=observation.valuation_date,
            fund_var=observation.fund_var,
            reference_portfolio_var=observation.reference_portfolio_var,
            relative_var_ratio=relative_var_ratio,
            limit_ratio=limit_ratio,
            status=status,
            excess_ratio=excess_ratio,
            confidence_level=observation.confidence_level,
            holding_period_days=observation.holding_period_days,
        )
