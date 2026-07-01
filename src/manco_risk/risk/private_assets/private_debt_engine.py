"""Private debt monitoring calculation engine.

Stateless orchestration of private debt loan metrics packaging and LTV calculation.

Formula:
- loan_to_value = outstanding_balance / collateral_value (or None if collateral_value is None or zero)

All other metrics are already computed and passed through unchanged.
No covenant ratio calculation, cash flow projection, or credit analysis performed.
"""

from manco_risk.risk.private_assets.private_debt import (
    PrivateDebtLoanInput,
    PrivateDebtLoanResult,
)

__all__ = ["PrivateDebtEngine"]


class PrivateDebtEngine:
    """Stateless engine for private debt loan monitoring.

    Packages loan metrics and calculates loan-to-value from collateral.
    """

    @staticmethod
    def analyze(
        loan: PrivateDebtLoanInput,
    ) -> PrivateDebtLoanResult:
        """Analyze private debt loan and calculate metrics.

        Parameters
        ----------
        loan : PrivateDebtLoanInput
            Private debt loan with financial metrics and covenant status.

        Returns
        -------
        PrivateDebtLoanResult
            Immutable result with packaged metrics and calculated loan-to-value.
            loan_to_value is None if collateral_value is None or zero.

        Raises
        ------
        ValueError
            If input data is invalid.

        Notes
        -----
        Calculates only loan-to-value from supplied collateral value.
        All other metrics are already-computed and passed through unchanged.
        No covenant ratio calculation, cash flow projection, default probability,
        or credit analysis performed.
        """
        loan_to_value = None
        if loan.collateral_value is not None and loan.collateral_value > 0:
            loan_to_value = loan.outstanding_balance / loan.collateral_value

        return PrivateDebtLoanResult(
            loan_id=loan.loan_id,
            valuation_date=loan.valuation_date,
            outstanding_balance=loan.outstanding_balance,
            collateral_value=loan.collateral_value,
            loan_to_value=loan_to_value,
            interest_coverage_ratio=loan.interest_coverage_ratio,
            debt_service_coverage_ratio=loan.debt_service_coverage_ratio,
            leverage_ratio=loan.leverage_ratio,
            covenant_breached=loan.covenant_breached,
            covenant_name=loan.covenant_name,
            methodology_version=loan.methodology_version,
        )
