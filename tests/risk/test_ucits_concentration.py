"""Tests for UCITS single-issuer concentration monitoring.

Validates concentration limit compliance status calculation.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.ucits import (
    UCITSConcentrationEngine,
    UCITSConcentrationInput,
    UCITSConcentrationStatus,
)


@pytest.fixture
def engine():
    """Create engine instance."""
    return UCITSConcentrationEngine()


# ============================================================================
# Basic Compliance Tests
# ============================================================================


def test_exposure_well_below_threshold_is_within_limit(engine):
    """Exposure significantly below 10% threshold should be WITHIN_LIMIT."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_name="Example Bank",
        issuer_exposure_amount=Decimal("500000"),  # 5% of 10M
    )
    result = engine.calculate(observation)

    assert result.status == UCITSConcentrationStatus.WITHIN_LIMIT
    assert result.exposure_ratio == Decimal("500000") / Decimal("10000000")
    assert result.excess_amount == Decimal("0")
    assert result.excess_ratio == Decimal("0")


def test_exposure_just_below_threshold_is_within_limit(engine):
    """Exposure just below 10% threshold should be WITHIN_LIMIT."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("999900"),  # 9.999% of 10M
    )
    result = engine.calculate(observation)

    assert result.status == UCITSConcentrationStatus.WITHIN_LIMIT
    assert result.exposure_ratio == Decimal("999900") / Decimal("10000000")
    assert result.excess_amount == Decimal("0")
    assert result.excess_ratio == Decimal("0")


def test_exposure_exactly_at_threshold_is_within_limit(engine):
    """Exposure exactly at 10% threshold should be WITHIN_LIMIT."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("1000000"),  # exactly 10% of 10M
    )
    result = engine.calculate(observation)

    assert result.status == UCITSConcentrationStatus.WITHIN_LIMIT
    assert result.exposure_ratio == Decimal("0.10")
    assert result.excess_amount == Decimal("0")
    assert result.excess_ratio == Decimal("0")


def test_exposure_just_above_threshold_is_breach(engine):
    """Exposure just above 10% threshold should be BREACH."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("1000001"),  # 10.0001% of 10M
    )
    result = engine.calculate(observation)

    assert result.status == UCITSConcentrationStatus.BREACH
    assert result.exposure_ratio == Decimal("1000001") / Decimal("10000000")
    assert result.excess_amount > Decimal("0")
    assert result.excess_ratio > Decimal("0")


def test_exposure_well_above_threshold_is_breach(engine):
    """Exposure significantly above 10% threshold should be BREACH."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("2000000"),  # 20% of 10M
    )
    result = engine.calculate(observation)

    assert result.status == UCITSConcentrationStatus.BREACH
    assert result.exposure_ratio == Decimal("0.20")
    assert result.excess_amount == Decimal("1000000")
    assert result.excess_ratio == Decimal("0.10")


# ============================================================================
# Edge Cases: Exposure Extremes
# ============================================================================


def test_zero_exposure_is_within_limit(engine):
    """Zero exposure (no holding) should be WITHIN_LIMIT."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("0"),
    )
    result = engine.calculate(observation)

    assert result.status == UCITSConcentrationStatus.WITHIN_LIMIT
    assert result.exposure_ratio == Decimal("0")
    assert result.issuer_exposure_amount == Decimal("0")


def test_very_high_exposure_is_breach(engine):
    """Very high exposure should be BREACH."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Concentrated",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("5000000"),  # 50% of NAV
    )
    result = engine.calculate(observation)

    assert result.status == UCITSConcentrationStatus.BREACH
    assert result.exposure_ratio == Decimal("0.5")


# ============================================================================
# Boundary Tests
# ============================================================================


def test_boundary_10_percent_lower(engine):
    """Exposure just below 10% should be WITHIN_LIMIT."""
    observation = UCITSConcentrationInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("999999"),  # 9.99999% of 10M
    )
    result = engine.calculate(observation)
    assert result.status == UCITSConcentrationStatus.WITHIN_LIMIT


def test_boundary_10_percent_upper(engine):
    """Exposure at exactly 10% should be WITHIN_LIMIT."""
    observation = UCITSConcentrationInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("1000000"),  # exactly 10% of 10M
    )
    result = engine.calculate(observation)
    assert result.status == UCITSConcentrationStatus.WITHIN_LIMIT


def test_boundary_10_percent_breach(engine):
    """Exposure just above 10% should be BREACH."""
    observation = UCITSConcentrationInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("1000001"),  # 10.0001% of 10M
    )
    result = engine.calculate(observation)
    assert result.status == UCITSConcentrationStatus.BREACH


# ============================================================================
# Input Validation: Rejections
# ============================================================================


def test_negative_exposure_rejected():
    """Negative exposure should be rejected at input model."""
    with pytest.raises(ValueError, match="issuer_exposure_amount must be non-negative"):
        UCITSConcentrationInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            issuer_id="IE1234567890",
            issuer_exposure_amount=Decimal("-100000"),
        )


def test_zero_nav_rejected():
    """Zero NAV should be rejected at input model."""
    with pytest.raises(ValueError, match="nav must be positive"):
        UCITSConcentrationInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("0"),
            issuer_id="IE1234567890",
            issuer_exposure_amount=Decimal("500000"),
        )


def test_negative_nav_rejected():
    """Negative NAV should be rejected at input model."""
    with pytest.raises(ValueError, match="nav must be positive"):
        UCITSConcentrationInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("-10000000"),
            issuer_id="IE1234567890",
            issuer_exposure_amount=Decimal("500000"),
        )


def test_empty_fund_id_rejected():
    """Empty fund_id should be rejected."""
    with pytest.raises(ValueError, match="fund_id must be non-empty"):
        UCITSConcentrationInput(
            fund_id="",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            issuer_id="IE1234567890",
            issuer_exposure_amount=Decimal("500000"),
        )


def test_empty_issuer_id_rejected():
    """Empty issuer_id should be rejected."""
    with pytest.raises(ValueError, match="issuer_id must be non-empty"):
        UCITSConcentrationInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            issuer_id="",
            issuer_exposure_amount=Decimal("500000"),
        )


def test_whitespace_only_fund_id_rejected():
    """Whitespace-only fund_id should be rejected."""
    with pytest.raises(ValueError, match="fund_id must be non-empty"):
        UCITSConcentrationInput(
            fund_id="   ",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            issuer_id="IE1234567890",
            issuer_exposure_amount=Decimal("500000"),
        )


def test_whitespace_only_issuer_id_rejected():
    """Whitespace-only issuer_id should be rejected."""
    with pytest.raises(ValueError, match="issuer_id must be non-empty"):
        UCITSConcentrationInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            issuer_id="   ",
            issuer_exposure_amount=Decimal("500000"),
        )


# ============================================================================
# Immutability
# ============================================================================


def test_input_model_is_immutable():
    """Input model should be frozen (immutable)."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("500000"),
    )
    with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen
        observation.issuer_exposure_amount = Decimal("1000000")


def test_result_model_is_immutable(engine):
    """Result model should be frozen (immutable)."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("500000"),
    )
    result = engine.calculate(observation)
    with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen
        result.status = UCITSConcentrationStatus.BREACH


# ============================================================================
# Precision and Decimal Handling
# ============================================================================


def test_decimal_precision_preserved(engine):
    """Decimal precision should be preserved through calculation."""
    observation = UCITSConcentrationInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("9999999.99"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("1234567.89"),
    )
    result = engine.calculate(observation)

    # exposure_ratio should equal the computed division
    expected_ratio = Decimal("1234567.89") / Decimal("9999999.99")
    assert result.exposure_ratio == expected_ratio


def test_string_decimal_conversion(engine):
    """Engine should handle Decimal-from-string conversions."""
    observation = UCITSConcentrationInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("1000000"),
    )
    result = engine.calculate(observation)

    assert result.exposure_ratio == Decimal("0.10")


# ============================================================================
# Audit Field Preservation
# ============================================================================


def test_audit_fields_copied_unchanged(engine):
    """Audit fields (fund_id, issuer_id, issuer_name, date, NAV) should be unchanged."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Equity",
        valuation_date=date(2026, 6, 15),
        nav=Decimal("25000000"),
        issuer_id="FR0000120172",
        issuer_name="Société Générale",
        issuer_exposure_amount=Decimal("2500000"),  # 10%
    )
    result = engine.calculate(observation)

    assert result.fund_id == "UCITS_Equity"
    assert result.valuation_date == date(2026, 6, 15)
    assert result.nav == Decimal("25000000")
    assert result.issuer_id == "FR0000120172"
    assert result.issuer_name == "Société Générale"
    assert result.issuer_exposure_amount == Decimal("2500000")


def test_different_issuers_tracked_independently(engine):
    """Different issuers should be tracked independently."""
    for issuer_id, issuer_name in [
        ("IE1234567890", "Bank A"),
        ("FR0000120172", "Bank B"),
        ("DE1234567890", "Bank C"),
    ]:
        observation = UCITSConcentrationInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            issuer_id=issuer_id,
            issuer_name=issuer_name,
            issuer_exposure_amount=Decimal("500000"),
        )
        result = engine.calculate(observation)
        assert result.issuer_id == issuer_id
        assert result.issuer_name == issuer_name


def test_issuer_name_optional(engine):
    """Issuer name should be optional in both input and output."""
    observation = UCITSConcentrationInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("500000"),
        # issuer_name omitted
    )
    result = engine.calculate(observation)

    assert result.issuer_name is None


# ============================================================================
# Engine Statelessness
# ============================================================================


def test_engine_is_stateless(engine):
    """Engine should produce consistent results regardless of call order."""
    obs1 = UCITSConcentrationInput(
        fund_id="Fund_A",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1111111111",
        issuer_exposure_amount=Decimal("500000"),  # 5%
    )
    obs2 = UCITSConcentrationInput(
        fund_id="Fund_B",
        valuation_date=date(2026, 6, 12),
        nav=Decimal("20000000"),
        issuer_id="IE2222222222",
        issuer_exposure_amount=Decimal("2500000"),  # 12.5%
    )

    # Call with obs1, then obs2
    result1a = engine.calculate(obs1)
    result2a = engine.calculate(obs2)

    # Call with obs2, then obs1
    result2b = engine.calculate(obs2)
    result1b = engine.calculate(obs1)

    # Results should be identical regardless of order
    assert result1a.status == result1b.status
    assert result1a.exposure_ratio == result1b.exposure_ratio
    assert result1a.excess_amount == result1b.excess_amount

    assert result2a.status == result2b.status
    assert result2a.exposure_ratio == result2b.exposure_ratio
    assert result2a.excess_amount == result2b.excess_amount


# ============================================================================
# Result Internal Consistency
# ============================================================================


def test_result_fields_internally_consistent(engine):
    """Result DTO fields should be internally consistent."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        issuer_id="IE1234567890",
        issuer_exposure_amount=Decimal("1500000"),  # 15%
    )
    result = engine.calculate(observation)

    # limit_amount should equal nav * limit_ratio
    assert result.limit_amount == result.nav * result.limit_ratio

    # exposure_ratio should equal issuer_exposure_amount / nav
    assert result.exposure_ratio == result.issuer_exposure_amount / result.nav

    # status should match excess fields
    if result.status == UCITSConcentrationStatus.WITHIN_LIMIT:
        assert result.excess_amount == Decimal("0")
        assert result.excess_ratio == Decimal("0")
    else:
        assert result.excess_amount > Decimal("0")
        assert result.excess_ratio > Decimal("0")


# ============================================================================
# Integration: Realistic UCITS Fund Scenarios
# ============================================================================


def test_realistic_conservative_fund_single_issuer(engine):
    """Test realistic conservative UCITS fund with minimal single-issuer exposure."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Conservative",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("50000000"),  # EUR 50M
        issuer_id="DE0008404005",
        issuer_name="Siemens AG",
        issuer_exposure_amount=Decimal("1000000"),  # EUR 1M = 2% of NAV
    )
    result = engine.calculate(observation)

    assert result.status == UCITSConcentrationStatus.WITHIN_LIMIT
    assert result.exposure_ratio == Decimal("0.02")
    assert result.limit_amount == Decimal("5000000")
    assert result.excess_amount == Decimal("0")


def test_realistic_balanced_fund_at_limit(engine):
    """Test realistic balanced UCITS fund at concentration limit."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("75000000"),  # EUR 75M
        issuer_id="IE0005042456",
        issuer_name="CRH plc",
        issuer_exposure_amount=Decimal("7500000"),  # EUR 7.5M = 10% of NAV
    )
    result = engine.calculate(observation)

    assert result.status == UCITSConcentrationStatus.WITHIN_LIMIT
    assert result.exposure_ratio == Decimal("0.10")
    assert result.limit_amount == Decimal("7500000")
    assert result.excess_amount == Decimal("0")


def test_realistic_aggressive_fund_in_breach(engine):
    """Test realistic aggressive UCITS fund exceeding concentration limit."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_Aggressive",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("100000000"),  # EUR 100M
        issuer_id="FR0000120172",
        issuer_name="Société Générale",
        issuer_exposure_amount=Decimal("12000000"),  # EUR 12M = 12% of NAV
    )
    result = engine.calculate(observation)

    assert result.status == UCITSConcentrationStatus.BREACH
    assert result.exposure_ratio == Decimal("0.12")
    assert result.limit_amount == Decimal("10000000")
    assert result.excess_amount == Decimal("2000000")
    assert result.excess_ratio == Decimal("0.02")


def test_realistic_high_aum_fund(engine):
    """Test high-AUM fund with proportional single-issuer exposure."""
    observation = UCITSConcentrationInput(
        fund_id="UCITS_LargeAUM",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("500000000"),  # EUR 500M
        issuer_id="NL0000009165",
        issuer_name="Unilever N.V.",
        issuer_exposure_amount=Decimal("40000000"),  # EUR 40M = 8% of NAV
    )
    result = engine.calculate(observation)

    assert result.status == UCITSConcentrationStatus.WITHIN_LIMIT
    assert result.exposure_ratio == Decimal("0.08")
    assert result.limit_amount == Decimal("50000000")
    assert result.excess_amount == Decimal("0")


def test_realistic_multi_issuer_monitoring(engine):
    """Test monitoring multiple issuers independently (not aggregating)."""
    # Fund has three major holdings, each monitored separately
    issuers = [
        ("IE1234567890", "Bank A", Decimal("3000000")),  # 3%
        ("FR0000120172", "Bank B", Decimal("5000000")),  # 5%
        ("DE1234567890", "Bank C", Decimal("10500000")),  # 10.5% - BREACH
    ]

    fund_nav = Decimal("100000000")
    for issuer_id, issuer_name, exposure in issuers:
        observation = UCITSConcentrationInput(
            fund_id="UCITS_Portfolio",
            valuation_date=date(2026, 6, 11),
            nav=fund_nav,
            issuer_id=issuer_id,
            issuer_name=issuer_name,
            issuer_exposure_amount=exposure,
        )
        result = engine.calculate(observation)

        # Each issuer is evaluated independently
        if exposure <= Decimal("10000000"):
            assert result.status == UCITSConcentrationStatus.WITHIN_LIMIT
        else:
            assert result.status == UCITSConcentrationStatus.BREACH
