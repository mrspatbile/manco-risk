# Conventions and Standards

Project-specific conventions belong here.

The goal is to define units, representations, naming conventions, validation rules, and assumptions in a single location.

## Example Areas

### Numerical Representation

Examples:

- Percentages stored as decimals (`0.05` = 5%)
- Basis points stored as integers (`150` = 150 bps)
- Monetary amounts stored using `Decimal`
- Ratios stored as decimals (`1.25` = 125%)

### Basis Points (bps)

Use integer basis points only when:
- Data is sourced in bps (market data, credit spreads)
- Precision below 1 bps is not needed

**Conversion:**
- 1 bps = 0.0001 as decimal = 0.01%
- 150 bps = 0.015 as decimal = 1.5%

### Percentage Values

**Never store raw percentages.** Always convert:
- 5% → 0.05 (as Decimal)
- 150 bps → as integer 150

### Units

Examples:

- Monetary values in EUR
- Maturity expressed in days
- Interest rates per annum
- Dates stored as ISO 8601

### Naming Conventions

Examples:

- `spread_bps`
- `haircut_rate`
- `coverage_ratio`
- `market_value`

Field names should make units explicit where ambiguity is possible.

### Validation Rules

Examples:

- Non-negative monetary values
- Percentages constrained to valid ranges
- Valid identifier formats
- Required date ranges

### Identifier Standards

Examples:

- ISIN
- LEI
- CUSIP
- Internal identifiers

### Methodology Assumptions

Document assumptions that influence calculations.

Examples:

- Day count conventions
- Coverage ratio definitions
- Haircut methodologies
- Classification rules

## Project-Specific Rules

### Rates and Returns

Store rates and returns as decimals.

Examples:

- `0.05` = 5%
- `0.025` = 2.5%
- `-0.03` = -3%

Applies to:

- returns
- yields
- coupon rates
- haircuts
- LTV ratios
- recovery rates
- leverage ratios
- volatility
- VaR
- Expected Shortfall

### Basis Points

Store spreads and spread shocks as integer basis points.

Examples:

- `50` = 50 bps = 0.50%
- `150` = 150 bps = 1.50%

Field naming:

- `spread_bps`
- `spread_shock_bps`

### Monetary Values

Store monetary values using `Decimal`.

Examples:

- market value
- NAV
- exposure
- collateral value
- P&L

Field naming:

- `market_value`
- `nav`
- `exposure_amount`
- `pnl_amount`

### Fixed Income Conventions

Bloomberg conventions should be preserved at ingestion.

Examples:

- bond price `102.35` = 102.35% of par
- bond price `98.50` = 98.50% of par

Store:

- modified duration in years
- spread duration in years
- maturity in years unless explicitly documented otherwise

Field naming:

- `modified_duration`
- `spread_duration`
- `maturity_years`

### Risk Measures

VaR and Expected Shortfall should be stored as positive loss magnitudes.

Examples:

- `0.025` = 2.5% VaR
- `0.040` = 4.0% Expected Shortfall

Returns remain signed.

Examples:

- `-0.03` = loss of 3%
- `0.02` = gain of 2%

### Sign Conventions

Returns:

- positive = gain
- negative = loss

P&L:

- positive = profit
- negative = loss

VaR and Expected Shortfall:

- positive values representing loss thresholds

### Historical VaR Methodology

Historical VaR uses a fixed-position approach.

For a VaR date:

- portfolio positions are fixed
- historical market moves are applied to the fixed portfolio
- a hypothetical P&L distribution is generated
- VaR is estimated from the resulting return distribution

Historical NAV-return VaR is considered a separate methodology and must be explicitly labelled as such.

### Dates

Store dates as ISO 8601.

Examples:

- `2026-06-10`
- `2026-06-10T15:30:00Z`

Use UTC unless a timezone requirement is explicitly documented.

## Module Documentation

Each module includes:
- Module-level docstring explaining unit conventions
- Field-level docstrings for non-obvious fields
- Examples in comments where values appear
