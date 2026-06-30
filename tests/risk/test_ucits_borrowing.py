"""Tests for UCITS direct borrowing limit monitoring.

Validates borrowing limit compliance status calculation.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.ucits import UCITSBorrowingEngine, UCITSBorrowingInput, UCITSBorrowingStatus


@pytest.fixture
def engine():
    """Create engine instance."""
    return UCITSBorrowingEngine()


# ============================================================================
# Basic Compliance Tests
# ============================================================================


def test_borrowing_well_below_threshold_is_within_limit(engine):
    """Borrowing significantly below 10% threshold should be WITHIN_LIMIT."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("500000"),  # 5% of 10M
    )
    result = engine.calculate(observation)

    assert result.status == UCITSBorrowingStatus.WITHIN_LIMIT
    assert result.borrowing_ratio == Decimal("500000") / Decimal("10000000")
    assert result.excess_amount == Decimal("0")
    assert result.excess_ratio == Decimal("0")


def test_borrowing_just_below_threshold_is_within_limit(engine):
    """Borrowing just below 10% threshold should be WITHIN_LIMIT."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("999900"),  # 9.999% of 10M
    )
    result = engine.calculate(observation)

    assert result.status == UCITSBorrowingStatus.WITHIN_LIMIT
    assert result.borrowing_ratio == Decimal("999900") / Decimal("10000000")
    assert result.excess_amount == Decimal("0")
    assert result.excess_ratio == Decimal("0")


def test_borrowing_exactly_at_threshold_is_within_limit(engine):
    """Borrowing exactly at 10% threshold should be WITHIN_LIMIT."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("1000000"),  # exactly 10% of 10M
    )
    result = engine.calculate(observation)

    assert result.status == UCITSBorrowingStatus.WITHIN_LIMIT
    assert result.borrowing_ratio == Decimal("0.10")
    assert result.excess_amount == Decimal("0")
    assert result.excess_ratio == Decimal("0")


def test_borrowing_just_above_threshold_is_breach(engine):
    """Borrowing just above 10% threshold should be BREACH."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("1000001"),  # 10.0001% of 10M
    )
    result = engine.calculate(observation)

    assert result.status == UCITSBorrowingStatus.BREACH
    assert result.borrowing_ratio == Decimal("1000001") / Decimal("10000000")
    assert result.excess_amount > Decimal("0")
    assert result.excess_ratio > Decimal("0")


def test_borrowing_well_above_threshold_is_breach(engine):
    """Borrowing significantly above 10% threshold should be BREACH."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("1500000"),  # 15% of 10M
    )
    result = engine.calculate(observation)

    assert result.status == UCITSBorrowingStatus.BREACH
    assert result.borrowing_ratio == Decimal("0.15")
    assert result.excess_amount == Decimal("500000")
    assert result.excess_ratio == Decimal("0.05")


# ============================================================================
# Edge Cases: Borrowing Extremes
# ============================================================================


def test_zero_borrowing_is_within_limit(engine):
    """Zero borrowing (no direct borrowing) should be WITHIN_LIMIT."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("0"),
    )
    result = engine.calculate(observation)

    assert result.status == UCITSBorrowingStatus.WITHIN_LIMIT
    assert result.borrowing_ratio == Decimal("0")
    assert result.direct_borrowing_amount == Decimal("0")


def test_very_high_borrowing_is_breach(engine):
    """Very high borrowing should be BREACH."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Aggressive",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("5000000"),  # 50% of NAV
    )
    result = engine.calculate(observation)

    assert result.status == UCITSBorrowingStatus.BREACH
    assert result.borrowing_ratio == Decimal("0.5")


# ============================================================================
# Boundary Tests
# ============================================================================


def test_boundary_10_percent_lower(engine):
    """Borrowing just below 10% should be WITHIN_LIMIT."""
    observation = UCITSBorrowingInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("999999"),  # 9.99999% of 10M
    )
    result = engine.calculate(observation)
    assert result.status == UCITSBorrowingStatus.WITHIN_LIMIT


def test_boundary_10_percent_upper(engine):
    """Borrowing at exactly 10% should be WITHIN_LIMIT."""
    observation = UCITSBorrowingInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("1000000"),  # exactly 10% of 10M
    )
    result = engine.calculate(observation)
    assert result.status == UCITSBorrowingStatus.WITHIN_LIMIT


def test_boundary_10_percent_breach(engine):
    """Borrowing just above 10% should be BREACH."""
    observation = UCITSBorrowingInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("1000001"),  # 10.0001% of 10M
    )
    result = engine.calculate(observation)
    assert result.status == UCITSBorrowingStatus.BREACH


# ============================================================================
# Input Validation: Rejections
# ============================================================================


def test_negative_borrowing_rejected():
    """Negative borrowing should be rejected at input model."""
    with pytest.raises(ValueError, match="direct_borrowing_amount must be non-negative"):
        UCITSBorrowingInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            direct_borrowing_amount=Decimal("-100000"),
        )


def test_zero_nav_rejected():
    """Zero NAV should be rejected at input model."""
    with pytest.raises(ValueError, match="nav must be positive"):
        UCITSBorrowingInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("0"),
            direct_borrowing_amount=Decimal("500000"),
        )


def test_negative_nav_rejected():
    """Negative NAV should be rejected at input model."""
    with pytest.raises(ValueError, match="nav must be positive"):
        UCITSBorrowingInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("-10000000"),
            direct_borrowing_amount=Decimal("500000"),
        )


def test_empty_fund_id_rejected():
    """Empty fund_id should be rejected."""
    with pytest.raises(ValueError, match="fund_id must be non-empty"):
        UCITSBorrowingInput(
            fund_id="",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            direct_borrowing_amount=Decimal("500000"),
        )


def test_whitespace_only_fund_id_rejected():
    """Whitespace-only fund_id should be rejected."""
    with pytest.raises(ValueError, match="fund_id must be non-empty"):
        UCITSBorrowingInput(
            fund_id="   ",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            direct_borrowing_amount=Decimal("500000"),
        )


# ============================================================================
# Immutability
# ============================================================================


def test_input_model_is_immutable():
    """Input model should be frozen (immutable)."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("500000"),
    )
    with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen
        observation.direct_borrowing_amount = Decimal("1000000")


def test_result_model_is_immutable(engine):
    """Result model should be frozen (immutable)."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("500000"),
    )
    result = engine.calculate(observation)
    with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen
        result.status = UCITSBorrowingStatus.BREACH


# ============================================================================
# Precision and Decimal Handling
# ============================================================================


def test_decimal_precision_preserved(engine):
    """Decimal precision should be preserved through calculation."""
    observation = UCITSBorrowingInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("9999999.99"),
        direct_borrowing_amount=Decimal("1234567.89"),
    )
    result = engine.calculate(observation)

    # borrowing_ratio should equal the computed division
    expected_ratio = Decimal("1234567.89") / Decimal("9999999.99")
    assert result.borrowing_ratio == expected_ratio


def test_string_decimal_conversion(engine):
    """Engine should handle Decimal-from-string conversions."""
    observation = UCITSBorrowingInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("1000000"),
    )
    result = engine.calculate(observation)

    assert result.borrowing_ratio == Decimal("0.10")


# ============================================================================
# Audit Field Preservation
# ============================================================================


def test_audit_fields_copied_unchanged(engine):
    """Audit fields (fund_id, date, NAV, borrowing) should be unchanged."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Equity",
        valuation_date=date(2026, 6, 15),
        nav=Decimal("25000000"),
        direct_borrowing_amount=Decimal("2500000"),  # 10%
    )
    result = engine.calculate(observation)

    assert result.fund_id == "UCITS_Equity"
    assert result.valuation_date == date(2026, 6, 15)
    assert result.nav == Decimal("25000000")
    assert result.direct_borrowing_amount == Decimal("2500000")


def test_different_fund_ids_preserved(engine):
    """Different fund IDs should be preserved correctly."""
    for fund_id in ["UCITS_Conservative", "UCITS_Balanced", "UCITS_Aggressive"]:
        observation = UCITSBorrowingInput(
            fund_id=fund_id,
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            direct_borrowing_amount=Decimal("500000"),
        )
        result = engine.calculate(observation)
        assert result.fund_id == fund_id


# ============================================================================
# Engine Statelessness
# ============================================================================


def test_engine_is_stateless(engine):
    """Engine should produce consistent results regardless of call order."""
    obs1 = UCITSBorrowingInput(
        fund_id="Fund_A",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("500000"),  # 5%
    )
    obs2 = UCITSBorrowingInput(
        fund_id="Fund_B",
        valuation_date=date(2026, 6, 12),
        nav=Decimal("20000000"),
        direct_borrowing_amount=Decimal("2500000"),  # 12.5%
    )

    # Call with obs1, then obs2
    result1a = engine.calculate(obs1)
    result2a = engine.calculate(obs2)

    # Call with obs2, then obs1
    result2b = engine.calculate(obs2)
    result1b = engine.calculate(obs1)

    # Results should be identical regardless of order
    assert result1a.status == result1b.status
    assert result1a.borrowing_ratio == result1b.borrowing_ratio
    assert result1a.excess_amount == result1b.excess_amount

    assert result2a.status == result2b.status
    assert result2a.borrowing_ratio == result2b.borrowing_ratio
    assert result2a.excess_amount == result2b.excess_amount


# ============================================================================
# Result Internal Consistency
# ============================================================================


def test_result_fields_internally_consistent(engine):
    """Result DTO fields should be internally consistent."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        direct_borrowing_amount=Decimal("1500000"),  # 15%
    )
    result = engine.calculate(observation)

    # limit_amount should equal nav * limit_ratio
    assert result.limit_amount == result.nav * result.limit_ratio

    # borrowing_ratio should equal direct_borrowing_amount / nav
    assert result.borrowing_ratio == result.direct_borrowing_amount / result.nav

    # status should match excess fields
    if result.status == UCITSBorrowingStatus.WITHIN_LIMIT:
        assert result.excess_amount == Decimal("0")
        assert result.excess_ratio == Decimal("0")
    else:
        assert result.excess_amount > Decimal("0")
        assert result.excess_ratio > Decimal("0")


# ============================================================================
# Integration: Realistic UCITS Fund Scenarios
# ============================================================================


def test_realistic_conservative_ucits_fund(engine):
    """Test realistic conservative UCITS fund with minimal borrowing."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Conservative",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("50000000"),  # EUR 50M
        direct_borrowing_amount=Decimal("2000000"),  # EUR 2M = 4% of NAV
    )
    result = engine.calculate(observation)

    assert result.status == UCITSBorrowingStatus.WITHIN_LIMIT
    assert result.borrowing_ratio == Decimal("0.04")
    assert result.limit_amount == Decimal("5000000")
    assert result.excess_amount == Decimal("0")


def test_realistic_balanced_ucits_fund(engine):
    """Test realistic balanced UCITS fund at borderline borrowing."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("75000000"),  # EUR 75M
        direct_borrowing_amount=Decimal("7500000"),  # EUR 7.5M = 10% of NAV
    )
    result = engine.calculate(observation)

    assert result.status == UCITSBorrowingStatus.WITHIN_LIMIT
    assert result.borrowing_ratio == Decimal("0.10")
    assert result.limit_amount == Decimal("7500000")
    assert result.excess_amount == Decimal("0")


def test_realistic_aggressive_ucits_fund_in_breach(engine):
    """Test realistic aggressive UCITS fund exceeding borrowing limit."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_Aggressive",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("100000000"),  # EUR 100M
        direct_borrowing_amount=Decimal("12000000"),  # EUR 12M = 12% of NAV
    )
    result = engine.calculate(observation)

    assert result.status == UCITSBorrowingStatus.BREACH
    assert result.borrowing_ratio == Decimal("0.12")
    assert result.limit_amount == Decimal("10000000")
    assert result.excess_amount == Decimal("2000000")
    assert result.excess_ratio == Decimal("0.02")


def test_realistic_high_nav_fund(engine):
    """Test high-AUM fund with proportional borrowing."""
    observation = UCITSBorrowingInput(
        fund_id="UCITS_LargeAUM",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("500000000"),  # EUR 500M
        direct_borrowing_amount=Decimal("45000000"),  # EUR 45M = 9% of NAV
    )
    result = engine.calculate(observation)

    assert result.status == UCITSBorrowingStatus.WITHIN_LIMIT
    assert result.borrowing_ratio == Decimal("0.09")
    assert result.limit_amount == Decimal("50000000")
    assert result.excess_amount == Decimal("0")
