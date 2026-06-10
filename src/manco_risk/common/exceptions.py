"""Domain exceptions for manco-risk."""


class MancoRiskError(Exception):
    """Base exception for the manco-risk package."""

    pass


class MarketDataError(MancoRiskError):
    """Base exception for market data layer."""

    pass


class SecurityNotFoundError(MarketDataError):
    """Security not found in market data provider."""

    pass


class InsufficientPriceDataError(MarketDataError):
    """Not enough price data for the requested date range or date."""

    pass


class FXRateNotAvailableError(MarketDataError):
    """FX rate not available for requested currency pair and date."""

    pass


class InvalidSecurityError(MarketDataError):
    """Security identifier format or content is invalid."""

    pass
