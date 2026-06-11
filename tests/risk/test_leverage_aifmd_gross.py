"""Tests for AIFMD gross leverage aggregation engine.

Validates gross exposure aggregation from source results and leverage ratio calculation.
"""

from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.leverage import (
    AIFMDGrossLeverageEngine,
    AIFMDLeverageAggregationInput,
    ExposureTreatment,
    LeverageExposureSourceContribution,
    LeverageMethod,
    LeverageSource,
)
from manco_risk.risk.leverage.cash_result import CashExposureResult
from manco_risk.risk.leverage.derivative_result import DerivativeExposureResult
from manco_risk.risk.leverage.direct_borrowing_result import DirectBorrowingExposureResult
from manco_risk.risk.leverage.models import UnsupportedLeverageExposure
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
def physical_result():
    """Create a physical instrument exposure result."""
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
    """Create a cash exposure result (zero exposure, excluded)."""
    source_contribution = LeverageExposureSourceContribution(
        source=LeverageSource.CASH_AND_CASH_EQUIVALENT,
        gross_exposure=Decimal("0"),
        commitment_exposure=Decimal("0"),
        treatment=ExposureTreatment.EXCLUDED,
        exclusion_reason="base-currency cash is excluded from leverage",
    )
    return CashExposureResult(
        position_contributions=[],
        source_contribution=source_contribution,
        unsupported_exposures=[],
        warnings=[],
    )


@pytest.fixture
def borrowing_result():
    """Create a direct borrowing exposure result."""
    direct_borrowing = LeverageExposureSourceContribution(
        source=LeverageSource.DIRECT_BORROWING,
        gross_exposure=Decimal("2000000"),
        commitment_exposure=Decimal("2000000"),
        treatment=ExposureTreatment.INCLUDED,
    )
    reinvested = LeverageExposureSourceContribution(
        source=LeverageSource.REINVESTED_BORROWING,
        gross_exposure=Decimal("500000"),
        commitment_exposure=Decimal("500000"),
        treatment=ExposureTreatment.INCLUDED,
    )
    return DirectBorrowingExposureResult(
        borrowing_records=[],
        source_contributions=[direct_borrowing, reinvested],
        warnings=[],
    )


@pytest.fixture
def sft_result():
    """Create an SFT exposure result."""
    repo = LeverageExposureSourceContribution(
        source=LeverageSource.SFT_REPO,
        gross_exposure=Decimal("1000000"),
        commitment_exposure=Decimal("1000000"),
        treatment=ExposureTreatment.INCLUDED,
    )
    return SFTExposureResult(
        sft_records=[],
        source_contributions=[repo],
        warnings=[],
    )


@pytest.fixture
def derivative_result():
    """Create a derivative exposure result."""
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


class TestAIFMDGrossBasics:
    """Test basic gross engine functionality."""

    def test_engine_instantiation(self):
        """Engine can be instantiated."""
        engine = AIFMDGrossLeverageEngine()
        assert engine is not None

    def test_physical_only_gross_exposure(self, base_portfolio, physical_result):
        """Physical instruments only: gross exposure equals source exposure."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        assert result.method == LeverageMethod.AIFMD_GROSS
        assert result.total_exposure == Decimal("5000000")
        assert result.leverage_ratio == Decimal("5000000") / base_portfolio.nav
        assert len(result.source_contributions) == 1

    def test_cash_only_gross_exposure(self, base_portfolio, cash_result):
        """Cash only: gross exposure is zero (cash excluded)."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            cash_result=cash_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        assert result.total_exposure == Decimal("0")
        assert result.leverage_ratio == Decimal("0")

    def test_physical_and_cash_excludes_cash(self, base_portfolio, physical_result, cash_result):
        """Physical + cash: cash is excluded from gross."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result,
            cash_result=cash_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        # Only physical instrument exposure counted
        assert result.total_exposure == Decimal("5000000")

    def test_multiple_sources_aggregated(
        self, base_portfolio, physical_result, borrowing_result, sft_result
    ):
        """Multiple sources: exposures aggregated correctly."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result,
            direct_borrowing_result=borrowing_result,
            sft_result=sft_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        # Physical (5M) + direct borrowing (2M) + reinvested (0.5M) + SFT repo (1M)
        expected_exposure = Decimal("8500000")
        assert result.total_exposure == expected_exposure
        assert result.leverage_ratio == expected_exposure / base_portfolio.nav

    def test_all_sources_aggregated(
        self,
        base_portfolio,
        physical_result,
        cash_result,
        borrowing_result,
        sft_result,
        derivative_result,
    ):
        """All sources: exposures aggregated with cash excluded."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result,
            cash_result=cash_result,
            direct_borrowing_result=borrowing_result,
            sft_result=sft_result,
            derivative_result=derivative_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        # Physical (5M) + direct (2M) + reinvested (0.5M) + SFT (1M) + derivatives (1.5M)
        expected_exposure = Decimal("10000000")
        assert result.total_exposure == expected_exposure
        assert result.leverage_ratio == expected_exposure / base_portfolio.nav

    def test_excluded_source_contributes_zero(self, base_portfolio):
        """Excluded source contributions contribute zero to gross."""
        excluded_contribution = LeverageExposureSourceContribution(
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            gross_exposure=Decimal("1000000"),
            treatment=ExposureTreatment.EXCLUDED,
            exclusion_reason="hedge fund restriction",
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
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        assert result.total_exposure == Decimal("0")

    def test_pending_method_rule_included(self, base_portfolio, derivative_result):
        """PENDING_METHOD_RULE treatment is included in gross."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            derivative_result=derivative_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        assert result.total_exposure == Decimal("1500000")


class TestAIFMDGrossLeverageRatio:
    """Test leverage ratio calculation."""

    def test_leverage_ratio_calculation(self, physical_result):
        """Leverage ratio = total exposure / NAV."""
        nav = Decimal("10000000")
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date="2026-06-11",
            nav=nav,
            positions=[],
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=portfolio,
            physical_result=physical_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        expected_ratio = Decimal("5000000") / nav
        assert result.leverage_ratio == expected_ratio

    def test_leverage_ratio_zero_exposure(self, base_portfolio, cash_result):
        """Leverage ratio with zero exposure."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            cash_result=cash_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        assert result.leverage_ratio == Decimal("0")

    def test_leverage_ratio_high_leverage(self):
        """Leverage ratio > 1 (leverage > 100%)."""
        nav = Decimal("5000000")
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date="2026-06-11",
            nav=nav,
            positions=[],
        )

        source_contribution = LeverageExposureSourceContribution(
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            gross_exposure=Decimal("7500000"),
            treatment=ExposureTreatment.INCLUDED,
        )
        physical_result = PhysicalInstrumentExposureResult(
            position_contributions=[],
            source_contribution=source_contribution,
            unsupported_exposures=[],
            warnings=[],
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=portfolio,
            physical_result=physical_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        expected_ratio = Decimal("7500000") / nav
        assert result.leverage_ratio == expected_ratio
        assert result.leverage_ratio > Decimal("1")


class TestAIFMDGrossSourceContributions:
    """Test source contribution tracking."""

    def test_source_contributions_included(self, base_portfolio, physical_result, cash_result):
        """Source contributions are included in result."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result,
            cash_result=cash_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        # Both physical and cash contributions tracked
        assert len(result.source_contributions) == 2
        assert any(
            c.source == LeverageSource.PHYSICAL_INSTRUMENT for c in result.source_contributions
        )
        assert any(
            c.source == LeverageSource.CASH_AND_CASH_EQUIVALENT for c in result.source_contributions
        )

    def test_multiple_borrowing_sources(self, base_portfolio, borrowing_result):
        """Multiple borrowing sources (direct + reinvested) are included."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            direct_borrowing_result=borrowing_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        # Both direct borrowing and reinvested borrowing contributions
        assert len(result.source_contributions) == 2
        assert any(c.source == LeverageSource.DIRECT_BORROWING for c in result.source_contributions)
        assert any(
            c.source == LeverageSource.REINVESTED_BORROWING for c in result.source_contributions
        )


class TestAIFMDGrossUnsupportedAndWarnings:
    """Test unsupported exposure and warning propagation."""

    def test_unsupported_exposures_propagated(self, base_portfolio):
        """Unsupported exposures are propagated to result."""
        unsupported = UnsupportedLeverageExposure(
            asset_class="Structured Note",
            source=LeverageSource.PHYSICAL_INSTRUMENT,
            reason="Embedded derivative not yet supported",
        )
        physical_result = PhysicalInstrumentExposureResult(
            position_contributions=[],
            source_contribution=None,
            unsupported_exposures=[unsupported],
            warnings=[],
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        assert len(result.unsupported_exposures) == 1
        assert result.unsupported_exposures[0].asset_class == "Structured Note"

    def test_warnings_propagated(self, base_portfolio, physical_result):
        """Warnings from source results are propagated."""
        physical_result = PhysicalInstrumentExposureResult(
            position_contributions=[],
            source_contribution=physical_result.source_contribution,
            unsupported_exposures=[],
            warnings=["Position ABC123: missing market data"],
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        assert len(result.warnings) >= 1
        assert any("market data" in w for w in result.warnings)

    def test_multiple_warnings_aggregated(self, base_portfolio, physical_result, derivative_result):
        """Warnings from multiple sources are aggregated."""
        physical_result = PhysicalInstrumentExposureResult(
            position_contributions=[],
            source_contribution=physical_result.source_contribution,
            unsupported_exposures=[],
            warnings=["Physical warning 1"],
        )
        derivative_result = DerivativeExposureResult(
            derivative_records=[],
            source_contribution=derivative_result.source_contribution,
            unsupported_exposures=[],
            warnings=["Derivative warning 1"],
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result,
            derivative_result=derivative_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        assert len(result.warnings) == 2
        assert "Physical warning 1" in result.warnings
        assert "Derivative warning 1" in result.warnings


class TestAIFMDGrossEmptyInput:
    """Test edge cases with empty or None inputs."""

    def test_all_none_results(self, base_portfolio):
        """All source results are None."""
        input_data = AIFMDLeverageAggregationInput(portfolio=base_portfolio)
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        assert result.total_exposure == Decimal("0")
        assert result.leverage_ratio == Decimal("0")
        assert len(result.source_contributions) == 0

    def test_no_source_contribution_in_physical(self, base_portfolio):
        """Physical result exists but source_contribution is None."""
        physical_result = PhysicalInstrumentExposureResult(
            position_contributions=[],
            source_contribution=None,
            unsupported_exposures=[],
            warnings=[],
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        assert result.total_exposure == Decimal("0")

    def test_no_source_contributions_in_borrowing(self, base_portfolio):
        """Borrowing result exists but source_contributions is empty."""
        borrowing_result = DirectBorrowingExposureResult(
            borrowing_records=[],
            source_contributions=[],
            warnings=[],
        )

        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            direct_borrowing_result=borrowing_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        assert result.total_exposure == Decimal("0")


class TestAIFMDGrossPositionContributions:
    """Test position contribution handling."""

    def test_no_position_contributions_in_result(self, base_portfolio, physical_result):
        """Gross aggregation does not populate position_contributions."""
        input_data = AIFMDLeverageAggregationInput(
            portfolio=base_portfolio,
            physical_result=physical_result,
        )
        engine = AIFMDGrossLeverageEngine()
        result = engine.calculate(input_data)

        assert result.position_contributions == []
