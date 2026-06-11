"""Mappers for leverage calculation results to ORM models.

Converts pure leverage calculation results to database ORM entities.
Handles both gross and commitment method results.
"""

from decimal import Decimal

from manco_risk.database.models import (
    LeverageResult,
    LeverageSourceContributionResult,
)
from manco_risk.risk.leverage import (
    AIFMDCommitmentLeverageResult,
    LeverageMethodResult,
)


def map_leverage_method_result_to_orm(
    result: LeverageMethodResult,
    calculation_run_id: int,
    fund_id: int,
) -> LeverageResult:
    """Map gross method LeverageMethodResult to ORM LeverageResult.

    Parameters
    ----------
    result
        Pure leverage method result (gross method).
    calculation_run_id
        Foreign key to CalculationRun.
    fund_id
        Foreign key to Fund.

    Returns
    -------
    LeverageResult
        ORM model ready for persistence.
    """
    return LeverageResult(
        calculation_run_id=calculation_run_id,
        fund_id=fund_id,
        valuation_date=result.nav > Decimal("0")
        and result.nav
        or Decimal("0"),  # Placeholder; will be set by service
        method=result.method.value,
        nav=result.nav,
        total_exposure=result.total_exposure,
        leverage_ratio=result.leverage_ratio,
        base_exposure_before_reductions=None,
        total_reductions=None,
        final_exposure=None,
        num_applied_reductions=0,
        num_ignored_reductions=0,
        warnings="\n".join(result.warnings) if result.warnings else None,
    )


def map_commitment_leverage_result_to_orm(
    result: AIFMDCommitmentLeverageResult,
    calculation_run_id: int,
    fund_id: int,
) -> LeverageResult:
    """Map commitment method AIFMDCommitmentLeverageResult to ORM LeverageResult.

    Parameters
    ----------
    result
        Pure commitment leverage result with audit trail.
    calculation_run_id
        Foreign key to CalculationRun.
    fund_id
        Foreign key to Fund.

    Returns
    -------
    LeverageResult
        ORM model ready for persistence.
    """
    return LeverageResult(
        calculation_run_id=calculation_run_id,
        fund_id=fund_id,
        valuation_date=result.method_result.nav > Decimal("0")
        and result.method_result.nav
        or Decimal("0"),  # Placeholder; will be set by service
        method=result.method_result.method.value,
        nav=result.method_result.nav,
        total_exposure=result.final_exposure,
        leverage_ratio=result.method_result.leverage_ratio,
        base_exposure_before_reductions=result.base_exposure_before_reductions,
        total_reductions=result.total_reductions,
        final_exposure=result.final_exposure,
        num_applied_reductions=len(result.applied_reductions),
        num_ignored_reductions=len(result.ignored_reductions),
        warnings="\n".join(result.warnings) if result.warnings else None,
    )


def map_source_contributions_to_orm(
    leverage_result_id: int,
    method_result: LeverageMethodResult,
) -> list[LeverageSourceContributionResult]:
    """Map source contributions to ORM LeverageSourceContributionResult.

    Parameters
    ----------
    leverage_result_id
        Foreign key to LeverageResult.
    method_result
        Leverage method result with source contributions.

    Returns
    -------
    list[LeverageSourceContributionResult]
        ORM models ready for persistence, one per source.
    """
    nav = method_result.nav
    results = []

    for contribution in method_result.source_contributions:
        # Select exposure for percentage calculation based on context
        exposure_for_pct = contribution.gross_exposure

        results.append(
            LeverageSourceContributionResult(
                leverage_result_id=leverage_result_id,
                source=contribution.source.value,
                gross_exposure=contribution.gross_exposure,
                commitment_exposure=contribution.commitment_exposure,
                treatment=contribution.treatment.value,
                exclusion_reason=contribution.exclusion_reason,
                percentage_of_nav=(exposure_for_pct / nav) if nav > Decimal("0") else Decimal("0"),
            )
        )

    return results
