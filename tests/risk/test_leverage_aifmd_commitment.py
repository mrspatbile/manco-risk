"""Tests for AIFMD commitment leverage aggregation engine.

Validates commitment exposure aggregation, reduction eligibility, and reduction application.
"""

from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.leverage import (
    AIFMDCommitmentLeverageEngine,
    AIFMDLeverageAggregationInput,
    CommitmentReduction,
    CommitmentReductionType,
    ExposureTreatment,
    LeverageExposureSourceContribution,
    LeverageMethod,
    LeverageSource,
)
from manco_risk.risk.leverage.cash_result import CashExposureResult
from manco_risk.risk.leverage.derivative_result import DerivativeExposureResult
from manco_risk.risk.leverage.direct_borrowing_result import DirectBorrowingExposureResult
from manco_risk.risk.leverage.physical_instrument_result import PhysicalInstrumentExposureResult
from manco_risk.risk.leverage.sft_result import SFTExposureResult


@pytest.fixture
def base_portfolio():
    """Create a basic risk-ready portfolio for aggregation tests."""
    nav = Decimal("10000000")
    return RiskReadyPortfolio(
        fund_id=1,
        fund_base_currency="EUR",
        valuation_date="2026-06-11",
        nav=nav,
        positions=[],
    )


@pytest.fixture
def physical_result_with_commitment():
    """Create a physical instrument result with commitment exposure."""
    source_contribution = LeverageExposureSourceContribution(
        source=LeverageSource.PHYSICAL_INSTRUMENT,
        gross_exposure=Decimal("5000000"),
        commitment_exposure=Decimal("5000000"),
        treatment=ExposureTreatment.INCLUDED,
    )
    return PhysicalInstrumentExposureResult(
        position_contributions=[],
        source_contribution=source_contribution,
        unsupported_exposures=[],
        warnings=[],
    )


@pytest.fixture
def cash_result():
    """Create a cash result (zero exposure, excluded)."""
    source_contribution = LeverageExposureSourceContribution(
        source=LeverageSource.CASH_AND_CASH_EQUIVALENT,
        gross_exposure=Decimal("0"),
        commitment_exposure=Decimal("0"),
        treatment=ExposureTreatment.EXCLUDED,
        exclusion_reason="base-currency cash is excluded",
    )
    return CashExposureResult(
        position_contributions=[],
        source_contribution=source_contribution,
        unsupported_exposures=[],
        warnings=[],
    )


@pytest.fixture
def derivative_result_pending():
    """Create a derivative result with PENDING_METHOD_RULE treatment."""
    source_contribution = LeverageExposureSourceContribution(
        source=LeverageSource.DERIVATIVE,
        gross_exposure=Decimal("1500000"),
        commitment_exposure=None,
        treatment=ExposureTreatment.PENDING_METHOD_RULE,
    )
    return DerivativeExposureResult(
        derivative_records=[],
        source_contribution=source_contribution,
        unsupported_exposures=[],
        warnings=[],
    )


@pytest.fixture
def borrowing_result():
    """Create a direct borrowing result."""
    direct = LeverageExposureSourceContribution(
        source=LeverageSource.DIRECT_BORROWING,
        gross_exposure=Decimal("2000000"),
        commitment_exposure=Decimal("2000000"),
        treatment=ExposureTreatment.INCLUDED,
    )
    reinvested = LeverageExposureSourceContribution(
        source=LeverageSource.REINVESTED_BORROWING,
        gross_exposure=Decimal("500000"),
        commitment_exposure=None,
        treatment=ExposureTreatment.INCLUDED,
    )
    return DirectBorrowingExposureResult(
        borrowing_records=[],
        source_contributions=[direct, reinvested],
        warnings=[],
    )


@pytest.fixture
def sft_result():
    """Create an SFT result."""
    repo = LeverageExposureSourceContribution(
        source=LeverageSource.SFT_REPO,
        gross_exposure=Decimal("1000000"),
        commitment_exposure=None,
        treatment=ExposureTreatment.INCLUDED,
    )
    return SFTExposureResult(
        sft_records=[],
        source_contributions=[repo],
        warnings=[],
    )


class TestAIFMDCommitmentBasics:
    """Test basic commitment engine functionality."""

    def test_engine_instantiation(self):
        """Engine can be instantiated."""
        engine = AIFMDCommitmentLeverageEngine()
        assert engine is not None

    def test_physical_only_commitment_exposure(
        self, base_portfolio, physical_result_with_commitment
    ):
        """Physical instruments only: commitment equals physical commitment exposure."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert result.method_result.method == LeverageMethod.AIFMD_COMMITMENT
        assert result.base_exposure_before_reductions == Decimal("5000000")
        assert result.total_reductions == Decimal("0")
        assert result.final_exposure == Decimal("5000000")
        assert len(result.applied_reductions) == 0

    def test_cash_only_commitment_exposure(self, base_portfolio, cash_result):
        """Cash only: commitment exposure is zero (excluded)."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            cash_result=cash_result,
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert result.base_exposure_before_reductions == Decimal("0")
        assert result.final_exposure == Decimal("0")

    def test_no_reductions_base_equals_final(self, base_portfolio, physical_result_with_commitment):
        """No reductions: final exposure equals base exposure."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert result.base_exposure_before_reductions == result.final_exposure
        assert result.total_reductions == Decimal("0")

    def test_commitment_exposure_fallback_to_gross(self, base_portfolio):
        """If commitment_exposure is None, use gross_exposure conservatively."""
        source_contribution = LeverageExposureSourceContribution(
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            gross_exposure=Decimal("3000000"),
            commitment_exposure=None,
            treatment=ExposureTreatment.INCLUDED,
        )
        physical_result = PhysicalInstrumentExposureResult(
            position_contributions=[],
            source_contribution=source_contribution,
            unsupported_exposures=[],
            warnings=[],
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result,
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        # Falls back to gross_exposure (3M)
        assert result.base_exposure_before_reductions == Decimal("3000000")

    def test_multiple_sources_aggregated(
        self,
        base_portfolio,
        physical_result_with_commitment,
        borrowing_result,
        derivative_result_pending,
    ):
        """Multiple sources: exposures aggregated correctly."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            direct_borrowing_result=borrowing_result,
            derivative_result=derivative_result_pending,
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        # Physical (5M) + direct (2M) + reinvested (0.5M fallback to gross) + derivative (1.5M)
        expected_base = (
            Decimal("5000000") + Decimal("2000000") + Decimal("500000") + Decimal("1500000")
        )
        assert result.base_exposure_before_reductions == expected_base


class TestAIFMDCommitmentLeverageRatio:
    """Test commitment leverage ratio calculation."""

    def test_leverage_ratio_calculation(self, base_portfolio, physical_result_with_commitment):
        """Leverage ratio = final exposure / NAV."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        expected_ratio = Decimal("5000000") / base_portfolio.nav
        assert result.method_result.leverage_ratio == expected_ratio

    def test_leverage_ratio_with_reductions(self, base_portfolio, physical_result_with_commitment):
        """Leverage ratio reflects reduced exposure."""
        reduction = CommitmentReduction(
            reduction_id="NETTING-001",
            reduction_type=CommitmentReductionType.NETTING,
            source_position_id=1,
            target_position_id=2,
            underlying_identifier="IE00B4L5Y983",
            reduction_amount=Decimal("1000000"),
            reason="Same ISIN netting",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        expected_ratio = (Decimal("5000000") - Decimal("1000000")) / base_portfolio.nav
        assert result.method_result.leverage_ratio == expected_ratio


class TestAIFMDCommitmentReductions:
    """Test commitment reduction application and eligibility."""

    def test_eligible_netting_reduction_applied(
        self, base_portfolio, physical_result_with_commitment
    ):
        """Eligible NETTING reduction is applied."""
        reduction = CommitmentReduction(
            reduction_id="NETTING-001",
            reduction_type=CommitmentReductionType.NETTING,
            source_position_id=1,
            target_position_id=2,
            underlying_identifier="IE00B4L5Y983",
            reduction_amount=Decimal("1000000"),
            reason="Long-short same ISIN",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert result.final_exposure == Decimal("4000000")
        assert result.total_reductions == Decimal("1000000")
        assert len(result.applied_reductions) == 1
        assert result.applied_reductions[0].reduction_id == "NETTING-001"

    def test_ineligible_netting_missing_underlying(
        self, base_portfolio, physical_result_with_commitment
    ):
        """NETTING without underlying_identifier is ineligible."""
        reduction = CommitmentReduction(
            reduction_id="NETTING-001",
            reduction_type=CommitmentReductionType.NETTING,
            source_position_id=1,
            target_position_id=2,
            underlying_identifier=None,
            reduction_amount=Decimal("1000000"),
            reason="Offset",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert result.final_exposure == Decimal("5000000")
        assert result.total_reductions == Decimal("0")
        assert len(result.ignored_reductions) == 1
        assert "underlying_identifier" in result.warnings[0]

    def test_ineligible_netting_missing_target(
        self, base_portfolio, physical_result_with_commitment
    ):
        """NETTING without target is ineligible."""
        reduction = CommitmentReduction(
            reduction_id="NETTING-001",
            reduction_type=CommitmentReductionType.NETTING,
            source_position_id=1,
            target_position_id=None,
            target_derivative_id=None,
            underlying_identifier="IE00B4L5Y983",
            reduction_amount=Decimal("1000000"),
            reason="Offset",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert result.final_exposure == Decimal("5000000")
        assert len(result.ignored_reductions) == 1
        assert "source and target" in result.warnings[0]

    def test_eligible_hedging_reduction_applied(
        self, base_portfolio, physical_result_with_commitment
    ):
        """Eligible HEDGING reduction is applied."""
        reduction = CommitmentReduction(
            reduction_id="HEDGE-001",
            reduction_type=CommitmentReductionType.HEDGING,
            source_position_id=1,
            target_position_id=2,
            reduction_amount=Decimal("500000"),
            reason="Put option hedge for equity position",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert result.final_exposure == Decimal("4500000")
        assert len(result.applied_reductions) == 1

    def test_ineligible_hedging_missing_target(
        self, base_portfolio, physical_result_with_commitment
    ):
        """HEDGING without target is ineligible."""
        reduction = CommitmentReduction(
            reduction_id="HEDGE-001",
            reduction_type=CommitmentReductionType.HEDGING,
            source_position_id=1,
            target_position_id=None,
            target_derivative_id=None,
            reduction_amount=Decimal("500000"),
            reason="Hedge",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert result.final_exposure == Decimal("5000000")
        assert len(result.ignored_reductions) == 1
        assert "source and target" in result.warnings[0]

    def test_eligible_currency_hedging_reduction(
        self, base_portfolio, physical_result_with_commitment
    ):
        """Eligible CURRENCY_HEDGING reduction is applied."""
        reduction = CommitmentReduction(
            reduction_id="FX-HEDGE-001",
            reduction_type=CommitmentReductionType.CURRENCY_HEDGING,
            source_derivative_id="FX-001",
            target_position_id=1,
            reduction_amount=Decimal("750000"),
            reason="USD exposure hedge with EUR put",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert result.final_exposure == Decimal("4250000")
        assert len(result.applied_reductions) == 1

    def test_ineligible_not_regulatory_eligible(
        self, base_portfolio, physical_result_with_commitment
    ):
        """Reduction marked as not regulatory eligible is ignored."""
        reduction = CommitmentReduction(
            reduction_id="INVALID-001",
            reduction_type=CommitmentReductionType.NETTING,
            source_position_id=1,
            target_position_id=2,
            underlying_identifier="IE00B4L5Y983",
            reduction_amount=Decimal("1000000"),
            reason="Offset",
            is_regulatory_eligible=False,  # Not eligible
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert result.final_exposure == Decimal("5000000")
        assert len(result.ignored_reductions) == 1
        assert "regulatory eligible" in result.warnings[0]

    def test_reduction_with_zero_amount_rejected(
        self, base_portfolio, physical_result_with_commitment
    ):
        """Reduction with zero amount is ineligible."""
        reduction = CommitmentReduction(
            reduction_id="ZERO-001",
            reduction_type=CommitmentReductionType.HEDGING,
            source_position_id=1,
            target_position_id=2,
            reduction_amount=Decimal("0"),
            reason="Offset",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert result.final_exposure == Decimal("5000000")
        assert len(result.ignored_reductions) == 1

    def test_reduction_cannot_make_exposure_negative(
        self, base_portfolio, physical_result_with_commitment
    ):
        """Reduction that would make exposure negative is ignored."""
        reduction = CommitmentReduction(
            reduction_id="EXCESSIVE-001",
            reduction_type=CommitmentReductionType.HEDGING,
            source_position_id=1,
            target_position_id=2,
            reduction_amount=Decimal("10000000"),  # Exceeds base exposure
            reason="Hedge",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        # Exposure should not go negative
        assert result.final_exposure == Decimal("5000000")
        assert len(result.ignored_reductions) == 1
        assert "would make exposure negative" in result.warnings[0]

    def test_multiple_reductions_applied_sequentially(
        self, base_portfolio, physical_result_with_commitment
    ):
        """Multiple eligible reductions are applied sequentially."""
        reduction1 = CommitmentReduction(
            reduction_id="HEDGE-001",
            reduction_type=CommitmentReductionType.HEDGING,
            source_position_id=1,
            target_position_id=2,
            reduction_amount=Decimal("1000000"),
            reason="Put hedge",
            is_regulatory_eligible=True,
        )
        reduction2 = CommitmentReduction(
            reduction_id="HEDGE-002",
            reduction_type=CommitmentReductionType.HEDGING,
            source_position_id=3,
            target_position_id=4,
            reduction_amount=Decimal("500000"),
            reason="Call hedge",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction1, reduction2],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert result.final_exposure == Decimal("3500000")
        assert result.total_reductions == Decimal("1500000")
        assert len(result.applied_reductions) == 2

    def test_mixed_eligible_and_ineligible_reductions(
        self, base_portfolio, physical_result_with_commitment
    ):
        """Mix of eligible and ineligible reductions."""
        eligible = CommitmentReduction(
            reduction_id="ELIGIBLE-001",
            reduction_type=CommitmentReductionType.HEDGING,
            source_position_id=1,
            target_position_id=2,
            reduction_amount=Decimal("1000000"),
            reason="Hedge",
            is_regulatory_eligible=True,
        )
        ineligible = CommitmentReduction(
            reduction_id="INELIGIBLE-001",
            reduction_type=CommitmentReductionType.HEDGING,
            source_position_id=3,
            target_position_id=4,
            reduction_amount=Decimal("500000"),
            reason="Hedge",
            is_regulatory_eligible=False,  # Marked as ineligible
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[eligible, ineligible],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        # Only eligible reduction applied
        assert result.final_exposure == Decimal("4000000")
        assert len(result.applied_reductions) == 1
        assert len(result.ignored_reductions) == 1


class TestAIFMDCommitmentAuditTrail:
    """Test audit trail and warning generation."""

    def test_applied_reductions_tracked(self, base_portfolio, physical_result_with_commitment):
        """Applied reductions are tracked in result."""
        reduction = CommitmentReduction(
            reduction_id="NETTING-001",
            reduction_type=CommitmentReductionType.NETTING,
            source_position_id=1,
            target_position_id=2,
            underlying_identifier="IE00B4L5Y983",
            reduction_amount=Decimal("1000000"),
            reason="Same ISIN",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert len(result.applied_reductions) == 1
        assert result.applied_reductions[0].reduction_id == "NETTING-001"

    def test_ignored_reductions_tracked(self, base_portfolio, physical_result_with_commitment):
        """Ignored reductions are tracked in result."""
        reduction = CommitmentReduction(
            reduction_id="INELIGIBLE-001",
            reduction_type=CommitmentReductionType.NETTING,
            source_position_id=1,
            target_position_id=None,
            target_derivative_id=None,
            underlying_identifier="IE00B4L5Y983",
            reduction_amount=Decimal("1000000"),
            reason="Offset",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert len(result.ignored_reductions) == 1
        assert result.ignored_reductions[0].reduction_id == "INELIGIBLE-001"

    def test_warnings_generated_for_ignored_reductions(
        self, base_portfolio, physical_result_with_commitment
    ):
        """Warnings are generated for ignored reductions."""
        reduction = CommitmentReduction(
            reduction_id="INELIGIBLE-001",
            reduction_type=CommitmentReductionType.NETTING,
            source_position_id=1,
            target_position_id=None,
            target_derivative_id=None,
            underlying_identifier="IE00B4L5Y983",
            reduction_amount=Decimal("1000000"),
            reason="Offset",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result_with_commitment,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert len(result.warnings) >= 1
        assert "INELIGIBLE-001" in result.warnings[0]
        assert "ineligible" in result.warnings[0]

    def test_zero_base_exposure_with_reductions(self, base_portfolio, cash_result):
        """Reductions on zero base exposure are handled gracefully."""
        reduction = CommitmentReduction(
            reduction_id="REDUCTION-001",
            reduction_type=CommitmentReductionType.HEDGING,
            source_position_id=1,
            target_position_id=2,
            reduction_amount=Decimal("100000"),
            reason="Hedge",
            is_regulatory_eligible=True,
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            cash_result=cash_result,
            commitment_reductions=[reduction],
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        # Reduction would make exposure negative; should be ignored
        assert result.final_exposure == Decimal("0")
        assert len(result.ignored_reductions) == 1


class TestAIFMDCommitmentExcludedSources:
    """Test handling of excluded source contributions."""

    def test_excluded_source_excluded_from_commitment(self, base_portfolio):
        """Excluded sources do not contribute to commitment exposure."""
        excluded_contribution = LeverageExposureSourceContribution(
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            gross_exposure=Decimal("1000000"),
            commitment_exposure=Decimal("1000000"),
            treatment=ExposureTreatment.EXCLUDED,
            exclusion_reason="Restricted sector",
        )
        physical_result = PhysicalInstrumentExposureResult(
            position_contributions=[],
            source_contribution=excluded_contribution,
            unsupported_exposures=[],
            warnings=[],
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result,
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        assert result.base_exposure_before_reductions == Decimal("0")

    def test_mixed_included_and_excluded_sources(self, base_portfolio):
        """Included sources aggregate, excluded sources ignored."""
        # Create two physical results: one included, one excluded
        included = LeverageExposureSourceContribution(
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            gross_exposure=Decimal("5000000"),
            commitment_exposure=Decimal("5000000"),
            treatment=ExposureTreatment.INCLUDED,
        )
        physical_included = PhysicalInstrumentExposureResult(
            position_contributions=[],
            source_contribution=included,
            unsupported_exposures=[],
            warnings=[],
        )

        excluded = LeverageExposureSourceContribution(
            source=LeverageSource.SFT_REPO,
            gross_exposure=Decimal("1000000"),
            commitment_exposure=Decimal("1000000"),
            treatment=ExposureTreatment.EXCLUDED,
            exclusion_reason="Repo excluded by policy",
        )
        sft_excluded = SFTExposureResult(
            sft_records=[],
            source_contributions=[excluded],
            warnings=[],
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_included,
            sft_result=sft_excluded,
        )
        engine = AIFMDCommitmentLeverageEngine()
        result = engine.calculate(input_data)

        # Only included source counts
        assert result.base_exposure_before_reductions == Decimal("5000000")
