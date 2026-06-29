# Market Data Abstraction Design (MRS-125)

## Overview

The market data abstraction provides a clean interface for retrieving:
- Current and historical instrument prices
- FX rates
- Instrument metadata (asset class, currency, duration, etc.)

The interface is designed to support multiple implementations (Bloomberg, yfinance, ECB, cached layers) without modification to consumer code.

---

## Package Structure

```
src/manco_risk/
├── common/
│   ├── __init__.py
│   ├── exceptions.py          # MarketDataError, InsufficientDataError, etc.
│   └── types.py               # AssetClass, Currency enums
│
└── market_data/
    ├── __init__.py            # Exports public API
    ├── schemas.py             # Pydantic models
    ├── provider.py            # Abstract base class
    └── csv_provider.py        # CSV-backed mock implementation
```

---

## Schemas (Pydantic v2)

### Core Types

```python
# schemas.py

class Price(BaseModel):
    """Current price for a security on a date."""
    security_id: str
    date: date
    price: Decimal          # in native currency
    currency: str           # e.g., 'USD', 'EUR'
    
    model_config = ConfigDict(validate_assignment=True)


class PriceHistory(BaseModel):
    """Time series of prices."""
    security_id: str
    prices: list[Price]     # sorted by date, ascending
    
    model_config = ConfigDict(validate_assignment=True)


class InstrumentInfo(BaseModel):
    """Metadata for an instrument."""
    security_id: str
    name: str
    asset_class: AssetClass        # Equity, Bond, FX, etc.
    currency: str
    # Bond-specific
    maturity_date: date | None = None
    coupon_rate: Decimal | None = None        # as decimal, e.g., 0.035 = 3.5%
    modified_duration_years: Decimal | None = None
    # Equity-specific
    beta: Decimal | None = None
    
    model_config = ConfigDict(validate_assignment=True)


class FXRate(BaseModel):
    """Exchange rate at a point in time."""
    from_currency: str
    to_currency: str
    date: date
    rate: Decimal              # e.g., 1.0850 = 1 EUR = 1.0850 USD
    
    model_config = ConfigDict(validate_assignment=True)
```

### Enums

```python
# types.py

class AssetClass(str, Enum):
    EQUITY = "Equity"
    BOND = "Bond"
    FX = "FX"
    INDEX = "Index"
    CASH = "Cash"


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    # Add as needed
```

### Exceptions

```python
# common/exceptions.py

class MarketDataError(Exception):
    """Base exception for market data layer."""
    pass


class SecurityNotFoundError(MarketDataError):
    """Security not found in provider."""
    pass


class InsufficientPriceDataError(MarketDataError):
    """Not enough price data for the requested date range."""
    pass


class FXRateNotAvailableError(MarketDataError):
    """FX rate not available for requested date."""
    pass
```

---

## Abstract Provider Interface

```python
# provider.py

from abc import ABC, abstractmethod
from datetime import date

class MarketDataProvider(ABC):
    """
    Abstract base for market data providers.
    
    Implementations: CSVProvider, BloombergProvider, CachedProvider, etc.
    """
    
    @abstractmethod
    def get_instrument_info(self, security_id: str) -> InstrumentInfo:
        """
        Retrieve metadata for a security.
        
        Raises:
            SecurityNotFoundError: if security not in provider
        """
        pass
    
    @abstractmethod
    def get_price(self, security_id: str, date: date) -> Price:
        """
        Get price for a security on a specific date.
        
        Raises:
            SecurityNotFoundError: if security not in provider
            InsufficientPriceDataError: if no price available for that date
        """
        pass
    
    @abstractmethod
    def get_price_history(
        self,
        security_id: str,
        start_date: date,
        end_date: date,
    ) -> PriceHistory:
        """
        Get price history for a security over a date range.
        
        Prices must be sorted by date (ascending).
        Gaps in data (weekends, holidays) are allowed; the calling code
        handles forward-fill or interpolation as needed.
        
        Raises:
            SecurityNotFoundError: if security not in provider
            InsufficientPriceDataError: if insufficient data for range
        """
        pass
    
    @abstractmethod
    def get_fx_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: date,
    ) -> FXRate:
        """
        Get exchange rate on a specific date.
        
        Rate is from_currency -> to_currency.
        E.g., get_fx_rate('EUR', 'USD', date) returns USD/EUR.
        
        Raises:
            FXRateNotAvailableError: if rate not available for that date
        """
        pass
```

---

## CSV Provider Implementation (Minimal)

### Responsibilities

**CSVProvider will:**
- Load instrument reference data from CSV
- Load price history from CSV
- Load FX rates from CSV
- Handle date lookups and missing data gracefully
- Support only business days (Mon-Fri)

**CSVProvider will NOT:**
- Fetch live data
- Cache results
- Integrate with external APIs
- Support intraday data

### CSV File Structure

#### `data/instruments.csv`

```csv
security_id,name,asset_class,currency,maturity_date,coupon_rate,modified_duration_years,beta
SPY US Equity,SPDR S&P 500 ETF,Equity,USD,,,1.00
AAPL US Equity,Apple Inc,Equity,USD,,0.02,
US912828YK09 Govt,US Treasury 2.875 05/15/28,Bond,USD,2028-05-15,0.02875,2.31,
EURUSD Curncy,Euro / USD,FX,USD,,,
DBR 0 08/15/29 Govt,German Bund 0% 08/15/29,Bond,EUR,2029-08-15,0.00,3.98,
XS2543791470 Corp,LVMH 3.5 06/15/31,Bond,EUR,2031-06-15,0.035,4.71,
```

#### `data/prices.csv`

```csv
date,security_id,price
2026-01-02,SPY US Equity,580.45
2026-01-03,SPY US Equity,582.10
2026-01-06,SPY US Equity,581.50
...
2026-06-10,SPY US Equity,592.30
2026-01-02,AAPL US Equity,245.60
2026-01-03,AAPL US Equity,246.80
...
```

#### `data/fx_rates.csv`

```csv
date,from_currency,to_currency,rate
2026-01-02,EUR,USD,1.0820
2026-01-03,EUR,USD,1.0840
...
2026-06-10,EUR,USD,1.0910
2026-01-02,GBP,USD,1.2750
2026-01-03,GBP,USD,1.2760
...
```

**Notes:**
- Dates are ISO 8601 (YYYY-MM-DD)
- Prices in security's native currency
- FX rates as decimals (e.g., 1.0850 = 1 EUR to 1.0850 USD)
- All values must be convertible to Decimal (no NaN)
- CSVs loaded once at provider initialization

---

## Public API (Module Exports)

```python
# market_data/__init__.py

from .schemas import Price, PriceHistory, InstrumentInfo, FXRate
from .provider import MarketDataProvider
from .csv_provider import CSVProvider

__all__ = [
    "Price",
    "PriceHistory", 
    "InstrumentInfo",
    "FXRate",
    "MarketDataProvider",
    "CSVProvider",
]
```

---

## Usage Example (Consumer Code)

```python
from manco_risk.market_data import CSVProvider
from datetime import date

provider = CSVProvider(data_dir="data/")

# Get instrument metadata
spy = provider.get_instrument_info("SPY US Equity")
print(f"{spy.name}: {spy.currency} {spy.asset_class}")

# Get current price
price = provider.get_price("SPY US Equity", date(2026, 6, 10))
print(f"SPY price: {price.price}")

# Get historical prices for VaR
history = provider.get_price_history(
    "SPY US Equity",
    start_date=date(2025, 1, 1),
    end_date=date(2026, 6, 10),
)
returns = [(history.prices[i].price / history.prices[i-1].price) - 1 
           for i in range(1, len(history.prices))]

# Get FX rate
eur_usd = provider.get_fx_rate("EUR", "USD", date(2026, 6, 10))
print(f"EUR/USD: {eur_usd.rate}")
```

---

## Future Extension Points

### New Provider Implementations

```python
class BloombergProvider(MarketDataProvider):
    """Real Bloomberg API integration."""
    def __init__(self, session_handle):
        ...

class YFinanceProvider(MarketDataProvider):
    """yfinance-backed provider."""
    def __init__(self, cache_dir=None):
        ...

class CachedProvider(MarketDataProvider):
    """Caching wrapper around another provider."""
    def __init__(self, inner_provider: MarketDataProvider, cache_ttl: timedelta):
        ...
```

These implementations plug in without changing the interface contract or consumer code.

---

## Testing Strategy

### Test Coverage

1. **Schemas** — Pydantic validation tests
2. **CSVProvider** — Data loading, lookups, missing data handling
3. **Integration** — End-to-end test with sample data

No tests for external APIs (live data, Bloomberg) since they're not implemented.

---

## Notes on Data Conventions

All prices and rates follow `docs/CONVENTIONS.md`:
- Prices stored as `Decimal`
- Rates/yields stored as `Decimal` (0.035 = 3.5%)
- Durations in years as `Decimal`
- FX rates as `Decimal`
- All dates are ISO 8601

---

## Out of Scope (MRS-125)

- Live data fetching
- API integrations
- Caching infrastructure
- Real Bloomberg client
- Full field coverage
- Intraday data
- Tick data
- Options Greeks
- Credit curves
