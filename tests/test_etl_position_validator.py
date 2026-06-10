"""Tests for ETL position validation framework."""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.etl import PositionInput, PositionValidator
from manco_risk.etl.position_validator import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)


class TestValidationTypes:
    """Tests for validation result types."""

    def test_validation_severity_enum_values(self) -> None:
        """ValidationSeverity enum has WARNING and ERROR."""
        assert ValidationSeverity.WARNING.value == "warning"
        assert ValidationSeverity.ERROR.value == "error"

    def test_validation_issue_is_immutable(self) -> None:
        """ValidationIssue is frozen."""
        issue = ValidationIssue(
            field="quantity",
            severity=ValidationSeverity.WARNING,
            code="ZERO_QUANTITY",
            message="Test message",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            issue.field = "modified"

    def test_validation_issue_structure(self) -> None:
        """ValidationIssue contains field, severity, code, message."""
        issue = ValidationIssue(
            field="market_value",
            severity=ValidationSeverity.ERROR,
            code="NEGATIVE_MARKET_VALUE",
            message="Market value cannot be negative",
        )

        assert issue.field == "market_value"
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.code == "NEGATIVE_MARKET_VALUE"
        assert issue.message == "Market value cannot be negative"

    def test_validation_result_is_immutable(self) -> None:
        """ValidationResult is frozen."""
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="EUR",
        )

        result = ValidationResult(
            position_input=position,
            source_position_identifier="POS-001",
            isin="IE00B4L5Y983",
            issues=[],
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            result.isin = "modified"

    def test_validation_result_is_valid_no_issues(self) -> None:
        """is_valid returns True when no issues exist."""
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="EUR",
        )

        result = ValidationResult(
            position_input=position,
            source_position_identifier=None,
            isin="IE00B4L5Y983",
            issues=[],
        )

        assert result.is_valid is True
        assert result.has_warnings is False

    def test_validation_result_is_valid_warnings_only(self) -> None:
        """is_valid returns True when only WARNING issues exist."""
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("0"),
            market_value=Decimal("12500"),
            currency="EUR",
        )

        warning = ValidationIssue(
            field="quantity",
            severity=ValidationSeverity.WARNING,
            code="ZERO_QUANTITY",
            message="Quantity is zero",
        )

        result = ValidationResult(
            position_input=position,
            source_position_identifier=None,
            isin="IE00B4L5Y983",
            issues=[warning],
        )

        assert result.is_valid is True
        assert result.has_warnings is True

    def test_validation_result_is_valid_with_error(self) -> None:
        """is_valid returns False when ERROR issues exist."""
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("-500"),
            currency="EUR",
        )

        error = ValidationIssue(
            field="market_value",
            severity=ValidationSeverity.ERROR,
            code="NEGATIVE_MARKET_VALUE",
            message="Market value is negative",
        )

        result = ValidationResult(
            position_input=position,
            source_position_identifier=None,
            isin="IE00B4L5Y983",
            issues=[error],
        )

        assert result.is_valid is False
        assert result.has_warnings is False


class TestPositionValidator:
    """Tests for PositionValidator."""

    def test_valid_position_no_issues(self) -> None:
        """Valid position generates empty issues list."""
        validator = PositionValidator()

        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="EUR",
        )

        results = validator.validate_positions([position])

        assert len(results) == 1
        assert results[0].is_valid is True
        assert len(results[0].issues) == 0

    def test_zero_quantity_warning(self) -> None:
        """Zero quantity generates ZERO_QUANTITY warning."""
        validator = PositionValidator()

        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("0"),
            market_value=Decimal("12500"),
            currency="EUR",
        )

        results = validator.validate_positions([position])

        assert len(results[0].issues) == 1
        assert results[0].issues[0].field == "quantity"
        assert results[0].issues[0].severity == ValidationSeverity.WARNING
        assert results[0].issues[0].code == "ZERO_QUANTITY"

    def test_zero_market_value_warning(self) -> None:
        """Zero market value generates ZERO_MARKET_VALUE warning."""
        validator = PositionValidator()

        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("0"),
            currency="EUR",
        )

        results = validator.validate_positions([position])

        assert len(results[0].issues) == 1
        assert results[0].issues[0].field == "market_value"
        assert results[0].issues[0].severity == ValidationSeverity.WARNING
        assert results[0].issues[0].code == "ZERO_MARKET_VALUE"

    def test_negative_market_value_error(self) -> None:
        """Negative market value generates NEGATIVE_MARKET_VALUE error."""
        validator = PositionValidator()

        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("-500"),
            currency="EUR",
        )

        results = validator.validate_positions([position])

        assert len(results[0].issues) == 1
        assert results[0].issues[0].field == "market_value"
        assert results[0].issues[0].severity == ValidationSeverity.ERROR
        assert results[0].issues[0].code == "NEGATIVE_MARKET_VALUE"
        assert results[0].is_valid is False

    def test_collect_all_issues(self) -> None:
        """Validator collects all issues; does not fail fast."""
        validator = PositionValidator()

        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("0"),
            market_value=Decimal("0"),
            currency="EUR",
        )

        results = validator.validate_positions([position])

        assert len(results[0].issues) == 2
        codes = {issue.code for issue in results[0].issues}
        assert codes == {"ZERO_QUANTITY", "ZERO_MARKET_VALUE"}

    def test_negative_quantity_allowed(self) -> None:
        """Negative quantity (short position) is allowed."""
        validator = PositionValidator()

        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("-50"),
            market_value=Decimal("6250"),
            currency="EUR",
        )

        results = validator.validate_positions([position])

        assert results[0].is_valid is True
        assert len(results[0].issues) == 0

    def test_zero_quantity_and_negative_market_value(self) -> None:
        """Validator collects both zero quantity warning and negative market value error."""
        validator = PositionValidator()

        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("0"),
            market_value=Decimal("-100"),
            currency="EUR",
        )

        results = validator.validate_positions([position])

        assert len(results[0].issues) == 2
        assert results[0].is_valid is False  # ERROR present
        assert results[0].has_warnings is True

        severities = [issue.severity for issue in results[0].issues]
        assert ValidationSeverity.ERROR in severities
        assert ValidationSeverity.WARNING in severities

    def test_multiple_positions(self) -> None:
        """Validator processes multiple positions and returns result per position."""
        validator = PositionValidator()

        positions = [
            PositionInput(
                fund_name="Test Fund",
                valuation_date=date(2025, 1, 15),
                isin="IE00B4L5Y983",
                quantity=Decimal("100"),
                market_value=Decimal("12500"),
                currency="EUR",
            ),
            PositionInput(
                fund_name="Test Fund",
                valuation_date=date(2025, 1, 15),
                isin="US0378331005",
                quantity=Decimal("0"),
                market_value=Decimal("8000"),
                currency="USD",
            ),
            PositionInput(
                fund_name="Test Fund",
                valuation_date=date(2025, 1, 15),
                isin="DE0005933931",
                quantity=Decimal("50"),
                market_value=Decimal("-1000"),
                currency="EUR",
            ),
        ]

        results = validator.validate_positions(positions)

        assert len(results) == 3
        assert results[0].is_valid is True
        assert len(results[0].issues) == 0

        assert results[1].is_valid is True
        assert results[1].has_warnings is True
        assert len(results[1].issues) == 1

        assert results[2].is_valid is False
        assert len(results[2].issues) == 1
        assert results[2].issues[0].code == "NEGATIVE_MARKET_VALUE"
