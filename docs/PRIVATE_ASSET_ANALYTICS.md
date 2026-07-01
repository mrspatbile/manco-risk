# Private Asset Analytics

## Purpose

Private asset analytics covers performance measurement and risk monitoring for illiquid investments, including private equity, infrastructure, real estate, and private debt.

This document describes the private equity analytics module. Infrastructure, real estate, and private debt modules are planned for future releases.

## Architecture

Private asset analytics are implemented as stateless engines that operate on typed input/output objects.

```
Input (cash flows, residual value)
    ↓
Private Equity Engine (calculate multiples)
    ↓
Output (DPI, RVPI, TVPI, MOIC)
```

The private asset module:
- Does not calculate returns or IRR in this slice
- Does not query databases
- Does not load files or access external data
- Does not contain UI or notebook code
- Returns immutable typed result objects

## Module Structure

```
src/manco_risk/risk/private_assets/
├── __init__.py
├── private_equity.py          (models)
└── private_equity_engine.py   (calculations)

tests/
└── test_private_equity_analytics.py
```

## Models

### PrivateEquityCashFlow

Represents a single cash flow (contribution or distribution).

```python
class PrivateEquityCashFlow:
    flow_amount: Decimal        # Non-negative amount
    flow_date: date             # Date of cash flow
    flow_type: str              # "paid_in" or "distribution"
```

**Notes:**
- `flow_amount` must be non-negative
- `flow_type` is normalized to lowercase
- Immutable (read-only attributes)

### PrivateEquityInvestmentInput

Input data for analysis: cash flows and residual value.

```python
class PrivateEquityInvestmentInput:
    cash_flows: list[PrivateEquityCashFlow]  # May be empty
    residual_value: Decimal                   # Current NAV or remaining value
    investment_id: str | None                 # Optional identifier
```

**Notes:**
- `residual_value` must be non-negative
- `cash_flows` may be empty
- No calculations performed; input validation only

### PrivateEquityAnalyticsResult

Immutable result with computed multiples.

```python
class PrivateEquityAnalyticsResult:
    dpi: Decimal | None         # Distributed to Paid-In
    rvpi: Decimal | None        # Residual to Paid-In
    tvpi: Decimal | None        # Total Value to Paid-In
    moic: Decimal | None        # Multiple on Invested Capital (TVPI)
    total_paid_in: Decimal      # Sum of contributions
    total_distributed: Decimal  # Sum of distributions
    residual_value: Decimal     # Current value
```

**Notes:**
- All ratios are `None` if total paid-in is zero
- All ratios are non-negative Decimal values
- MOIC = TVPI (same calculation)

## Formulas

### DPI (Distributed to Paid-In Capital)

```
DPI = Cumulative Distributions / Cumulative Paid-In Capital
```

Measures cash returned to investors relative to capital invested.

**Range:** 0–∞

**Example:**
- Paid-in: $1M
- Distributions: $500K
- DPI = 0.5 (50% of capital returned as cash)

### RVPI (Residual Value to Paid-In Capital)

```
RVPI = Current NAV / Cumulative Paid-In Capital
```

Measures remaining value relative to capital invested.

**Range:** 0–∞

**Example:**
- Paid-in: $1M
- Residual value: $1M
- RVPI = 1.0 (remaining value equals invested capital)

### TVPI (Total Value to Paid-In Capital)

```
TVPI = (Cumulative Distributions + Current NAV) / Cumulative Paid-In Capital
```

Measures total value (distributed + remaining) relative to capital invested.

**Range:** 0–∞

**Example:**
- Paid-in: $1M
- Distributions: $500K
- Residual value: $1M
- TVPI = 1.5 (total value is 150% of invested capital)

### MOIC (Multiple on Invested Capital)

```
MOIC = TVPI
```

Equivalent to TVPI; measures total return multiple.

**Range:** 0–∞

## Cash Flow Conventions

### Input Convention

All cash flows are represented as **positive** amounts:

- **Paid-in capital (contributions):** Positive amount, flow_type = "paid_in"
- **Distributions:** Positive amount, flow_type = "distribution"
- **Residual value:** Positive or zero amount

### Data Convention

All values are stored as `Decimal`:

```python
from decimal import Decimal

cf = PrivateEquityCashFlow(
    flow_amount=Decimal("1000000.00"),  # $1M
    flow_date=date(2020, 1, 1),
    flow_type="paid_in"
)

investment = PrivateEquityInvestmentInput(
    cash_flows=[cf],
    residual_value=Decimal("1500000.00")  # $1.5M
)

result = PrivateEquityEngine.analyze(investment)
# result.tvpi == Decimal("2.5")  # 250% = 2.5x
```

### Ratio Convention

All output ratios are stored as `Decimal` with range 0–∞:

- 1.0 = 100% (breakeven, DPI or RVPI equal to paid-in)
- 1.5 = 150% (150% return multiple)
- 0.5 = 50% (50% of capital)

## Calculation Engine

### PrivateEquityEngine

Stateless orchestration for private equity analysis.

```python
@staticmethod
def analyze(investment: PrivateEquityInvestmentInput) -> PrivateEquityAnalyticsResult:
    """Analyze private equity investment and compute multiples.
    
    Parameters
    ----------
    investment : PrivateEquityInvestmentInput
        Investment with cash flows and residual value.
    
    Returns
    -------
    PrivateEquityAnalyticsResult
        Immutable result with DPI, RVPI, TVPI, MOIC.
        All ratios are None if total paid-in is zero.
    """
```

**Example:**

```python
from manco_risk.risk.private_assets import (
    PrivateEquityCashFlow,
    PrivateEquityInvestmentInput,
    PrivateEquityEngine,
)
from datetime import date
from decimal import Decimal

cf1 = PrivateEquityCashFlow(
    flow_amount=Decimal("10000000"),
    flow_date=date(2015, 3, 1),
    flow_type="paid_in"
)

cf2 = PrivateEquityCashFlow(
    flow_amount=Decimal("20000000"),
    flow_date=date(2023, 12, 31),
    flow_type="distribution"
)

investment = PrivateEquityInvestmentInput(
    cash_flows=[cf1, cf2],
    residual_value=Decimal("5000000")
)

result = PrivateEquityEngine.analyze(investment)

print(f"DPI: {result.dpi}")                # DPI: 2.0
print(f"TVPI: {result.tvpi}")              # TVPI: 2.5
print(f"Total paid-in: {result.total_paid_in}")  # 10000000
```

## Inputs

### Fund Summary

To analyze an investment, provide:

- List of cash flows (contributions and distributions)
  - Each flow: date, amount (positive Decimal), type ("paid_in" or "distribution")
- Residual value (current NAV or remaining investment value)
  - Positive or zero Decimal
  - As of the same date as the analysis

### Example: Buyout Investment

```python
investment = PrivateEquityInvestmentInput(
    cash_flows=[
        PrivateEquityCashFlow(Decimal("10000000"), date(2015, 3, 1), "paid_in"),
        PrivateEquityCashFlow(Decimal("5000000"), date(2019, 6, 30), "distribution"),
        PrivateEquityCashFlow(Decimal("15000000"), date(2023, 12, 31), "distribution"),
    ],
    residual_value=Decimal("5000000"),
    investment_id="BUYOUT_2015_A"
)
```

## Outputs

### Result Metrics

All output ratios as `Decimal`:

- **DPI:** 0–∞, None if zero paid-in
- **RVPI:** 0–∞, None if zero paid-in
- **TVPI:** 0–∞, None if zero paid-in
- **MOIC:** 0–∞, None if zero paid-in (MOIC = TVPI)

### Example Output

```python
result = PrivateEquityEngine.analyze(investment)

assert result.dpi == Decimal("2.0")      # 200% of paid-in distributed
assert result.rvpi == Decimal("0.5")     # 50% of paid-in remains
assert result.tvpi == Decimal("2.5")     # 250% total value multiple
assert result.moic == Decimal("2.5")     # Same as TVPI

assert result.total_paid_in == Decimal("10000000")
assert result.total_distributed == Decimal("20000000")
assert result.residual_value == Decimal("5000000")
```

## Scope: Private Equity (Slice 1)

**Implemented:**

- PrivateEquityCashFlow model
- PrivateEquityInvestmentInput model
- PrivateEquityAnalyticsResult model
- PrivateEquityEngine calculation
- DPI, RVPI, TVPI, MOIC metrics
- Comprehensive tests
- Decimal preservation
- Model immutability

**Deferred to future slices:**

- IRR calculation (not prioritized for Slice 1)
- Infrastructure DSCR and LTV
- Real estate stress calculations
- Private debt loan and covenant monitoring

## Out of Scope

The following are **not** implemented and are out of scope for private asset analytics:

- Full valuation platform
- Production private asset database
- Database querying or persistence
- File loading or ETL
- Streamlit pages or UI code
- Notebook-based calculations
- IRR calculation (Slice 1)
- Interest calculation or accrual
- Secondary market pricing
- Fund-of-funds aggregation
- Performance attribution

## Limitations

### Cash Flow Timing

This implementation does **not**:

- Account for cash flow timing in time-weighted return calculations
- Adjust for market values between cash flow dates
- Implement money-weighted returns or IRR

DPI, RVPI, TVPI, and MOIC are **not** time-weighted measures. They reflect cumulative values without temporal adjustment.

### Valuation Approach

This implementation does **not**:

- Question the accuracy of residual values
- Validate residual values against market benchmarks
- Apply haircuts or adjustments to NAV
- Account for fund management fees or expenses

Residual values are taken at face value as supplied in the input.

### Infrastructure, Real Estate, Private Debt

These modules are not yet implemented. Planned for future releases.

### IRR

Internal Rate of Return is deferred to a future slice. It requires:

- Efficient numerical solving (scipy.optimize)
- Day count convention decisions
- Cash flow timing validation
- Edge case handling (no cash flows, single period, flat IRR)

Implementing IRR in Slice 1 would add complexity without value if the four main multiples suffice.

## Testing

Comprehensive test suite in `tests/test_private_equity_analytics.py`:

- Model construction and validation
- Edge cases (zero paid-in, zero distributions, zero residual)
- Invalid inputs (negative values, invalid types)
- Decimal precision preservation
- Model equality and inequality
- Realistic scenarios (successful buyout, underperforming investment, fund with remaining NAV)
- Large-scale examples

## References

- **Private Equity Performance:** Cambridge Associates, Preqin (DPI, TVPI, MOIC definitions)
- **Decimal Precision:** Python Decimal module for exact arithmetic
- **Pydantic:** v2 models for typed, validated data structures
