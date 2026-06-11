"""UCITS global exposure calculation using commitment approach.

Calculates UCITS global exposure under the commitment approach.
Focuses on derivative-based market exposure.

Key design:
- Uses provided derivative exposure (no pricing or Greeks)
- Applies explicit eligible reductions only
- Does NOT implement automatic netting/hedging
- Limit: 100% of NAV (ratio = 1.0)
- Status: WITHIN_LIMIT (ratio <= 1), BREACH (ratio > 1), NOT_ASSESSED (no data)
"""

from datetime import date
from decimal import Decimal

from manco_risk.risk.leverage import (
    ExposureTreatment,
    LeverageSource,
)
from manco_risk.risk.ucits.global_exposure_models import (
    UCITSGlobalExposureInput,
    UCITSGlobalExposureMethod,
    UCITSGlobalExposureResult,
    UCITSGlobalExposureStatus,
)


class UCITSCommitmentGlobalExposureEngine:
    """Calculate UCITS global exposure using commitment approach.

    Commitment approach converts financial derivatives to equivalent underlying
    positions and aggregates to measure global market exposure.

    Rules:
    - Global exposure = derivative source contribution gross exposure (after reductions)
    - Physical instruments, cash, borrowing, and SFTs are excluded in Phase 1
    - Limit = 100% of NAV (limit_ratio = 1.0)
    - Status: WITHIN_LIMIT if ratio <= 1, BREACH if > 1
    """

    def calculate(self, input: UCITSGlobalExposureInput) -> UCITSGlobalExposureResult:
        """Calculate UCITS global exposure under commitment approach.

        Parameters
        ----------
        input
            UCITS global exposure input with portfolio and derivative result.

        Returns
        -------
        UCITSGlobalExposureResult
            Global exposure measurement with limit status.
        """
        valuation_date = date.fromisoformat(input.portfolio.valuation_date)
        nav = input.portfolio.nav
        global_exposure = Decimal("0")
        unsupported_exposures = []
        warnings = []
        source_contributions = []

        # Extract derivative global exposure
        if input.derivative_result is not None:
            if input.derivative_result.source_contribution is not None:
                contrib = input.derivative_result.source_contribution

                # Only DERIVATIVE source is included in UCITS global exposure Phase 1
                if contrib.source == LeverageSource.DERIVATIVE:
                    # Only include if not explicitly excluded
                    if contrib.treatment != ExposureTreatment.EXCLUDED:
                        global_exposure = contrib.gross_exposure

                    # Track contribution for audit
                    source_contributions.append(contrib)

            # Track unsupported exposures
            unsupported_exposures.extend(input.derivative_result.unsupported_exposures)
            warnings.extend(input.derivative_result.warnings)

        # Apply explicit eligible reductions (Phase 1: simple approach)
        total_reductions = Decimal("0")
        if input.eligible_reductions:
            for reduction in input.eligible_reductions:
                if self._is_reduction_eligible(reduction):
                    # Reduction cannot make exposure negative
                    if global_exposure - reduction.reduction_amount >= Decimal("0"):
                        global_exposure -= reduction.reduction_amount
                        total_reductions += reduction.reduction_amount
                    else:
                        warnings.append(
                            f"Reduction {reduction.reduction_id} would make exposure negative; "
                            f"capped at zero"
                        )
                        total_reductions += global_exposure
                        global_exposure = Decimal("0")
                else:
                    warnings.append(f"Reduction {reduction.reduction_id} ineligible; ignored")

        # Calculate ratio and status
        global_exposure_ratio = global_exposure / nav if nav > Decimal("0") else Decimal("0")
        limit_ratio = Decimal("1.0")  # 100% of NAV for commitment approach

        status = self._determine_status(global_exposure_ratio, limit_ratio)

        return UCITSGlobalExposureResult(
            fund_id=input.portfolio.fund_id,
            valuation_date=valuation_date,
            method=UCITSGlobalExposureMethod.COMMITMENT,
            nav=nav,
            global_exposure=global_exposure,
            global_exposure_ratio=global_exposure_ratio,
            limit_ratio=limit_ratio,
            status=status,
            source_contributions=source_contributions,
            unsupported_exposures=unsupported_exposures,
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
            True if reduction is eligible and should be applied.
        """
        if not reduction.is_regulatory_eligible:
            return False
        if reduction.reduction_amount <= Decimal("0"):
            return False
        return True

    def _determine_status(
        self, global_exposure_ratio: Decimal, limit_ratio: Decimal
    ) -> UCITSGlobalExposureStatus:
        """Determine global exposure status relative to limit.

        Parameters
        ----------
        global_exposure_ratio
            Global exposure / NAV.
        limit_ratio
            Regulatory limit ratio (1.0 = 100%).

        Returns
        -------
        UCITSGlobalExposureStatus
            WITHIN_LIMIT, BREACH, or NOT_ASSESSED.
        """
        if global_exposure_ratio <= limit_ratio:
            return UCITSGlobalExposureStatus.WITHIN_LIMIT
        else:
            return UCITSGlobalExposureStatus.BREACH
