"""Tests for UCITS global exposure measurement.

Validates UCITS commitment approach global exposure calculation.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.leverage import (
    CommitmentReduction,
    CommitmentReductionType,
    ExposureTreatment,
    LeverageExposureSourceContribution,
    LeverageSource,
)
from manco_risk.risk.leverage.derivative_result import DerivativeExposureResult
from manco_risk.risk.ucits import (
    UCITSCommitmentGlobalExposureEngine,
    UCITSGlobalExposureInput,
    UCITSGlobalExposureMethod,
    UCITSGlobalExposureResult,
    UCITSGlobalExposureStatus,
)


@pytest.fixture
def base_portfolio():
    """Create a basic portfolio."""
    return RiskReadyPortfolio(
        fund_id=1,
        fund_base_currency="EUR",
        valuation_date="2026-06-11",
        nav=Decimal("10000000"),
        positions=[],
    )


@pytest.fixture
def derivative_result_with_exposure():
    """Create a derivative result with exposure."""
    source_contribution = LeverageExposureSourceContribution(
        source=LeverageSource.DERIVATIVE,
        gross_exposure=Decimal("5000000"),
        commitment_exposure=None,
        treatment=ExposureTreatment.PENDING_METHOD_RULE,
    )
    return DerivativeExposureResult(
        derivative_records=[],
        source_contribution=source_contribution,
        unsupported_exposures=[],
        warnings=[],
    )


class TestUCITSGlobalExposureModels:
    """Test UCITS global exposure models."""

    def test_global_exposure_input_creation(self, base_portfolio):
        """Create valid UCITS global exposure input."""
        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=None,
            eligible_reductions=[],
        )

        assert input_data.portfolio == base_portfolio
        assert input_data.derivative_result is None
        assert input_data.eligible_reductions == []

    def test_global_exposure_result_frozen(self):
        """Result model is immutable."""
        result = UCITSGlobalExposureResult(
            fund_id=1,
            valuation_date=date(2026, 6, 11),
            method=UCITSGlobalExposureMethod.COMMITMENT,
            nav=Decimal("10000000"),
            global_exposure=Decimal("5000000"),
            global_exposure_ratio=Decimal("0.50"),
            limit_ratio=Decimal("1.0"),
            status=UCITSGlobalExposureStatus.WITHIN_LIMIT,
        )

        with pytest.raises(Exception):
            result.nav = Decimal("11000000")

    def test_global_exposure_result_validation_positive_nav(self):
        """NAV must be positive."""
        with pytest.raises(ValueError, match="nav must be positive"):
            UCITSGlobalExposureResult(
                fund_id=1,
                valuation_date=date(2026, 6, 11),
                method=UCITSGlobalExposureMethod.COMMITMENT,
                nav=Decimal("0"),
                global_exposure=Decimal("5000000"),
                global_exposure_ratio=Decimal("0.50"),
                limit_ratio=Decimal("1.0"),
                status=UCITSGlobalExposureStatus.WITHIN_LIMIT,
            )

    def test_global_exposure_result_validation_non_negative_exposure(self):
        """Global exposure must be non-negative."""
        with pytest.raises(ValueError, match="global_exposure must be non-negative"):
            UCITSGlobalExposureResult(
                fund_id=1,
                valuation_date=date(2026, 6, 11),
                method=UCITSGlobalExposureMethod.COMMITMENT,
                nav=Decimal("10000000"),
                global_exposure=Decimal("-1000000"),
                global_exposure_ratio=Decimal("0.50"),
                limit_ratio=Decimal("1.0"),
                status=UCITSGlobalExposureStatus.WITHIN_LIMIT,
            )


class TestUCITSCommitmentEngine:
    """Test UCITS commitment global exposure engine."""

    def test_engine_instantiation(self):
        """Engine can be instantiated."""
        engine = UCITSCommitmentGlobalExposureEngine()
        assert engine is not None

    def test_no_derivative_result_gives_zero_exposure(self, base_portfolio):
        """No derivative result yields zero global exposure."""
        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=None,
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert result.global_exposure == Decimal("0")
        assert result.global_exposure_ratio == Decimal("0")
        assert result.status == UCITSGlobalExposureStatus.WITHIN_LIMIT

    def test_derivative_exposure_included(self, base_portfolio, derivative_result_with_exposure):
        """Derivative exposure is included as UCITS global exposure."""
        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result_with_exposure,
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert result.global_exposure == Decimal("5000000")
        assert result.global_exposure_ratio == Decimal("0.50")

    def test_global_exposure_ratio_calculated(
        self, base_portfolio, derivative_result_with_exposure
    ):
        """Global exposure ratio = global exposure / NAV."""
        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result_with_exposure,
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        expected_ratio = Decimal("5000000") / Decimal("10000000")
        assert result.global_exposure_ratio == expected_ratio

    def test_status_within_limit(self, base_portfolio, derivative_result_with_exposure):
        """Status is WITHIN_LIMIT when ratio <= 1."""
        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result_with_exposure,
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert result.global_exposure_ratio == Decimal("0.50")
        assert result.status == UCITSGlobalExposureStatus.WITHIN_LIMIT

    def test_status_breach(self):
        """Status is BREACH when ratio > 1."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date="2026-06-11",
            nav=Decimal("5000000"),
            positions=[],
        )

        source_contribution = LeverageExposureSourceContribution(
            source=LeverageSource.DERIVATIVE,
            gross_exposure=Decimal("7000000"),
            commitment_exposure=None,
            treatment=ExposureTreatment.PENDING_METHOD_RULE,
        )
        derivative_result = DerivativeExposureResult(
            derivative_records=[],
            source_contribution=source_contribution,
            unsupported_exposures=[],
            warnings=[],
        )

        input_data = UCITSGlobalExposureInput(
            portfolio=portfolio,
            derivative_result=derivative_result,
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert result.global_exposure_ratio == Decimal("1.40")
        assert result.status == UCITSGlobalExposureStatus.BREACH

    def test_limit_ratio_is_one(self, base_portfolio, derivative_result_with_exposure):
        """Limit ratio is 1.0 (100% NAV)."""
        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result_with_exposure,
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert result.limit_ratio == Decimal("1.0")

    def test_method_is_commitment(self, base_portfolio, derivative_result_with_exposure):
        """Method is COMMITMENT."""
        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result_with_exposure,
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert result.method == UCITSGlobalExposureMethod.COMMITMENT

    def test_excluded_derivative_not_included(self, base_portfolio):
        """Explicitly excluded derivatives are not included."""
        source_contribution = LeverageExposureSourceContribution(
            source=LeverageSource.DERIVATIVE,
            gross_exposure=Decimal("5000000"),
            commitment_exposure=None,
            treatment=ExposureTreatment.EXCLUDED,
            exclusion_reason="Prohibited strategy",
        )
        derivative_result = DerivativeExposureResult(
            derivative_records=[],
            source_contribution=source_contribution,
            unsupported_exposures=[],
            warnings=[],
        )

        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result,
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert result.global_exposure == Decimal("0")

    def test_unsupported_exposures_propagated(self, base_portfolio):
        """Unsupported exposures from derivative result are propagated."""
        from manco_risk.risk.leverage import UnsupportedLeverageExposure

        unsupported = UnsupportedLeverageExposure(
            asset_class="Structured Note",
            source=LeverageSource.DERIVATIVE,
            reason="Embedded derivative not supported",
        )

        source_contribution = LeverageExposureSourceContribution(
            source=LeverageSource.DERIVATIVE,
            gross_exposure=Decimal("1000000"),
            commitment_exposure=None,
            treatment=ExposureTreatment.PENDING_METHOD_RULE,
        )
        derivative_result = DerivativeExposureResult(
            derivative_records=[],
            source_contribution=source_contribution,
            unsupported_exposures=[unsupported],
            warnings=[],
        )

        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result,
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert len(result.unsupported_exposures) == 1
        assert result.unsupported_exposures[0].asset_class == "Structured Note"

    def test_warnings_propagated(self, base_portfolio):
        """Warnings from derivative result are propagated."""
        source_contribution = LeverageExposureSourceContribution(
            source=LeverageSource.DERIVATIVE,
            gross_exposure=Decimal("1000000"),
            commitment_exposure=None,
            treatment=ExposureTreatment.PENDING_METHOD_RULE,
        )
        derivative_result = DerivativeExposureResult(
            derivative_records=[],
            source_contribution=source_contribution,
            unsupported_exposures=[],
            warnings=["Derivative ABC123: missing market data"],
        )

        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result,
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert len(result.warnings) >= 1
        assert "missing market data" in result.warnings[0]

    def test_eligible_reduction_applied(self, base_portfolio, derivative_result_with_exposure):
        """Eligible reduction reduces global exposure."""
        reduction = CommitmentReduction(
            reduction_id="NETTING-001",
            reduction_type=CommitmentReductionType.NETTING,
            source_position_id=1,
            target_position_id=2,
            underlying_identifier="IE00B4L5Y983",
            reduction_amount=Decimal("1000000"),
            reason="Same underlying",
            is_regulatory_eligible=True,
        )

        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result_with_exposure,
            eligible_reductions=[reduction],
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert result.global_exposure == Decimal("4000000")
        assert result.global_exposure_ratio == Decimal("0.40")

    def test_ineligible_reduction_ignored(self, base_portfolio, derivative_result_with_exposure):
        """Ineligible reduction is ignored and warned."""
        reduction = CommitmentReduction(
            reduction_id="INVALID-001",
            reduction_type=CommitmentReductionType.NETTING,
            source_position_id=1,
            target_position_id=2,
            underlying_identifier="IE00B4L5Y983",
            reduction_amount=Decimal("1000000"),
            reason="Not eligible",
            is_regulatory_eligible=False,
        )

        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result_with_exposure,
            eligible_reductions=[reduction],
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert result.global_exposure == Decimal("5000000")
        assert len(result.warnings) >= 1
        assert "ineligible" in result.warnings[0]

    def test_reduction_cannot_make_negative(self, base_portfolio):
        """Reduction cannot make exposure negative."""
        source_contribution = LeverageExposureSourceContribution(
            source=LeverageSource.DERIVATIVE,
            gross_exposure=Decimal("500000"),
            commitment_exposure=None,
            treatment=ExposureTreatment.PENDING_METHOD_RULE,
        )
        derivative_result = DerivativeExposureResult(
            derivative_records=[],
            source_contribution=source_contribution,
            unsupported_exposures=[],
            warnings=[],
        )

        reduction = CommitmentReduction(
            reduction_id="EXCESSIVE-001",
            reduction_type=CommitmentReductionType.NETTING,
            source_position_id=1,
            target_position_id=2,
            underlying_identifier="IE00B4L5Y983",
            reduction_amount=Decimal("10000000"),
            reason="Large reduction",
            is_regulatory_eligible=True,
        )

        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result,
            eligible_reductions=[reduction],
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert result.global_exposure == Decimal("0")
        assert len(result.warnings) >= 1
        assert "would make exposure negative" in result.warnings[0]

    def test_valuation_date_preserved(self, base_portfolio, derivative_result_with_exposure):
        """Valuation date is preserved from portfolio."""
        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result_with_exposure,
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert result.valuation_date == date(2026, 6, 11)

    def test_fund_id_preserved(self, base_portfolio, derivative_result_with_exposure):
        """Fund ID is preserved from portfolio."""
        input_data = UCITSGlobalExposureInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result_with_exposure,
        )

        engine = UCITSCommitmentGlobalExposureEngine()
        result = engine.calculate(input_data)

        assert result.fund_id == base_portfolio.fund_id

    def test_no_database_imports(self):
        """Module has no database imports."""
        import inspect

        import manco_risk.risk.ucits.commitment_engine as module

        # Check module source doesn't import from database module
        source = inspect.getsource(module)
        assert "from manco_risk.database" not in source
        assert "import.*repository" not in source.lower()
        assert "from.*orm" not in source.lower()
