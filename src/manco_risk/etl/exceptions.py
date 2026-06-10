"""ETL and ingestion exceptions for manco-risk."""

from manco_risk.common.exceptions import MancoRiskError


class ETLError(MancoRiskError):
    """Base exception for ETL layer."""

    pass


class PositionInputValidationError(ETLError):
    """Position input data validation failed."""

    pass


class InvalidPositionFieldError(PositionInputValidationError):
    """A required position field is invalid or missing."""

    pass


class PositionCSVLoadError(ETLError):
    """Error loading positions from CSV file."""

    pass


class PositionIngestionError(ETLError):
    """Error during position ingestion and persistence."""

    pass


class FundNotFoundError(PositionIngestionError):
    """Fund not found in database."""

    pass


class InstrumentNotFoundError(PositionIngestionError):
    """Instrument (by ISIN) not found in database."""

    pass


class PositionValidationFailure(PositionIngestionError):
    """Position validation found blocking errors.

    Carries validation results for detailed inspection by the caller.
    """

    def __init__(self, message: str, validation_results: list) -> None:
        """Initialize validation failure exception.

        Parameters
        ----------
        message : str
            Summary message about validation failure.
        validation_results : list
            Detailed validation results (list[ValidationResult] from position_validator).
        """
        super().__init__(message)
        self.validation_results = validation_results
