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


# ============================================================================
# Enrichment Exceptions
# ============================================================================


class PositionEnrichmentError(ETLError):
    """Base exception for position enrichment failures."""

    pass


class InstrumentReferenceNotFoundError(PositionEnrichmentError):
    """Instrument reference not found during enrichment.

    Raised when a position references an ISIN not found in the
    instruments_by_isin map during enrichment.
    """

    def __init__(self, isin: str, position_id: int | None = None) -> None:
        """Initialize instrument reference not found exception.

        Parameters
        ----------
        isin : str
            The ISIN that was not found.
        position_id : int | None
            The position_id referencing the missing ISIN (if available).
        """
        msg = f"Instrument with ISIN '{isin}' not found"
        if position_id is not None:
            msg += f" (referenced by position_id {position_id})"
        super().__init__(msg)
        self.isin = isin
        self.position_id = position_id


class MissingFXRateError(PositionEnrichmentError):
    """Required FX rate not found during enrichment.

    Raised when a position requires currency conversion but the
    needed FX rate is not provided.
    """

    def __init__(
        self,
        from_currency: str,
        to_currency: str,
        position_id: int | None = None,
    ) -> None:
        """Initialize missing FX rate exception.

        Parameters
        ----------
        from_currency : str
            Source currency code.
        to_currency : str
            Target currency code.
        position_id : int | None
            The position_id requiring the conversion (if available).
        """
        msg = f"FX rate not found for {from_currency}/{to_currency}"
        if position_id is not None:
            msg += f" (required by position_id {position_id})"
        super().__init__(msg)
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.position_id = position_id
