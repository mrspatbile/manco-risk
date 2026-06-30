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

## Current Scope: Fund Identification

This first implementation slice covers **fund identification only**.

Future slices will add:
- Asset breakdown
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

## Outputs

### AnnexIVFundIdentificationSection

Immutable fund identification result. Contains the same fields as input, after validation.

All fields are defensive-checked during construction:
- `fund_id` must be positive
- All string fields must be non-empty
- Dates must be valid

**Immutability:**
Once constructed, the section cannot be modified. Attempts to reassign fields raise an exception.

### AnnexIVReport

Immutable report container that references one or more report sections.

For this slice, contains only `fund_identification`.

**Fields:**
- `fund_identification`: AnnexIVFundIdentificationSection
- `included_sections`: List of section names (informational)

For this slice, `included_sections` must contain `"Fund Identification"`.

Future slices will add additional sections (e.g., `"Asset Breakdown"`, `"Risk Measures"`).

## Service: AnnexIVReportingService

Stateless service for building report objects.

### build_fund_identification()

Assembles a fund identification section from input data.

```python
from manco_risk.reporting import AnnexIVReportingService

input_data = AnnexIVFundIdentificationInput(...)
section = AnnexIVReportingService.build_fund_identification(input_data)
```

**Returns:** `AnnexIVFundIdentificationSection`

**Raises:** `ValueError` if input validation fails.

### build_report()

Assembles a complete Annex IV report from section objects.

```python
fund_id_section = AnnexIVFundIdentificationSection(...)
report = AnnexIVReportingService.build_report(fund_id_section)
```

**Returns:** `AnnexIVReport`

**Raises:** `ValueError` if section objects are invalid.

## Example Workflow

### UCITS Fund

```python
from datetime import date
from manco_risk.reporting import (
    AnnexIVFundIdentificationInput,
    AnnexIVReportingService,
)

# 1. Create input data (from database or supplied source)
input_data = AnnexIVFundIdentificationInput(
    fund_id=101,
    fund_name="European Growth UCITS Fund",
    fund_regime="UCITS",
    domicile="LU",
    base_currency="EUR",
    valuation_date=date(2024, 6, 30),
    reporting_period_end=date(2024, 6, 30),
)

# 2. Build fund identification section
fund_id_section = AnnexIVReportingService.build_fund_identification(input_data)

# 3. Build complete report (fund identification only for this slice)
report = AnnexIVReportingService.build_report(fund_id_section)

# 4. Export or display
print(f"Fund: {report.fund_identification.fund_name}")
print(f"Domicile: {report.fund_identification.domicile}")
print(f"Sections: {report.included_sections}")
```

### AIF Fund

```python
input_data = AnnexIVFundIdentificationInput(
    fund_id=202,
    fund_name="Strategic Opportunities AIF",
    fund_regime="AIF",
    domicile="IE",
    base_currency="USD",
    valuation_date=date(2024, 6, 30),
    reporting_period_end=date(2024, 6, 30),
)

section = AnnexIVReportingService.build_fund_identification(input_data)
report = AnnexIVReportingService.build_report(section)
```

## Source Assumptions

**Fund Data:**
- `fund_id`, `fund_name`, `fund_regime`, `domicile`, `base_currency` are sourced from the Fund table
- `valuation_date` is the portfolio snapshot date
- `reporting_period_end` is the end of the reporting period (typically equal to valuation_date for daily reports)

**No Calculations:**
- No risk metrics are calculated in the reporting layer
- No positions are aggregated
- No portfolio analysis is performed

**Data Integrity:**
- Callers are responsible for ensuring fund data is valid and up-to-date
- Reporting validates required fields but does not query the database

## Limitations

**This slice does NOT implement:**
- Asset breakdown or position grouping
- Risk measures (VaR, Expected Shortfall, backtesting results)
- Leverage calculations or ratios
- Liquidity profiling or time-to-liquidate
- XML or PDF generation
- CSSF or regulatory submission workflows
- Streamlit dashboard integration

**These capabilities are planned for future slices.**

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

1. **Asset Breakdown** — Position grouping by asset class, issuer, rating, maturity
2. **Risk Measures** — VaR, Expected Shortfall, backtesting results
3. **Leverage** — Leverage ratios, notional exposures
4. **Liquidity Profile** — Time-to-liquidate buckets, redemption stress scenarios

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
