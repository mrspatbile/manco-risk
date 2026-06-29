"""Position validation framework for manco-risk.

Responsibilities:
- Define validation result types (severity, issue, result)
- Implement position validation engine
- Collect all validation issues per position
- Provide immutable result objects

Notes:
- Validation is separate from parsing and enrichment
- All checks run; caller decides how to handle results
- Severity levels: WARNING (non-blocking), ERROR (blocking)
- Immutable Pydantic v2 models for consistency with PositionInput
"""

from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict

from manco_risk.etl.position_loader import PositionInput

if TYPE_CHECKING:
    from manco_risk.database import Instrument


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

    def validate_positions(
        self,
        position_inputs: list[PositionInput],
        instruments_by_isin: Optional[dict[str, "Instrument"]] = None,
    ) -> list[ValidationResult]:
        """Validate all positions and return results.

        Parameters
        ----------
        position_inputs : list[PositionInput]
            Validated position input records from CSV loader.
        instruments_by_isin : dict[str, Instrument] | None
            Optional map of ISIN to Instrument for reference validation.
            If None, instrument-based checks are skipped.

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

        # Detect duplicates across batch
        duplicate_keys = self._find_duplicate_position_keys(position_inputs)

        for position_input in position_inputs:
            issues = self._validate_single_position(position_input)

            # Check for duplicates
            position_key = self._get_position_key(position_input)
            if position_key in duplicate_keys:
                issues.append(
                    ValidationIssue(
                        field="position_identity",
                        severity=ValidationSeverity.ERROR,
                        code="DUPLICATE_POSITION",
                        message="Duplicate position in batch; same fund/date/isin/source_id combination already exists",
                    )
                )

            # Check instrument reference if provided
            if instruments_by_isin is not None:
                instrument_issues = self._validate_instrument_reference(
                    position_input, instruments_by_isin
                )
                issues.extend(instrument_issues)

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

    def _get_position_key(self, position_input: PositionInput) -> tuple:
        """Get unique key for position (fund/date/isin/source_id).

        Parameters
        ----------
        position_input : PositionInput
            Position to extract key from.

        Returns
        -------
        tuple
            Unique identifier tuple (fund_name, valuation_date, isin, source_id or None).
        """
        return (
            position_input.fund_name,
            position_input.valuation_date,
            position_input.isin,
            position_input.source_position_identifier,
        )

    def _find_duplicate_position_keys(self, position_inputs: list[PositionInput]) -> set:
        """Find all duplicate position keys in batch.

        Parameters
        ----------
        position_inputs : list[PositionInput]
            Positions to check.

        Returns
        -------
        set
            Set of position keys that appear more than once.
        """
        key_counts: dict = {}
        for position_input in position_inputs:
            key = self._get_position_key(position_input)
            key_counts[key] = key_counts.get(key, 0) + 1

        return {key for key, count in key_counts.items() if count > 1}

    def _validate_instrument_reference(
        self, position_input: PositionInput, instruments_by_isin: dict[str, "Instrument"]
    ) -> list[ValidationIssue]:
        """Validate position against instrument reference data.

        Parameters
        ----------
        position_input : PositionInput
            Position to validate.
        instruments_by_isin : dict[str, Instrument]
            Map of ISIN to Instrument.

        Returns
        -------
        list[ValidationIssue]
            Issues found (empty if all checks pass).
        """
        issues: list[ValidationIssue] = []

        # Check 1: Instrument exists
        instrument = instruments_by_isin.get(position_input.isin)
        if instrument is None:
            issues.append(
                ValidationIssue(
                    field="isin",
                    severity=ValidationSeverity.ERROR,
                    code="UNKNOWN_INSTRUMENT",
                    message=f"Instrument with ISIN '{position_input.isin}' not found in reference data",
                )
            )
            return issues  # Cannot check currency if instrument not found

        # Check 2: Currency matches
        if position_input.currency != instrument.currency:
            issues.append(
                ValidationIssue(
                    field="currency",
                    severity=ValidationSeverity.ERROR,
                    code="CURRENCY_MISMATCH",
                    message=f"Position currency '{position_input.currency}' does not match instrument currency '{instrument.currency}'",
                )
            )

        return issues
