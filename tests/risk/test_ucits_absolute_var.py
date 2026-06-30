"""Tests for UCITS Absolute VaR monitoring.

Validates absolute VaR monitoring compliance status calculation.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.ucits import (
    UCITS_ABSOLUTE_VAR_LIMIT_RATIO,
    UCITSAbsoluteVaREngine,
    UCITSAbsoluteVaRInput,
    UCITSAbsoluteVaRStatus,
)


@pytest.fixture
def engine():
    """Create engine instance."""
    return UCITSAbsoluteVaREngine()


# ============================================================================
# Basic compliance tests
# ============================================================================


def test_var_well_below_threshold_is_within_limit(engine):
    """VaR significantly below 20% threshold should be WITHIN_LIMIT."""
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        var_amount=Decimal("1500000"),  # 15% of 10M
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSAbsoluteVaRStatus.WITHIN_LIMIT
    assert result.var_ratio == Decimal("1500000") / Decimal("10000000")
    assert result.excess_amount == Decimal("0")
    assert result.excess_ratio == Decimal("0")


def test_var_just_below_threshold_is_within_limit(engine):
    """VaR just below 20% threshold should be WITHIN_LIMIT."""
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        var_amount=Decimal("1999900"),  # 19.999% of 10M
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSAbsoluteVaRStatus.WITHIN_LIMIT
    assert result.var_ratio == Decimal("1999900") / Decimal("10000000")
    assert result.excess_amount == Decimal("0")
    assert result.excess_ratio == Decimal("0")


def test_var_exactly_at_threshold_is_within_limit(engine):
    """VaR exactly at 20% threshold should be WITHIN_LIMIT."""
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        var_amount=Decimal("2000000"),  # exactly 20% of 10M
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSAbsoluteVaRStatus.WITHIN_LIMIT
    assert result.var_ratio == Decimal("0.20")
    assert result.excess_amount == Decimal("0")
    assert result.excess_ratio == Decimal("0")


def test_var_just_above_threshold_is_breach(engine):
    """VaR just above 20% threshold should be BREACH."""
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        var_amount=Decimal("2000001"),  # 20.0001% of 10M
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSAbsoluteVaRStatus.BREACH
    assert result.var_ratio == Decimal("2000001") / Decimal("10000000")
    assert result.excess_amount > Decimal("0")
    assert result.excess_ratio > Decimal("0")


def test_var_well_above_threshold_is_breach(engine):
    """VaR significantly above 20% threshold should be BREACH."""
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        var_amount=Decimal("2500000"),  # 25% VaR
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSAbsoluteVaRStatus.BREACH
    assert result.var_ratio == Decimal("0.25")
    assert result.excess_amount == Decimal("500000")
    assert result.excess_ratio == Decimal("0.05")


# ============================================================================
# Edge cases: VaR extremes
# ============================================================================


def test_zero_var_is_within_limit(engine):
    """Zero VaR (no risk) should be WITHIN_LIMIT."""
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        var_amount=Decimal("0"),
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSAbsoluteVaRStatus.WITHIN_LIMIT
    assert result.var_ratio == Decimal("0")
    assert result.var_amount == Decimal("0")


def test_var_exceeds_nav_in_leveraged_portfolio(engine):
    """VaR exceeding NAV (>100%) is allowed in leveraged portfolios."""
    # Synthetic portfolio with derivatives and leverage
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Synthetic",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        var_amount=Decimal("15000000"),  # 150% VaR (leveraged)
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    # Should report BREACH (well above 20% threshold)
    assert result.status == UCITSAbsoluteVaRStatus.BREACH
    assert result.var_ratio == Decimal("1.5")
    assert result.excess_amount == Decimal("13000000")
    assert result.excess_ratio == Decimal("1.3")


# ============================================================================
# Input validation: rejections (construct fresh models)
# ============================================================================


def test_negative_var_amount_rejected():
    """Negative VaR amount should be rejected at input model."""
    with pytest.raises(ValueError, match="var_amount must be non-negative"):
        UCITSAbsoluteVaRInput(
            fund_id="UCITS_Balanced",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("-100000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )


def test_zero_nav_rejected():
    """Zero NAV should be rejected at input model."""
    with pytest.raises(ValueError, match="nav must be positive"):
        UCITSAbsoluteVaRInput(
            fund_id="UCITS_Balanced",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("0"),
            var_amount=Decimal("1000000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )


def test_negative_nav_rejected():
    """Negative NAV should be rejected at input model."""
    with pytest.raises(ValueError, match="nav must be positive"):
        UCITSAbsoluteVaRInput(
            fund_id="UCITS_Balanced",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("-1000000"),
            var_amount=Decimal("500000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )


def test_confidence_level_zero_rejected():
    """Confidence level of 0 should be rejected."""
    with pytest.raises(ValueError, match="confidence_level must be in"):
        UCITSAbsoluteVaRInput(
            fund_id="UCITS_Balanced",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("1500000"),
            confidence_level=Decimal("0"),
            holding_period_days=10,
        )


def test_confidence_level_one_rejected():
    """Confidence level of 1.0 should be rejected."""
    with pytest.raises(ValueError, match="confidence_level must be in"):
        UCITSAbsoluteVaRInput(
            fund_id="UCITS_Balanced",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("1500000"),
            confidence_level=Decimal("1.0"),
            holding_period_days=10,
        )


def test_confidence_level_negative_rejected():
    """Negative confidence level should be rejected."""
    with pytest.raises(ValueError, match="confidence_level must be in"):
        UCITSAbsoluteVaRInput(
            fund_id="UCITS_Balanced",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("1500000"),
            confidence_level=Decimal("-0.99"),
            holding_period_days=10,
        )


def test_confidence_level_over_one_rejected():
    """Confidence level > 1.0 should be rejected."""
    with pytest.raises(ValueError, match="confidence_level must be in"):
        UCITSAbsoluteVaRInput(
            fund_id="UCITS_Balanced",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("1500000"),
            confidence_level=Decimal("1.01"),
            holding_period_days=10,
        )


def test_holding_period_zero_rejected():
    """Holding period of 0 should be rejected."""
    with pytest.raises(ValueError, match="holding_period_days must be positive"):
        UCITSAbsoluteVaRInput(
            fund_id="UCITS_Balanced",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("1500000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=0,
        )


def test_holding_period_negative_rejected():
    """Negative holding period should be rejected."""
    with pytest.raises(ValueError, match="holding_period_days must be positive"):
        UCITSAbsoluteVaRInput(
            fund_id="UCITS_Balanced",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("1500000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=-10,
        )


def test_empty_fund_id_rejected():
    """Empty fund_id should be rejected."""
    with pytest.raises(ValueError, match="fund_id must be non-empty"):
        UCITSAbsoluteVaRInput(
            fund_id="",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("1500000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )


def test_whitespace_only_fund_id_rejected():
    """Whitespace-only fund_id should be rejected."""
    with pytest.raises(ValueError, match="fund_id must be non-empty"):
        UCITSAbsoluteVaRInput(
            fund_id="   ",
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("1500000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )


# ============================================================================
# Immutability
# ============================================================================


def test_input_model_is_immutable():
    """Input model should be frozen (immutable)."""
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        var_amount=Decimal("1500000"),
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen
        observation.var_amount = Decimal("5000000")


def test_result_model_is_immutable(engine):
    """Result model should be frozen (immutable)."""
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        var_amount=Decimal("1500000"),
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)
    with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen
        result.status = UCITSAbsoluteVaRStatus.BREACH


# ============================================================================
# Precision and Decimal handling
# ============================================================================


def test_decimal_precision_preserved(engine):
    """Decimal precision should be preserved through calculation."""
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("9999999.99"),
        var_amount=Decimal("1999999.998"),
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    # var_ratio should equal the computed division
    expected_ratio = Decimal("1999999.998") / Decimal("9999999.99")
    assert result.var_ratio == expected_ratio


def test_threshold_constant_is_correct():
    """Verify UCITS regulatory constant is correct."""
    assert UCITS_ABSOLUTE_VAR_LIMIT_RATIO == Decimal("0.20")


# ============================================================================
# Audit field preservation
# ============================================================================


def test_audit_fields_copied_unchanged(engine):
    """Audit fields (confidence_level, holding_period_days) should be unchanged."""
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Equity",
        valuation_date=date(2026, 6, 15),
        nav=Decimal("5000000"),
        var_amount=Decimal("750000"),  # 15% VaR
        confidence_level=Decimal("0.95"),  # Non-standard
        holding_period_days=5,  # Non-standard
    )
    result = engine.calculate(observation)

    assert result.confidence_level == Decimal("0.95")
    assert result.holding_period_days == 5
    assert result.fund_id == "UCITS_Equity"
    assert result.valuation_date == date(2026, 6, 15)


def test_different_fund_ids_preserved(engine):
    """Different fund IDs should be preserved correctly."""
    for fund_id in ["UCITS_Balanced", "UCITS_Equity", "UCITS_Bonds"]:
        observation = UCITSAbsoluteVaRInput(
            fund_id=fund_id,
            valuation_date=date(2026, 6, 11),
            nav=Decimal("10000000"),
            var_amount=Decimal("1500000"),
            confidence_level=Decimal("0.99"),
            holding_period_days=10,
        )
        result = engine.calculate(observation)
        assert result.fund_id == fund_id


# ============================================================================
# Engine statelessness
# ============================================================================


def test_engine_is_stateless(engine):
    """Engine should produce consistent results regardless of call order."""
    obs1 = UCITSAbsoluteVaRInput(
        fund_id="Fund_A",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        var_amount=Decimal("1500000"),  # 15%
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    obs2 = UCITSAbsoluteVaRInput(
        fund_id="Fund_B",
        valuation_date=date(2026, 6, 12),
        nav=Decimal("20000000"),
        var_amount=Decimal("4500000"),  # 22.5%
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
    assert result1a.var_ratio == result1b.var_ratio
    assert result1a.excess_amount == result1b.excess_amount

    assert result2a.status == result2b.status
    assert result2a.var_ratio == result2b.var_ratio
    assert result2a.excess_amount == result2b.excess_amount


# ============================================================================
# Result internal consistency
# ============================================================================


def test_result_fields_internally_consistent(engine):
    """Result DTO fields should maintain internal consistency."""
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("10000000"),
        var_amount=Decimal("2500000"),  # 25% VaR
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    # threshold_amount should equal nav × threshold_ratio
    assert result.threshold_amount == result.nav * result.threshold_ratio

    # var_ratio should equal var_amount / nav
    assert result.var_ratio == result.var_amount / result.nav


# ============================================================================
# Integration: realistic scenarios
# ============================================================================


def test_realistic_ucits_balanced_scenario(engine):
    """Test realistic UCITS Balanced Fund scenario."""
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Balanced",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("50000000"),  # EUR 50M
        var_amount=Decimal("7500000"),  # EUR 7.5M = 15% VaR
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSAbsoluteVaRStatus.WITHIN_LIMIT
    assert result.var_ratio == Decimal("0.15")
    assert result.threshold_amount == Decimal("10000000")  # 20% of 50M
    assert result.excess_amount == Decimal("0")


def test_realistic_market_stress_scenario(engine):
    """Test market stress scenario pushing VaR above limit."""
    observation = UCITSAbsoluteVaRInput(
        fund_id="UCITS_Equity",
        valuation_date=date(2026, 6, 11),
        nav=Decimal("25000000"),  # EUR 25M
        var_amount=Decimal("5500000"),  # EUR 5.5M = 22% VaR
        confidence_level=Decimal("0.99"),
        holding_period_days=10,
    )
    result = engine.calculate(observation)

    assert result.status == UCITSAbsoluteVaRStatus.BREACH
    assert result.var_ratio == Decimal("0.22")
    assert result.threshold_amount == Decimal("5000000")  # 20% of 25M
    assert result.excess_amount == Decimal("500000")
    assert result.excess_ratio == Decimal("0.02")
