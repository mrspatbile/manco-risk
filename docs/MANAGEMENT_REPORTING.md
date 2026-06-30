# Management Reporting

## Purpose

Management reporting outputs deliver risk analytics to fund governance, board review, and management decision-making. Management reports consume:

- Source fund data (identifiers, dates, NAV, AUM)
- Already-computed risk metrics (VaR, leverage, liquidity)
- Compliance and monitoring outputs

Management reporting **does not calculate risk**. It packages source data and pre-calculated results into export-ready typed objects.

## Architecture

### Separation of Concerns

```
Risk Calculation Layer (risk/)
    ↓ (outputs risk objects)
Reporting Layer (reporting/)
    ↓ (packages data into report objects)
UI/Export Layer (ui/, notebooks)
    ↓ (displays or exports results)
```

Management reporting imports from:
- `common/` — shared types and exceptions
- `risk/` — pre-calculated risk objects (input only; no direct calculation)

Management reporting does not:
- Calculate risk metrics
- Query databases directly
- Access market data
- Generate PDF, HTML, or visual output
- Contain Streamlit code
- Persist data to files or databases

### Models

**ManagementFundSummaryInput**
- Input validation model
- Accepts source fund data
- Validates field presence and ranges
- Optional fields allowed

**ManagementFundSummarySection**
- Immutable result model
- Frozen Pydantic v2 model (`ConfigDict(frozen=True)`)
- Defensive validation (second-layer checks)
- Ready for export

**ManagementMarketRiskInput**
- Input validation model
- Accepts already-computed market risk outputs
- Validates field presence and non-negative ranges
- Optional fields allowed

**ManagementMarketRiskSection**
- Immutable result model
- Frozen Pydantic v2 model
- Defensive validation (second-layer checks)
- Contains pre-calculated risk metrics

**ManagementRiskReport**
- Report container
- Assembles sections into a consolidated report
- Tracks which sections are included
- For Slice 1, includes fund summary only
- For Slice 2, optionally includes market risk
- Future slices will add leverage, liquidity, stress, exception sections

### Service

**ManagementReportService**
- Stateless orchestration layer (`@staticmethod` methods)
- `build_fund_summary(input) → ManagementFundSummarySection`
  - Accepts typed input with source data
  - Returns immutable section
  - No calculations performed
- `build_market_risk(input) → ManagementMarketRiskSection`
  - Accepts typed input with pre-calculated risk metrics
  - Returns immutable section
  - No calculations performed
- `build_report(fund_summary, market_risk=None) → ManagementRiskReport`
  - Assembles section(s) into report
  - fund_summary is always required
  - market_risk is optional
  - Tracks included sections

## Inputs

### Fund Summary Input

Source data required:

- **fund_id** (str, required, non-empty) — Fund identifier
- **fund_name** (str, required, non-empty) — Fund name
- **fund_regime** (str, required, non-empty) — "UCITS", "AIF", or other regime classification
- **base_currency** (str, required, non-empty) — Currency code (e.g., "EUR", "USD")
- **valuation_date** (date, required) — Portfolio snapshot date
- **nav** (Decimal, required, non-negative) — Net asset value in base currency
- **aum** (Decimal, optional, non-negative when supplied) — Assets under management
- **inception_date** (date, optional) — Fund inception date
- **reporting_period_end** (date, optional) — End of reporting period
- **methodology_version** (str, optional, non-empty when supplied) — Risk methodology version

### Market Risk Input

Already-computed market risk outputs required:

- **var_value** (Decimal, required, non-negative) — Value-at-Risk measure (e.g., `0.025` = 2.5% VaR)
- **var_method** (str, required, non-empty) — VaR calculation method
  - Examples: "Historical Simulation", "Parametric (Normal)", "Student-t"
- **expected_shortfall** (Decimal, optional, non-negative when supplied) — Expected shortfall measure
- **srri_class** (str, optional, non-empty when supplied) — Synthetic Risk and Reward Indicator class
  - Valid values: "1", "2", "3", "4", "5", "6", "7" (per UCITS PRIIPS)
- **global_exposure** (Decimal, optional, non-negative when supplied) — Global exposure ratio (e.g., `1.5` = 150%)
- **stress_summary_reference** (str, optional, non-empty when supplied) — Reference to stress testing results
- **methodology_version** (str, optional, non-empty when supplied) — Risk methodology version identifier

### Data Conventions

**Monetary values:** Store as `Decimal`.

Examples:
```python
nav = Decimal("250000000.00")  # €250M
aum = Decimal("1500000000.50") # €1.5B
```

**Rates and ratios:** Store as `Decimal` with range 0–1.

Example:
```python
leverage_ratio = Decimal("1.5")  # 150% leverage
```

**Basis points:** Store as `int`.

Example:
```python
spread_bps = 150  # 150 basis points = 1.5%
```

## Outputs

### Fund Summary Section

Immutable result containing:

- fund_id, fund_name, fund_regime, base_currency
- valuation_date, nav, (optional) aum, inception_date, reporting_period_end, methodology_version

Example:

```python
from decimal import Decimal
from datetime import date
from manco_risk.reporting import (
    ManagementFundSummaryInput,
    ManagementReportService,
)

input_data = ManagementFundSummaryInput(
    fund_id="LU001234567890",
    fund_name="Global Equity UCITS Fund",
    fund_regime="UCITS",
    base_currency="EUR",
    valuation_date=date(2024, 6, 30),
    nav=Decimal("250000000.00"),
    aum=Decimal("250000000.00"),
    inception_date=date(2010, 3, 15),
    reporting_period_end=date(2024, 6, 30),
    methodology_version="VaR_HistoricalSimulation_v1.0",
)

section = ManagementReportService.build_fund_summary(input_data)
# section.fund_name == "Global Equity UCITS Fund"
# section.nav == Decimal("250000000.00")
```

### Market Risk Section

Immutable result containing:

- var_value, var_method (required)
- (optional) expected_shortfall, srri_class, global_exposure, stress_summary_reference, methodology_version

Example:

```python
from manco_risk.reporting import (
    ManagementMarketRiskInput,
    ManagementReportService,
)

market_risk_input = ManagementMarketRiskInput(
    var_value=Decimal("0.0275"),
    var_method="Historical Simulation",
    expected_shortfall=Decimal("0.0425"),
    srri_class="5",
    global_exposure=Decimal("1.2"),
    stress_summary_reference="Stress Scenarios Q2 2024",
    methodology_version="VaR_HistoricalSimulation_v1.0",
)

market_risk = ManagementReportService.build_market_risk(market_risk_input)
# market_risk.var_value == Decimal("0.0275")
# market_risk.srri_class == "5"
```

### Management Report

Immutable container with:

- fund_summary (ManagementFundSummarySection, required)
- market_risk (ManagementMarketRiskSection, optional)
- included_sections (list of section names included)

Example:

```python
report = ManagementReportService.build_report(section, market_risk)
# report.fund_summary.fund_name == "Global Equity UCITS Fund"
# report.market_risk.var_value == Decimal("0.0275")
# report.included_sections == ["Fund Summary", "Market Risk"]
```

## Scope by Slice

### Slice 1

- Fund summary section
- ManagementReportService.build_fund_summary()
- ManagementReportService.build_report() (includes fund summary only)

### Slice 2 (Current)

- Market risk summary section
- ManagementReportService.build_market_risk()
- ManagementReportService.build_report() (includes fund summary and optional market risk)

### Future Slices

- Stress testing summary (P&L outcomes vs. limits)
- Leverage summary (gross, commitment, by asset class)
- Liquidity summary (TTL profile, redemption capacity)
- Exception summary (policy breaches, data gaps, validation issues)
- Board-style report layout and export

## Source Assumptions

### Fund Data

- Fund identifiers are stable across valuations
- Fund names follow consistent conventions
- Fund regime (UCITS/AIF) is stable
- Base currency is stable per fund
- NAV is the authoritative net asset value as of valuation_date

### Dates

- valuation_date is the portfolio snapshot date
- reporting_period_end is the end of the management reporting period
- inception_date is the historical fund inception (immutable)
- All dates are ISO 8601 format

### Optional Fields

- aum is assets under management (may differ from nav, e.g., if leverage is applied)
- inception_date is known for most funds but may be unknown for new or legacy entities
- reporting_period_end is the end of the reporting month/quarter/year
- methodology_version identifies the risk calculation methodology (e.g., "VaR_HistoricalSimulation_v1.0")

### Market Risk Data

- var_value is supplied from risk calculation module (not calculated here)
- var_method describes the VaR calculation methodology used (e.g., "Historical Simulation", "Parametric")
- expected_shortfall is supplied from risk calculation module
- srri_class is supplied from PRIIPS or risk analytics module (values 1–7)
- global_exposure is supplied from risk calculation module (leverage-adjusted)
- stress_summary_reference points to stress testing results generated by risk module
- All risk metrics are already-computed outputs; no calculations performed here

## Limitations

### What This Reporting Module Does Not Do

- Calculate NAV (supplied from source)
- Calculate AUM (supplied from source)
- Calculate returns or performance metrics
- Calculate VaR (supplied from risk module)
- Calculate Expected Shortfall (supplied from risk module)
- Calculate SRRI class (supplied from PRIIPS or risk module)
- Calculate global exposure (supplied from risk module)
- Calculate stress tests (supplied from risk module)
- Calculate leverage or liquidity metrics
- Query databases
- Fetch or manipulate market data
- Generate PDF, HTML, or Streamlit output
- Persist data to files or databases
- Implement display-specific logic or styling

### Data Quality Assumptions

- Input data is already validated at the source layer
- Fund identifiers are valid and stable
- Dates are valid and consistent
- NAV and AUM are non-negative
- Strings are trimmed and non-empty

Input validation enforces these assumptions; the output is trusted to be consistent.

## Testing

Comprehensive test coverage includes:

- Valid input construction
- Field-level validation (empty, negative, out-of-range)
- Decimal precision preservation
- Immutability enforcement
- Stateless service behavior
- Realistic UCITS and AIF examples
- Report assembly and section tracking

See `tests/test_management_report.py` for test suite.

## References

- **AIFMD Annex IV** — AIF disclosures and reporting requirements
- **UCITS Directive** — Fund identification and risk monitoring
- **Feature Parity Roadmap** — Management reporting capabilities and milestones
