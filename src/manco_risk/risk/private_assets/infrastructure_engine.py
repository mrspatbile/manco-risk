"""Infrastructure analytics calculation engine.

Stateless orchestration of infrastructure asset metrics computation.

Formulas:
- DSCR (Debt Service Coverage Ratio) = Cash Available for Debt Service / Debt Service Amount
- LTV (Loan-to-Value Ratio) = Debt Outstanding / Asset Value

All inputs are Decimal; all outputs are non-negative Decimal or None.

Point-in-time ratios only. No forecasting, valuation, or duration calculations.
"""

from manco_risk.risk.private_assets.infrastructure import (
    InfrastructureAnalyticsResult,
    InfrastructureAssetInput,
)

__all__ = ["InfrastructureEngine"]


class InfrastructureEngine:
    """Stateless engine for infrastructure asset analytics.

    Computes point-in-time metrics (DSCR, LTV) from typed input.
    """

    @staticmethod
    def analyze(
        asset: InfrastructureAssetInput,
    ) -> InfrastructureAnalyticsResult:
        """Analyze infrastructure asset and compute metrics.

        Parameters
        ----------
        asset : InfrastructureAssetInput
            Infrastructure asset with financial metrics (cash available for debt
            service, debt service amount, asset value, debt outstanding).

        Returns
        -------
        InfrastructureAnalyticsResult
            Immutable result with computed metrics (DSCR, LTV).
            DSCR is None if debt_service_amount is zero.
            LTV is None if asset_value is zero.

        Raises
        ------
        ValueError
            If input data is invalid.
        """
        dscr = None
        ltv = None

        if asset.debt_service_amount > 0:
            dscr = asset.cash_available_for_debt_service / asset.debt_service_amount

        if asset.asset_value > 0:
            ltv = asset.debt_outstanding / asset.asset_value

        return InfrastructureAnalyticsResult(
            asset_id=asset.asset_id,
            valuation_date=asset.valuation_date,
            dscr=dscr,
            ltv=ltv,
            cash_available_for_debt_service=asset.cash_available_for_debt_service,
            debt_service_amount=asset.debt_service_amount,
            asset_value=asset.asset_value,
            debt_outstanding=asset.debt_outstanding,
        )
