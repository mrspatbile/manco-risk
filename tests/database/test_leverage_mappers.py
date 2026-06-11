"""Tests for leverage result mappers.

Validates conversion of pure leverage results to ORM models.
"""

from decimal import Decimal

import pytest

from manco_risk.database.leverage_mappers import (
    map_commitment_leverage_result_to_orm,
    map_leverage_method_result_to_orm,
    map_source_contributions_to_orm,
)
from manco_risk.risk.leverage import (
    AIFMDCommitmentLeverageResult,
    CommitmentReduction,
    CommitmentReductionType,
    ExposureTreatment,
    LeverageExposureSourceContribution,
    LeverageMethod,
    LeverageMethodResult,
    LeverageSource,
)


@pytest.fixture
def gross_leverage_result():
    """Create a gross method leverage result."""
    source_contributions = [
        LeverageExposureSourceContribution(
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            gross_exposure=Decimal("5000000"),
            commitment_exposure=Decimal("5000000"),
            treatment=ExposureTreatment.INCLUDED,
        ),
        LeverageExposureSourceContribution(
            source=LeverageSource.DERIVATIVE,
            gross_exposure=Decimal("1500000"),
            commitment_exposure=None,
            treatment=ExposureTreatment.PENDING_METHOD_RULE,
        ),
    ]

    return LeverageMethodResult(
        method=LeverageMethod.AIFMD_GROSS,
        nav=Decimal("10000000"),
        total_exposure=Decimal("6500000"),
        leverage_ratio=Decimal("0.65"),
        position_contributions=[],
        source_contributions=source_contributions,
        unsupported_exposures=[],
        warnings=["Warning 1", "Warning 2"],
    )


@pytest.fixture
def commitment_leverage_result():
    """Create a commitment method leverage result with reductions."""
    source_contributions = [
        LeverageExposureSourceContribution(
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            gross_exposure=Decimal("5000000"),
            commitment_exposure=Decimal("5000000"),
            treatment=ExposureTreatment.INCLUDED,
        ),
    ]

    method_result = LeverageMethodResult(
        method=LeverageMethod.AIFMD_COMMITMENT,
        nav=Decimal("10000000"),
        total_exposure=Decimal("4500000"),
        leverage_ratio=Decimal("0.45"),
        position_contributions=[],
        source_contributions=source_contributions,
        unsupported_exposures=[],
        warnings=[],
    )

    applied_reductions = [
        CommitmentReduction(
            reduction_id="NETTING-001",
            reduction_type=CommitmentReductionType.NETTING,
            source_position_id=1,
            target_position_id=2,
            underlying_identifier="IE00B4L5Y983",
            reduction_amount=Decimal("500000"),
            reason="Same ISIN",
            is_regulatory_eligible=True,
        ),
    ]

    return AIFMDCommitmentLeverageResult(
        method_result=method_result,
        base_exposure_before_reductions=Decimal("5000000"),
        total_reductions=Decimal("500000"),
        final_exposure=Decimal("4500000"),
        applied_reductions=applied_reductions,
        ignored_reductions=[],
        warnings=[],
    )


class TestMapLeverageMethodResult:
    """Test mapping of gross leverage results."""

    def test_map_gross_result_to_orm(self, gross_leverage_result):
        """Map gross method result to ORM model."""
        orm_result = map_leverage_method_result_to_orm(
            gross_leverage_result, calculation_run_id=1, fund_id=1
        )

        assert orm_result.calculation_run_id == 1
        assert orm_result.fund_id == 1
        assert orm_result.method == "AIFMD_GROSS"
        assert orm_result.nav == Decimal("10000000")
        assert orm_result.total_exposure == Decimal("6500000")
        assert orm_result.leverage_ratio == Decimal("0.65")
        assert orm_result.base_exposure_before_reductions is None
        assert orm_result.total_reductions is None
        assert orm_result.final_exposure is None
        assert orm_result.num_applied_reductions == 0
        assert orm_result.num_ignored_reductions == 0

    def test_map_gross_result_preserves_warnings(self, gross_leverage_result):
        """Warnings are concatenated in ORM model."""
        orm_result = map_leverage_method_result_to_orm(
            gross_leverage_result, calculation_run_id=1, fund_id=1
        )

        assert orm_result.warnings == "Warning 1\nWarning 2"

    def test_map_gross_result_no_warnings(self):
        """ORM model handles empty warnings."""
        source_contributions = [
            LeverageExposureSourceContribution(
                source=LeverageSource.PHYSICAL_INSTRUMENT,
                gross_exposure=Decimal("5000000"),
                commitment_exposure=Decimal("5000000"),
                treatment=ExposureTreatment.INCLUDED,
            ),
        ]

        result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_GROSS,
            nav=Decimal("10000000"),
            total_exposure=Decimal("5000000"),
            leverage_ratio=Decimal("0.50"),
            position_contributions=[],
            source_contributions=source_contributions,
            unsupported_exposures=[],
            warnings=[],
        )

        orm_result = map_leverage_method_result_to_orm(result, calculation_run_id=1, fund_id=1)
        assert orm_result.warnings is None


class TestMapCommitmentLeverageResult:
    """Test mapping of commitment leverage results."""

    def test_map_commitment_result_to_orm(self, commitment_leverage_result):
        """Map commitment method result to ORM model."""
        orm_result = map_commitment_leverage_result_to_orm(
            commitment_leverage_result, calculation_run_id=1, fund_id=1
        )

        assert orm_result.calculation_run_id == 1
        assert orm_result.fund_id == 1
        assert orm_result.method == "AIFMD_COMMITMENT"
        assert orm_result.nav == Decimal("10000000")
        assert orm_result.total_exposure == Decimal("4500000")
        assert orm_result.leverage_ratio == commitment_leverage_result.method_result.leverage_ratio
        assert orm_result.base_exposure_before_reductions == Decimal("5000000")
        assert orm_result.total_reductions == Decimal("500000")
        assert orm_result.final_exposure == Decimal("4500000")
        assert orm_result.num_applied_reductions == 1
        assert orm_result.num_ignored_reductions == 0

    def test_map_commitment_result_with_ignored_reductions(self):
        """Map commitment result with ignored reductions."""
        method_result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_COMMITMENT,
            nav=Decimal("10000000"),
            total_exposure=Decimal("5000000"),
            leverage_ratio=Decimal("0.50"),
            position_contributions=[],
            source_contributions=[
                LeverageExposureSourceContribution(
                    source=LeverageSource.PHYSICAL_INSTRUMENT,
                    gross_exposure=Decimal("5000000"),
                    commitment_exposure=Decimal("5000000"),
                    treatment=ExposureTreatment.INCLUDED,
                ),
            ],
            unsupported_exposures=[],
            warnings=["Ignored reduction"],
        )

        ignored_reduction = CommitmentReduction(
            reduction_id="INVALID-001",
            reduction_type=CommitmentReductionType.NETTING,
            source_position_id=1,
            target_position_id=2,
            underlying_identifier="IE00B4L5Y983",
            reduction_amount=Decimal("100000"),
            reason="Invalid",
            is_regulatory_eligible=False,
        )

        result = AIFMDCommitmentLeverageResult(
            method_result=method_result,
            base_exposure_before_reductions=Decimal("5000000"),
            total_reductions=Decimal("0"),
            final_exposure=Decimal("5000000"),
            applied_reductions=[],
            ignored_reductions=[ignored_reduction],
            warnings=["Ignored reduction"],
        )

        orm_result = map_commitment_leverage_result_to_orm(result, calculation_run_id=1, fund_id=1)

        assert orm_result.num_applied_reductions == 0
        assert orm_result.num_ignored_reductions == 1


class TestMapSourceContributions:
    """Test mapping of source contributions."""

    def test_map_source_contributions(self):
        """Map source contributions to ORM models."""
        source_contributions = [
            LeverageExposureSourceContribution(
                source=LeverageSource.PHYSICAL_INSTRUMENT,
                gross_exposure=Decimal("5000000"),
                commitment_exposure=Decimal("5000000"),
                treatment=ExposureTreatment.INCLUDED,
            ),
            LeverageExposureSourceContribution(
                source=LeverageSource.CASH_AND_CASH_EQUIVALENT,
                gross_exposure=Decimal("0"),
                commitment_exposure=Decimal("0"),
                treatment=ExposureTreatment.EXCLUDED,
                exclusion_reason="Cash excluded from leverage",
            ),
        ]

        method_result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_GROSS,
            nav=Decimal("10000000"),
            total_exposure=Decimal("5000000"),
            leverage_ratio=Decimal("0.50"),
            position_contributions=[],
            source_contributions=source_contributions,
            unsupported_exposures=[],
            warnings=[],
        )

        orm_contributions = map_source_contributions_to_orm(
            leverage_result_id=1, method_result=method_result
        )

        assert len(orm_contributions) == 2

        # Physical instrument
        assert orm_contributions[0].source == "PHYSICAL_INSTRUMENT"
        assert orm_contributions[0].gross_exposure == Decimal("5000000")
        assert orm_contributions[0].commitment_exposure == Decimal("5000000")
        assert orm_contributions[0].treatment == "INCLUDED"
        assert orm_contributions[0].percentage_of_nav == Decimal("0.50")

        # Cash
        assert orm_contributions[1].source == "CASH_AND_CASH_EQUIVALENT"
        assert orm_contributions[1].gross_exposure == Decimal("0")
        assert orm_contributions[1].treatment == "EXCLUDED"
        assert orm_contributions[1].exclusion_reason == "Cash excluded from leverage"
        assert orm_contributions[1].percentage_of_nav == Decimal("0")

    def test_percentage_of_nav_calculated(self):
        """Percentage of NAV is calculated correctly."""
        source_contribution = LeverageExposureSourceContribution(
            source=LeverageSource.DERIVATIVE,
            gross_exposure=Decimal("2000000"),
            commitment_exposure=None,
            treatment=ExposureTreatment.PENDING_METHOD_RULE,
        )

        method_result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_GROSS,
            nav=Decimal("10000000"),
            total_exposure=Decimal("2000000"),
            leverage_ratio=Decimal("0.20"),
            position_contributions=[],
            source_contributions=[source_contribution],
            unsupported_exposures=[],
            warnings=[],
        )

        orm_contributions = map_source_contributions_to_orm(
            leverage_result_id=1, method_result=method_result
        )

        assert len(orm_contributions) == 1
        assert orm_contributions[0].percentage_of_nav == Decimal("0.20")
