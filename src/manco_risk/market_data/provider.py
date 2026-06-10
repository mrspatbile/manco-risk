"""Abstract base class for market data providers."""

from abc import ABC, abstractmethod
from datetime import date

from .schemas import FXRate, InstrumentInfo, Price, PriceHistory


class MarketDataProvider(ABC):
    """Abstract base for market data providers.

    Implementations can be CSV-backed, Bloomberg, yfinance, cached, etc.
    The interface is designed to support multiple implementations without
    requiring changes to consumer code.

    Data Quality and Transformations
    --------------------------------
    Provider implementations may apply documented transformations, validations,
    or overrides before exposing data through this interface. Examples include:

    - Correcting known data anomalies (e.g., market index beta reported as 0.0
      when the expected value is 1.0)
    - Normalizing inconsistent conventions (e.g., currency codes, bond prices)
    - Handling missing or invalid values

    All adjustments must be:
    - documented in the provider implementation
    - testable
    - traceable to the original source value
    - applied before data reaches downstream modules

    Risk engines, reporting, ETL, and UI layers must NOT implement
    provider-specific corrections. See ARCHITECTURE.md for complete policy.

    All methods raise specific exceptions on failure (see exceptions module).
    """

    @abstractmethod
    def get_instrument_info(self, security_id: str) -> InstrumentInfo:
        """Retrieve metadata for a security.

        Parameters
        ----------
        security_id : str
            The security identifier (e.g., 'SPY US Equity')

        Returns
        -------
        InstrumentInfo
            Metadata including name, asset class, currency, and optional
            fields like duration, coupon, beta.

        Raises
        ------
        SecurityNotFoundError
            If security not found in provider
        """
        pass

    @abstractmethod
    def get_price(self, security_id: str, target_date: date) -> Price:
        """Get price for a security on a specific date.

        For single-date queries, the provider may return the price on an
        earlier business day if the exact date is not available (e.g.,
        weekend or holiday).

        Parameters
        ----------
        security_id : str
            The security identifier
        target_date : date
            The requested date

        Returns
        -------
        Price
            Price on the target date or nearest previous business day.
            Always returns a Price with the actual date (may differ from target).

        Raises
        ------
        SecurityNotFoundError
            If security not found in provider
        InsufficientPriceDataError
            If no price available on or before target date
        """
        pass

    @abstractmethod
    def get_price_history(
        self,
        security_id: str,
        start_date: date,
        end_date: date,
    ) -> PriceHistory:
        """Get price history for a security over a date range.

        Returns only the observations available in the provider. No gaps are
        filled; missing data is explicit. This allows the risk engine to decide
        whether to drop dates, forward-fill, or raise an error.

        Prices are sorted by date (ascending).

        Parameters
        ----------
        security_id : str
            The security identifier
        start_date : date
            Start of date range (inclusive)
        end_date : date
            End of date range (inclusive)

        Returns
        -------
        PriceHistory
            Available prices in the range, sorted by date.
            May contain gaps (missing business days).

        Raises
        ------
        SecurityNotFoundError
            If security not found in provider
        InsufficientPriceDataError
            If insufficient data within the range (provider-dependent)
        """
        pass

    @abstractmethod
    def get_fx_rate(
        self,
        from_currency: str,
        to_currency: str,
        target_date: date,
    ) -> FXRate:
        """Get exchange rate on a specific date.

        For single-date queries, the provider may return the rate on an
        earlier business day if the exact date is not available.

        The returned FXRate always contains the actual date (may differ from target).

        Parameters
        ----------
        from_currency : str
            Source currency code (e.g., 'EUR')
        to_currency : str
            Target currency code (e.g., 'USD')
        target_date : date
            The requested date

        Returns
        -------
        FXRate
            Exchange rate from from_currency to to_currency.
            rate field represents: 1 unit of from_currency = rate units of to_currency.

        Raises
        ------
        FXRateNotAvailableError
            If rate not available for the requested currency pair and date
        """
        pass
