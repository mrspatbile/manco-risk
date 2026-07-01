"""Tests for private debt loan monitoring analytics.

Covers models, engine, and realistic scenarios.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.private_assets import (
    PrivateDebtEngine,
    PrivateDebtLoanInput,
    PrivateDebtLoanResult,
)


class TestPrivateDebtLoanInput:
    """Test PrivateDebtLoanInput model."""

    def test_valid_secured_loan(self) -> None:
        """Valid secured loan with all fields."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("5000000"),
            covenant_breached=False,
            collateral_value=Decimal("6000000"),
            interest_coverage_ratio=Decimal("2.5"),
            debt_service_coverage_ratio=Decimal("1.8"),
            leverage_ratio=Decimal("3.0"),
            loan_id="LOAN_DIRECT_001",
            methodology_version="MONITORING_v1.0",
        )

        assert loan.outstanding_balance == Decimal("5000000")
        assert loan.covenant_breached is False
        assert loan.collateral_value == Decimal("6000000")

    def test_valid_unsecured_loan(self) -> None:
        """Valid unsecured loan (no collateral)."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("2000000"),
            covenant_breached=False,
            interest_coverage_ratio=Decimal("1.5"),
        )

        assert loan.outstanding_balance == Decimal("2000000")
        assert loan.collateral_value is None

    def test_covenant_breached(self) -> None:
        """Loan with covenant breach and covenant name."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("3000000"),
            covenant_breached=True,
            covenant_name="Leverage Ratio Covenant",
            collateral_value=Decimal("3500000"),
        )

        assert loan.covenant_breached is True
        assert loan.covenant_name == "Leverage Ratio Covenant"

    def test_covenant_not_breached(self) -> None:
        """Loan without covenant breach."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("1000000"),
            covenant_breached=False,
        )

        assert loan.covenant_breached is False
        assert loan.covenant_name is None

    def test_zero_balance_allowed(self) -> None:
        """Zero outstanding balance allowed (paid down loan)."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("0"),
            covenant_breached=False,
        )

        assert loan.outstanding_balance == Decimal("0")

    def test_zero_collateral_allowed(self) -> None:
        """Zero collateral value allowed."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("1000000"),
            covenant_breached=False,
            collateral_value=Decimal("0"),
        )

        assert loan.collateral_value == Decimal("0")

    def test_negative_outstanding_balance_rejected(self) -> None:
        """Negative outstanding balance rejected."""
        with pytest.raises(ValueError, match="outstanding_balance must be non-negative"):
            PrivateDebtLoanInput(
                valuation_date=date(2024, 6, 30),
                outstanding_balance=Decimal("-1000000"),
                covenant_breached=False,
            )

    def test_negative_collateral_rejected(self) -> None:
        """Negative collateral value rejected."""
        with pytest.raises(ValueError, match="collateral_value must be non-negative"):
            PrivateDebtLoanInput(
                valuation_date=date(2024, 6, 30),
                outstanding_balance=Decimal("1000000"),
                covenant_breached=False,
                collateral_value=Decimal("-1000000"),
            )

    def test_negative_interest_coverage_rejected(self) -> None:
        """Negative interest coverage ratio rejected."""
        with pytest.raises(ValueError, match="interest_coverage_ratio must be non-negative"):
            PrivateDebtLoanInput(
                valuation_date=date(2024, 6, 30),
                outstanding_balance=Decimal("1000000"),
                covenant_breached=False,
                interest_coverage_ratio=Decimal("-1.5"),
            )

    def test_negative_dscr_rejected(self) -> None:
        """Negative debt service coverage ratio rejected."""
        with pytest.raises(ValueError, match="debt_service_coverage_ratio must be non-negative"):
            PrivateDebtLoanInput(
                valuation_date=date(2024, 6, 30),
                outstanding_balance=Decimal("1000000"),
                covenant_breached=False,
                debt_service_coverage_ratio=Decimal("-1.0"),
            )

    def test_negative_leverage_rejected(self) -> None:
        """Negative leverage ratio rejected."""
        with pytest.raises(ValueError, match="leverage_ratio must be non-negative"):
            PrivateDebtLoanInput(
                valuation_date=date(2024, 6, 30),
                outstanding_balance=Decimal("1000000"),
                covenant_breached=False,
                leverage_ratio=Decimal("-2.0"),
            )

    def test_empty_covenant_name_rejected(self) -> None:
        """Empty covenant name rejected."""
        with pytest.raises(ValueError, match="covenant_name must be non-empty"):
            PrivateDebtLoanInput(
                valuation_date=date(2024, 6, 30),
                outstanding_balance=Decimal("1000000"),
                covenant_breached=True,
                covenant_name="",
            )

    def test_decimal_precision_preserved(self) -> None:
        """Decimal precision is preserved exactly."""
        balance = Decimal("1234567.89")
        collateral = Decimal("2345678.90")
        icr = Decimal("1.234567")

        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=balance,
            covenant_breached=False,
            collateral_value=collateral,
            interest_coverage_ratio=icr,
        )

        assert loan.outstanding_balance == balance
        assert loan.collateral_value == collateral
        assert loan.interest_coverage_ratio == icr


class TestPrivateDebtLoanResult:
    """Test PrivateDebtLoanResult model."""

    def test_valid_result_with_ltv(self) -> None:
        """Valid result with loan-to-value calculated."""
        result = PrivateDebtLoanResult(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("5000000"),
            covenant_breached=False,
            collateral_value=Decimal("6000000"),
            loan_to_value=Decimal("0.833333"),
        )

        assert result.outstanding_balance == Decimal("5000000")
        assert result.loan_to_value == Decimal("0.833333")

    def test_result_with_none_ltv(self) -> None:
        """Result with None loan-to-value (no collateral)."""
        result = PrivateDebtLoanResult(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("2000000"),
            covenant_breached=False,
            loan_to_value=None,
        )

        assert result.outstanding_balance == Decimal("2000000")
        assert result.loan_to_value is None

    def test_result_with_covenant_breach(self) -> None:
        """Result with covenant breach details."""
        result = PrivateDebtLoanResult(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("3000000"),
            covenant_breached=True,
            covenant_name="Leverage Ratio",
            loan_id="LOAN_BREACH_001",
        )

        assert result.covenant_breached is True
        assert result.covenant_name == "Leverage Ratio"

    def test_negative_loan_to_value_rejected(self) -> None:
        """Negative loan-to-value rejected."""
        with pytest.raises(ValueError, match="loan_to_value must be non-negative"):
            PrivateDebtLoanResult(
                valuation_date=date(2024, 6, 30),
                outstanding_balance=Decimal("1000000"),
                covenant_breached=False,
                loan_to_value=Decimal("-0.5"),
            )

    def test_decimal_precision_preserved(self) -> None:
        """Decimal precision is preserved exactly."""
        balance = Decimal("1234567.89")
        ltv = Decimal("0.456789")

        result = PrivateDebtLoanResult(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=balance,
            covenant_breached=False,
            loan_to_value=ltv,
        )

        assert result.outstanding_balance == balance
        assert result.loan_to_value == ltv


class TestPrivateDebtEngine:
    """Test PrivateDebtEngine calculation logic."""

    def test_secured_loan_ltv_calculation(self) -> None:
        """Calculate loan-to-value for secured loan."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("5000000"),
            covenant_breached=False,
            collateral_value=Decimal("6000000"),
            interest_coverage_ratio=Decimal("2.5"),
            loan_id="LOAN_SECURED_001",
        )

        result = PrivateDebtEngine.analyze(loan)

        assert result.outstanding_balance == Decimal("5000000")
        assert result.collateral_value == Decimal("6000000")
        assert result.loan_to_value == Decimal("5000000") / Decimal("6000000")

    def test_unsecured_loan_none_ltv(self) -> None:
        """Unsecured loan returns None for loan-to-value."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("2000000"),
            covenant_breached=False,
        )

        result = PrivateDebtEngine.analyze(loan)

        assert result.outstanding_balance == Decimal("2000000")
        assert result.collateral_value is None
        assert result.loan_to_value is None

    def test_zero_collateral_none_ltv(self) -> None:
        """Zero collateral returns None loan-to-value."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("1000000"),
            covenant_breached=False,
            collateral_value=Decimal("0"),
        )

        result = PrivateDebtEngine.analyze(loan)

        assert result.loan_to_value is None

    def test_covenant_breach_passthrough(self) -> None:
        """Covenant breach status passes through unchanged."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("3000000"),
            covenant_breached=True,
            covenant_name="Leverage Covenant",
            collateral_value=Decimal("3500000"),
        )

        result = PrivateDebtEngine.analyze(loan)

        assert result.covenant_breached is True
        assert result.covenant_name == "Leverage Covenant"

    def test_ratios_passthrough(self) -> None:
        """All ratio metrics pass through unchanged."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("4000000"),
            covenant_breached=False,
            collateral_value=Decimal("5000000"),
            interest_coverage_ratio=Decimal("2.2"),
            debt_service_coverage_ratio=Decimal("1.5"),
            leverage_ratio=Decimal("2.8"),
        )

        result = PrivateDebtEngine.analyze(loan)

        assert result.interest_coverage_ratio == Decimal("2.2")
        assert result.debt_service_coverage_ratio == Decimal("1.5")
        assert result.leverage_ratio == Decimal("2.8")

    def test_decimal_precision_in_ltv(self) -> None:
        """Decimal precision preserved in LTV calculation."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("2"),
            covenant_breached=False,
            collateral_value=Decimal("3"),
        )

        result = PrivateDebtEngine.analyze(loan)

        assert result.loan_to_value == Decimal("2") / Decimal("3")
        assert result.loan_to_value < Decimal("0.67")


class TestRealisticExamples:
    """Realistic private debt scenarios."""

    def test_direct_lending_loan(self) -> None:
        """Direct lending loan with full monitoring."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("50000000"),
            covenant_breached=False,
            collateral_value=Decimal("60000000"),
            interest_coverage_ratio=Decimal("3.0"),
            debt_service_coverage_ratio=Decimal("2.5"),
            leverage_ratio=Decimal("2.5"),
            loan_id="DIRECT_LENDING_2023_A",
            methodology_version="MONITORING_v2.0",
        )

        result = PrivateDebtEngine.analyze(loan)

        assert result.outstanding_balance == Decimal("50000000")
        assert result.loan_to_value == Decimal("50000000") / Decimal("60000000")
        assert result.interest_coverage_ratio == Decimal("3.0")
        assert result.covenant_breached is False

    def test_infrastructure_debt_covenant_breach(self) -> None:
        """Infrastructure debt with covenant breach."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("20000000"),
            covenant_breached=True,
            covenant_name="DSCR < 1.25x",
            collateral_value=Decimal("25000000"),
            interest_coverage_ratio=Decimal("1.8"),
            debt_service_coverage_ratio=Decimal("1.1"),
            leverage_ratio=Decimal("2.0"),
            loan_id="INFRA_DEBT_TOLL_ROAD",
        )

        result = PrivateDebtEngine.analyze(loan)

        assert result.covenant_breached is True
        assert result.covenant_name == "DSCR < 1.25x"
        assert result.debt_service_coverage_ratio == Decimal("1.1")
        assert result.loan_to_value == Decimal("0.8")

    def test_mezzanine_loan_no_collateral(self) -> None:
        """Mezzanine loan without collateral (unsecured)."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("10000000"),
            covenant_breached=False,
            interest_coverage_ratio=Decimal("1.3"),
            debt_service_coverage_ratio=Decimal("1.2"),
            leverage_ratio=Decimal("3.5"),
            loan_id="MEZZ_LOAN_PRIVATE_EQUITY",
        )

        result = PrivateDebtEngine.analyze(loan)

        assert result.outstanding_balance == Decimal("10000000")
        assert result.collateral_value is None
        assert result.loan_to_value is None
        assert result.leverage_ratio == Decimal("3.5")

    def test_real_estate_debt_stressed(self) -> None:
        """Real estate debt under stress with declining metrics."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("15000000"),
            covenant_breached=False,
            collateral_value=Decimal("18000000"),
            interest_coverage_ratio=Decimal("1.4"),
            debt_service_coverage_ratio=Decimal("1.1"),
            leverage_ratio=Decimal("2.2"),
            loan_id="RE_DEBT_OFFICE_TOWER",
        )

        result = PrivateDebtEngine.analyze(loan)

        assert result.loan_to_value == Decimal("15000000") / Decimal("18000000")
        assert result.loan_to_value < Decimal("0.85")
        assert result.interest_coverage_ratio == Decimal("1.4")
        assert result.debt_service_coverage_ratio == Decimal("1.1")

    def test_acquisition_financing_healthy(self) -> None:
        """Acquisition financing with healthy metrics."""
        loan = PrivateDebtLoanInput(
            valuation_date=date(2024, 6, 30),
            outstanding_balance=Decimal("75000000"),
            covenant_breached=False,
            collateral_value=Decimal("100000000"),
            interest_coverage_ratio=Decimal("2.8"),
            debt_service_coverage_ratio=Decimal("2.2"),
            leverage_ratio=Decimal("2.1"),
            loan_id="ACQ_FINANCING_PLATFORM",
            methodology_version="MONITORING_v2.0",
        )

        result = PrivateDebtEngine.analyze(loan)

        assert result.loan_to_value == Decimal("0.75")
        assert result.interest_coverage_ratio == Decimal("2.8")
        assert result.debt_service_coverage_ratio == Decimal("2.2")
        assert result.covenant_breached is False
