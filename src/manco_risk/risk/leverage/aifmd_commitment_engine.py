"""AIFMD commitment leverage aggregation engine.

Aggregates source-layer exposure into AIFMD commitment method result.
Applies explicit, eligible commitment reductions.
Pure calculation layer with no pricing, derivatives handling, or persistence.
"""

from decimal import Decimal

from manco_risk.risk.leverage.aifmd_aggregation_models import (
    AIFMDCommitmentLeverageResult,
    AIFMDLeverageAggregationInput,
    CommitmentReductionType,
)
from manco_risk.risk.leverage.enums import ExposureTreatment, LeverageMethod
from manco_risk.risk.leverage.models import (
    LeverageExposureSourceContribution,
    LeverageMethodResult,
    UnsupportedLeverageExposure,
)


class AIFMDCommitmentLeverageEngine:
    """Calculate AIFMD commitment leverage from source results.

    Aggregates commitment exposures from all leverage sources.
    Applies explicit commitment reductions with eligibility checks.
    Does NOT infer netting or hedging automatically.

    Formula:
        base commitment exposure = sum of source commitment exposures
        final commitment exposure = base - eligible reductions
        commitment leverage = final exposure / NAV
    """

    def calculate(self, input: AIFMDLeverageAggregationInput) -> AIFMDCommitmentLeverageResult:
        """Calculate AIFMD commitment leverage with reduction audit.

        Parameters
        ----------
        input
            Aggregation input with portfolio and all source results.

        Returns
        -------
        AIFMDCommitmentLeverageResult
            Commitment method result with base exposure, reductions applied,
            final exposure, leverage ratio, and audit trail.
        """
        base_exposure = Decimal("0")
        source_contributions: list[LeverageExposureSourceContribution] = []
        unsupported_exposures: list[UnsupportedLeverageExposure] = []
        warnings: list[str] = []

        # Aggregate base commitment exposure from all sources
        if input.physical_result is not None:
            if input.physical_result.source_contribution is not None:
                contribution = input.physical_result.source_contribution
                if contribution.treatment != ExposureTreatment.EXCLUDED:
                    # Use commitment exposure if available, else gross conservatively
                    exposure = (
                        contribution.commitment_exposure
                        if contribution.commitment_exposure is not None
                        else contribution.gross_exposure
                    )
                    base_exposure += exposure
                source_contributions.append(contribution)

            unsupported_exposures.extend(input.physical_result.unsupported_exposures)
            warnings.extend(input.physical_result.warnings)

        # Aggregate cash exposure (already zero or excluded in source layer)
        if input.cash_result is not None:
            if input.cash_result.source_contribution is not None:
                contribution = input.cash_result.source_contribution
                source_contributions.append(contribution)

            unsupported_exposures.extend(input.cash_result.unsupported_exposures)
            warnings.extend(input.cash_result.warnings)

        # Aggregate direct borrowing and reinvested borrowing
        if input.direct_borrowing_result is not None:
            for contribution in input.direct_borrowing_result.source_contributions:
                if contribution.treatment != ExposureTreatment.EXCLUDED:
                    # Use commitment exposure if available, else gross conservatively
                    exposure = (
                        contribution.commitment_exposure
                        if contribution.commitment_exposure is not None
                        else contribution.gross_exposure
                    )
                    base_exposure += exposure
                source_contributions.append(contribution)

            warnings.extend(input.direct_borrowing_result.warnings)

        # Aggregate SFT exposure
        if input.sft_result is not None:
            for contribution in input.sft_result.source_contributions:
                if contribution.treatment != ExposureTreatment.EXCLUDED:
                    # Use commitment exposure if available, else gross conservatively
                    exposure = (
                        contribution.commitment_exposure
                        if contribution.commitment_exposure is not None
                        else contribution.gross_exposure
                    )
                    base_exposure += exposure
                source_contributions.append(contribution)

            warnings.extend(input.sft_result.warnings)

        # Aggregate derivative exposure
        if input.derivative_result is not None:
            if input.derivative_result.source_contribution is not None:
                contribution = input.derivative_result.source_contribution
                if contribution.treatment != ExposureTreatment.EXCLUDED:
                    # Derivatives use source-layer exposure (commitment_exposure is None at source)
                    exposure = (
                        contribution.commitment_exposure
                        if contribution.commitment_exposure is not None
                        else contribution.gross_exposure
                    )
                    base_exposure += exposure
                source_contributions.append(contribution)

            unsupported_exposures.extend(input.derivative_result.unsupported_exposures)
            warnings.extend(input.derivative_result.warnings)

        # Apply eligible commitment reductions
        applied_reductions: list = []
        ignored_reductions: list = []

        final_exposure = base_exposure
        for reduction in input.commitment_reductions:
            if self._is_reduction_eligible(reduction):
                # Apply reduction only if it doesn't make exposure negative
                if final_exposure - reduction.reduction_amount >= Decimal("0"):
                    final_exposure -= reduction.reduction_amount
                    applied_reductions.append(reduction)
                else:
                    # Reduction would make exposure negative; ignore it
                    ignored_reductions.append(reduction)
                    warnings.append(
                        f"Reduction {reduction.reduction_id} ({reduction.reduction_type.value}) "
                        f"would make exposure negative; ignored"
                    )
            else:
                ignored_reductions.append(reduction)
                reason = self._reduction_ineligibility_reason(reduction)
                warnings.append(
                    f"Reduction {reduction.reduction_id} ({reduction.reduction_type.value}) "
                    f"ineligible: {reason}"
                )

        # Calculate leverage ratio
        nav = input.portfolio.nav
        leverage_ratio = final_exposure / nav if nav > Decimal("0") else Decimal("0")

        # Build method result
        method_result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_COMMITMENT,
            nav=nav,
            total_exposure=final_exposure,
            leverage_ratio=leverage_ratio,
            position_contributions=[],  # Commitment aggregation doesn't track position level
            source_contributions=source_contributions,
            unsupported_exposures=unsupported_exposures,
            warnings=warnings,
        )

        # Build commitment result with reduction audit trail
        total_reductions = base_exposure - final_exposure

        return AIFMDCommitmentLeverageResult(
            method_result=method_result,
            base_exposure_before_reductions=base_exposure,
            total_reductions=total_reductions,
            final_exposure=final_exposure,
            applied_reductions=applied_reductions,
            ignored_reductions=ignored_reductions,
            warnings=warnings,
        )

    def _is_reduction_eligible(self, reduction) -> bool:
        """Check if a reduction is eligible for application.

        Parameters
        ----------
        reduction
            CommitmentReduction to evaluate.

        Returns
        -------
        bool
            True if reduction meets all eligibility criteria for its type.
        """
        if not reduction.is_regulatory_eligible:
            return False

        if reduction.reduction_amount <= Decimal("0"):
            return False

        if reduction.reduction_type == CommitmentReductionType.NETTING:
            # Netting requires underlying_identifier and source/target relationship
            if not reduction.underlying_identifier or not reduction.underlying_identifier.strip():
                return False
            # Must have traceable source/target
            has_source = (
                reduction.source_position_id is not None
                or reduction.source_derivative_id is not None
            )
            has_target = (
                reduction.target_position_id is not None
                or reduction.target_derivative_id is not None
            )
            return has_source and has_target

        elif reduction.reduction_type == CommitmentReductionType.HEDGING:
            # Hedging requires reason and source/target relationship
            if not reduction.reason or not reduction.reason.strip():
                return False
            has_source = (
                reduction.source_position_id is not None
                or reduction.source_derivative_id is not None
            )
            has_target = (
                reduction.target_position_id is not None
                or reduction.target_derivative_id is not None
            )
            return has_source and has_target

        elif reduction.reduction_type == CommitmentReductionType.CURRENCY_HEDGING:
            # Currency hedging requires reason and source/target relationship
            if not reduction.reason or not reduction.reason.strip():
                return False
            has_source = (
                reduction.source_position_id is not None
                or reduction.source_derivative_id is not None
            )
            has_target = (
                reduction.target_position_id is not None
                or reduction.target_derivative_id is not None
            )
            return has_source and has_target

        elif reduction.reduction_type == CommitmentReductionType.OTHER:
            # Other type requires at least reason and source/target
            if not reduction.reason or not reduction.reason.strip():
                return False
            has_source = (
                reduction.source_position_id is not None
                or reduction.source_derivative_id is not None
            )
            has_target = (
                reduction.target_position_id is not None
                or reduction.target_derivative_id is not None
            )
            return has_source and has_target

        return False

    def _reduction_ineligibility_reason(self, reduction) -> str:
        """Generate ineligibility reason for a reduction.

        Parameters
        ----------
        reduction
            CommitmentReduction to evaluate.

        Returns
        -------
        str
            Human-readable reason for ineligibility.
        """
        if not reduction.is_regulatory_eligible:
            return "not marked as regulatory eligible"

        if reduction.reduction_amount <= Decimal("0"):
            return f"reduction amount not positive ({reduction.reduction_amount})"

        if reduction.reduction_type == CommitmentReductionType.NETTING:
            if not reduction.underlying_identifier or not reduction.underlying_identifier.strip():
                return "NETTING requires underlying_identifier"
            has_source = (
                reduction.source_position_id is not None
                or reduction.source_derivative_id is not None
            )
            has_target = (
                reduction.target_position_id is not None
                or reduction.target_derivative_id is not None
            )
            if not (has_source and has_target):
                return "NETTING requires traceable source and target"

        elif reduction.reduction_type == CommitmentReductionType.HEDGING:
            if not reduction.reason or not reduction.reason.strip():
                return "HEDGING requires reason"
            has_source = (
                reduction.source_position_id is not None
                or reduction.source_derivative_id is not None
            )
            has_target = (
                reduction.target_position_id is not None
                or reduction.target_derivative_id is not None
            )
            if not (has_source and has_target):
                return "HEDGING requires traceable source and target"

        elif reduction.reduction_type == CommitmentReductionType.CURRENCY_HEDGING:
            if not reduction.reason or not reduction.reason.strip():
                return "CURRENCY_HEDGING requires reason"
            has_source = (
                reduction.source_position_id is not None
                or reduction.source_derivative_id is not None
            )
            has_target = (
                reduction.target_position_id is not None
                or reduction.target_derivative_id is not None
            )
            if not (has_source and has_target):
                return "CURRENCY_HEDGING requires traceable source and target"

        elif reduction.reduction_type == CommitmentReductionType.OTHER:
            if not reduction.reason or not reduction.reason.strip():
                return "OTHER type requires reason"
            has_source = (
                reduction.source_position_id is not None
                or reduction.source_derivative_id is not None
            )
            has_target = (
                reduction.target_position_id is not None
                or reduction.target_derivative_id is not None
            )
            if not (has_source and has_target):
                return "OTHER type requires traceable source and target"

        return "unknown ineligibility reason"
