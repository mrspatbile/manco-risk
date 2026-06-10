"""Position validation framework for manco-risk.

Responsibilities:
- Define validation result types (severity, issue, result)
- Implement position validation engine
- Collect all validation issues per position
- Provide immutable result objects

Notes:
- Validation is separate from parsing (MRS-131) and enrichment (MRS-133)
- All checks run; caller decides how to handle results
- Severity levels: WARNING (non-blocking), ERROR (blocking)
- Immutable Pydantic v2 models for consistency with PositionInput
"""

from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict

from manco_risk.etl.position_loader import PositionInput


class ValidationSeverity(str, Enum):
    """Validation issue severity level."""

    WARNING = "warning"
    ERROR = "error"


class ValidationIssue(BaseModel):
    """Single validation issue found in a position.

    Fields:
    - field: Position field that triggered the issue
    - severity: WARNING or ERROR
    - code: Machine-readable issue code
    - message: Human-readable description
    """

    field: str
    severity: ValidationSeverity
    code: str
    message: str

    model_config = ConfigDict(frozen=True)


class ValidationResult(BaseModel):
    """Validation result for a single position input.

    Fields:
    - position_input: Original validated position input
    - source_position_identifier: Position ID from source system (if available)
    - isin: Position ISIN
    - issues: List of validation issues found (empty if all valid)

    Properties:
    - is_valid: True if no ERROR issues exist
    - has_warnings: True if any WARNING issues exist
    """

    position_input: PositionInput
    source_position_identifier: Optional[str]
    isin: str
    issues: list[ValidationIssue]

    model_config = ConfigDict(frozen=True)

    @property
    def is_valid(self) -> bool:
        """Position is valid if no ERROR severity issues."""
        return not any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Position has at least one WARNING severity issue."""
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)


class PositionValidator:
    """Validate position inputs against business rules.

    Collects all validation issues per position without failing fast.
    Caller decides whether to block persistence or log issues.
    """

    def validate_positions(self, position_inputs: list[PositionInput]) -> list[ValidationResult]:
        """Validate all positions and return results.

        Parameters
        ----------
        position_inputs : list[PositionInput]
            Validated position input records from CSV loader.

        Returns
        -------
        list[ValidationResult]
            One result per input position, containing all issues found.
            Empty issues list means position passed all checks.

        Notes
        -----
        All checks run for all positions. Caller decides how to handle results.
        """
        results: list[ValidationResult] = []

        for position_input in position_inputs:
            issues = self._validate_single_position(position_input)
            result = ValidationResult(
                position_input=position_input,
                source_position_identifier=position_input.source_position_identifier,
                isin=position_input.isin,
                issues=issues,
            )
            results.append(result)

        return results

    def _validate_single_position(self, position_input: PositionInput) -> list[ValidationIssue]:
        """Run all checks on a single position.

        Parameters
        ----------
        position_input : PositionInput
            Position to validate.

        Returns
        -------
        list[ValidationIssue]
            All issues found. Empty list if all checks pass.
        """
        issues: list[ValidationIssue] = []

        # Check 1: Zero quantity
        if position_input.quantity == Decimal("0"):
            issues.append(
                ValidationIssue(
                    field="quantity",
                    severity=ValidationSeverity.WARNING,
                    code="ZERO_QUANTITY",
                    message="Quantity is zero; position may be closed or unwound",
                )
            )

        # Check 2: Zero market value
        if position_input.market_value == Decimal("0"):
            issues.append(
                ValidationIssue(
                    field="market_value",
                    severity=ValidationSeverity.WARNING,
                    code="ZERO_MARKET_VALUE",
                    message="Market value is zero; position may be worthless or data entry anomaly",
                )
            )

        # Check 3: Negative market value
        if position_input.market_value < Decimal("0"):
            issues.append(
                ValidationIssue(
                    field="market_value",
                    severity=ValidationSeverity.ERROR,
                    code="NEGATIVE_MARKET_VALUE",
                    message="Market value is negative; expected non-negative for Phase 1 position model",
                )
            )

        return issues
