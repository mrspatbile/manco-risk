"""Private equity calculation engine.

Stateless orchestration of private equity metrics computation.

Formulas:
- DPI (Distributed to Paid-In) = Cumulative Distributions / Cumulative Paid-In
- RVPI (Residual to Paid-In) = Residual Value / Cumulative Paid-In
- TVPI (Total Value to Paid-In) = (Cumulative Distributions + Residual Value) / Cumulative Paid-In
- MOIC (Multiple on Invested Capital) = TVPI

All inputs are Decimal; all outputs are non-negative Decimal or None.
"""

from decimal import Decimal

from manco_risk.risk.private_assets.private_equity import (
    PrivateEquityAnalyticsResult,
    PrivateEquityInvestmentInput,
)

__all__ = ["PrivateEquityEngine"]


class PrivateEquityEngine:
    """Stateless engine for private equity analytics.

    Computes multiples (DPI, RVPI, TVPI, MOIC) from typed input.
    """

    @staticmethod
    def analyze(
        investment: PrivateEquityInvestmentInput,
    ) -> PrivateEquityAnalyticsResult:
        """Analyze private equity investment and compute multiples.

        Parameters
        ----------
        investment : PrivateEquityInvestmentInput
            Investment with cash flows (contributions and distributions)
            and residual value (current NAV or remaining value).

        Returns
        -------
        PrivateEquityAnalyticsResult
            Immutable result with computed multiples (DPI, RVPI, TVPI, MOIC).
            All ratios are None if total paid-in is zero.

        Raises
        ------
        ValueError
            If input data is invalid.
        """
        total_paid_in = PrivateEquityEngine._sum_paid_in(investment.cash_flows)
        total_distributed = PrivateEquityEngine._sum_distributions(investment.cash_flows)
        residual_value = investment.residual_value

        dpi = None
        rvpi = None
        tvpi = None
        moic = None

        if total_paid_in > 0:
            dpi = total_distributed / total_paid_in
            rvpi = residual_value / total_paid_in
            tvpi = (total_distributed + residual_value) / total_paid_in
            moic = tvpi

        return PrivateEquityAnalyticsResult(
            dpi=dpi,
            rvpi=rvpi,
            tvpi=tvpi,
            moic=moic,
            total_paid_in=total_paid_in,
            total_distributed=total_distributed,
            residual_value=residual_value,
        )

    @staticmethod
    def _sum_paid_in(cash_flows: list) -> Decimal:
        """Sum all paid-in (contribution) cash flows.

        Parameters
        ----------
        cash_flows : list
            List of PrivateEquityCashFlow objects.

        Returns
        -------
        Decimal
            Sum of all paid-in amounts. Zero if no paid-in flows.
        """
        return sum(
            (cf.flow_amount for cf in cash_flows if cf.flow_type == "paid_in"),
            Decimal(0),
        )

    @staticmethod
    def _sum_distributions(cash_flows: list) -> Decimal:
        """Sum all distribution cash flows.

        Parameters
        ----------
        cash_flows : list
            List of PrivateEquityCashFlow objects.

        Returns
        -------
        Decimal
            Sum of all distribution amounts. Zero if no distribution flows.
        """
        return sum(
            (cf.flow_amount for cf in cash_flows if cf.flow_type == "distribution"),
            Decimal(0),
        )
