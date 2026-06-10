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
