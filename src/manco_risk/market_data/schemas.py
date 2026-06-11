"""Market data schemas using Pydantic v2."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator

from manco_risk.common import AssetClass


class Price(BaseModel):
    """A single price observation for a security on a date."""

    security_id: str
    date: date
    price: Decimal
    currency: str

    model_config = ConfigDict(validate_assignment=True)


class PriceHistory(BaseModel):
    """Time series of prices for a security.

    Prices are sorted by date in ascending order (earliest first).
    """

    security_id: str
    prices: list[Price]

    model_config = ConfigDict(validate_assignment=True)

    @model_validator(mode="after")
    def sort_prices_by_date(self) -> "PriceHistory":
        """Ensure prices are sorted by date."""
        self.prices.sort(key=lambda p: p.date)
        return self


class InstrumentInfo(BaseModel):
    """Metadata for an instrument.

    Includes common fields across asset classes and optional asset-specific fields.
    All rates and durations are stored as decimals (0.035 = 3.5%).

    Fixed-income fields (bonds only):
    - modified_duration_years: modified duration in years; used for rate-shock sensitivity
    - spread_duration_years: spread duration in years; used for credit-spread-shock sensitivity.
      Government bonds carry spread_duration_years = 0 (no credit spread exposure).
      Corporate bonds carry spread_duration_years > 0.
      Missing (None) means the data source did not provide a value.
    """

    security_id: str
    name: str
    asset_class: AssetClass
    currency: str

    maturity_date: date | None = None
    coupon_rate: Decimal | None = None
    modified_duration_years: Decimal | None = None
    spread_duration_years: Decimal | None = None
    beta: Decimal | None = None

    model_config = ConfigDict(validate_assignment=True)


class FXRate(BaseModel):
    """Exchange rate at a point in time.

    Represents the rate to convert from one currency to another.
    Example: from_currency='EUR', to_currency='USD', rate=1.0850
    means 1 EUR = 1.0850 USD.
    """

    from_currency: str
    to_currency: str
    date: date
    rate: Decimal

    model_config = ConfigDict(validate_assignment=True)
