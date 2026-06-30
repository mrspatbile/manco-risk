"""Tests for UCITS Relative VaR monitoring.

Validates relative VaR compliance status calculation.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.ucits import (
    UCITSRelativeVaREngine,
    UCITSRelativeVaRInput,
    UCITSRelativeVaRStatus,
)


@pytest.fixture
def engine():
    """Create engine instance."""
    return UCITSRelativeVaREngine()


# ============================================================================
# Basic Compliance Tests
# ============================================================================


def test_fund_var_well_below_reference_is_within_limit(engine):
    """Fund VaR well below reference portfolio VaR should be WITHIN_LIMIT."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("800000"),
        reference_portfolio_var=Decimal("1000000"),  # Fund at 80% of reference
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSRelativeVaRStatus.WITHIN_LIMIT
    assert result.relative_var_ratio == Decimal("0.8")
    assert result.excess_ratio == Decimal("0")


def test_fund_var_just_below_reference_is_within_limit(engine):
    """Fund VaR just below reference portfolio VaR should be WITHIN_LIMIT."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("999900"),
        reference_portfolio_var=Decimal("1000000"),  # Fund at 99.99% of reference
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSRelativeVaRStatus.WITHIN_LIMIT
    assert result.relative_var_ratio == Decimal("999900") / Decimal("1000000")
    assert result.excess_ratio == Decimal("0")


def test_fund_var_exactly_at_reference_is_within_limit(engine):
    """Fund VaR exactly equal to reference portfolio VaR should be WITHIN_LIMIT."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("1000000"),
        reference_portfolio_var=Decimal("1000000"),  # Fund at 100% of reference
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSRelativeVaRStatus.WITHIN_LIMIT
    assert result.relative_var_ratio == Decimal("1.0")
    assert result.excess_ratio == Decimal("0")


def test_fund_var_at_150_percent_is_within_limit(engine):
    """Fund VaR at 150% of reference portfolio VaR should be WITHIN_LIMIT."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("1500000"),
        reference_portfolio_var=Decimal("1000000"),  # Fund at 150% of reference (within 200% limit)
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSRelativeVaRStatus.WITHIN_LIMIT
    assert result.relative_var_ratio == Decimal("1.5")
    assert result.excess_ratio == Decimal("0")


def test_fund_var_well_above_reference_is_within_limit(engine):
    """Fund VaR well above reference portfolio VaR (150%) but below limit should be WITHIN_LIMIT."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_Aggressive",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("1500000"),
        reference_portfolio_var=Decimal("1000000"),  # Fund at 150% of reference (within 200% limit)
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSRelativeVaRStatus.WITHIN_LIMIT
    assert result.relative_var_ratio == Decimal("1.5")
    assert result.excess_ratio == Decimal("0")


# ============================================================================
# Edge Cases: VaR Extremes
# ============================================================================


def test_zero_fund_var_is_within_limit(engine):
    """Zero fund VaR (no risk) should be WITHIN_LIMIT."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_Stable",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("0"),
        reference_portfolio_var=Decimal("1000000"),
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSRelativeVaRStatus.WITHIN_LIMIT
    assert result.relative_var_ratio == Decimal("0")
    assert result.fund_var == Decimal("0")


def test_fund_var_much_higher_than_reference_is_breach(engine):
    """Fund VaR much higher than reference should be BREACH."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_HighLeverage",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("3000000"),
        reference_portfolio_var=Decimal("1000000"),  # Fund at 300% of reference
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSRelativeVaRStatus.BREACH
    assert result.relative_var_ratio == Decimal("3.0")


# ============================================================================
# Boundary Tests
# ============================================================================


def test_boundary_200_percent_lower(engine):
    """Fund VaR just below 200% of reference should be WITHIN_LIMIT."""
    observation = UCITSRelativeVaRInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("1999999"),
        reference_portfolio_var=Decimal("1000000"),
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)
    assert result.status == UCITSRelativeVaRStatus.WITHIN_LIMIT


def test_boundary_200_percent_upper(engine):
    """Fund VaR at exactly 200% of reference should be WITHIN_LIMIT."""
    observation = UCITSRelativeVaRInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("2000000"),
        reference_portfolio_var=Decimal("1000000"),
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)
    assert result.status == UCITSRelativeVaRStatus.WITHIN_LIMIT


def test_boundary_200_percent_breach(engine):
    """Fund VaR just above 200% of reference should be BREACH."""
    observation = UCITSRelativeVaRInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("2000001"),
        reference_portfolio_var=Decimal("1000000"),
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)
    assert result.status == UCITSRelativeVaRStatus.BREACH


# ============================================================================
# Input Validation: Rejections
# ============================================================================


def test_negative_fund_var_rejected():
    """Negative fund VaR should be rejected at input model."""
    with pytest.raises(ValueError, match="fund_var must be non-negative"):
        UCITSRelativeVaRInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            fund_var=Decimal("-100000"),
            reference_portfolio_var=Decimal("1000000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )


def test_zero_reference_var_rejected():
    """Zero reference portfolio VaR should be rejected (cannot divide by zero)."""
    with pytest.raises(ValueError, match="reference_portfolio_var must be positive"):
        UCITSRelativeVaRInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            fund_var=Decimal("500000"),
            reference_portfolio_var=Decimal("0"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )


def test_negative_reference_var_rejected():
    """Negative reference portfolio VaR should be rejected."""
    with pytest.raises(ValueError, match="reference_portfolio_var must be positive"):
        UCITSRelativeVaRInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            fund_var=Decimal("500000"),
            reference_portfolio_var=Decimal("-1000000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )


def test_empty_fund_id_rejected():
    """Empty fund_id should be rejected."""
    with pytest.raises(ValueError, match="fund_id must be non-empty"):
        UCITSRelativeVaRInput(
            fund_id="",
            valuation_date=date(2026, 6, 11),
            fund_var=Decimal("500000"),
            reference_portfolio_var=Decimal("1000000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )


def test_confidence_level_zero_rejected():
    """Confidence level of 0 should be rejected."""
    with pytest.raises(ValueError, match="confidence_level must be in"):
        UCITSRelativeVaRInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            fund_var=Decimal("500000"),
            reference_portfolio_var=Decimal("1000000"),
            confidence_level=Decimal("0"),
            holding_period_days=10,
        )


def test_confidence_level_one_rejected():
    """Confidence level of 1.0 should be rejected."""
    with pytest.raises(ValueError, match="confidence_level must be in"):
        UCITSRelativeVaRInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            fund_var=Decimal("500000"),
            reference_portfolio_var=Decimal("1000000"),
            confidence_level=Decimal("1.0"),
            holding_period_days=10,
        )


def test_holding_period_zero_rejected():
    """Holding period of 0 should be rejected."""
    with pytest.raises(ValueError, match="holding_period_days must be positive"):
        UCITSRelativeVaRInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            fund_var=Decimal("500000"),
            reference_portfolio_var=Decimal("1000000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=0,
        )


def test_holding_period_negative_rejected():
    """Negative holding period should be rejected."""
    with pytest.raises(ValueError, match="holding_period_days must be positive"):
        UCITSRelativeVaRInput(
            fund_id="test",
            valuation_date=date(2026, 6, 11),
            fund_var=Decimal("500000"),
            reference_portfolio_var=Decimal("1000000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=-10,
        )


# ============================================================================
# Immutability
# ============================================================================


def test_input_model_is_immutable():
    """Input model should be frozen (immutable)."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("800000"),
        reference_portfolio_var=Decimal("1000000"),
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen
        observation.fund_var = Decimal("500000")


def test_result_model_is_immutable(engine):
    """Result model should be frozen (immutable)."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("800000"),
        reference_portfolio_var=Decimal("1000000"),
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)
    with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen
        result.status = UCITSRelativeVaRStatus.BREACH


# ============================================================================
# Precision and Decimal Handling
# ============================================================================


def test_decimal_precision_preserved(engine):
    """Decimal precision should be preserved through calculation."""
    observation = UCITSRelativeVaRInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("1234567.89"),
        reference_portfolio_var=Decimal("9999999.99"),
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    # relative_var_ratio should equal the computed division
    expected_ratio = Decimal("1234567.89") / Decimal("9999999.99")
    assert result.relative_var_ratio == expected_ratio


def test_string_decimal_conversion(engine):
    """Engine should handle Decimal-from-string conversions."""
    observation = UCITSRelativeVaRInput(
        fund_id="test",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("1000000"),
        reference_portfolio_var=Decimal("1000000"),
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.relative_var_ratio == Decimal("1.0")


# ============================================================================
# Audit Field Preservation
# ============================================================================


def test_audit_fields_copied_unchanged(engine):
    """Audit fields should be copied unchanged."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_Equity",
        valuation_date=date(2026, 6, 15),
        fund_var=Decimal("1200000"),
        reference_portfolio_var=Decimal("1000000"),
        confidence_level=Decimal("0.95"),
        holding_period_days=5,
    )
    result = engine.calculate(observation)

    assert result.fund_id == "UCITS_Equity"
    assert result.valuation_date == date(2026, 6, 15)
    assert result.fund_var == Decimal("1200000")
    assert result.reference_portfolio_var == Decimal("1000000")
    assert result.confidence_level == Decimal("0.95")
    assert result.holding_period_days == 5


def test_different_fund_ids_preserved(engine):
    """Different fund IDs should be preserved correctly."""
    for fund_id in ["UCITS_Conservative", "UCITS_Balanced", "UCITS_Aggressive"]:
        observation = UCITSRelativeVaRInput(
            fund_id=fund_id,
            valuation_date=date(2026, 6, 11),
            fund_var=Decimal("800000"),
            reference_portfolio_var=Decimal("1000000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )
        result = engine.calculate(observation)
        assert result.fund_id == fund_id


# ============================================================================
# Engine Statelessness
# ============================================================================


def test_engine_is_stateless(engine):
    """Engine should produce consistent results regardless of call order."""
    obs1 = UCITSRelativeVaRInput(
        fund_id="Fund_A",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("800000"),
        reference_portfolio_var=Decimal("1000000"),  # 80%
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    obs2 = UCITSRelativeVaRInput(
        fund_id="Fund_B",
        valuation_date=date(2026, 6, 12),
        fund_var=Decimal("1200000"),
        reference_portfolio_var=Decimal("1000000"),  # 120% - BREACH
        confidence_level=Decimal("0.95"),
        holding_period_days=5,
    )

    # Call with obs1, then obs2
    result1a = engine.calculate(obs1)
    result2a = engine.calculate(obs2)

    # Call with obs2, then obs1
    result2b = engine.calculate(obs2)
    result1b = engine.calculate(obs1)

    # Results should be identical regardless of order
    assert result1a.status == result1b.status
    assert result1a.relative_var_ratio == result1b.relative_var_ratio
    assert result1a.excess_ratio == result1b.excess_ratio

    assert result2a.status == result2b.status
    assert result2a.relative_var_ratio == result2b.relative_var_ratio
    assert result2a.excess_ratio == result2b.excess_ratio


# ============================================================================
# Result Internal Consistency
# ============================================================================


def test_result_fields_internally_consistent(engine):
    """Result DTO fields should be internally consistent."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("1500000"),
        reference_portfolio_var=Decimal("1000000"),  # 150%
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    # relative_var_ratio should equal fund_var / reference_portfolio_var
    assert result.relative_var_ratio == result.fund_var / result.reference_portfolio_var

    # status should match excess fields
    if result.status == UCITSRelativeVaRStatus.WITHIN_LIMIT:
        assert result.excess_ratio == Decimal("0")
    else:
        assert result.excess_ratio > Decimal("0")


# ============================================================================
# Integration: Realistic UCITS Fund Scenarios
# ============================================================================


def test_realistic_conservative_fund(engine):
    """Test realistic conservative UCITS fund with low relative VaR."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_Conservative",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("600000"),
        reference_portfolio_var=Decimal("1000000"),  # Fund at 60% of benchmark VaR
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSRelativeVaRStatus.WITHIN_LIMIT
    assert result.relative_var_ratio == Decimal("0.6")
    assert result.excess_ratio == Decimal("0")


def test_realistic_balanced_fund_at_limit(engine):
    """Test realistic balanced UCITS fund exactly at limit."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("1000000"),
        reference_portfolio_var=Decimal("1000000"),  # Fund at 100% of benchmark VaR (limit)
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSRelativeVaRStatus.WITHIN_LIMIT
    assert result.relative_var_ratio == Decimal("1.0")
    assert result.excess_ratio == Decimal("0")


def test_realistic_aggressive_fund_in_breach(engine):
    """Test realistic aggressive UCITS fund exceeding 200% relative VaR limit."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_Aggressive",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("2500000"),
        reference_portfolio_var=Decimal(
            "1000000"
        ),  # Fund at 250% of benchmark VaR (exceeds 200% limit)
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSRelativeVaRStatus.BREACH
    assert result.relative_var_ratio == Decimal("2.5")
    assert result.excess_ratio == Decimal("0.5")


def test_realistic_enhanced_index_fund(engine):
    """Test realistic enhanced index UCITS fund slightly above benchmark but within limit."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_EnhancedIndex",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("1050000"),
        reference_portfolio_var=Decimal(
            "1000000"
        ),  # Fund at 105% of benchmark VaR (within 200% limit)
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSRelativeVaRStatus.WITHIN_LIMIT
    assert result.relative_var_ratio == Decimal("1.05")
    assert result.excess_ratio == Decimal("0")


def test_realistic_low_volatility_fund(engine):
    """Test realistic low-volatility UCITS fund with conservative positioning."""
    observation = UCITSRelativeVaRInput(
        fund_id="UCITS_LowVolatility",
        valuation_date=date(2026, 6, 11),
        fund_var=Decimal("400000"),
        reference_portfolio_var=Decimal("1000000"),  # Fund at 40% of benchmark VaR
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSRelativeVaRStatus.WITHIN_LIMIT
    assert result.relative_var_ratio == Decimal("0.4")
    assert result.excess_ratio == Decimal("0")
