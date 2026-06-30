"""PRIIPs Costs engine.

Stateless, pure pass-through. No calculation or simulation.

This engine is responsible for validating and packaging pre-computed
PRIIPs cost values into export-ready results.

It does NOT:
- Calculate transaction costs
- Calculate RIY (Reduction in Yield)
- Estimate implicit costs
- Calculate entry or exit costs
- Derive ongoing charges
- Fetch market data
- Access databases
"""

from decimal import Decimal

from manco_risk.risk.priips.costs import PRIIPSCostsInput, PRIIPSCostsResult


class PRIIPSCostsEngine:
    """PRIIPs Costs engine.

    Packages pre-computed cost values into immutable, export-ready
    result objects.

    The engine is stateless. Calculation is deterministic: same input always
    produces the same output.

    This engine does NOT perform any cost calculations, transformations, or
    derivations. It is a pure validation and packaging pass-through.

    Reference:
    - Commission Delegated Regulation (EU) 2017/653, Annex VI/VII: Cost
      calculation and presentation requirements.
    """

    @staticmethod
    def calculate(input_data: PRIIPSCostsInput) -> PRIIPSCostsResult:
        """Package pre-computed costs into export-ready result.

        Parameters
        ----------
        input_data : PRIIPSCostsInput
            Input containing product_id, valuation_date, methodology_version,
            RHP, and pre-computed cost values.

        Returns
        -------
        PRIIPSCostsResult
            Immutable result with all cost values preserved as Decimal.

        Notes
        -----
        This engine performs NO calculations or transformations.
        All cost values are passed through as-is.
        Decimal precision is preserved.
        """
        # Coerce cost values to Decimal if needed (input validator handles this)
        entry_cost = (
            input_data.entry_cost
            if isinstance(input_data.entry_cost, Decimal)
            else Decimal(str(input_data.entry_cost))
        )
        exit_cost = (
            input_data.exit_cost
            if isinstance(input_data.exit_cost, Decimal)
            else Decimal(str(input_data.exit_cost))
        )
        ongoing_cost = (
            input_data.ongoing_cost
            if isinstance(input_data.ongoing_cost, Decimal)
            else Decimal(str(input_data.ongoing_cost))
        )
        transaction_cost = (
            input_data.transaction_cost
            if isinstance(input_data.transaction_cost, Decimal)
            else Decimal(str(input_data.transaction_cost))
        )
        incidental_cost = (
            input_data.incidental_cost
            if isinstance(input_data.incidental_cost, Decimal)
            else Decimal(str(input_data.incidental_cost))
        )

        return PRIIPSCostsResult(
            product_id=input_data.product_id,
            valuation_date=input_data.valuation_date,
            methodology_version=input_data.methodology_version,
            recommended_holding_period_years=input_data.recommended_holding_period_years,
            entry_cost=entry_cost,
            exit_cost=exit_cost,
            ongoing_cost=ongoing_cost,
            transaction_cost=transaction_cost,
            incidental_cost=incidental_cost,
        )
