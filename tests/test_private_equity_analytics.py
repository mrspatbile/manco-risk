"""Tests for private equity analytics.

Covers models, engine, and realistic scenarios.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.private_assets import (
    PrivateEquityAnalyticsResult,
    PrivateEquityCashFlow,
    PrivateEquityEngine,
    PrivateEquityInvestmentInput,
)


class TestPrivateEquityCashFlow:
    """Test PrivateEquityCashFlow model."""

    def test_valid_paid_in_flow(self) -> None:
        """Valid paid-in cash flow."""
        cf = PrivateEquityCashFlow(
            flow_amount=Decimal("1000000"),
            flow_date=date(2020, 1, 15),
            flow_type="paid_in",
        )

        assert cf.flow_amount == Decimal("1000000")
        assert cf.flow_date == date(2020, 1, 15)
        assert cf.flow_type == "paid_in"

    def test_valid_distribution_flow(self) -> None:
        """Valid distribution cash flow."""
        cf = PrivateEquityCashFlow(
            flow_amount=Decimal("500000"),
            flow_date=date(2023, 6, 30),
            flow_type="distribution",
        )

        assert cf.flow_amount == Decimal("500000")
        assert cf.flow_type == "distribution"

    def test_flow_type_case_insensitive(self) -> None:
        """Flow type is normalized to lowercase."""
        cf = PrivateEquityCashFlow(
            flow_amount=Decimal("100000"),
            flow_date=date(2021, 1, 1),
            flow_type="PAID_IN",
        )

        assert cf.flow_type == "paid_in"

    def test_negative_amount_rejected(self) -> None:
        """Negative flow amount is rejected."""
        with pytest.raises(ValueError, match="flow_amount must be non-negative"):
            PrivateEquityCashFlow(
                flow_amount=Decimal("-100000"),
                flow_date=date(2020, 1, 1),
                flow_type="paid_in",
            )

    def test_invalid_flow_type_rejected(self) -> None:
        """Invalid flow type is rejected."""
        with pytest.raises(ValueError, match="flow_type must be 'paid_in' or 'distribution'"):
            PrivateEquityCashFlow(
                flow_amount=Decimal("100000"),
                flow_date=date(2020, 1, 1),
                flow_type="redemption",
            )

    def test_zero_amount_allowed(self) -> None:
        """Zero flow amount is allowed."""
        cf = PrivateEquityCashFlow(
            flow_amount=Decimal("0"),
            flow_date=date(2020, 1, 1),
            flow_type="paid_in",
        )

        assert cf.flow_amount == Decimal("0")

    def test_decimal_precision_preserved(self) -> None:
        """Decimal precision is preserved exactly."""
        amount = Decimal("1234567.89")
        cf = PrivateEquityCashFlow(
            flow_amount=amount,
            flow_date=date(2020, 1, 1),
            flow_type="paid_in",
        )

        assert cf.flow_amount == amount
        assert str(cf.flow_amount) == "1234567.89"

    def test_equality(self) -> None:
        """Cash flows with same attributes are equal."""
        cf1 = PrivateEquityCashFlow(
            flow_amount=Decimal("100000"),
            flow_date=date(2020, 1, 1),
            flow_type="paid_in",
        )
        cf2 = PrivateEquityCashFlow(
            flow_amount=Decimal("100000"),
            flow_date=date(2020, 1, 1),
            flow_type="paid_in",
        )

        assert cf1 == cf2

    def test_inequality(self) -> None:
        """Cash flows with different attributes are not equal."""
        cf1 = PrivateEquityCashFlow(
            flow_amount=Decimal("100000"),
            flow_date=date(2020, 1, 1),
            flow_type="paid_in",
        )
        cf2 = PrivateEquityCashFlow(
            flow_amount=Decimal("200000"),
            flow_date=date(2020, 1, 1),
            flow_type="paid_in",
        )

        assert cf1 != cf2


class TestPrivateEquityInvestmentInput:
    """Test PrivateEquityInvestmentInput model."""

    def test_valid_investment_input(self) -> None:
        """Valid investment with cash flows."""
        cf = PrivateEquityCashFlow(
            flow_amount=Decimal("1000000"),
            flow_date=date(2020, 1, 1),
            flow_type="paid_in",
        )
        input_data = PrivateEquityInvestmentInput(
            cash_flows=[cf],
            residual_value=Decimal("1500000"),
        )

        assert len(input_data.cash_flows) == 1
        assert input_data.residual_value == Decimal("1500000")
        assert input_data.investment_id is None

    def test_investment_with_id(self) -> None:
        """Investment with optional ID."""
        input_data = PrivateEquityInvestmentInput(
            cash_flows=[],
            residual_value=Decimal("0"),
            investment_id="FUND_2020_001",
        )

        assert input_data.investment_id == "FUND_2020_001"

    def test_empty_cash_flows_allowed(self) -> None:
        """Empty cash flow list is allowed."""
        input_data = PrivateEquityInvestmentInput(
            cash_flows=[],
            residual_value=Decimal("100000"),
        )

        assert input_data.cash_flows == []
        assert input_data.residual_value == Decimal("100000")

    def test_negative_residual_value_rejected(self) -> None:
        """Negative residual value is rejected."""
        with pytest.raises(ValueError, match="residual_value must be non-negative"):
            PrivateEquityInvestmentInput(
                cash_flows=[],
                residual_value=Decimal("-100000"),
            )

    def test_zero_residual_value_allowed(self) -> None:
        """Zero residual value is allowed."""
        input_data = PrivateEquityInvestmentInput(
            cash_flows=[],
            residual_value=Decimal("0"),
        )

        assert input_data.residual_value == Decimal("0")

    def test_decimal_precision_preserved(self) -> None:
        """Decimal precision in residual_value is preserved."""
        residual = Decimal("1234567.89")
        input_data = PrivateEquityInvestmentInput(
            cash_flows=[],
            residual_value=residual,
        )

        assert input_data.residual_value == residual


class TestPrivateEquityAnalyticsResult:
    """Test PrivateEquityAnalyticsResult model."""

    def test_valid_result_with_all_metrics(self) -> None:
        """Valid result with all metrics populated."""
        result = PrivateEquityAnalyticsResult(
            dpi=Decimal("0.50"),
            rvpi=Decimal("1.00"),
            tvpi=Decimal("1.50"),
            moic=Decimal("1.50"),
            total_paid_in=Decimal("1000000"),
            total_distributed=Decimal("500000"),
            residual_value=Decimal("1000000"),
        )

        assert result.dpi == Decimal("0.50")
        assert result.rvpi == Decimal("1.00")
        assert result.tvpi == Decimal("1.50")
        assert result.moic == Decimal("1.50")

    def test_result_with_none_metrics(self) -> None:
        """Result with None metrics (zero paid-in)."""
        result = PrivateEquityAnalyticsResult(
            dpi=None,
            rvpi=None,
            tvpi=None,
            moic=None,
            total_paid_in=Decimal("0"),
            total_distributed=Decimal("0"),
            residual_value=Decimal("0"),
        )

        assert result.dpi is None
        assert result.rvpi is None
        assert result.tvpi is None
        assert result.moic is None

    def test_negative_dpi_rejected(self) -> None:
        """Negative DPI is rejected."""
        with pytest.raises(ValueError, match="dpi must be non-negative"):
            PrivateEquityAnalyticsResult(
                dpi=Decimal("-0.50"),
                rvpi=None,
                tvpi=None,
                moic=None,
                total_paid_in=Decimal("1000000"),
                total_distributed=Decimal("0"),
                residual_value=Decimal("0"),
            )

    def test_negative_rvpi_rejected(self) -> None:
        """Negative RVPI is rejected."""
        with pytest.raises(ValueError, match="rvpi must be non-negative"):
            PrivateEquityAnalyticsResult(
                dpi=None,
                rvpi=Decimal("-0.50"),
                tvpi=None,
                moic=None,
                total_paid_in=Decimal("1000000"),
                total_distributed=Decimal("0"),
                residual_value=Decimal("0"),
            )

    def test_negative_tvpi_rejected(self) -> None:
        """Negative TVPI is rejected."""
        with pytest.raises(ValueError, match="tvpi must be non-negative"):
            PrivateEquityAnalyticsResult(
                dpi=None,
                rvpi=None,
                tvpi=Decimal("-0.50"),
                moic=None,
                total_paid_in=Decimal("1000000"),
                total_distributed=Decimal("0"),
                residual_value=Decimal("0"),
            )

    def test_negative_moic_rejected(self) -> None:
        """Negative MOIC is rejected."""
        with pytest.raises(ValueError, match="moic must be non-negative"):
            PrivateEquityAnalyticsResult(
                dpi=None,
                rvpi=None,
                tvpi=None,
                moic=Decimal("-0.50"),
                total_paid_in=Decimal("1000000"),
                total_distributed=Decimal("0"),
                residual_value=Decimal("0"),
            )

    def test_decimal_precision_preserved(self) -> None:
        """Decimal precision in all fields is preserved."""
        dpi = Decimal("0.123456789")
        result = PrivateEquityAnalyticsResult(
            dpi=dpi,
            rvpi=None,
            tvpi=None,
            moic=None,
            total_paid_in=Decimal("1000000"),
            total_distributed=Decimal("123456.789"),
            residual_value=Decimal("0.123456789"),
        )

        assert result.dpi == dpi
        assert result.total_distributed == Decimal("123456.789")
        assert result.residual_value == Decimal("0.123456789")

    def test_equality(self) -> None:
        """Results with same values are equal."""
        result1 = PrivateEquityAnalyticsResult(
            dpi=Decimal("1.50"),
            rvpi=Decimal("2.00"),
            tvpi=Decimal("3.50"),
            moic=Decimal("3.50"),
            total_paid_in=Decimal("1000000"),
            total_distributed=Decimal("1500000"),
            residual_value=Decimal("2000000"),
        )
        result2 = PrivateEquityAnalyticsResult(
            dpi=Decimal("1.50"),
            rvpi=Decimal("2.00"),
            tvpi=Decimal("3.50"),
            moic=Decimal("3.50"),
            total_paid_in=Decimal("1000000"),
            total_distributed=Decimal("1500000"),
            residual_value=Decimal("2000000"),
        )

        assert result1 == result2


class TestPrivateEquityEngine:
    """Test PrivateEquityEngine calculation logic."""

    def test_simple_buyout_scenario(self) -> None:
        """Simple buyout with contributions, distributions, and residual value."""
        cf1 = PrivateEquityCashFlow(
            flow_amount=Decimal("1000000"),
            flow_date=date(2020, 1, 1),
            flow_type="paid_in",
        )
        cf2 = PrivateEquityCashFlow(
            flow_amount=Decimal("500000"),
            flow_date=date(2023, 6, 30),
            flow_type="distribution",
        )

        investment = PrivateEquityInvestmentInput(
            cash_flows=[cf1, cf2],
            residual_value=Decimal("1000000"),
        )

        result = PrivateEquityEngine.analyze(investment)

        assert result.total_paid_in == Decimal("1000000")
        assert result.total_distributed == Decimal("500000")
        assert result.residual_value == Decimal("1000000")
        assert result.dpi == Decimal("0.5")
        assert result.rvpi == Decimal("1.0")
        assert result.tvpi == Decimal("1.5")
        assert result.moic == Decimal("1.5")

    def test_zero_paid_in_capital(self) -> None:
        """No paid-in capital results in None metrics."""
        investment = PrivateEquityInvestmentInput(
            cash_flows=[],
            residual_value=Decimal("100000"),
        )

        result = PrivateEquityEngine.analyze(investment)

        assert result.total_paid_in == Decimal("0")
        assert result.dpi is None
        assert result.rvpi is None
        assert result.tvpi is None
        assert result.moic is None

    def test_zero_distributions(self) -> None:
        """No distributions, only residual value."""
        cf = PrivateEquityCashFlow(
            flow_amount=Decimal("1000000"),
            flow_date=date(2020, 1, 1),
            flow_type="paid_in",
        )

        investment = PrivateEquityInvestmentInput(
            cash_flows=[cf],
            residual_value=Decimal("1500000"),
        )

        result = PrivateEquityEngine.analyze(investment)

        assert result.total_distributed == Decimal("0")
        assert result.dpi == Decimal("0")
        assert result.rvpi == Decimal("1.5")
        assert result.tvpi == Decimal("1.5")
        assert result.moic == Decimal("1.5")

    def test_zero_residual_value(self) -> None:
        """No residual value, only distributions."""
        cf1 = PrivateEquityCashFlow(
            flow_amount=Decimal("1000000"),
            flow_date=date(2020, 1, 1),
            flow_type="paid_in",
        )
        cf2 = PrivateEquityCashFlow(
            flow_amount=Decimal("1500000"),
            flow_date=date(2024, 6, 30),
            flow_type="distribution",
        )

        investment = PrivateEquityInvestmentInput(
            cash_flows=[cf1, cf2],
            residual_value=Decimal("0"),
        )

        result = PrivateEquityEngine.analyze(investment)

        assert result.residual_value == Decimal("0")
        assert result.dpi == Decimal("1.5")
        assert result.rvpi == Decimal("0")
        assert result.tvpi == Decimal("1.5")
        assert result.moic == Decimal("1.5")

    def test_multiple_contributions_and_distributions(self) -> None:
        """Multiple contributions and distributions over time."""
        cf1 = PrivateEquityCashFlow(
            flow_amount=Decimal("500000"),
            flow_date=date(2020, 1, 1),
            flow_type="paid_in",
        )
        cf2 = PrivateEquityCashFlow(
            flow_amount=Decimal("500000"),
            flow_date=date(2021, 1, 1),
            flow_type="paid_in",
        )
        cf3 = PrivateEquityCashFlow(
            flow_amount=Decimal("300000"),
            flow_date=date(2022, 6, 30),
            flow_type="distribution",
        )
        cf4 = PrivateEquityCashFlow(
            flow_amount=Decimal("600000"),
            flow_date=date(2023, 12, 31),
            flow_type="distribution",
        )

        investment = PrivateEquityInvestmentInput(
            cash_flows=[cf1, cf2, cf3, cf4],
            residual_value=Decimal("800000"),
        )

        result = PrivateEquityEngine.analyze(investment)

        assert result.total_paid_in == Decimal("1000000")
        assert result.total_distributed == Decimal("900000")
        assert result.dpi == Decimal("0.9")
        assert result.rvpi == Decimal("0.8")
        assert result.tvpi == Decimal("1.7")
        assert result.moic == Decimal("1.7")

    def test_decimal_precision_in_calculations(self) -> None:
        """Decimal precision is preserved in calculations."""
        cf = PrivateEquityCashFlow(
            flow_amount=Decimal("3"),
            flow_date=date(2020, 1, 1),
            flow_type="paid_in",
        )

        investment = PrivateEquityInvestmentInput(
            cash_flows=[cf],
            residual_value=Decimal("1"),
        )

        result = PrivateEquityEngine.analyze(investment)

        # 1/3 = 0.333... (repeating)
        assert result.rvpi == Decimal("1") / Decimal("3")
        assert result.rvpi < Decimal("0.334")
        assert result.rvpi > Decimal("0.333")


class TestRealisticExamples:
    """Realistic private equity scenarios."""

    def test_successful_buyout(self) -> None:
        """Successful buyout with strong returns."""
        cf1 = PrivateEquityCashFlow(
            flow_amount=Decimal("10000000"),
            flow_date=date(2015, 3, 1),
            flow_type="paid_in",
        )
        cf2 = PrivateEquityCashFlow(
            flow_amount=Decimal("5000000"),
            flow_date=date(2019, 6, 30),
            flow_type="distribution",
        )
        cf3 = PrivateEquityCashFlow(
            flow_amount=Decimal("15000000"),
            flow_date=date(2023, 12, 31),
            flow_type="distribution",
        )

        investment = PrivateEquityInvestmentInput(
            cash_flows=[cf1, cf2, cf3],
            residual_value=Decimal("5000000"),
            investment_id="BUYOUT_2015_A",
        )

        result = PrivateEquityEngine.analyze(investment)

        assert result.total_paid_in == Decimal("10000000")
        assert result.total_distributed == Decimal("20000000")
        assert result.dpi == Decimal("2.0")
        assert result.tvpi == Decimal("2.5")
        assert result.moic == Decimal("2.5")

    def test_fund_with_remaining_nav(self) -> None:
        """Fund in earlier stages with significant remaining NAV."""
        cf1 = PrivateEquityCashFlow(
            flow_amount=Decimal("5000000"),
            flow_date=date(2021, 1, 1),
            flow_type="paid_in",
        )
        cf2 = PrivateEquityCashFlow(
            flow_amount=Decimal("1000000"),
            flow_date=date(2022, 6, 30),
            flow_type="distribution",
        )

        investment = PrivateEquityInvestmentInput(
            cash_flows=[cf1, cf2],
            residual_value=Decimal("6000000"),
            investment_id="FUND_2021_B",
        )

        result = PrivateEquityEngine.analyze(investment)

        assert result.total_paid_in == Decimal("5000000")
        assert result.total_distributed == Decimal("1000000")
        assert result.dpi == Decimal("0.2")
        assert result.rvpi == Decimal("1.2")
        assert result.tvpi == Decimal("1.4")
        assert result.moic == Decimal("1.4")

    def test_underperforming_investment(self) -> None:
        """Underperforming investment with losses."""
        cf = PrivateEquityCashFlow(
            flow_amount=Decimal("2000000"),
            flow_date=date(2018, 1, 1),
            flow_type="paid_in",
        )

        investment = PrivateEquityInvestmentInput(
            cash_flows=[cf],
            residual_value=Decimal("1000000"),
            investment_id="LOSS_2018_C",
        )

        result = PrivateEquityEngine.analyze(investment)

        assert result.total_paid_in == Decimal("2000000")
        assert result.tvpi == Decimal("0.5")
        assert result.moic == Decimal("0.5")
        assert result.tvpi < Decimal("1.0")

    def test_large_fund_example(self) -> None:
        """Large fund with multiple investments."""
        cf1 = PrivateEquityCashFlow(
            flow_amount=Decimal("100000000"),
            flow_date=date(2010, 1, 1),
            flow_type="paid_in",
        )
        cf2 = PrivateEquityCashFlow(
            flow_amount=Decimal("150000000"),
            flow_date=date(2018, 6, 30),
            flow_type="distribution",
        )

        investment = PrivateEquityInvestmentInput(
            cash_flows=[cf1, cf2],
            residual_value=Decimal("75000000"),
            investment_id="MEGA_FUND_2010",
        )

        result = PrivateEquityEngine.analyze(investment)

        assert result.total_paid_in == Decimal("100000000")
        assert result.dpi == Decimal("1.5")
        assert result.rvpi == Decimal("0.75")
        assert result.tvpi == Decimal("2.25")
