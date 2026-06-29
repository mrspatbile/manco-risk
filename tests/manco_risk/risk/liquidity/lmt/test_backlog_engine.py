"""Tests for redemption backlog accounting engine."""

from decimal import Decimal

import pytest

from manco_risk.risk.liquidity.lmt.backlog_engine import BacklogEngine
from manco_risk.risk.liquidity.lmt.models import BacklogState


class TestBacklogEngineFullRedemption:
    """Tests for full redemption scenarios (no backlog)."""

    def test_no_backlog_carry_forward_full_redemption(self):
        """Beginning backlog zero, new redemptions fully met."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=0,
            beginning_backlog=Decimal("0"),
            new_redemptions=Decimal("1000000"),
            redeemed_in_month=Decimal("1000000"),
            deferral_reason=None,
        )

        assert isinstance(result, BacklogState)
        assert result.month_index == 0
        assert result.beginning_backlog == Decimal("0")
        assert result.new_redemptions == Decimal("1000000")
        assert result.total_redemptions_due == Decimal("1000000")
        assert result.redeemed_in_month == Decimal("1000000")
        assert result.ending_backlog == Decimal("0")
        assert result.deferral_reason is None  # No backlog means no deferral reason

    def test_no_backlog_multiple_months_full_redemption(self):
        """Full redemptions across multiple months."""
        engine = BacklogEngine()

        for month in range(3):
            result = engine.calculate(
                month_index=month,
                beginning_backlog=Decimal("0"),
                new_redemptions=Decimal("500000"),
                redeemed_in_month=Decimal("500000"),
                deferral_reason=None,
            )

            assert result.ending_backlog == Decimal("0")
            assert result.deferral_reason is None


class TestBacklogEnginePartialRedemption:
    """Tests for partial redemption scenarios (backlog generated)."""

    def test_no_backlog_carry_forward_partial_redemption(self):
        """Beginning backlog zero, new redemptions only partially met."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=0,
            beginning_backlog=Decimal("0"),
            new_redemptions=Decimal("1000000"),
            redeemed_in_month=Decimal("600000"),
            deferral_reason="gate",
        )

        assert result.month_index == 0
        assert result.beginning_backlog == Decimal("0")
        assert result.new_redemptions == Decimal("1000000")
        assert result.total_redemptions_due == Decimal("1000000")
        assert result.redeemed_in_month == Decimal("600000")
        assert result.ending_backlog == Decimal("400000")
        assert result.deferral_reason == "gate"  # Reason retained because backlog > 0

    def test_partial_redemption_multiple_deferral_reasons(self):
        """Different deferral reasons for partial redemptions."""
        engine = BacklogEngine()

        result_gate = engine.calculate(
            month_index=0,
            beginning_backlog=Decimal("0"),
            new_redemptions=Decimal("1000000"),
            redeemed_in_month=Decimal("500000"),
            deferral_reason="gate",
        )
        assert result_gate.deferral_reason == "gate"

        result_liquidity = engine.calculate(
            month_index=0,
            beginning_backlog=Decimal("0"),
            new_redemptions=Decimal("1000000"),
            redeemed_in_month=Decimal("500000"),
            deferral_reason="insufficient_liquidity",
        )
        assert result_liquidity.deferral_reason == "insufficient_liquidity"

        result_suspension = engine.calculate(
            month_index=0,
            beginning_backlog=Decimal("0"),
            new_redemptions=Decimal("1000000"),
            redeemed_in_month=Decimal("0"),
            deferral_reason="suspension",
        )
        assert result_suspension.deferral_reason == "suspension"


class TestBacklogEngineCarryForward:
    """Tests for backlog carry-forward scenarios."""

    def test_backlog_carry_forward_full_redemption(self):
        """Backlog from prior month, new redemptions, full satisfaction."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=1,
            beginning_backlog=Decimal("400000"),  # From prior month
            new_redemptions=Decimal("600000"),
            redeemed_in_month=Decimal("1000000"),  # Fully cover both
            deferral_reason=None,
        )

        assert result.beginning_backlog == Decimal("400000")
        assert result.new_redemptions == Decimal("600000")
        assert result.total_redemptions_due == Decimal("1000000")
        assert result.redeemed_in_month == Decimal("1000000")
        assert result.ending_backlog == Decimal("0")
        assert result.deferral_reason is None

    def test_backlog_carry_forward_partial_redemption(self):
        """Backlog from prior month, new redemptions, partial satisfaction."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=1,
            beginning_backlog=Decimal("400000"),
            new_redemptions=Decimal("600000"),
            redeemed_in_month=Decimal("700000"),  # Cover some but not all
            deferral_reason="gate",
        )

        assert result.beginning_backlog == Decimal("400000")
        assert result.new_redemptions == Decimal("600000")
        assert result.total_redemptions_due == Decimal("1000000")
        assert result.redeemed_in_month == Decimal("700000")
        assert result.ending_backlog == Decimal("300000")
        assert result.deferral_reason == "gate"

    def test_backlog_cascade_multiple_months(self):
        """Backlog carried forward through multiple months."""
        engine = BacklogEngine()

        # Month 0: Create initial backlog
        result0 = engine.calculate(
            month_index=0,
            beginning_backlog=Decimal("0"),
            new_redemptions=Decimal("1000000"),
            redeemed_in_month=Decimal("500000"),
            deferral_reason="gate",
        )
        assert result0.ending_backlog == Decimal("500000")

        # Month 1: Carry forward backlog, add new redemptions, partial satisfaction
        result1 = engine.calculate(
            month_index=1,
            beginning_backlog=result0.ending_backlog,  # Cascade
            new_redemptions=Decimal("800000"),
            redeemed_in_month=Decimal("700000"),
            deferral_reason="gate",
        )
        assert result1.beginning_backlog == Decimal("500000")
        assert result1.total_redemptions_due == Decimal("1300000")
        assert result1.ending_backlog == Decimal("600000")

        # Month 2: Carry forward again
        result2 = engine.calculate(
            month_index=2,
            beginning_backlog=result1.ending_backlog,
            new_redemptions=Decimal("400000"),
            redeemed_in_month=Decimal("900000"),
            deferral_reason=None,
        )
        assert result2.beginning_backlog == Decimal("600000")
        assert result2.total_redemptions_due == Decimal("1000000")
        assert result2.ending_backlog == Decimal("100000")


class TestBacklogEngineZeroNewRedemptions:
    """Tests for zero new redemptions with existing backlog."""

    def test_zero_new_redemptions_with_backlog(self):
        """No new redemptions, but prior backlog exists."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=1,
            beginning_backlog=Decimal("500000"),
            new_redemptions=Decimal("0"),
            redeemed_in_month=Decimal("300000"),
            deferral_reason="insufficient_liquidity",
        )

        assert result.beginning_backlog == Decimal("500000")
        assert result.new_redemptions == Decimal("0")
        assert result.total_redemptions_due == Decimal("500000")
        assert result.redeemed_in_month == Decimal("300000")
        assert result.ending_backlog == Decimal("200000")
        assert result.deferral_reason == "insufficient_liquidity"

    def test_zero_new_redemptions_full_backlog_satisfaction(self):
        """Zero new redemptions, but full backlog satisfied."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=1,
            beginning_backlog=Decimal("300000"),
            new_redemptions=Decimal("0"),
            redeemed_in_month=Decimal("300000"),
            deferral_reason=None,
        )

        assert result.total_redemptions_due == Decimal("300000")
        assert result.ending_backlog == Decimal("0")
        assert result.deferral_reason is None


class TestBacklogEngineDeferralReasonLogic:
    """Tests for deferral reason handling."""

    def test_reason_retained_when_backlog_positive(self):
        """Deferral reason retained when ending backlog > 0."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=0,
            beginning_backlog=Decimal("0"),
            new_redemptions=Decimal("1000000"),
            redeemed_in_month=Decimal("600000"),
            deferral_reason="gate",
        )

        assert result.ending_backlog == Decimal("400000")
        assert result.deferral_reason == "gate"

    def test_reason_discarded_when_backlog_zero(self):
        """Deferral reason is None when ending backlog == 0, even if provided."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=0,
            beginning_backlog=Decimal("0"),
            new_redemptions=Decimal("1000000"),
            redeemed_in_month=Decimal("1000000"),
            deferral_reason="gate",  # Provided but ignored because no backlog
        )

        assert result.ending_backlog == Decimal("0")
        assert result.deferral_reason is None

    def test_reason_none_with_zero_backlog(self):
        """No reason needed when redemptions fully met."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=0,
            beginning_backlog=Decimal("0"),
            new_redemptions=Decimal("1000000"),
            redeemed_in_month=Decimal("1000000"),
            deferral_reason=None,
        )

        assert result.ending_backlog == Decimal("0")
        assert result.deferral_reason is None


class TestBacklogEngineValidation:
    """Tests for input validation."""

    def test_negative_month_index(self):
        """Negative month index raises ValueError."""
        engine = BacklogEngine()

        with pytest.raises(ValueError, match="month_index must be non-negative"):
            engine.calculate(
                month_index=-1,
                beginning_backlog=Decimal("0"),
                new_redemptions=Decimal("1000000"),
                redeemed_in_month=Decimal("500000"),
            )

    def test_negative_beginning_backlog(self):
        """Negative beginning backlog raises ValueError."""
        engine = BacklogEngine()

        with pytest.raises(ValueError, match="beginning_backlog must be non-negative"):
            engine.calculate(
                month_index=0,
                beginning_backlog=Decimal("-100000"),
                new_redemptions=Decimal("1000000"),
                redeemed_in_month=Decimal("500000"),
            )

    def test_negative_new_redemptions(self):
        """Negative new redemptions raises ValueError."""
        engine = BacklogEngine()

        with pytest.raises(ValueError, match="new_redemptions must be non-negative"):
            engine.calculate(
                month_index=0,
                beginning_backlog=Decimal("0"),
                new_redemptions=Decimal("-1000000"),
                redeemed_in_month=Decimal("500000"),
            )

    def test_negative_redeemed_in_month(self):
        """Negative redeemed amount raises ValueError."""
        engine = BacklogEngine()

        with pytest.raises(ValueError, match="redeemed_in_month must be non-negative"):
            engine.calculate(
                month_index=0,
                beginning_backlog=Decimal("0"),
                new_redemptions=Decimal("1000000"),
                redeemed_in_month=Decimal("-500000"),
            )

    def test_redeemed_exceeds_total_due(self):
        """Redeemed exceeding total due raises ValueError."""
        engine = BacklogEngine()

        with pytest.raises(
            ValueError, match="redeemed_in_month.*cannot exceed.*total_redemptions_due"
        ):
            engine.calculate(
                month_index=0,
                beginning_backlog=Decimal("300000"),
                new_redemptions=Decimal("700000"),
                redeemed_in_month=Decimal("2000000"),  # Exceeds 1M total
            )

    def test_empty_deferral_reason_rejected(self):
        """Empty string deferral reason raises ValueError."""
        engine = BacklogEngine()

        with pytest.raises(ValueError, match="deferral_reason must be non-empty"):
            engine.calculate(
                month_index=0,
                beginning_backlog=Decimal("0"),
                new_redemptions=Decimal("1000000"),
                redeemed_in_month=Decimal("500000"),
                deferral_reason="",
            )

    def test_whitespace_deferral_reason_rejected(self):
        """Whitespace-only deferral reason raises ValueError."""
        engine = BacklogEngine()

        with pytest.raises(ValueError, match="deferral_reason must be non-empty"):
            engine.calculate(
                month_index=0,
                beginning_backlog=Decimal("0"),
                new_redemptions=Decimal("1000000"),
                redeemed_in_month=Decimal("500000"),
                deferral_reason="   ",
            )


class TestBacklogEngineAccountingConsistency:
    """Tests for accounting consistency via BacklogState validation."""

    def test_total_redemptions_consistency(self):
        """BacklogState validates total_redemptions_due = beginning + new."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=0,
            beginning_backlog=Decimal("300000"),
            new_redemptions=Decimal("700000"),
            redeemed_in_month=Decimal("500000"),
            deferral_reason="gate",
        )

        # BacklogState model validates this
        assert result.total_redemptions_due == Decimal("1000000")
        assert result.beginning_backlog + result.new_redemptions == result.total_redemptions_due

    def test_ending_backlog_consistency(self):
        """BacklogState validates ending_backlog = total - redeemed."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=0,
            beginning_backlog=Decimal("200000"),
            new_redemptions=Decimal("800000"),
            redeemed_in_month=Decimal("700000"),
            deferral_reason="insufficient_liquidity",
        )

        # BacklogState model validates this
        assert result.ending_backlog == Decimal("300000")
        assert result.total_redemptions_due - result.redeemed_in_month == result.ending_backlog


class TestBacklogEngineStateless:
    """Tests for stateless and deterministic behavior."""

    def test_identical_inputs_identical_outputs(self):
        """Identical inputs always produce identical outputs."""
        engine = BacklogEngine()

        result1 = engine.calculate(
            month_index=1,
            beginning_backlog=Decimal("500000"),
            new_redemptions=Decimal("1000000"),
            redeemed_in_month=Decimal("900000"),
            deferral_reason="gate",
        )
        result2 = engine.calculate(
            month_index=1,
            beginning_backlog=Decimal("500000"),
            new_redemptions=Decimal("1000000"),
            redeemed_in_month=Decimal("900000"),
            deferral_reason="gate",
        )

        assert result1.month_index == result2.month_index
        assert result1.beginning_backlog == result2.beginning_backlog
        assert result1.new_redemptions == result2.new_redemptions
        assert result1.ending_backlog == result2.ending_backlog
        assert result1.deferral_reason == result2.deferral_reason

    def test_engine_reusable(self):
        """Engine can be reused for multiple calculations."""
        engine = BacklogEngine()

        for month in range(12):
            result = engine.calculate(
                month_index=month,
                beginning_backlog=Decimal("0"),
                new_redemptions=Decimal("100000"),
                redeemed_in_month=Decimal("100000"),
            )

            assert result.month_index == month
            assert result.ending_backlog == Decimal("0")


class TestBacklogEnginePrecision:
    """Tests for Decimal precision handling."""

    def test_decimal_precision_preserved(self):
        """Decimal precision is preserved in calculations."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=0,
            beginning_backlog=Decimal("123456.789"),
            new_redemptions=Decimal("987654.321"),
            redeemed_in_month=Decimal("500000.123"),
            deferral_reason="gate",
        )

        expected_total = Decimal("123456.789") + Decimal("987654.321")
        expected_ending = expected_total - Decimal("500000.123")

        assert result.total_redemptions_due == expected_total
        assert result.ending_backlog == expected_ending

    def test_small_amounts_precision(self):
        """Small Decimal amounts preserve precision."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=0,
            beginning_backlog=Decimal("0.01"),
            new_redemptions=Decimal("0.02"),
            redeemed_in_month=Decimal("0.015"),
            deferral_reason="gate",
        )

        assert result.total_redemptions_due == Decimal("0.03")
        assert result.ending_backlog == Decimal("0.015")


class TestBacklogEngineRealWorldScenarios:
    """Tests for realistic fund scenarios."""

    def test_large_fund_scenario(self):
        """Large fund with significant backlog."""
        engine = BacklogEngine()

        result = engine.calculate(
            month_index=3,
            beginning_backlog=Decimal("50000000"),  # 50M carry-forward
            new_redemptions=Decimal("30000000"),  # 30M new requests
            redeemed_in_month=Decimal("60000000"),  # Met most but not all
            deferral_reason="insufficient_liquidity",
        )

        assert result.total_redemptions_due == Decimal("80000000")
        assert result.ending_backlog == Decimal("20000000")
        assert result.deferral_reason == "insufficient_liquidity"

    def test_stress_scenario_cascading_backlog(self):
        """Stress scenario with backlog accumulation over months."""
        engine = BacklogEngine()
        current_backlog = Decimal("0")

        # Simulate 6 months of stress with decreasing redemption capacity
        redemption_rates = [
            (Decimal("10000000"), Decimal("8000000")),  # Month 0: 80%
            (Decimal("10000000"), Decimal("5000000")),  # Month 1: 50%
            (Decimal("10000000"), Decimal("3000000")),  # Month 2: 30%
            (Decimal("10000000"), Decimal("6000000")),  # Month 3: 60%
            (Decimal("10000000"), Decimal("7000000")),  # Month 4: 70%
            (Decimal("10000000"), Decimal("9000000")),  # Month 5: 90%
        ]

        for month, (new_redemptions, redeemed) in enumerate(redemption_rates):
            # Calculate provisional ending backlog to determine reason
            provisional_ending = current_backlog + new_redemptions - redeemed
            reason = "gate" if provisional_ending > Decimal("0") else None

            result = engine.calculate(
                month_index=month,
                beginning_backlog=current_backlog,
                new_redemptions=new_redemptions,
                redeemed_in_month=redeemed,
                deferral_reason=reason,
            )
            current_backlog = result.ending_backlog

        # Final backlog after stress scenario
        assert current_backlog >= Decimal("0")
