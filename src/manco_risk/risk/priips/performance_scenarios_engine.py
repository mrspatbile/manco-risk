"""PRIIPs Performance Scenarios engine.

Stateless, pure pass-through. No calculation or simulation.

This engine is responsible for validating and packaging pre-computed
PRIIPs scenario returns into export-ready results.

It does NOT:
- Simulate returns
- Calculate scenarios
- Fetch market data
- Access databases
"""

from decimal import Decimal

from manco_risk.risk.priips.performance_scenarios import (
    PerformanceScenariosInput,
    PerformanceScenariosResult,
)


class PerformanceScenariosEngine:
    """PRIIPs Performance Scenarios engine.

    Packages pre-computed scenario returns into immutable, export-ready
    result objects.

    The engine is stateless. Calculation is deterministic: same input always
    produces the same output.

    This engine does NOT perform any scenario calculations, simulations, or
    transformations. It is a pure validation and packaging pass-through.

    Reference:
    - Commission Delegated Regulation (EU) 2017/653, Annex IV/V: Performance
      scenario requirements and presentation.
    """

    @staticmethod
    def calculate(input_data: PerformanceScenariosInput) -> PerformanceScenariosResult:
        """Package pre-computed performance scenarios into export-ready result.

        Parameters
        ----------
        input_data : PerformanceScenariosInput
            Input containing product_id, valuation_date, methodology_version,
            RHP, and pre-computed scenario returns.

        Returns
        -------
        PerformanceScenariosResult
            Immutable result with all scenario returns preserved as Decimal.

        Notes
        -----
        This engine performs NO calculations or transformations.
        All scenario values are passed through as-is.
        Decimal precision is preserved.
        """
        # Coerce return values to Decimal if needed (input validator handles this)
        stress_return = (
            input_data.stress_return
            if isinstance(input_data.stress_return, Decimal)
            else Decimal(str(input_data.stress_return))
        )
        unfavourable_return = (
            input_data.unfavourable_return
            if isinstance(input_data.unfavourable_return, Decimal)
            else Decimal(str(input_data.unfavourable_return))
        )
        moderate_return = (
            input_data.moderate_return
            if isinstance(input_data.moderate_return, Decimal)
            else Decimal(str(input_data.moderate_return))
        )
        favourable_return = (
            input_data.favourable_return
            if isinstance(input_data.favourable_return, Decimal)
            else Decimal(str(input_data.favourable_return))
        )

        return PerformanceScenariosResult(
            product_id=input_data.product_id,
            valuation_date=input_data.valuation_date,
            methodology_version=input_data.methodology_version,
            recommended_holding_period_years=input_data.recommended_holding_period_years,
            stress_return=stress_return,
            unfavourable_return=unfavourable_return,
            moderate_return=moderate_return,
            favourable_return=favourable_return,
        )
