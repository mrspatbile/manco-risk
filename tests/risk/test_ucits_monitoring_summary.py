"""Tests for UCITS monitoring summary orchestration.

Validates that the summary service correctly assembles monitoring results
and determines overall compliance status.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.ucits import (
    SRRIEngine,
    SRRIInput,
    UCITSAbsoluteVaREngine,
    UCITSAbsoluteVaRInput,
    UCITSBorrowingEngine,
    UCITSBorrowingInput,
    UCITSConcentrationEngine,
    UCITSConcentrationInput,
    UCITSCounterpartyCategory,
    UCITSMonitoringSummaryService,
    UCITSOTCCounterpartyEngine,
    UCITSOTCCounterpartyInput,
    UCITSRelativeVaREngine,
    UCITSRelativeVaRInput,
)


@pytest.fixture
def compliant_results():
    """Generate all-compliant monitoring results."""
    abs_var_engine = UCITSAbsoluteVaREngine()
    rel_var_engine = UCITSRelativeVaREngine()
    srri_engine = SRRIEngine()
    borrowing_engine = UCITSBorrowingEngine()
    concentration_engine = UCITSConcentrationEngine()
    otc_engine = UCITSOTCCounterpartyEngine()

    abs_var_result = abs_var_engine.calculate(
        UCITSAbsoluteVaRInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("1500000"),  # 15% (within 20%)
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )
    )

    rel_var_result = rel_var_engine.calculate(
        UCITSRelativeVaRInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            fund_var=Decimal("1500000"),
            reference_portfolio_var=Decimal("1000000"),  # 150% (within 200%)
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )
    )

    srri_result = srri_engine.calculate(
        SRRIInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            annualised_volatility=Decimal("0.12"),  # 12% = SRRI 5
        )
    )

    borrowing_result = borrowing_engine.calculate(
        UCITSBorrowingInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            direct_borrowing_amount=Decimal("800000"),  # 8% (within 10%)
        )
    )

    concentration_result = concentration_engine.calculate(
        UCITSConcentrationInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            issuer_id="ISSUER001",
            issuer_exposure_amount=Decimal("900000"),  # 9% (within 10%)
        )
    )

    otc_result = otc_engine.calculate(
        UCITSOTCCounterpartyInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            counterparty_id="CPTY001",
            nav=Decimal("10000000"),
            exposure_amount=Decimal("400000"),  # 4% (within 5%)
            counterparty_category=UCITSCounterpartyCategory.STANDARD,
        )
    )

    return {
        "abs_var": abs_var_result,
        "rel_var": rel_var_result,
        "srri": srri_result,
        "borrowing": borrowing_result,
        "concentration": concentration_result,
        "otc": otc_result,
    }


@pytest.fixture
def one_breach_results():
    """Generate results with one breach (absolute VaR)."""
    abs_var_engine = UCITSAbsoluteVaREngine()
    rel_var_engine = UCITSRelativeVaREngine()
    srri_engine = SRRIEngine()
    borrowing_engine = UCITSBorrowingEngine()
    concentration_engine = UCITSConcentrationEngine()
    otc_engine = UCITSOTCCounterpartyEngine()

    abs_var_result = abs_var_engine.calculate(
        UCITSAbsoluteVaRInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("2500000"),  # 25% (exceeds 20% limit)
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )
    )

    rel_var_result = rel_var_engine.calculate(
        UCITSRelativeVaRInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            fund_var=Decimal("1500000"),
            reference_portfolio_var=Decimal("1000000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )
    )

    srri_result = srri_engine.calculate(
        SRRIInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            annualised_volatility=Decimal("0.12"),
        )
    )

    borrowing_result = borrowing_engine.calculate(
        UCITSBorrowingInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            direct_borrowing_amount=Decimal("800000"),
        )
    )

    concentration_result = concentration_engine.calculate(
        UCITSConcentrationInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            issuer_id="ISSUER001",
            issuer_exposure_amount=Decimal("900000"),
        )
    )

    otc_result = otc_engine.calculate(
        UCITSOTCCounterpartyInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            counterparty_id="CPTY001",
            nav=Decimal("10000000"),
            exposure_amount=Decimal("400000"),
            counterparty_category=UCITSCounterpartyCategory.STANDARD,
        )
    )

    return {
        "abs_var": abs_var_result,
        "rel_var": rel_var_result,
        "srri": srri_result,
        "borrowing": borrowing_result,
        "concentration": concentration_result,
        "otc": otc_result,
    }


@pytest.fixture
def multiple_breach_results():
    """Generate results with multiple breaches."""
    abs_var_engine = UCITSAbsoluteVaREngine()
    rel_var_engine = UCITSRelativeVaREngine()
    srri_engine = SRRIEngine()
    borrowing_engine = UCITSBorrowingEngine()
    concentration_engine = UCITSConcentrationEngine()
    otc_engine = UCITSOTCCounterpartyEngine()

    # Absolute VaR: breach (25% > 20%)
    abs_var_result = abs_var_engine.calculate(
        UCITSAbsoluteVaRInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("2500000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )
    )

    # Relative VaR: breach (250% > 200%)
    rel_var_result = rel_var_engine.calculate(
        UCITSRelativeVaRInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            fund_var=Decimal("2500000"),
            reference_portfolio_var=Decimal("1000000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )
    )

    srri_result = srri_engine.calculate(
        SRRIInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            annualised_volatility=Decimal("0.12"),
        )
    )

    # Borrowing: breach (15% > 10%)
    borrowing_result = borrowing_engine.calculate(
        UCITSBorrowingInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            direct_borrowing_amount=Decimal("1500000"),
        )
    )

    # Concentration: compliant (9% < 10%)
    concentration_result = concentration_engine.calculate(
        UCITSConcentrationInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            issuer_id="ISSUER001",
            issuer_exposure_amount=Decimal("900000"),
        )
    )

    # OTC: compliant (4% < 5%)
    otc_result = otc_engine.calculate(
        UCITSOTCCounterpartyInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            counterparty_id="CPTY001",
            nav=Decimal("10000000"),
            exposure_amount=Decimal("400000"),
            counterparty_category=UCITSCounterpartyCategory.STANDARD,
        )
    )

    return {
        "abs_var": abs_var_result,
        "rel_var": rel_var_result,
        "srri": srri_result,
        "borrowing": borrowing_result,
        "concentration": concentration_result,
        "otc": otc_result,
    }


# ============================================================================
# Compliance Status Tests
# ============================================================================


def test_all_compliant(compliant_results):
    """All monitoring checks compliant should result in WITHIN_LIMIT."""
    summary = UCITSMonitoringSummaryService.build(
        absolute_var_result=compliant_results["abs_var"],
        relative_var_result=compliant_results["rel_var"],
        srri_result=compliant_results["srri"],
        borrowing_result=compliant_results["borrowing"],
        concentration_result=compliant_results["concentration"],
        otc_counterparty_result=compliant_results["otc"],
    )

    assert summary.overall_compliance is True
    assert summary.breach_count == 0
    assert summary.breached_checks == []


def test_one_breach(one_breach_results):
    """One monitoring check in breach should result in BREACH."""
    summary = UCITSMonitoringSummaryService.build(
        absolute_var_result=one_breach_results["abs_var"],
        relative_var_result=one_breach_results["rel_var"],
        srri_result=one_breach_results["srri"],
        borrowing_result=one_breach_results["borrowing"],
        concentration_result=one_breach_results["concentration"],
        otc_counterparty_result=one_breach_results["otc"],
    )

    assert summary.overall_compliance is False
    assert summary.breach_count == 1
    assert "Absolute VaR" in summary.breached_checks


def test_multiple_breaches(multiple_breach_results):
    """Multiple monitoring checks in breach should be identified."""
    summary = UCITSMonitoringSummaryService.build(
        absolute_var_result=multiple_breach_results["abs_var"],
        relative_var_result=multiple_breach_results["rel_var"],
        srri_result=multiple_breach_results["srri"],
        borrowing_result=multiple_breach_results["borrowing"],
        concentration_result=multiple_breach_results["concentration"],
        otc_counterparty_result=multiple_breach_results["otc"],
    )

    assert summary.overall_compliance is False
    assert summary.breach_count == 3
    assert "Absolute VaR" in summary.breached_checks
    assert "Relative VaR" in summary.breached_checks
    assert "Direct Borrowing" in summary.breached_checks


# ============================================================================
# Breach Count and Names
# ============================================================================


def test_breach_count_consistency(compliant_results):
    """Breach count should match breached_checks length."""
    summary = UCITSMonitoringSummaryService.build(
        absolute_var_result=compliant_results["abs_var"],
        relative_var_result=compliant_results["rel_var"],
        srri_result=compliant_results["srri"],
        borrowing_result=compliant_results["borrowing"],
        concentration_result=compliant_results["concentration"],
        otc_counterparty_result=compliant_results["otc"],
    )

    assert summary.breach_count == len(summary.breached_checks)


def test_breached_checks_names(multiple_breach_results):
    """Breached checks should have correct names."""
    summary = UCITSMonitoringSummaryService.build(
        absolute_var_result=multiple_breach_results["abs_var"],
        relative_var_result=multiple_breach_results["rel_var"],
        srri_result=multiple_breach_results["srri"],
        borrowing_result=multiple_breach_results["borrowing"],
        concentration_result=multiple_breach_results["concentration"],
        otc_counterparty_result=multiple_breach_results["otc"],
    )

    # Should include exact names for breached checks
    assert len(summary.breached_checks) == 3
    expected_breaches = {"Absolute VaR", "Relative VaR", "Direct Borrowing"}
    assert set(summary.breached_checks) == expected_breaches


# ============================================================================
# Fund ID Consistency Validation
# ============================================================================


def test_fund_id_consistency_validation_passes(compliant_results):
    """Fund IDs must be consistent across all results."""
    summary = UCITSMonitoringSummaryService.build(
        absolute_var_result=compliant_results["abs_var"],
        relative_var_result=compliant_results["rel_var"],
        srri_result=compliant_results["srri"],
        borrowing_result=compliant_results["borrowing"],
        concentration_result=compliant_results["concentration"],
        otc_counterparty_result=compliant_results["otc"],
    )

    assert summary.fund_id == "UCITS_Test"


def test_fund_id_consistency_validation_fails():
    """Fund IDs must be consistent; mismatch should raise error."""
    abs_var_engine = UCITSAbsoluteVaREngine()
    rel_var_engine = UCITSRelativeVaREngine()
    srri_engine = SRRIEngine()
    borrowing_engine = UCITSBorrowingEngine()
    concentration_engine = UCITSConcentrationEngine()
    otc_engine = UCITSOTCCounterpartyEngine()

    # Create results with different fund IDs
    abs_var_result = abs_var_engine.calculate(
        UCITSAbsoluteVaRInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("1500000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )
    )

    rel_var_result = rel_var_engine.calculate(
        UCITSRelativeVaRInput(
            fund_id="UCITS_Different",  # Different fund ID
            valuation_date=date(2026, 6, 11),
            fund_var=Decimal("1500000"),
            reference_portfolio_var=Decimal("1000000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )
    )

    srri_result = srri_engine.calculate(
        SRRIInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            annualised_volatility=Decimal("0.12"),
        )
    )

    borrowing_result = borrowing_engine.calculate(
        UCITSBorrowingInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            direct_borrowing_amount=Decimal("800000"),
        )
    )

    concentration_result = concentration_engine.calculate(
        UCITSConcentrationInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            issuer_id="ISSUER001",
            issuer_exposure_amount=Decimal("900000"),
        )
    )

    otc_result = otc_engine.calculate(
        UCITSOTCCounterpartyInput(
            fund_id="UCITS_Test",
            valuation_date=date(2026, 6, 11),
            counterparty_id="CPTY001",
            nav=Decimal("10000000"),
            exposure_amount=Decimal("400000"),
            counterparty_category=UCITSCounterpartyCategory.STANDARD,
        )
    )

    with pytest.raises(ValueError, match="Fund IDs are not consistent"):
        UCITSMonitoringSummaryService.build(
            absolute_var_result=abs_var_result,
            relative_var_result=rel_var_result,
            srri_result=srri_result,
            borrowing_result=borrowing_result,
            concentration_result=concentration_result,
            otc_counterparty_result=otc_result,
        )


# ============================================================================
# Immutability
# ============================================================================


def test_summary_model_is_immutable(compliant_results):
    """Summary model should be frozen."""
    summary = UCITSMonitoringSummaryService.build(
        absolute_var_result=compliant_results["abs_var"],
        relative_var_result=compliant_results["rel_var"],
        srri_result=compliant_results["srri"],
        borrowing_result=compliant_results["borrowing"],
        concentration_result=compliant_results["concentration"],
        otc_counterparty_result=compliant_results["otc"],
    )

    with pytest.raises(Exception):
        summary.overall_compliance = False


# ============================================================================
# Statelessness
# ============================================================================


def test_service_is_stateless(compliant_results, one_breach_results):
    """Service should produce consistent results regardless of call order."""
    # Call with compliant results first
    summary1 = UCITSMonitoringSummaryService.build(
        absolute_var_result=compliant_results["abs_var"],
        relative_var_result=compliant_results["rel_var"],
        srri_result=compliant_results["srri"],
        borrowing_result=compliant_results["borrowing"],
        concentration_result=compliant_results["concentration"],
        otc_counterparty_result=compliant_results["otc"],
    )

    # Call with breach results
    summary2 = UCITSMonitoringSummaryService.build(
        absolute_var_result=one_breach_results["abs_var"],
        relative_var_result=one_breach_results["rel_var"],
        srri_result=one_breach_results["srri"],
        borrowing_result=one_breach_results["borrowing"],
        concentration_result=one_breach_results["concentration"],
        otc_counterparty_result=one_breach_results["otc"],
    )

    # Call with compliant results again
    summary1b = UCITSMonitoringSummaryService.build(
        absolute_var_result=compliant_results["abs_var"],
        relative_var_result=compliant_results["rel_var"],
        srri_result=compliant_results["srri"],
        borrowing_result=compliant_results["borrowing"],
        concentration_result=compliant_results["concentration"],
        otc_counterparty_result=compliant_results["otc"],
    )

    # Results should match
    assert summary1.overall_compliance == summary1b.overall_compliance
    assert summary1.breach_count == summary1b.breach_count
    assert summary2.overall_compliance is False


# ============================================================================
# Realistic Scenarios
# ============================================================================


def test_realistic_conservative_fund(compliant_results):
    """Test realistic conservative fund (all compliant)."""
    summary = UCITSMonitoringSummaryService.build(
        absolute_var_result=compliant_results["abs_var"],
        relative_var_result=compliant_results["rel_var"],
        srri_result=compliant_results["srri"],
        borrowing_result=compliant_results["borrowing"],
        concentration_result=compliant_results["concentration"],
        otc_counterparty_result=compliant_results["otc"],
    )

    assert summary.overall_compliance is True
    assert summary.fund_id == "UCITS_Test"
    assert summary.valuation_date == date(2026, 6, 11)


def test_realistic_leveraged_fund(multiple_breach_results):
    """Test realistic leveraged fund (multiple breaches)."""
    summary = UCITSMonitoringSummaryService.build(
        absolute_var_result=multiple_breach_results["abs_var"],
        relative_var_result=multiple_breach_results["rel_var"],
        srri_result=multiple_breach_results["srri"],
        borrowing_result=multiple_breach_results["borrowing"],
        concentration_result=multiple_breach_results["concentration"],
        otc_counterparty_result=multiple_breach_results["otc"],
    )

    assert summary.overall_compliance is False
    assert summary.breach_count >= 2
