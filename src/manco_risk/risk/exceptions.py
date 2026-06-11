"""Risk calculation exceptions.

Domain-specific exceptions for risk engines and scenario generation.
"""


class RiskCalculationError(Exception):
    """Base exception for risk calculation errors."""

    pass


class UnsupportedAssetClassError(RiskCalculationError):
    """Asset class is not supported by the scenario generator.

    Supported classes: EQUITY, ETF, LISTED_FUND, INDEX, CASH.
    """

    def __init__(self, asset_class: str, isin: str, reason: str) -> None:
        """Initialize exception.

        Parameters
        ----------
        asset_class : str
            Unsupported asset class.
        isin : str
            Instrument ISIN.
        reason : str
            Explanation of why not supported.
        """
        self.asset_class = asset_class
        self.isin = isin
        self.reason = reason
        super().__init__(f"Unsupported asset class '{asset_class}' for {isin}: {reason}")


class MissingHistoricalDataError(RiskCalculationError):
    """Historical return data missing for a position on a scenario date.

    Strict policy: all non-cash, supported positions must have return data for all scenario dates.
    """

    def __init__(self, isin: str, scenario_date: str) -> None:
        """Initialize exception.

        Parameters
        ----------
        isin : str
            Instrument ISIN.
        scenario_date : str
            Date (ISO format) for which data is missing.
        """
        self.isin = isin
        self.scenario_date = scenario_date
        super().__init__(f"Missing return data for {isin} on {scenario_date}")


class InvalidScenarioInputError(RiskCalculationError):
    """Scenario input validation failed.

    Covers portfolio structure, return data consistency, or input validation errors.
    """

    def __init__(self, reason: str) -> None:
        """Initialize exception.

        Parameters
        ----------
        reason : str
            Description of the validation failure.
        """
        self.reason = reason
        super().__init__(f"Invalid scenario input: {reason}")


class InvalidPriceDataError(RiskCalculationError):
    """Price data validation failed.

    Covers negative/zero prices, duplicate dates, invalid ISINs, etc.
    """

    def __init__(self, reason: str) -> None:
        """Initialize exception.

        Parameters
        ----------
        reason : str
            Description of the validation failure.
        """
        self.reason = reason
        super().__init__(f"Invalid price data: {reason}")


class InsufficientPriceDataError(RiskCalculationError):
    """Insufficient price observations for return calculation.

    At least two price observations per ISIN are required for 1-day returns.
    """

    def __init__(self, isin: str, count: int) -> None:
        """Initialize exception.

        Parameters
        ----------
        isin : str
            Instrument ISIN.
        count : int
            Number of price observations available.
        """
        self.isin = isin
        self.count = count
        super().__init__(f"ISIN {isin} has {count} price observations; at least 2 required")


class MissingDurationError(RiskCalculationError):
    """Required duration analytics are absent from an enriched position.

    Raised by fixed-income pricers when a non-zero shock component requires
    a duration field that was not populated during enrichment.

    Examples:
    - rate_shock_bps != 0 and modified_duration is None
    - spread_shock_bps != 0 and spread_duration is None
    """

    def __init__(self, isin: str, field: str, reason: str) -> None:
        """Initialize exception.

        Parameters
        ----------
        isin : str
            Instrument ISIN.
        field : str
            Name of the missing duration field, e.g. 'modified_duration'.
        reason : str
            Explanation of why the field is required for this calculation.
        """
        self.isin = isin
        self.field = field
        self.reason = reason
        super().__init__(f"Missing '{field}' for {isin}: {reason}")
