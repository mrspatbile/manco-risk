"""Real estate stress calculation engine.

Stateless orchestration of real estate stress metrics computation.

Formulas:
- stressed_property_value = property_value * (1 + value_shock)
- stressed_rental_income = rental_income * (1 + rental_income_shock)
- stressed_operating_expenses = operating_expenses * (1 + expense_shock)
- stressed_noi = stressed_rental_income - stressed_operating_expenses
- stressed_ltv = debt_outstanding / stressed_property_value (or None if stressed_property_value = 0)

Single-period stress only. No multi-period forecasting or cap-rate modelling.
All inputs are Decimal; all outputs are non-negative Decimal or None.
"""

from decimal import Decimal

from manco_risk.risk.private_assets.real_estate import (
    RealEstateStressInput,
    RealEstateStressResult,
)

__all__ = ["RealEstateStressEngine"]


class RealEstateStressEngine:
    """Stateless engine for real estate stress analysis.

    Calculates single-period stressed property metrics under market shocks.
    """

    @staticmethod
    def analyze(
        property_data: RealEstateStressInput,
    ) -> RealEstateStressResult:
        """Analyze real estate property under stress shocks.

        Parameters
        ----------
        property_data : RealEstateStressInput
            Property with financial data and stress shocks (value, rental income,
            operating expense).

        Returns
        -------
        RealEstateStressResult
            Immutable result with stressed property value, NOI, and LTV.
            stressed_ltv is None if stressed_property_value is zero.

        Raises
        ------
        ValueError
            If input data is invalid.

        Notes
        -----
        Single-period calculation only. No multi-period forecasting or cap-rate
        modelling performed.
        """
        stressed_property_value = property_data.property_value * (
            Decimal("1") + property_data.value_shock
        )
        stressed_rental_income = property_data.rental_income * (
            Decimal("1") + property_data.rental_income_shock
        )
        stressed_operating_expenses = property_data.operating_expenses * (
            Decimal("1") + property_data.expense_shock
        )
        stressed_noi = stressed_rental_income - stressed_operating_expenses

        stressed_ltv = None
        if stressed_property_value > 0:
            stressed_ltv = property_data.debt_outstanding / stressed_property_value

        return RealEstateStressResult(
            property_id=property_data.property_id,
            valuation_date=property_data.valuation_date,
            stressed_property_value=stressed_property_value,
            stressed_rental_income=stressed_rental_income,
            stressed_operating_expenses=stressed_operating_expenses,
            stressed_noi=stressed_noi,
            stressed_ltv=stressed_ltv,
            debt_outstanding=property_data.debt_outstanding,
            methodology_version=property_data.methodology_version,
        )
