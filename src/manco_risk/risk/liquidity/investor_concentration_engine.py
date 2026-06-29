"""Investor concentration analytics engine.

Analyzes investor base concentration and computes largest investor metrics
and top-N investor rankings.

Does NOT:
- Connect to redemption stress or LMT logic
- Model redemption queues or multi-period effects
- Include gate triggers or swing pricing
- Perform fund-level aggregation across multiple funds
"""

from decimal import Decimal

from manco_risk.risk.liquidity.models import (
    InvestorConcentrationResult,
    InvestorHolding,
    TopNInvestor,
)


class InvestorConcentrationEngine:
    """Analyze investor concentration in a fund.

    Given fund NAV and investor holdings, calculates:
    - Largest investor amount and percentage
    - Top-N investor rankings for configured N values
    - Total investor count
    """

    def calculate(
        self,
        fund_id: int,
        valuation_date,
        fund_nav: Decimal,
        investor_holdings: list[InvestorHolding],
        top_n_levels: list[int],
    ) -> InvestorConcentrationResult:
        """Calculate investor concentration metrics.

        Parameters
        ----------
        fund_id
            Fund identifier.
        valuation_date
            Date of portfolio snapshot.
        fund_nav
            Fund NAV (total of investor holdings, typically).
        investor_holdings
            List of investor holdings (investor_id, nav_amount).
        top_n_levels
            Top-N levels to calculate (e.g., [1, 5, 10]).

        Returns
        -------
        InvestorConcentrationResult
            Concentration metrics with largest investor and top-N rankings.

        Raises
        ------
        ValueError
            If duplicate investor IDs found, holdings > NAV, or invalid inputs.
        """
        self._validate_inputs(investor_holdings, fund_nav, top_n_levels)

        sorted_investors = self._sort_investors_by_holding(investor_holdings, fund_nav)

        largest_investor = sorted_investors[0]

        top_n_investors = self._calculate_top_n(sorted_investors, top_n_levels)

        return InvestorConcentrationResult(
            fund_id=fund_id,
            valuation_date=valuation_date,
            fund_nav=fund_nav,
            total_investor_count=len(investor_holdings),
            largest_investor_id=largest_investor.investor_id,
            largest_investor_amount=largest_investor.total_amount,
            largest_investor_percentage=largest_investor.percentage_of_nav,
            top_n_levels=sorted(top_n_levels),
            top_n_investors=top_n_investors,
        )

    def _validate_inputs(
        self,
        investor_holdings: list[InvestorHolding],
        fund_nav: Decimal,
        top_n_levels: list[int],
    ) -> None:
        """Validate inputs for concentration calculation."""
        if not investor_holdings:
            raise ValueError("investor_holdings must contain at least one investor")

        investor_ids = [h.investor_id for h in investor_holdings]
        unique_ids = set(investor_ids)
        if len(unique_ids) != len(investor_ids):
            raise ValueError("Duplicate investor IDs found")

        total_holdings = sum(h.nav_amount for h in investor_holdings)
        if total_holdings > fund_nav * Decimal("1.01"):
            raise ValueError(
                f"Total investor holdings ({total_holdings}) exceeds fund NAV ({fund_nav})"
            )

        if not top_n_levels:
            raise ValueError("top_n_levels must not be empty")
        for level in top_n_levels:
            if level < 1:
                raise ValueError("top_n_levels must contain positive integers")

    def _sort_investors_by_holding(
        self, investor_holdings: list[InvestorHolding], fund_nav: Decimal
    ) -> list[TopNInvestor]:
        """Sort investors by holding amount (descending)."""
        sorted_holdings = sorted(investor_holdings, key=lambda h: h.nav_amount, reverse=True)

        investors = []
        for holding in sorted_holdings:
            percentage = holding.nav_amount / fund_nav
            investor = TopNInvestor(
                investor_id=holding.investor_id,
                total_amount=holding.nav_amount,
                percentage_of_nav=percentage,
            )
            investors.append(investor)

        return investors

    def _calculate_top_n(
        self, sorted_investors: list[TopNInvestor], top_n_levels: list[int]
    ) -> dict[int, list[TopNInvestor]]:
        """Extract top-N investors for each N level."""
        top_n_dict = {}
        for level in top_n_levels:
            top_n_dict[level] = sorted_investors[:level]
        return top_n_dict
