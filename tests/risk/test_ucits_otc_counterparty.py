"""Tests for UCITS OTC counterparty exposure monitoring.

Validates counterparty limit compliance status calculation.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.ucits import (
    UCITSCounterpartyCategory,
    UCITSOTCCounterpartyEngine,
    UCITSOTCCounterpartyInput,
    UCITSOTCCounterpartyStatus,
)


@pytest.fixture
def engine():
    """Create engine instance."""
    return UCITSOTCCounterpartyEngine()


# ============================================================================
# Standard Counterparty Tests (5% Limit)
# ============================================================================


def test_standard_counterparty_well_below_limit(engine):
    """Standard counterparty well below 5% limit should be WITHIN_LIMIT."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY001",
        counterparty_name="Bank A",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("200000"),  # 2% of 10M
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSOTCCounterpartyStatus.WITHIN_LIMIT
    assert result.exposure_ratio == Decimal("0.02")
    assert result.limit_ratio == Decimal("0.05")
    assert result.excess_amount == Decimal("0")
    assert result.excess_ratio == Decimal("0")


def test_standard_counterparty_exactly_at_5_percent(engine):
    """Standard counterparty exactly at 5% limit should be WITHIN_LIMIT."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY001",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("500000"),  # exactly 5% of 10M
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSOTCCounterpartyStatus.WITHIN_LIMIT
    assert result.exposure_ratio == Decimal("0.05")
    assert result.limit_ratio == Decimal("0.05")
    assert result.excess_amount == Decimal("0")


def test_standard_counterparty_just_above_5_percent(engine):
    """Standard counterparty just above 5% limit should be BREACH."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY001",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("500001"),  # 5.0001% of 10M
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSOTCCounterpartyStatus.BREACH
    assert result.excess_amount > Decimal("0")
    assert result.excess_ratio > Decimal("0")


# ============================================================================
# Eligible Credit Institution Tests (10% Limit)
# ============================================================================


def test_credit_institution_well_below_limit(engine):
    """Eligible credit institution well below 10% limit should be WITHIN_LIMIT."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY002",
        counterparty_name="Central Bank",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("600000"),  # 6% of 10M (within 10% limit)
        counterparty_category=UCITSCounterpartyCategory.ELIGIBLE_CREDIT_INSTITUTION,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSOTCCounterpartyStatus.WITHIN_LIMIT
    assert result.exposure_ratio == Decimal("0.06")
    assert result.limit_ratio == Decimal("0.10")
    assert result.excess_amount == Decimal("0")


def test_credit_institution_exactly_at_10_percent(engine):
    """Eligible credit institution exactly at 10% limit should be WITHIN_LIMIT."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY002",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("1000000"),  # exactly 10% of 10M
        counterparty_category=UCITSCounterpartyCategory.ELIGIBLE_CREDIT_INSTITUTION,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSOTCCounterpartyStatus.WITHIN_LIMIT
    assert result.exposure_ratio == Decimal("0.10")
    assert result.limit_ratio == Decimal("0.10")
    assert result.excess_amount == Decimal("0")


def test_credit_institution_just_above_10_percent(engine):
    """Eligible credit institution just above 10% limit should be BREACH."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY002",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("1000001"),  # 10.0001% of 10M
        counterparty_category=UCITSCounterpartyCategory.ELIGIBLE_CREDIT_INSTITUTION,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSOTCCounterpartyStatus.BREACH
    assert result.excess_amount > Decimal("0")
    assert result.excess_ratio > Decimal("0")


# ============================================================================
# Edge Cases
# ============================================================================


def test_zero_exposure_is_within_limit(engine):
    """Zero exposure should be WITHIN_LIMIT."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY001",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("0"),
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSOTCCounterpartyStatus.WITHIN_LIMIT
    assert result.exposure_ratio == Decimal("0")


def test_high_exposure_standard_counterparty(engine):
    """High exposure to standard counterparty should be BREACH."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY001",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("2000000"),  # 20% of 10M
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSOTCCounterpartyStatus.BREACH
    assert result.excess_amount == Decimal("1500000")


# ============================================================================
# Input Validation: Rejections
# ============================================================================


def test_negative_exposure_rejected():
    """Negative exposure should be rejected."""
    with pytest.raises(ValueError, match="exposure_amount must be non-negative"):
        UCITSOTCCounterpartyInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            counterparty_id="CPTY001",
            nav=Decimal("10000000"),
            exposure_amount=Decimal("-100000"),
            counterparty_category=UCITSCounterpartyCategory.STANDARD,
        )


def test_zero_nav_rejected():
    """Zero NAV should be rejected."""
    with pytest.raises(ValueError, match="nav must be positive"):
        UCITSOTCCounterpartyInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            counterparty_id="CPTY001",
            nav=Decimal("0"),
            exposure_amount=Decimal("500000"),
            counterparty_category=UCITSCounterpartyCategory.STANDARD,
        )


def test_negative_nav_rejected():
    """Negative NAV should be rejected."""
    with pytest.raises(ValueError, match="nav must be positive"):
        UCITSOTCCounterpartyInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            counterparty_id="CPTY001",
            nav=Decimal("-10000000"),
            exposure_amount=Decimal("500000"),
            counterparty_category=UCITSCounterpartyCategory.STANDARD,
        )


def test_empty_fund_id_rejected():
    """Empty fund_id should be rejected."""
    with pytest.raises(ValueError, match="fund_id must be non-empty"):
        UCITSOTCCounterpartyInput(
            fund_id="",
            valuation_date=date(2026, 6, 11),
            counterparty_id="CPTY001",
            nav=Decimal("10000000"),
            exposure_amount=Decimal("500000"),
            counterparty_category=UCITSCounterpartyCategory.STANDARD,
        )


def test_empty_counterparty_id_rejected():
    """Empty counterparty_id should be rejected."""
    with pytest.raises(ValueError, match="counterparty_id must be non-empty"):
        UCITSOTCCounterpartyInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            counterparty_id="",
            nav=Decimal("10000000"),
            exposure_amount=Decimal("500000"),
            counterparty_category=UCITSCounterpartyCategory.STANDARD,
        )


# ============================================================================
# Immutability
# ============================================================================


def test_input_model_is_immutable():
    """Input model should be frozen."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY001",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("500000"),
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    with pytest.raises(Exception):
        observation.exposure_amount = Decimal("1000000")


def test_result_model_is_immutable(engine):
    """Result model should be frozen."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY001",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("500000"),
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    result = engine.calculate(observation)
    with pytest.raises(Exception):
        result.status = UCITSOTCCounterpartyStatus.BREACH


# ============================================================================
# Precision and Decimal Handling
# ============================================================================


def test_decimal_precision_preserved(engine):
    """Decimal precision should be preserved."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY001",
        nav=Decimal("9999999.99"),
        exposure_amount=Decimal("1234567.89"),
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    result = engine.calculate(observation)

    expected_ratio = Decimal("1234567.89") / Decimal("9999999.99")
    assert result.exposure_ratio == expected_ratio


# ============================================================================
# Audit Field Preservation
# ============================================================================


def test_audit_fields_preserved(engine):
    """Audit fields should be preserved unchanged."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Equity",
        valuation_date=date(2026, 6, 15),
        counterparty_id="INTERBK",
        counterparty_name="Interbank Ltd",
        nav=Decimal("25000000"),
        exposure_amount=Decimal("1250000"),  # 5%
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    result = engine.calculate(observation)

    assert result.fund_id == "UCITS_Equity"
    assert result.counterparty_id == "INTERBK"
    assert result.counterparty_name == "Interbank Ltd"
    assert result.valuation_date == date(2026, 6, 15)
    assert result.nav == Decimal("25000000")
    assert result.counterparty_category == UCITSCounterpartyCategory.STANDARD


def test_counterparty_name_optional(engine):
    """Counterparty name should be optional."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY001",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("500000"),
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    result = engine.calculate(observation)

    assert result.counterparty_name is None


# ============================================================================
# Engine Statelessness
# ============================================================================


def test_engine_is_stateless(engine):
    """Engine should produce consistent results regardless of call order."""
    obs1 = UCITSOTCCounterpartyInput(
        fund_id="Fund_A",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY001",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("200000"),  # 2%
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    obs2 = UCITSOTCCounterpartyInput(
        fund_id="Fund_B",
        valuation_date=date(2026, 6, 12),
        counterparty_id="CPTY002",
        nav=Decimal("20000000"),
        exposure_amount=Decimal("2500000"),  # 12.5% (exceeds 10%)
        counterparty_category=UCITSCounterpartyCategory.ELIGIBLE_CREDIT_INSTITUTION,
    )

    # Call with obs1, then obs2
    result1a = engine.calculate(obs1)
    result2a = engine.calculate(obs2)

    # Call with obs2, then obs1
    result2b = engine.calculate(obs2)
    result1b = engine.calculate(obs1)

    # Results should match
    assert result1a.status == result1b.status
    assert result2a.status == result2b.status


# ============================================================================
# Result Internal Consistency
# ============================================================================


def test_result_consistency_standard(engine):
    """Result fields should be internally consistent for standard counterparty."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY001",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("600000"),  # 6% (above standard 5% limit)
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    result = engine.calculate(observation)

    # limit_amount should equal nav * limit_ratio
    assert result.limit_amount == result.nav * result.limit_ratio

    # exposure_ratio should equal exposure_amount / nav
    assert result.exposure_ratio == result.exposure_amount / result.nav

    # status should match excess fields
    assert result.status == UCITSOTCCounterpartyStatus.BREACH
    assert result.excess_amount > Decimal("0")
    assert result.excess_ratio > Decimal("0")


def test_result_consistency_credit_institution(engine):
    """Result fields should be internally consistent for eligible credit institution."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY002",
        nav=Decimal("10000000"),
        exposure_amount=Decimal("1100000"),  # 11% (above 10% limit)
        counterparty_category=UCITSCounterpartyCategory.ELIGIBLE_CREDIT_INSTITUTION,
    )
    result = engine.calculate(observation)

    assert result.limit_ratio == Decimal("0.10")
    assert result.status == UCITSOTCCounterpartyStatus.BREACH
    assert result.excess_ratio == Decimal("0.01")


# ============================================================================
# Realistic Scenarios
# ============================================================================


def test_realistic_standard_bank_within_limit(engine):
    """Test realistic standard counterparty bank within limit."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Derivatives",
        valuation_date=date(2026, 6, 11),
        counterparty_id="JP0000123456",  # JPMorgan LEI
        counterparty_name="JPMorgan Chase",
        nav=Decimal("100000000"),
        exposure_amount=Decimal("3000000"),  # EUR 3M = 3%
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSOTCCounterpartyStatus.WITHIN_LIMIT
    assert result.limit_ratio == Decimal("0.05")


def test_realistic_central_bank_within_limit(engine):
    """Test realistic eligible credit institution (central bank) within limit."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_FX",
        valuation_date=date(2026, 6, 11),
        counterparty_id="ECB0000001",
        counterparty_name="European Central Bank",
        nav=Decimal("50000000"),
        exposure_amount=Decimal("4000000"),  # EUR 4M = 8%
        counterparty_category=UCITSCounterpartyCategory.ELIGIBLE_CREDIT_INSTITUTION,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSOTCCounterpartyStatus.WITHIN_LIMIT
    assert result.limit_ratio == Decimal("0.10")
    assert result.exposure_ratio == Decimal("0.08")


def test_realistic_counterparty_in_breach(engine):
    """Test realistic counterparty exposure in breach."""
    observation = UCITSOTCCounterpartyInput(
        fund_id="UCITS_Leveraged",
        valuation_date=date(2026, 6, 11),
        counterparty_id="CPTY_OVER",
        counterparty_name="Over-leveraged Dealer",
        nav=Decimal("20000000"),
        exposure_amount=Decimal("1500000"),  # EUR 1.5M = 7.5% (exceeds 5%)
        counterparty_category=UCITSCounterpartyCategory.STANDARD,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSOTCCounterpartyStatus.BREACH
    assert result.excess_amount == Decimal("500000")  # 1.5M - 1.0M
    assert result.excess_ratio == Decimal("0.025")  # 2.5 percentage points
