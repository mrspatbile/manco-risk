"""Tests for UCITS SRRI calculation.

Validates SRRI class mapping from annualised volatility.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.ucits import SRRIEngine, SRRIInput


@pytest.fixture
def engine():
    """Create engine instance."""
    return SRRIEngine()


# ============================================================================
# SRRI Class Mapping - Each Class
# ============================================================================


def test_srri_class_1_below_lower_bound(engine):
    """Volatility < 0.5% should map to SRRI 1."""
    observation = SRRIInput(
        fund_id="UCITS_Conservative",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.003"),  # 0.3%
    )
    result = engine.calculate(observation)

    assert result.srri_class == 1


def test_srri_class_2_in_range(engine):
    """Volatility in [0.5%, 2%) should map to SRRI 2."""
    observation = SRRIInput(
        fund_id="UCITS_Conservative",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.01"),  # 1%
    )
    result = engine.calculate(observation)

    assert result.srri_class == 2


def test_srri_class_3_in_range(engine):
    """Volatility in [2%, 5%) should map to SRRI 3."""
    observation = SRRIInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.035"),  # 3.5%
    )
    result = engine.calculate(observation)

    assert result.srri_class == 3


def test_srri_class_4_in_range(engine):
    """Volatility in [5%, 10%) should map to SRRI 4."""
    observation = SRRIInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.075"),  # 7.5%
    )
    result = engine.calculate(observation)

    assert result.srri_class == 4


def test_srri_class_5_in_range(engine):
    """Volatility in [10%, 15%) should map to SRRI 5."""
    observation = SRRIInput(
        fund_id="UCITS_Growth",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.125"),  # 12.5%
    )
    result = engine.calculate(observation)

    assert result.srri_class == 5


def test_srri_class_6_in_range(engine):
    """Volatility in [15%, 25%) should map to SRRI 6."""
    observation = SRRIInput(
        fund_id="UCITS_Aggressive",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.20"),  # 20%
    )
    result = engine.calculate(observation)

    assert result.srri_class == 6


def test_srri_class_7_at_and_above_lower_bound(engine):
    """Volatility >= 25% should map to SRRI 7."""
    observation = SRRIInput(
        fund_id="UCITS_VeryAggressive",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.30"),  # 30%
    )
    result = engine.calculate(observation)

    assert result.srri_class == 7


# ============================================================================
# Boundary Tests - Each Transition Point
# ============================================================================


def test_boundary_0_5_percent_lower(engine):
    """Volatility just below 0.5% should be SRRI 1."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.00499"),  # 0.499%
    )
    result = engine.calculate(observation)
    assert result.srri_class == 1


def test_boundary_0_5_percent_upper(engine):
    """Volatility at exactly 0.5% should be SRRI 2."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.005"),  # 0.5%
    )
    result = engine.calculate(observation)
    assert result.srri_class == 2


def test_boundary_2_percent_lower(engine):
    """Volatility just below 2% should be SRRI 2."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.01999"),  # 1.999%
    )
    result = engine.calculate(observation)
    assert result.srri_class == 2


def test_boundary_2_percent_upper(engine):
    """Volatility at exactly 2% should be SRRI 3."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.02"),  # 2%
    )
    result = engine.calculate(observation)
    assert result.srri_class == 3


def test_boundary_5_percent_lower(engine):
    """Volatility just below 5% should be SRRI 3."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.04999"),  # 4.999%
    )
    result = engine.calculate(observation)
    assert result.srri_class == 3


def test_boundary_5_percent_upper(engine):
    """Volatility at exactly 5% should be SRRI 4."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.05"),  # 5%
    )
    result = engine.calculate(observation)
    assert result.srri_class == 4


def test_boundary_10_percent_lower(engine):
    """Volatility just below 10% should be SRRI 4."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.09999"),  # 9.999%
    )
    result = engine.calculate(observation)
    assert result.srri_class == 4


def test_boundary_10_percent_upper(engine):
    """Volatility at exactly 10% should be SRRI 5."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.10"),  # 10%
    )
    result = engine.calculate(observation)
    assert result.srri_class == 5


def test_boundary_15_percent_lower(engine):
    """Volatility just below 15% should be SRRI 5."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.14999"),  # 14.999%
    )
    result = engine.calculate(observation)
    assert result.srri_class == 5


def test_boundary_15_percent_upper(engine):
    """Volatility at exactly 15% should be SRRI 6."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.15"),  # 15%
    )
    result = engine.calculate(observation)
    assert result.srri_class == 6


def test_boundary_25_percent_lower(engine):
    """Volatility just below 25% should be SRRI 6."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.24999"),  # 24.999%
    )
    result = engine.calculate(observation)
    assert result.srri_class == 6


def test_boundary_25_percent_upper(engine):
    """Volatility at exactly 25% should be SRRI 7."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.25"),  # 25%
    )
    result = engine.calculate(observation)
    assert result.srri_class == 7


# ============================================================================
# Edge Cases: Volatility Extremes
# ============================================================================


def test_zero_volatility_is_srri_1(engine):
    """Zero volatility (no risk) should be SRRI 1."""
    observation = SRRIInput(
        fund_id="UCITS_Stable",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0"),
    )
    result = engine.calculate(observation)

    assert result.srri_class == 1


def test_very_high_volatility_is_srri_7(engine):
    """Very high volatility should still be SRRI 7."""
    observation = SRRIInput(
        fund_id="UCITS_HighRisk",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("1.5"),  # 150%
    )
    result = engine.calculate(observation)

    assert result.srri_class == 7


# ============================================================================
# Input Validation: Rejections
# ============================================================================


def test_negative_volatility_rejected():
    """Negative volatility should be rejected at input model."""
    with pytest.raises(ValueError, match="annualised_volatility must be non-negative"):
        SRRIInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            annualised_volatility=Decimal("-0.05"),
        )


def test_empty_fund_id_rejected():
    """Empty fund_id should be rejected."""
    with pytest.raises(ValueError, match="fund_id must be non-empty"):
        SRRIInput(
            fund_id="",
            valuation_date=date(2026, 6, 11),
            annualised_volatility=Decimal("0.10"),
        )


def test_whitespace_only_fund_id_rejected():
    """Whitespace-only fund_id should be rejected."""
    with pytest.raises(ValueError, match="fund_id must be non-empty"):
        SRRIInput(
            fund_id="   ",
            valuation_date=date(2026, 6, 11),
            annualised_volatility=Decimal("0.10"),
        )


# ============================================================================
# Immutability
# ============================================================================


def test_input_model_is_immutable():
    """Input model should be frozen (immutable)."""
    observation = SRRIInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.10"),
    )
    with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen
        observation.annualised_volatility = Decimal("0.15")


def test_result_model_is_immutable(engine):
    """Result model should be frozen (immutable)."""
    observation = SRRIInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.10"),
    )
    result = engine.calculate(observation)
    with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen
        result.srri_class = 6


# ============================================================================
# Precision and Decimal Handling
# ============================================================================


def test_decimal_precision_preserved(engine):
    """Decimal precision should be preserved through calculation."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.1234567"),  # High precision
    )
    result = engine.calculate(observation)

    # Volatility should be preserved exactly
    assert result.annualised_volatility == Decimal("0.1234567")
    assert result.srri_class == 5


def test_string_decimal_conversion(engine):
    """Engine should handle Decimal-from-string conversions."""
    observation = SRRIInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.075"),
    )
    result = engine.calculate(observation)

    assert result.srri_class == 4


# ============================================================================
# Audit Field Preservation
# ============================================================================


def test_audit_fields_copied_unchanged(engine):
    """Audit fields (fund_id, date, volatility) should be unchanged."""
    observation = SRRIInput(
        fund_id="UCITS_Equity",
        valuation_date=date(2026, 6, 15),
        annualised_volatility=Decimal("0.12"),
    )
    result = engine.calculate(observation)

    assert result.fund_id == "UCITS_Equity"
    assert result.valuation_date == date(2026, 6, 15)
    assert result.annualised_volatility == Decimal("0.12")


def test_different_fund_ids_preserved(engine):
    """Different fund IDs should be preserved correctly."""
    for fund_id in ["UCITS_Conservative", "UCITS_Balanced", "UCITS_Aggressive"]:
        observation = SRRIInput(
            fund_id=fund_id,
            valuation_date=date(2026, 6, 11),
            annualised_volatility=Decimal("0.10"),
        )
        result = engine.calculate(observation)
        assert result.fund_id == fund_id


# ============================================================================
# Engine Statelessness
# ============================================================================


def test_engine_is_stateless(engine):
    """Engine should produce consistent results regardless of call order."""
    obs1 = SRRIInput(
        fund_id="Fund_A",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.03"),
    )
    obs2 = SRRIInput(
        fund_id="Fund_B",
        valuation_date=date(2026, 6, 12),
        annualised_volatility=Decimal("0.15"),
    )

    # Call with obs1, then obs2
    result1a = engine.calculate(obs1)
    result2a = engine.calculate(obs2)

    # Call with obs2, then obs1
    result2b = engine.calculate(obs2)
    result1b = engine.calculate(obs1)

    # Results should be identical regardless of order
    assert result1a.srri_class == result1b.srri_class
    assert result2a.srri_class == result2b.srri_class


# ============================================================================
# Result Internal Consistency
# ============================================================================


def test_result_fields_internally_consistent(engine):
    """Result DTO fields should be consistent."""
    observation = SRRIInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.10"),
    )
    result = engine.calculate(observation)

    # All fields should match input
    assert result.fund_id == observation.fund_id
    assert result.valuation_date == observation.valuation_date
    assert result.annualised_volatility == observation.annualised_volatility
    # SRRI class should be in valid range
    assert 1 <= result.srri_class <= 7


# ============================================================================
# Integration: Realistic UCITS Fund Scenarios
# ============================================================================


def test_realistic_conservative_ucits_fund(engine):
    """Test realistic conservative UCITS fund volatility."""
    observation = SRRIInput(
        fund_id="UCITS_Conservative",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.008"),  # 0.8% volatility
    )
    result = engine.calculate(observation)

    assert result.srri_class == 2


def test_realistic_balanced_ucits_fund(engine):
    """Test realistic balanced UCITS fund volatility."""
    observation = SRRIInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.12"),  # 12% volatility
    )
    result = engine.calculate(observation)

    assert result.srri_class == 5


def test_realistic_aggressive_ucits_fund(engine):
    """Test realistic aggressive UCITS fund volatility."""
    observation = SRRIInput(
        fund_id="UCITS_Aggressive",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.22"),  # 22% volatility
    )
    result = engine.calculate(observation)

    assert result.srri_class == 6


def test_realistic_very_aggressive_ucits_fund(engine):
    """Test realistic very aggressive UCITS fund volatility."""
    observation = SRRIInput(
        fund_id="UCITS_VeryAggressive",
        valuation_date=date(2026, 6, 11),
        annualised_volatility=Decimal("0.35"),  # 35% volatility
    )
    result = engine.calculate(observation)

    assert result.srri_class == 7
