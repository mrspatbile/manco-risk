# Annex IV-Style Reporting

## Purpose

The reporting layer packages risk calculations and source data into export-ready, typed report objects.

This reporting module implements Annex IV-style fund risk disclosure and identification for AIFM/UCITS funds.

**Key principle:** Reporting consumes risk outputs and source data. Reporting does not calculate risk.

## Architecture

The reporting module:

1. **Accepts immutable input objects** containing source data or pre-computed risk results
2. **Validates consistency** across multiple input sources (e.g., matching fund_id, valuation_date)
3. **Assembles immutable result objects** suitable for export and external systems
4. **Performs NO calculations** — all calculations happen in the risk module

### Module Boundaries

**Reporting MUST NOT:**
- Calculate VaR, Expected Shortfall, or any risk metric
- Query the database directly
- Fetch market data
- Perform ETL or data transformation
- Generate XML, PDF, or other file formats
- Use Streamlit or other UI frameworks

**Reporting SHOULD:**
- Package data supplied by the caller
- Validate consistency and required fields
- Return immutable, explicitly typed objects
- Document assumptions about input data

## Current Scope: Fund Identification and Asset Breakdown

**Slice 1** covered **fund identification**.

**Slice 2** (this slice) covers **asset breakdown**.

Future slices will add:
- Risk measures (VaR, ES, backtesting)
- Leverage
- Liquidity profile

### Fund Identification Section

Contains basic fund identifying information:

- `fund_id`: Fund identifier (integer)
- `fund_name`: Fund name (non-empty string)
- `fund_regime`: Fund regime classification (e.g., "UCITS", "AIF")
- `domicile`: Fund domicile country code (e.g., "LU", "IE")
- `base_currency`: Fund base currency (e.g., "EUR", "USD")
- `valuation_date`: Portfolio snapshot date
- `reporting_period_end`: End date of reporting period

All fields are required. All models are immutable.

### Asset Breakdown Section

Contains pre-aggregated asset class breakdown rows.

**Slice 2 scope:** Asset breakdown accepts pre-aggregated rows and does NOT aggregate positions.

Each asset breakdown row contains:

- `asset_class`: Asset class identifier (e.g., "Equities", "Bonds", "Cash", "Derivatives")
- `market_value`: Market value in base currency (Decimal, non-negative)
- `nav_percentage`: Percentage of NAV as decimal (e.g., 0.25 = 25%, non-negative)
- `currency`: Optional currency code (e.g., "EUR", "USD")
- `exposure_basis`: Optional exposure basis (e.g., "Long", "Short", "Notional")

**Important:** The asset breakdown section does NOT aggregate positions. Callers must supply already-aggregated rows. The service only validates and packages the supplied data.

## Inputs

### AnnexIVFundIdentificationInput

Represents the source data required to build a fund identification section.

**Constructor:**
```python
from datetime import date
from manco_risk.reporting import AnnexIVFundIdentificationInput

input_data = AnnexIVFundIdentificationInput(
    fund_id=1,
    fund_name="European Growth Fund",
    fund_regime="UCITS",
    domicile="LU",
    base_currency="EUR",
    valuation_date=date(2024, 6, 30),
    reporting_period_end=date(2024, 6, 30),
)
```

**Validation:**
- `fund_id`: Must be a positive integer
- `fund_name`: Must be non-empty (whitespace is stripped)
- `fund_regime`: Must be non-empty (e.g., "UCITS", "AIF")
- `domicile`: Must be non-empty (country code)
- `base_currency`: Must be non-empty (e.g., "EUR")
- `valuation_date`: Valid date
- `reporting_period_end`: Valid date

Raises `ValueError` if validation fails.

### AnnexIVAssetBreakdownRow

Represents a single asset class row in the asset breakdown.

**Constructor:**
```python
from decimal import Decimal
from manco_risk.reporting import AnnexIVAssetBreakdownRow

row = AnnexIVAssetBreakdownRow(
    asset_class="Equities",
    market_value=Decimal("500000.00"),
    nav_percentage=Decimal("0.50"),
    currency="EUR",
    exposure_basis="Long",
)
```

**Validation:**
- `asset_class`: Must be non-empty
- `market_value`: Must be non-negative (Decimal preserved)
- `nav_percentage`: Must be non-negative (Decimal preserved)
- `currency`: Optional
- `exposure_basis`: Optional

Raises `ValueError` if validation fails.

### AnnexIVAssetBreakdownInput

Container for pre-aggregated asset breakdown rows.

**Constructor:**
```python
from decimal import Decimal
from manco_risk.reporting import AnnexIVAssetBreakdownInput, AnnexIVAssetBreakdownRow

rows = [
    AnnexIVAssetBreakdownRow(
        asset_class="Equities",
        market_value=Decimal("600000.00"),
        nav_percentage=Decimal("0.60"),
    ),
    AnnexIVAssetBreakdownRow(
        asset_class="Bonds",
        market_value=Decimal("400000.00"),
        nav_percentage=Decimal("0.40"),
    ),
]

input_data = AnnexIVAssetBreakdownInput(rows=rows)
```

**Validation:**
- `rows`: Must contain at least one row

Raises `ValueError` if validation fails.

## Outputs

### AnnexIVFundIdentificationSection

Immutable fund identification result. Contains the same fields as input, after validation.

All fields are defensive-checked during construction:
- `fund_id` must be positive
- All string fields must be non-empty
- Dates must be valid

**Immutability:**
Once constructed, the section cannot be modified. Attempts to reassign fields raise an exception.

### AnnexIVAssetBreakdownSection

Immutable asset breakdown result. Contains pre-aggregated asset class rows.

**Fields:**
- `rows`: List of AnnexIVAssetBreakdownRow (at least one required)

All rows are defensive-checked during construction:
- Each row must be valid AnnexIVAssetBreakdownRow
- List must contain at least one row

**Immutability:**
Once constructed, the section cannot be modified.

### AnnexIVReport

Immutable report container that references one or more report sections.

**Fields:**
- `fund_identification`: AnnexIVFundIdentificationSection (required)
- `asset_breakdown`: AnnexIVAssetBreakdownSection (optional, default None)
- `included_sections`: List of section names (informational)

**Invariants:**
- `fund_identification` must be present
- `included_sections` must contain `"Fund Identification"`
- If `asset_breakdown` is supplied, `included_sections` must include `"Asset Breakdown"`

Future slices will add additional sections (e.g., `"Risk Measures"`, `"Leverage"`, `"Liquidity"`).

## Service: AnnexIVReportingService

Stateless service for building report objects. All methods are static.

### build_fund_identification()

Assembles a fund identification section from input data.

```python
from manco_risk.reporting import AnnexIVReportingService

input_data = AnnexIVFundIdentificationInput(...)
section = AnnexIVReportingService.build_fund_identification(input_data)
```

**Returns:** `AnnexIVFundIdentificationSection`

**Raises:** `ValueError` if input validation fails.

### build_asset_breakdown()

Assembles an asset breakdown section from pre-aggregated rows.

```python
input_data = AnnexIVAssetBreakdownInput(rows=[...])
section = AnnexIVReportingService.build_asset_breakdown(input_data)
```

**Returns:** `AnnexIVAssetBreakdownSection`

**Raises:** `ValueError` if rows are empty or invalid.

**Important:** This method does NOT aggregate positions. It accepts pre-aggregated rows and validates them.

### build_report()

Assembles a complete Annex IV report from section objects.

```python
fund_id_section = AnnexIVFundIdentificationSection(...)
asset_breakdown_section = AnnexIVAssetBreakdownSection(...)

# With fund identification only
report = AnnexIVReportingService.build_report(fund_id_section)

# With fund identification and asset breakdown
report = AnnexIVReportingService.build_report(
    fund_id_section,
    asset_breakdown_section,
)
```

**Parameters:**
- `fund_identification`: AnnexIVFundIdentificationSection (required)
- `asset_breakdown`: AnnexIVAssetBreakdownSection (optional)

**Returns:** `AnnexIVReport`

**Raises:** `ValueError` if section objects are invalid.

## Example Workflows

### UCITS Fund with Asset Breakdown

```python
from datetime import date
from decimal import Decimal
from manco_risk.reporting import (
    AnnexIVFundIdentificationInput,
    AnnexIVAssetBreakdownInput,
    AnnexIVAssetBreakdownRow,
    AnnexIVReportingService,
)

# 1. Create fund identification input
fund_id_input = AnnexIVFundIdentificationInput(
    fund_id=101,
    fund_name="European Growth UCITS Fund",
    fund_regime="UCITS",
    domicile="LU",
    base_currency="EUR",
    valuation_date=date(2024, 6, 30),
    reporting_period_end=date(2024, 6, 30),
)

# 2. Build fund identification section
fund_id_section = AnnexIVReportingService.build_fund_identification(fund_id_input)

# 3. Create pre-aggregated asset breakdown rows
rows = [
    AnnexIVAssetBreakdownRow(
        asset_class="Equities",
        market_value=Decimal("600000.00"),
        nav_percentage=Decimal("0.60"),
        currency="EUR",
    ),
    AnnexIVAssetBreakdownRow(
        asset_class="Bonds",
        market_value=Decimal("300000.00"),
        nav_percentage=Decimal("0.30"),
        currency="EUR",
    ),
    AnnexIVAssetBreakdownRow(
        asset_class="Cash",
        market_value=Decimal("100000.00"),
        nav_percentage=Decimal("0.10"),
        currency="EUR",
    ),
]

# 4. Create and build asset breakdown section
asset_breakdown_input = AnnexIVAssetBreakdownInput(rows=rows)
asset_breakdown_section = AnnexIVReportingService.build_asset_breakdown(
    asset_breakdown_input
)

# 5. Build complete report with both sections
report = AnnexIVReportingService.build_report(
    fund_id_section,
    asset_breakdown_section,
)

# 6. Export or display
print(f"Fund: {report.fund_identification.fund_name}")
print(f"Sections: {report.included_sections}")
for row in report.asset_breakdown.rows:
    print(f"  {row.asset_class}: {row.nav_percentage * 100}%")
```

### AIF Fund with Asset Breakdown (Long/Short)

```python
from datetime import date
from decimal import Decimal
from manco_risk.reporting import (
    AnnexIVFundIdentificationInput,
    AnnexIVAssetBreakdownInput,
    AnnexIVAssetBreakdownRow,
    AnnexIVReportingService,
)

fund_id_input = AnnexIVFundIdentificationInput(
    fund_id=202,
    fund_name="Strategic Opportunities AIF",
    fund_regime="AIF",
    domicile="IE",
    base_currency="USD",
    valuation_date=date(2024, 6, 30),
    reporting_period_end=date(2024, 6, 30),
)

fund_id_section = AnnexIVReportingService.build_fund_identification(fund_id_input)

# AIF with long and short positions
rows = [
    AnnexIVAssetBreakdownRow(
        asset_class="Equities",
        market_value=Decimal("400000.00"),
        nav_percentage=Decimal("0.40"),
        exposure_basis="Long",
    ),
    AnnexIVAssetBreakdownRow(
        asset_class="Equities",
        market_value=Decimal("100000.00"),
        nav_percentage=Decimal("0.10"),
        exposure_basis="Short",
    ),
    AnnexIVAssetBreakdownRow(
        asset_class="Derivatives",
        market_value=Decimal("500000.00"),
        nav_percentage=Decimal("0.50"),
        exposure_basis="Notional",
    ),
]

asset_breakdown_section = AnnexIVReportingService.build_asset_breakdown(
    AnnexIVAssetBreakdownInput(rows=rows)
)

report = AnnexIVReportingService.build_report(
    fund_id_section,
    asset_breakdown_section,
)
```

### Fund Identification Only

```python
from datetime import date
from manco_risk.reporting import (
    AnnexIVFundIdentificationInput,
    AnnexIVReportingService,
)

input_data = AnnexIVFundIdentificationInput(
    fund_id=101,
    fund_name="Test Fund",
    fund_regime="UCITS",
    domicile="LU",
    base_currency="EUR",
    valuation_date=date(2024, 6, 30),
    reporting_period_end=date(2024, 6, 30),
)

section = AnnexIVReportingService.build_fund_identification(input_data)

# Report with only fund identification (asset breakdown is optional)
report = AnnexIVReportingService.build_report(section)

print(f"Fund: {report.fund_identification.fund_name}")
print(f"Sections: {report.included_sections}")
```

## Source Assumptions

**Fund Data:**
- `fund_id`, `fund_name`, `fund_regime`, `domicile`, `base_currency` are sourced from the Fund table
- `valuation_date` is the portfolio snapshot date
- `reporting_period_end` is the end of the reporting period (typically equal to valuation_date for daily reports)

**Asset Breakdown Data:**
- Asset breakdown rows must be **pre-aggregated** by the caller
- `market_value` and `nav_percentage` are supplied by the caller, not calculated
- The reporting layer does NOT aggregate positions into asset classes
- Multiple rows for the same asset class are accepted as-is (e.g., Long and Short equities)
- NAV percentages do not need to sum to 1.0 (funds may have leverage or other structures)

**No Calculations:**
- No risk metrics are calculated in the reporting layer
- No positions are aggregated
- No portfolio analysis is performed
- No market values or NAV percentages are calculated

**Data Integrity:**
- Callers are responsible for ensuring all data is valid and up-to-date
- Reporting validates required fields but does not query the database
- Reporting accepts data exactly as supplied (no transformation or adjustment)

## Limitations

**Current limitations (by design, not bugs):**
- Asset breakdown does NOT aggregate positions. Callers must supply pre-aggregated rows.
- NAV percentages are not validated to sum to 1.0 (different fund structures may vary).
- No calculation of market values or NAV percentages.
- No position-level detail (only aggregated asset class rows).

**Future slices will add:**
- Risk measures (VaR, Expected Shortfall, backtesting results)
- Leverage calculations or ratios
- Liquidity profiling or time-to-liquidate
- XML or PDF generation
- CSSF or regulatory submission workflows
- Streamlit dashboard integration

## Out of Scope

- Full Annex IV XML filing
- CSSF submission workflow
- Production Bloomberg integration
- UI/dashboard rendering

## Testing

The test suite covers:
- Valid input and section construction
- Field validation and empty field rejection
- Immutability of all models
- Service statelessness
- Full workflows (UCITS and AIF examples)
- Consistency validation across section objects

Run tests with:
```bash
uv run pytest tests/test_annex_iv_reporting.py -v
```

## Future Extensions

Planned future slices will add sections for:

1. **Risk Measures** — VaR, Expected Shortfall, backtesting results
2. **Leverage** — Leverage ratios, notional exposures
3. **Liquidity Profile** — Time-to-liquidate buckets, redemption stress scenarios

Each section will follow the same pattern:
- Immutable input model
- Immutable result section
- Service method to build the section
- Comprehensive tests
- Documentation

## References

- AIFMD Annex IV: AIF risk disclosures and reporting requirements
- UCITS Directive Annex IV: Fund identification and risk reporting
- [PROJECT_SPEC.md](PROJECT_SPEC.md) — Project overview and architecture
- [CONVENTIONS.md](CONVENTIONS.md) — Data and naming conventions
