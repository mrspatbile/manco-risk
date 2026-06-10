"""Price and price-to-return models for equity-like instruments.

Models for historical price data and the output of price-to-return conversion.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class PricePoint(BaseModel):
    """Single historical price observation for an instrument.

    Fields:
    - isin: Instrument ISIN (business identifier).
    - price_date: Date of the price observation.
    - price: Price in instrument currency (must be strictly positive).

    Invariants:
    - price > 0
    - isin non-empty
    - price_date is valid date
    """

    isin: str
    price_date: date
    price: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("isin")
    @classmethod
    def validate_isin(cls, v: str) -> str:
        """ISIN must be non-empty."""
        if not v or not v.strip():
            raise ValueError("ISIN must be non-empty")
        return v

    @field_validator("price", mode="before")
    @classmethod
    def validate_price_is_decimal(cls, v) -> Decimal:
        """Ensure price is Decimal."""
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))

    @field_validator("price")
    @classmethod
    def validate_price_positive(cls, v: Decimal) -> Decimal:
        """Price must be strictly positive."""
        if v <= Decimal("0"):
            raise ValueError(f"Price must be strictly positive, got {v}")
        return v


class PriceToReturnInput(BaseModel):
    """Input for price-to-return conversion.

    Contains all price observations for one or more instruments.

    Fields:
    - price_points: List of price observations.

    Invariants:
    - price_points non-empty
    - no duplicate (isin, price_date) pairs
    - per ISIN, at least 2 observations
    """

    price_points: list[PricePoint]

    model_config = ConfigDict(frozen=True)

    @field_validator("price_points")
    @classmethod
    def validate_price_points_not_empty(cls, v: list[PricePoint]) -> list[PricePoint]:
        """Price points list must not be empty."""
        if len(v) == 0:
            raise ValueError("Price points list must not be empty")
        return v

    @field_validator("price_points")
    @classmethod
    def validate_no_duplicate_isin_dates(cls, v: list[PricePoint]) -> list[PricePoint]:
        """No duplicate (isin, price_date) pairs allowed."""
        seen: set[tuple[str, date]] = set()
        for point in v:
            key = (point.isin, point.price_date)
            if key in seen:
                raise ValueError(f"Duplicate price point: ISIN {point.isin} on {point.price_date}")
            seen.add(key)
        return v


class PriceToReturnResult(BaseModel):
    """Result of price-to-return conversion.

    Contains historical returns in the format expected by equity scenario generator.

    Fields:
    - historical_returns: dict mapping ISIN → {date → signed_return}.
    - num_isins: Count of unique ISINs.
    - num_price_points: Total price observations.
    - num_returns: Total return observations.
    - num_unique_return_dates: Count of unique scenario dates across all ISINs.

    Sign convention:
    - Returns are signed: negative = loss, positive = gain.
    - Example: -0.025 = 2.5% loss, 0.03 = 3% gain.
    """

    historical_returns: dict[str, dict[date, Decimal]]
    num_isins: int
    num_price_points: int
    num_returns: int
    num_unique_return_dates: int

    model_config = ConfigDict(frozen=True)

    @field_validator("num_isins")
    @classmethod
    def validate_num_isins(cls, v: int) -> int:
        """Number of ISINs must be non-negative."""
        if v < 0:
            raise ValueError(f"Number of ISINs must be non-negative, got {v}")
        return v

    @field_validator("num_price_points")
    @classmethod
    def validate_num_price_points(cls, v: int) -> int:
        """Number of price points must be non-negative."""
        if v < 0:
            raise ValueError(f"Number of price points must be non-negative, got {v}")
        return v

    @field_validator("num_returns")
    @classmethod
    def validate_num_returns(cls, v: int) -> int:
        """Number of returns must be non-negative."""
        if v < 0:
            raise ValueError(f"Number of returns must be non-negative, got {v}")
        return v

    @field_validator("num_unique_return_dates")
    @classmethod
    def validate_num_unique_return_dates(cls, v: int) -> int:
        """Number of unique return dates must be non-negative."""
        if v < 0:
            raise ValueError(f"Number of unique return dates must be non-negative, got {v}")
        return v
