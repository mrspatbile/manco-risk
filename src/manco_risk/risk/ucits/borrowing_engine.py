"""UCITS direct borrowing limit monitoring engine.

Evaluates direct borrowing observation against a regulatory threshold.
"""

from decimal import Decimal

from manco_risk.risk.ucits.borrowing import (
    UCITSBorrowingInput,
    UCITSBorrowingResult,
    UCITSBorrowingStatus,
)
from manco_risk.risk.ucits.constants import UCITS_BORROWING_LIMIT_RATIO


class UCITSBorrowingEngine:
    """UCITS direct borrowing limit monitoring engine.

    Evaluates a direct borrowing observation against a regulatory threshold.

    The engine:
    1. Receives a borrowing observation (fund, date, NAV, direct borrowing amount).
    2. Calculates borrowing_ratio from direct_borrowing_amount and NAV.
    3. Calculates limit amount from NAV and limit ratio (10%).
    4. Determines compliance status.
    5. Calculates excess amount and ratio.
    6. Returns a typed result.

    The engine monitors only direct borrowings and does NOT:
    - Calculate or infer borrowing from positions or derivatives.
    - Fetch market data.
    - Access databases.
    - Validate cross-object consistency beyond the input/output models.

    The engine is the single source of truth for derived calculations.
    """

    def calculate(self, observation: UCITSBorrowingInput) -> UCITSBorrowingResult:
        """Calculate borrowing limit monitoring status.

        Parameters
        ----------
        observation : UCITSBorrowingInput
            Borrowing observation (fund, date, NAV, direct_borrowing_amount).

        Returns
        -------
        UCITSBorrowingResult
            Monitoring result with status, threshold, excess, and audit fields.
        """
        limit_ratio = UCITS_BORROWING_LIMIT_RATIO

        # Calculate borrowing_ratio
        borrowing_ratio = observation.direct_borrowing_amount / observation.nav

        # Calculate limit amount
        limit_amount = observation.nav * limit_ratio

        # Determine status and calculate excess
        if borrowing_ratio <= limit_ratio:
            status = UCITSBorrowingStatus.WITHIN_LIMIT
            excess_amount = Decimal("0")
            excess_ratio = Decimal("0")
        else:
            status = UCITSBorrowingStatus.BREACH
            excess_amount = observation.direct_borrowing_amount - limit_amount
            excess_ratio = borrowing_ratio - limit_ratio

        return UCITSBorrowingResult(
            fund_id=observation.fund_id,
            valuation_date=observation.valuation_date,
            nav=observation.nav,
            direct_borrowing_amount=observation.direct_borrowing_amount,
            borrowing_ratio=borrowing_ratio,
            limit_ratio=limit_ratio,
            limit_amount=limit_amount,
            status=status,
            excess_amount=excess_amount,
            excess_ratio=excess_ratio,
        )
