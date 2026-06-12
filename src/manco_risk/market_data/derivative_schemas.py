"""Derivative market data schemas.

Pure models for derivative pricing market data: yield curves, volatility surfaces,
and spot prices. These schemas represent market-data contracts without defining
pricing logic, interpolation, bootstrapping, or regulatory treatment.

Conventions:
- Rates, yields, volatilities stored as Decimal (0.05 = 5%, 0.20 = 20%)
- Maturities in years as Decimal (0.25 = 3 months, 1 = 1 year)
- No pricing engine conversion; no database access; no curve manipulation
"""

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class YieldCurveType(str, Enum):
    """Type of yield curve.

    RISK_FREE: Risk-free discount curve (government bond yields or swap curve)
    DIVIDEND_YIELD: Dividend yield curve for equity underlyings
    CREDIT_SPREAD: Credit spread curve (above risk-free baseline)
    """

    RISK_FREE = "RISK_FREE"
    DIVIDEND_YIELD = "DIVIDEND_YIELD"
    CREDIT_SPREAD = "CREDIT_SPREAD"


class VolatilitySurfaceType(str, Enum):
    """Type of volatility surface.

    EQUITY_VOL: Equity option volatility surface
    FX_VOL: FX option volatility surface
    RATE_VOL: Interest-rate option volatility surface (caplet/floorlet)
    """

    EQUITY_VOL = "EQUITY_VOL"
    FX_VOL = "FX_VOL"
    RATE_VOL = "RATE_VOL"


class YieldCurvePoint(BaseModel):
    """A single point on a yield curve.

    Represents the yield at a specific maturity on a specific date.
    Can be negative (e.g., for EUR or JPY risk-free rates).

    Fields:
    - curve_date: date for which this point applies
    - maturity_years: years to maturity (must be > 0)
    - yield_rate: yield as decimal (0.05 = 5%, can be negative)
    - curve_type: type of curve (RISK_FREE, DIVIDEND_YIELD, CREDIT_SPREAD)
    - currency: currency code (e.g., "USD", "EUR")
    - source: optional source label (e.g., "Bloomberg", "CME")
    """

    curve_date: date
    maturity_years: Decimal
    yield_rate: Decimal
    curve_type: YieldCurveType
    currency: str
    source: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("maturity_years")
    @classmethod
    def validate_maturity_years(cls, v: Decimal) -> Decimal:
        """Maturity must be positive."""
        if v <= Decimal("0"):
            raise ValueError(f"maturity_years must be positive, got {v}")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Currency must be non-empty."""
        if not v or not v.strip():
            raise ValueError("currency must be non-empty")
        return v.strip()

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        """Source, if provided, must be non-empty."""
        if v is not None and not v.strip():
            raise ValueError("source must be non-empty if provided")
        return v.strip() if v else None


class YieldCurve(BaseModel):
    """A yield curve: collection of points from short to long maturity.

    Represents the term structure of interest rates on a given date.
    All points must be for the same curve type, date, and currency.
    Maturities must be strictly increasing.

    Fields:
    - curve_type: type of curve (RISK_FREE, DIVIDEND_YIELD, CREDIT_SPREAD)
    - curve_date: date for which this curve applies (all points must match)
    - currency: currency of the curve (all points must match)
    - points: list of yield curve points (must be non-empty, sorted by maturity)
    - source: optional source label
    """

    curve_type: YieldCurveType
    curve_date: date
    currency: str
    points: list[YieldCurvePoint]
    source: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Currency must be non-empty."""
        if not v or not v.strip():
            raise ValueError("currency must be non-empty")
        return v.strip()

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        """Source, if provided, must be non-empty."""
        if v is not None and not v.strip():
            raise ValueError("source must be non-empty if provided")
        return v.strip() if v else None

    @model_validator(mode="after")
    def validate_curve(self) -> "YieldCurve":
        """Validate curve consistency and point ordering."""
        if not self.points:
            raise ValueError("points must be non-empty")

        # All points must have same curve type, date, and currency
        for point in self.points:
            if point.curve_type != self.curve_type:
                raise ValueError(
                    f"all points must have curve_type {self.curve_type}, got {point.curve_type}"
                )
            if point.curve_date != self.curve_date:
                raise ValueError(
                    f"all points must have curve_date {self.curve_date}, got {point.curve_date}"
                )
            if point.currency != self.currency:
                raise ValueError(
                    f"all points must have currency {self.currency}, got {point.currency}"
                )

        # Maturities must be strictly increasing
        maturities = [p.maturity_years for p in self.points]
        for i in range(len(maturities) - 1):
            if maturities[i] >= maturities[i + 1]:
                raise ValueError(
                    f"maturities must be strictly increasing; "
                    f"got {maturities[i]} at position {i} and {maturities[i + 1]} "
                    f"at position {i + 1}"
                )

        return self


class VolatilityPoint(BaseModel):
    """A single point on a volatility surface.

    Represents implied volatility for a specific underlying, maturity, and
    moneyness on a specific date.

    Fields:
    - surface_date: date for which this point applies
    - underlying_id: identifier of underlying (ISIN, ticker)
    - maturity_years: years to maturity (must be > 0)
    - moneyness: strike / spot ratio (must be > 0; 1.0 = ATM, 1.1 = 10% OTM call)
    - implied_volatility: annualized vol as decimal (0.20 = 20%, must be > 0)
    - surface_type: type of surface (EQUITY_VOL, FX_VOL, RATE_VOL)
    - source: optional source label
    """

    surface_date: date
    underlying_id: str
    maturity_years: Decimal
    moneyness: Decimal
    implied_volatility: Decimal
    surface_type: VolatilitySurfaceType
    source: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("underlying_id")
    @classmethod
    def validate_underlying_id(cls, v: str) -> str:
        """Underlying ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("underlying_id must be non-empty")
        return v.strip()

    @field_validator("maturity_years")
    @classmethod
    def validate_maturity_years(cls, v: Decimal) -> Decimal:
        """Maturity must be positive."""
        if v <= Decimal("0"):
            raise ValueError(f"maturity_years must be positive, got {v}")
        return v

    @field_validator("moneyness")
    @classmethod
    def validate_moneyness(cls, v: Decimal) -> Decimal:
        """Moneyness must be positive."""
        if v <= Decimal("0"):
            raise ValueError(f"moneyness must be positive, got {v}")
        return v

    @field_validator("implied_volatility")
    @classmethod
    def validate_implied_volatility(cls, v: Decimal) -> Decimal:
        """Implied volatility must be positive."""
        if v <= Decimal("0"):
            raise ValueError(f"implied_volatility must be positive, got {v}")
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        """Source, if provided, must be non-empty."""
        if v is not None and not v.strip():
            raise ValueError("source must be non-empty if provided")
        return v.strip() if v else None


class VolatilitySurface(BaseModel):
    """A volatility surface: collection of points across maturities and moneyness.

    Represents the full implied volatility surface for an underlying on a date.
    All points must be for the same surface type, date, and underlying.
    No duplicate (maturity, moneyness) pairs allowed.

    Fields:
    - surface_type: type of surface (EQUITY_VOL, FX_VOL, RATE_VOL)
    - surface_date: date for which this surface applies
    - underlying_id: identifier of underlying (all points must match)
    - points: list of volatility points (must be non-empty, no duplicates)
    - source: optional source label
    """

    surface_type: VolatilitySurfaceType
    surface_date: date
    underlying_id: str
    points: list[VolatilityPoint]
    source: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("underlying_id")
    @classmethod
    def validate_underlying_id(cls, v: str) -> str:
        """Underlying ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("underlying_id must be non-empty")
        return v.strip()

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        """Source, if provided, must be non-empty."""
        if v is not None and not v.strip():
            raise ValueError("source must be non-empty if provided")
        return v.strip() if v else None

    @model_validator(mode="after")
    def validate_surface(self) -> "VolatilitySurface":
        """Validate surface consistency and detect duplicate grid points."""
        if not self.points:
            raise ValueError("points must be non-empty")

        # All points must have same surface type, date, and underlying
        for point in self.points:
            if point.surface_type != self.surface_type:
                raise ValueError(
                    f"all points must have surface_type {self.surface_type}, "
                    f"got {point.surface_type}"
                )
            if point.surface_date != self.surface_date:
                raise ValueError(
                    f"all points must have surface_date {self.surface_date}, "
                    f"got {point.surface_date}"
                )
            if point.underlying_id != self.underlying_id:
                raise ValueError(
                    f"all points must have underlying_id {self.underlying_id}, "
                    f"got {point.underlying_id}"
                )

        # Detect duplicate (maturity, moneyness) pairs
        seen_grid_points = set()
        for point in self.points:
            grid_key = (point.maturity_years, point.moneyness)
            if grid_key in seen_grid_points:
                raise ValueError(
                    f"duplicate grid point: maturity={point.maturity_years}, "
                    f"moneyness={point.moneyness}"
                )
            seen_grid_points.add(grid_key)

        return self


class DerivativeMarketData(BaseModel):
    """Market data bundle for derivative pricing.

    Aggregates all market data needed to price a derivative: spot price, risk-free
    curve, dividend yield curve (optional for equity options), and volatility
    surface (optional).

    Fields:
    - derivative_id: unique identifier (non-empty)
    - pricing_date: date for which to price
    - underlying_id: identifier of underlying (ISIN, ticker)
    - spot_price: current price of underlying (must be > 0)
    - currency: currency of spot and curves (non-empty)
    - risk_free_curve: risk-free discount curve (date and currency must match)
    - dividend_yield_curve: optional dividend yield curve
    - volatility_surface: optional volatility surface
    - source: optional source label

    Invariants:
    - risk_free_curve must have type RISK_FREE and date equal to pricing_date
    - dividend_yield_curve (if provided) must have type DIVIDEND_YIELD
    - volatility_surface (if provided) must have correct date and underlying
    """

    derivative_id: str
    pricing_date: date
    underlying_id: str
    spot_price: Decimal
    currency: str
    risk_free_curve: YieldCurve
    dividend_yield_curve: YieldCurve | None = None
    volatility_surface: VolatilitySurface | None = None
    source: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("derivative_id")
    @classmethod
    def validate_derivative_id(cls, v: str) -> str:
        """Derivative ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("derivative_id must be non-empty")
        return v.strip()

    @field_validator("underlying_id")
    @classmethod
    def validate_underlying_id(cls, v: str) -> str:
        """Underlying ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("underlying_id must be non-empty")
        return v.strip()

    @field_validator("spot_price")
    @classmethod
    def validate_spot_price(cls, v: Decimal) -> Decimal:
        """Spot price must be positive."""
        if v <= Decimal("0"):
            raise ValueError(f"spot_price must be positive, got {v}")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Currency must be non-empty."""
        if not v or not v.strip():
            raise ValueError("currency must be non-empty")
        return v.strip()

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        """Source, if provided, must be non-empty."""
        if v is not None and not v.strip():
            raise ValueError("source must be non-empty if provided")
        return v.strip() if v else None

    @model_validator(mode="after")
    def validate_market_data(self) -> "DerivativeMarketData":
        """Validate market data bundle consistency."""
        # Risk-free curve must be RISK_FREE and match pricing_date and currency
        if self.risk_free_curve.curve_type != YieldCurveType.RISK_FREE:
            raise ValueError(
                f"risk_free_curve must have type RISK_FREE, got {self.risk_free_curve.curve_type}"
            )
        if self.risk_free_curve.curve_date != self.pricing_date:
            raise ValueError(
                f"risk_free_curve date {self.risk_free_curve.curve_date} must equal "
                f"pricing_date {self.pricing_date}"
            )
        if self.risk_free_curve.currency != self.currency:
            raise ValueError(
                f"risk_free_curve currency {self.risk_free_curve.currency} must equal "
                f"market data currency {self.currency}"
            )

        # Dividend yield curve (if provided) must be DIVIDEND_YIELD and match date/currency
        if self.dividend_yield_curve is not None:
            if self.dividend_yield_curve.curve_type != YieldCurveType.DIVIDEND_YIELD:
                raise ValueError(
                    f"dividend_yield_curve must have type DIVIDEND_YIELD, "
                    f"got {self.dividend_yield_curve.curve_type}"
                )
            if self.dividend_yield_curve.curve_date != self.pricing_date:
                raise ValueError(
                    f"dividend_yield_curve date {self.dividend_yield_curve.curve_date} "
                    f"must equal pricing_date {self.pricing_date}"
                )
            if self.dividend_yield_curve.currency != self.currency:
                raise ValueError(
                    f"dividend_yield_curve currency {self.dividend_yield_curve.currency} "
                    f"must equal market data currency {self.currency}"
                )

        # Volatility surface (if provided) must match date and underlying
        if self.volatility_surface is not None:
            if self.volatility_surface.surface_date != self.pricing_date:
                raise ValueError(
                    f"volatility_surface date {self.volatility_surface.surface_date} "
                    f"must equal pricing_date {self.pricing_date}"
                )
            if self.volatility_surface.underlying_id != self.underlying_id:
                raise ValueError(
                    f"volatility_surface underlying_id {self.volatility_surface.underlying_id} "
                    f"must equal market data underlying_id {self.underlying_id}"
                )

        return self
