"""Tests for leverage taxonomy and source models.

Validates enums, model construction, and all validation rules.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.leverage import (
    ExposureTreatment,
    LeverageExposureSourceContribution,
    LeverageInput,
    LeverageMethod,
    LeverageMethodResult,
    LeveragePositionContribution,
    LeverageResult,
    LeverageSource,
    UnsupportedLeverageExposure,
)

# Enum tests


class TestLeverageMethodEnum:
    """Test LeverageMethod enum."""

    def test_leverage_method_values_exist(self):
        """All required leverage methods are defined."""
        assert LeverageMethod.AIFMD_GROSS.value == "AIFMD_GROSS"
        assert LeverageMethod.AIFMD_COMMITMENT.value == "AIFMD_COMMITMENT"
        assert LeverageMethod.UCITS_COMMITMENT.value == "UCITS_COMMITMENT"
        assert LeverageMethod.UCITS_VAR_GLOBAL_EXPOSURE.value == "UCITS_VAR_GLOBAL_EXPOSURE"

    def test_leverage_method_count(self):
        """All expected leverage methods are present."""
        assert len(list(LeverageMethod)) == 4


class TestLeverageSourceEnum:
    """Test LeverageSource enum."""

    def test_leverage_source_values_exist(self):
        """All required leverage sources are defined."""
        assert LeverageSource.PHYSICAL_INSTRUMENT.value == "PHYSICAL_INSTRUMENT"
        assert LeverageSource.CASH_AND_CASH_EQUIVALENT.value == "CASH_AND_CASH_EQUIVALENT"
        assert LeverageSource.DIRECT_BORROWING.value == "DIRECT_BORROWING"
        assert LeverageSource.REINVESTED_BORROWING.value == "REINVESTED_BORROWING"
        assert LeverageSource.SFT_REPO.value == "SFT_REPO"
        assert LeverageSource.SFT_REVERSE_REPO.value == "SFT_REVERSE_REPO"
        assert LeverageSource.SECURITIES_LENDING.value == "SECURITIES_LENDING"
        assert LeverageSource.DERIVATIVE.value == "DERIVATIVE"
        assert LeverageSource.EMBEDDED_DERIVATIVE.value == "EMBEDDED_DERIVATIVE"
        assert LeverageSource.FUND_LOOK_THROUGH.value == "FUND_LOOK_THROUGH"
        assert LeverageSource.CONTROLLED_STRUCTURE.value == "CONTROLLED_STRUCTURE"
        assert LeverageSource.OTHER.value == "OTHER"

    def test_leverage_source_count(self):
        """All expected leverage sources are present."""
        assert len(list(LeverageSource)) == 12


class TestExposureTreatmentEnum:
    """Test ExposureTreatment enum."""

    def test_exposure_treatment_values_exist(self):
        """All required exposure treatments are defined."""
        assert ExposureTreatment.INCLUDED.value == "INCLUDED"
        assert ExposureTreatment.EXCLUDED.value == "EXCLUDED"
        assert ExposureTreatment.UNSUPPORTED.value == "UNSUPPORTED"
        assert ExposureTreatment.PENDING_METHOD_RULE.value == "PENDING_METHOD_RULE"

    def test_exposure_treatment_count(self):
        """All expected exposure treatments are present."""
        assert len(list(ExposureTreatment)) == 4


# UnsupportedLeverageExposure tests


class TestUnsupportedLeverageExposure:
    """Test UnsupportedLeverageExposure model."""

    def test_valid_minimal_construction(self):
        """Valid minimal unsupported exposure."""
        exp = UnsupportedLeverageExposure(
            asset_class="Bond",
            reason="Embedded derivative not yet supported",
        )
        assert exp.asset_class == "Bond"
        assert exp.reason == "Embedded derivative not yet supported"
        assert exp.position_id is None
        assert exp.isin is None
        assert exp.source is None

    def test_valid_full_construction(self):
        """Valid unsupported exposure with all fields."""
        exp = UnsupportedLeverageExposure(
            position_id=123,
            isin="DE0000000001",
            asset_class="Bond",
            source=LeverageSource.EMBEDDED_DERIVATIVE,
            reason="Embedded derivative not yet supported",
        )
        assert exp.position_id == 123
        assert exp.isin == "DE0000000001"
        assert exp.asset_class == "Bond"
        assert exp.source == LeverageSource.EMBEDDED_DERIVATIVE
        assert exp.reason == "Embedded derivative not yet supported"

    def test_rejects_empty_asset_class(self):
        """Asset class cannot be empty."""
        with pytest.raises(ValueError, match="asset_class must be non-empty"):
            UnsupportedLeverageExposure(
                asset_class="",
                reason="Test reason",
            )

    def test_rejects_whitespace_only_asset_class(self):
        """Asset class cannot be whitespace only."""
        with pytest.raises(ValueError, match="asset_class must be non-empty"):
            UnsupportedLeverageExposure(
                asset_class="   ",
                reason="Test reason",
            )

    def test_rejects_empty_reason(self):
        """Reason cannot be empty."""
        with pytest.raises(ValueError, match="reason must be non-empty"):
            UnsupportedLeverageExposure(
                asset_class="Bond",
                reason="",
            )

    def test_rejects_whitespace_only_reason(self):
        """Reason cannot be whitespace only."""
        with pytest.raises(ValueError, match="reason must be non-empty"):
            UnsupportedLeverageExposure(
                asset_class="Bond",
                reason="   ",
            )

    def test_model_is_frozen(self):
        """Model is immutable."""
        exp = UnsupportedLeverageExposure(
            asset_class="Bond",
            reason="Test",
        )
        with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen model
            exp.asset_class = "Equity"


# LeverageExposureSourceContribution tests


class TestLeverageExposureSourceContribution:
    """Test LeverageExposureSourceContribution model."""

    def test_valid_included_exposure(self):
        """Valid included source contribution."""
        src = LeverageExposureSourceContribution(
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            gross_exposure=Decimal("1000000"),
            commitment_exposure=Decimal("1000000"),
            treatment=ExposureTreatment.INCLUDED,
        )
        assert src.source == LeverageSource.PHYSICAL_INSTRUMENT
        assert src.gross_exposure == Decimal("1000000")
        assert src.commitment_exposure == Decimal("1000000")
        assert src.treatment == ExposureTreatment.INCLUDED
        assert src.exclusion_reason is None

    def test_valid_excluded_exposure(self):
        """Valid excluded source contribution with reason."""
        src = LeverageExposureSourceContribution(
            source=LeverageSource.CASH_AND_CASH_EQUIVALENT,
            gross_exposure=Decimal("0"),
            treatment=ExposureTreatment.EXCLUDED,
            exclusion_reason="Qualifying cash under AIFMD Article 7",
        )
        assert src.source == LeverageSource.CASH_AND_CASH_EQUIVALENT
        assert src.treatment == ExposureTreatment.EXCLUDED
        assert src.exclusion_reason == "Qualifying cash under AIFMD Article 7"

    def test_valid_unsupported_exposure(self):
        """Valid unsupported source contribution."""
        src = LeverageExposureSourceContribution(
            source=LeverageSource.DERIVATIVE,
            gross_exposure=Decimal("500000"),
            treatment=ExposureTreatment.UNSUPPORTED,
        )
        assert src.source == LeverageSource.DERIVATIVE
        assert src.treatment == ExposureTreatment.UNSUPPORTED

    def test_valid_pending_method_rule(self):
        """Valid pending method rule source contribution."""
        src = LeverageExposureSourceContribution(
            source=LeverageSource.SFT_REPO,
            gross_exposure=Decimal("750000"),
            treatment=ExposureTreatment.PENDING_METHOD_RULE,
        )
        assert src.source == LeverageSource.SFT_REPO
        assert src.treatment == ExposureTreatment.PENDING_METHOD_RULE

    def test_rejects_negative_gross_exposure(self):
        """Gross exposure cannot be negative."""
        with pytest.raises(ValueError, match="gross_exposure must be non-negative"):
            LeverageExposureSourceContribution(
                source=LeverageSource.PHYSICAL_INSTRUMENT,
                gross_exposure=Decimal("-100"),
                treatment=ExposureTreatment.INCLUDED,
            )

    def test_rejects_negative_commitment_exposure(self):
        """Commitment exposure cannot be negative."""
        with pytest.raises(ValueError, match="commitment_exposure must be non-negative"):
            LeverageExposureSourceContribution(
                source=LeverageSource.PHYSICAL_INSTRUMENT,
                gross_exposure=Decimal("1000"),
                commitment_exposure=Decimal("-500"),
                treatment=ExposureTreatment.INCLUDED,
            )

    def test_excluded_requires_exclusion_reason(self):
        """Excluded exposure must have exclusion reason."""
        with pytest.raises(ValueError, match="exclusion_reason must be non-empty"):
            LeverageExposureSourceContribution(
                source=LeverageSource.CASH_AND_CASH_EQUIVALENT,
                gross_exposure=Decimal("0"),
                treatment=ExposureTreatment.EXCLUDED,
            )

    def test_excluded_rejects_empty_reason(self):
        """Excluded exposure cannot have empty reason."""
        with pytest.raises(ValueError, match="exclusion_reason must be non-empty"):
            LeverageExposureSourceContribution(
                source=LeverageSource.CASH_AND_CASH_EQUIVALENT,
                gross_exposure=Decimal("0"),
                treatment=ExposureTreatment.EXCLUDED,
                exclusion_reason="",
            )

    def test_included_rejects_exclusion_reason(self):
        """Included exposure cannot have exclusion reason."""
        with pytest.raises(ValueError, match="exclusion_reason must be None"):
            LeverageExposureSourceContribution(
                source=LeverageSource.PHYSICAL_INSTRUMENT,
                gross_exposure=Decimal("1000"),
                treatment=ExposureTreatment.INCLUDED,
                exclusion_reason="Should not have reason",
            )

    def test_unsupported_rejects_exclusion_reason(self):
        """Unsupported exposure cannot have exclusion reason."""
        with pytest.raises(ValueError, match="exclusion_reason must be None"):
            LeverageExposureSourceContribution(
                source=LeverageSource.DERIVATIVE,
                gross_exposure=Decimal("1000"),
                treatment=ExposureTreatment.UNSUPPORTED,
                exclusion_reason="Should not have reason",
            )

    def test_zero_exposure_valid(self):
        """Zero exposure is valid."""
        src = LeverageExposureSourceContribution(
            source=LeverageSource.CASH_AND_CASH_EQUIVALENT,
            gross_exposure=Decimal("0"),
            treatment=ExposureTreatment.INCLUDED,
        )
        assert src.gross_exposure == Decimal("0")


# LeveragePositionContribution tests


class TestLeveragePositionContribution:
    """Test LeveragePositionContribution model."""

    def test_valid_included_position(self):
        """Valid included position contribution."""
        pos = LeveragePositionContribution(
            position_id=1,
            isin="US0378331005",
            position_name="Apple Inc.",
            asset_class="Equity",
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            treatment=ExposureTreatment.INCLUDED,
            market_value_base_ccy=Decimal("1000000"),
            raw_exposure=Decimal("1000000"),
            gross_exposure=Decimal("1000000"),
            commitment_exposure=Decimal("1000000"),
        )
        assert pos.position_id == 1
        assert pos.asset_class == "Equity"
        assert pos.treatment == ExposureTreatment.INCLUDED
        assert pos.exclusion_reason is None

    def test_valid_excluded_position(self):
        """Valid excluded position contribution."""
        pos = LeveragePositionContribution(
            position_id=2,
            asset_class="Cash",
            source=LeverageSource.CASH_AND_CASH_EQUIVALENT,
            treatment=ExposureTreatment.EXCLUDED,
            market_value_base_ccy=Decimal("500000"),
            raw_exposure=Decimal("0"),
            exclusion_reason="Qualifying cash exclusion",
        )
        assert pos.treatment == ExposureTreatment.EXCLUDED
        assert pos.exclusion_reason == "Qualifying cash exclusion"

    def test_valid_minimal_position(self):
        """Valid minimal position (required fields only)."""
        pos = LeveragePositionContribution(
            position_id=3,
            asset_class="Bond",
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            treatment=ExposureTreatment.INCLUDED,
            market_value_base_ccy=Decimal("500000"),
            raw_exposure=Decimal("500000"),
        )
        assert pos.position_id == 3
        assert pos.isin is None
        assert pos.position_name is None
        assert pos.gross_exposure is None
        assert pos.commitment_exposure is None

    def test_rejects_empty_asset_class(self):
        """Asset class cannot be empty."""
        with pytest.raises(ValueError, match="asset_class must be non-empty"):
            LeveragePositionContribution(
                position_id=1,
                asset_class="",
                source=LeverageSource.PHYSICAL_INSTRUMENT,
                treatment=ExposureTreatment.INCLUDED,
                market_value_base_ccy=Decimal("1000"),
                raw_exposure=Decimal("1000"),
            )

    def test_rejects_negative_raw_exposure(self):
        """Raw exposure cannot be negative."""
        with pytest.raises(ValueError, match="raw_exposure must be non-negative"):
            LeveragePositionContribution(
                position_id=1,
                asset_class="Equity",
                source=LeverageSource.PHYSICAL_INSTRUMENT,
                treatment=ExposureTreatment.INCLUDED,
                market_value_base_ccy=Decimal("1000"),
                raw_exposure=Decimal("-100"),
            )

    def test_rejects_negative_gross_exposure(self):
        """Gross exposure cannot be negative."""
        with pytest.raises(ValueError, match="gross_exposure must be non-negative"):
            LeveragePositionContribution(
                position_id=1,
                asset_class="Equity",
                source=LeverageSource.PHYSICAL_INSTRUMENT,
                treatment=ExposureTreatment.INCLUDED,
                market_value_base_ccy=Decimal("1000"),
                raw_exposure=Decimal("1000"),
                gross_exposure=Decimal("-100"),
            )

    def test_rejects_negative_commitment_exposure(self):
        """Commitment exposure cannot be negative."""
        with pytest.raises(ValueError, match="commitment_exposure must be non-negative"):
            LeveragePositionContribution(
                position_id=1,
                asset_class="Equity",
                source=LeverageSource.PHYSICAL_INSTRUMENT,
                treatment=ExposureTreatment.INCLUDED,
                market_value_base_ccy=Decimal("1000"),
                raw_exposure=Decimal("1000"),
                commitment_exposure=Decimal("-50"),
            )

    def test_excluded_requires_reason(self):
        """Excluded position must have reason."""
        with pytest.raises(ValueError, match="exclusion_reason must be non-empty"):
            LeveragePositionContribution(
                position_id=1,
                asset_class="Cash",
                source=LeverageSource.CASH_AND_CASH_EQUIVALENT,
                treatment=ExposureTreatment.EXCLUDED,
                market_value_base_ccy=Decimal("1000"),
                raw_exposure=Decimal("0"),
            )

    def test_included_rejects_reason(self):
        """Included position cannot have reason."""
        with pytest.raises(ValueError, match="exclusion_reason must be None"):
            LeveragePositionContribution(
                position_id=1,
                asset_class="Equity",
                source=LeverageSource.PHYSICAL_INSTRUMENT,
                treatment=ExposureTreatment.INCLUDED,
                market_value_base_ccy=Decimal("1000"),
                raw_exposure=Decimal("1000"),
                exclusion_reason="Should not have reason",
            )


# LeverageInput tests


class TestLeverageInput:
    """Test LeverageInput model."""

    @pytest.fixture
    def sample_portfolio(self):
        """Minimal valid portfolio for testing."""
        return RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("10000000"),
            positions=[],
        )

    def test_valid_single_method(self, sample_portfolio):
        """Valid input with single method."""
        inp = LeverageInput(
            portfolio=sample_portfolio,
            methods=[LeverageMethod.AIFMD_GROSS],
        )
        assert inp.portfolio.fund_id == 1
        assert inp.methods == [LeverageMethod.AIFMD_GROSS]

    def test_valid_multiple_methods(self, sample_portfolio):
        """Valid input with multiple methods."""
        inp = LeverageInput(
            portfolio=sample_portfolio,
            methods=[LeverageMethod.AIFMD_GROSS, LeverageMethod.AIFMD_COMMITMENT],
        )
        assert len(inp.methods) == 2

    def test_rejects_empty_methods_list(self, sample_portfolio):
        """Methods list cannot be empty."""
        with pytest.raises(ValueError, match="methods list must be non-empty"):
            LeverageInput(
                portfolio=sample_portfolio,
                methods=[],
            )

    def test_rejects_duplicate_methods(self, sample_portfolio):
        """Methods list cannot contain duplicates."""
        with pytest.raises(ValueError, match="methods list must not contain duplicates"):
            LeverageInput(
                portfolio=sample_portfolio,
                methods=[LeverageMethod.AIFMD_GROSS, LeverageMethod.AIFMD_GROSS],
            )


# LeverageMethodResult tests


class TestLeverageMethodResult:
    """Test LeverageMethodResult model."""

    def test_valid_result_aifmd_gross(self):
        """Valid AIFMD gross leverage result."""
        result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_GROSS,
            nav=Decimal("10000000"),
            total_exposure=Decimal("15000000"),
            leverage_ratio=Decimal("1.5"),
            position_contributions=[],
            source_contributions=[],
            unsupported_exposures=[],
            warnings=[],
        )
        assert result.method == LeverageMethod.AIFMD_GROSS
        assert result.nav == Decimal("10000000")
        assert result.leverage_ratio == Decimal("1.5")

    def test_valid_result_with_contributions(self):
        """Valid result with contributions and warnings."""
        src = LeverageExposureSourceContribution(
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            gross_exposure=Decimal("15000000"),
            treatment=ExposureTreatment.INCLUDED,
        )
        pos = LeveragePositionContribution(
            position_id=1,
            asset_class="Equity",
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            treatment=ExposureTreatment.INCLUDED,
            market_value_base_ccy=Decimal("15000000"),
            raw_exposure=Decimal("15000000"),
        )
        result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_COMMITMENT,
            nav=Decimal("10000000"),
            total_exposure=Decimal("15000000"),
            leverage_ratio=Decimal("1.5"),
            position_contributions=[pos],
            source_contributions=[src],
            unsupported_exposures=[],
            warnings=["Beta market data stale by 3 days"],
        )
        assert len(result.position_contributions) == 1
        assert len(result.warnings) == 1

    def test_rejects_non_positive_nav(self):
        """NAV must be positive."""
        with pytest.raises(ValueError, match="nav must be positive"):
            LeverageMethodResult(
                method=LeverageMethod.AIFMD_GROSS,
                nav=Decimal("0"),
                total_exposure=Decimal("100"),
                leverage_ratio=Decimal("1"),
                position_contributions=[],
                source_contributions=[],
                unsupported_exposures=[],
                warnings=[],
            )

    def test_rejects_negative_nav(self):
        """NAV cannot be negative."""
        with pytest.raises(ValueError, match="nav must be positive"):
            LeverageMethodResult(
                method=LeverageMethod.AIFMD_GROSS,
                nav=Decimal("-1000"),
                total_exposure=Decimal("100"),
                leverage_ratio=Decimal("1"),
                position_contributions=[],
                source_contributions=[],
                unsupported_exposures=[],
                warnings=[],
            )

    def test_rejects_negative_total_exposure(self):
        """Total exposure cannot be negative."""
        with pytest.raises(ValueError, match="total_exposure must be non-negative"):
            LeverageMethodResult(
                method=LeverageMethod.AIFMD_GROSS,
                nav=Decimal("1000"),
                total_exposure=Decimal("-100"),
                leverage_ratio=Decimal("1"),
                position_contributions=[],
                source_contributions=[],
                unsupported_exposures=[],
                warnings=[],
            )

    def test_rejects_negative_leverage_ratio(self):
        """Leverage ratio cannot be negative."""
        with pytest.raises(ValueError, match="leverage_ratio must be non-negative"):
            LeverageMethodResult(
                method=LeverageMethod.AIFMD_GROSS,
                nav=Decimal("1000"),
                total_exposure=Decimal("100"),
                leverage_ratio=Decimal("-0.5"),
                position_contributions=[],
                source_contributions=[],
                unsupported_exposures=[],
                warnings=[],
            )

    def test_zero_leverage_valid(self):
        """Zero leverage is valid."""
        result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_GROSS,
            nav=Decimal("1000"),
            total_exposure=Decimal("0"),
            leverage_ratio=Decimal("0"),
            position_contributions=[],
            source_contributions=[],
            unsupported_exposures=[],
            warnings=[],
        )
        assert result.leverage_ratio == Decimal("0")


# LeverageResult tests


class TestLeverageResult:
    """Test LeverageResult model."""

    def test_valid_single_method_result(self):
        """Valid result with single method."""
        method_result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_GROSS,
            nav=Decimal("10000000"),
            total_exposure=Decimal("15000000"),
            leverage_ratio=Decimal("1.5"),
            position_contributions=[],
            source_contributions=[],
            unsupported_exposures=[],
            warnings=[],
        )
        result = LeverageResult(
            fund_id=1,
            valuation_date=date(2026, 6, 10),
            method_results=[method_result],
        )
        assert result.fund_id == 1
        assert result.valuation_date == date(2026, 6, 10)
        assert len(result.method_results) == 1

    def test_valid_multiple_method_results(self):
        """Valid result with multiple methods."""
        gross_result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_GROSS,
            nav=Decimal("10000000"),
            total_exposure=Decimal("15000000"),
            leverage_ratio=Decimal("1.5"),
            position_contributions=[],
            source_contributions=[],
            unsupported_exposures=[],
            warnings=[],
        )
        commitment_result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_COMMITMENT,
            nav=Decimal("10000000"),
            total_exposure=Decimal("12000000"),
            leverage_ratio=Decimal("1.2"),
            position_contributions=[],
            source_contributions=[],
            unsupported_exposures=[],
            warnings=[],
        )
        result = LeverageResult(
            fund_id=1,
            valuation_date=date(2026, 6, 10),
            method_results=[gross_result, commitment_result],
        )
        assert len(result.method_results) == 2

    def test_rejects_empty_method_results(self):
        """Method results list cannot be empty."""
        with pytest.raises(ValueError, match="method_results list must be non-empty"):
            LeverageResult(
                fund_id=1,
                valuation_date=date(2026, 6, 10),
                method_results=[],
            )

    def test_rejects_duplicate_methods(self):
        """Method results cannot have duplicate methods."""
        method_result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_GROSS,
            nav=Decimal("10000000"),
            total_exposure=Decimal("15000000"),
            leverage_ratio=Decimal("1.5"),
            position_contributions=[],
            source_contributions=[],
            unsupported_exposures=[],
            warnings=[],
        )
        with pytest.raises(ValueError, match="method_results must not contain duplicate methods"):
            LeverageResult(
                fund_id=1,
                valuation_date=date(2026, 6, 10),
                method_results=[method_result, method_result],
            )


# Integration tests


class TestLeverageModelIntegration:
    """Integration tests with realistic scenarios."""

    def test_direct_borrowing_placeholder(self):
        """Valid source contribution for direct borrowing (Phase 1 placeholder)."""
        src = LeverageExposureSourceContribution(
            source=LeverageSource.DIRECT_BORROWING,
            gross_exposure=Decimal("2000000"),
            treatment=ExposureTreatment.PENDING_METHOD_RULE,
        )
        assert src.source == LeverageSource.DIRECT_BORROWING
        assert src.treatment == ExposureTreatment.PENDING_METHOD_RULE

    def test_derivative_placeholder(self):
        """Valid source contribution for derivative (Phase 1 placeholder)."""
        src = LeverageExposureSourceContribution(
            source=LeverageSource.DERIVATIVE,
            gross_exposure=Decimal("500000"),
            treatment=ExposureTreatment.UNSUPPORTED,
        )
        assert src.source == LeverageSource.DERIVATIVE
        assert src.treatment == ExposureTreatment.UNSUPPORTED

    def test_unsupported_embedded_derivative_tracking(self):
        """Valid unsupported embedded derivative exposure."""
        unsupported = UnsupportedLeverageExposure(
            position_id=42,
            isin="FR0000000001",
            asset_class="Structured Note",
            source=LeverageSource.EMBEDDED_DERIVATIVE,
            reason="Embedded derivative conversion not yet implemented",
        )
        assert unsupported.source == LeverageSource.EMBEDDED_DERIVATIVE
        assert "not yet implemented" in unsupported.reason

    def test_realistic_aifmd_gross_result(self):
        """Realistic AIFMD gross leverage result."""
        equity_src = LeverageExposureSourceContribution(
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            gross_exposure=Decimal("8000000"),
            commitment_exposure=Decimal("8000000"),
            treatment=ExposureTreatment.INCLUDED,
        )
        cash_src = LeverageExposureSourceContribution(
            source=LeverageSource.CASH_AND_CASH_EQUIVALENT,
            gross_exposure=Decimal("0"),
            treatment=ExposureTreatment.EXCLUDED,
            exclusion_reason="Qualifying cash under AIFMD Article 7",
        )
        result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_GROSS,
            nav=Decimal("10000000"),
            total_exposure=Decimal("8000000"),
            leverage_ratio=Decimal("0.8"),
            position_contributions=[],
            source_contributions=[equity_src, cash_src],
            unsupported_exposures=[],
            warnings=[],
        )
        assert result.leverage_ratio == Decimal("0.8")
        assert len(result.source_contributions) == 2

    def test_realistic_aifmd_commitment_result(self):
        """Realistic AIFMD commitment leverage result."""
        physical_src = LeverageExposureSourceContribution(
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            gross_exposure=Decimal("8000000"),
            commitment_exposure=Decimal("8000000"),
            treatment=ExposureTreatment.INCLUDED,
        )
        result = LeverageMethodResult(
            method=LeverageMethod.AIFMD_COMMITMENT,
            nav=Decimal("10000000"),
            total_exposure=Decimal("8000000"),
            leverage_ratio=Decimal("0.8"),
            position_contributions=[],
            source_contributions=[physical_src],
            unsupported_exposures=[],
            warnings=["Phase 1: derivative conversion not yet available"],
        )
        assert result.method == LeverageMethod.AIFMD_COMMITMENT
        assert len(result.warnings) == 1
