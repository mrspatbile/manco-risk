# PRIIPs Methodology and Implementation

## Purpose

This document describes the manco-risk implementation of PRIIPs (Packaged Retail and Insurance-based Investment Products) outputs.

PRIIPs is implemented as a series of focused slices, each responsible for packaging or transforming pre-computed regulatory values into export-ready typed containers.

**Critical Design Principle:** PRIIPs slices consume pre-computed inputs from external calculation engines. They do NOT perform scenario calculations, simulations, or methodology implementations themselves.

---

## Slices

### Slice 1: Summary Risk Indicator (SRI)

**Status:** Implemented

**Module:** `manco_risk.risk.priips.sri`

**Responsibility:**
- Combine pre-computed Market Risk Measure (MRM) class and Credit Risk Measure (CRM) class
- Look up final Summary Risk Indicator (SRI) class from the regulatory combination table
- Return immutable, export-ready result

**Input:**
- `product_id: str` – Product identifier
- `valuation_date: date` – Snapshot date
- `mrm_class: int` – Pre-computed MRM class (1-7)
- `crm_class: int | None` – Pre-computed CRM class (1-6) or None if not applicable

**Output:**
- `sri_class: int` – Final SRI (1-7) from Delegated Regulation 2017/653 Annex II table
- Normalized `crm_class` (None → 1)

**Regulatory Reference:**
- Commission Delegated Regulation (EU) 2017/653, Annex II
  - Table combining MRM and CRM to produce final SRI class (1-7)

**Does NOT Include:**
- MRM class calculation (from VaR or volatility)
- CRM class calculation (from credit ratings)

---

### Slice 2: Performance Scenarios

**Status:** Implemented

**Module:** `manco_risk.risk.priips.performance_scenarios`

**Responsibility:**
- Package pre-computed performance scenario returns
- Validate inputs and preserve Decimal precision
- Return immutable, export-ready result

**Input:**
- `product_id: str` – Product identifier
- `valuation_date: date` – Snapshot date
- `methodology_version: str` – PRIIPs RTS version (e.g., "2017/653", "2021/2268")
- `recommended_holding_period_years: int` – RHP (positive)
- `stress_return: Decimal` – Pre-computed stress scenario return
- `unfavourable_return: Decimal` – Pre-computed unfavourable return
- `moderate_return: Decimal` – Pre-computed moderate return
- `favourable_return: Decimal` – Pre-computed favourable return

**Output:**
- All input fields preserved as `PerformanceScenariosResult`
- Decimal precision maintained
- Immutable container

**Regulatory Reference:**
- Commission Delegated Regulation (EU) 2017/653, Annex IV/V
  - Performance scenario calculation and presentation requirements
  - Stress, unfavourable, moderate, and favourable scenarios

**Does NOT Include:**
- Scenario calculation or simulation
- Performance projection methodology
- Market data integration
- Return generation or bootstrapping
- Monte Carlo path simulation

**Assumptions:**
- Performance scenario values are pre-computed externally
- Methodology version string is arbitrary and extensible (no hardcoded validation)
- Recommended holding period is arbitrary (only > 0 required)

---

### Slice 3: Cost Table

**Status:** Implemented

**Module:** `manco_risk.risk.priips.costs`

**Responsibility:**
- Package pre-computed PRIIPs cost values
- Validate inputs and preserve Decimal precision
- Return immutable, export-ready result
- Organise costs by component (entry, exit, ongoing, transaction, incidental)

**Input:**
- `product_id: str` – Product identifier
- `valuation_date: date` – Snapshot date
- `methodology_version: str` – PRIIPs RTS version (e.g., "2017/653", "2021/2268")
- `recommended_holding_period_years: int` – RHP (positive)
- `entry_cost: Decimal` – Pre-computed entry cost (percentage)
- `exit_cost: Decimal` – Pre-computed exit cost (percentage)
- `ongoing_cost: Decimal` – Pre-computed ongoing charge (percentage per year)
- `transaction_cost: Decimal` – Pre-computed transaction cost (percentage)
- `incidental_cost: Decimal` – Pre-computed incidental cost (percentage)

**Output:**
- All input fields preserved as `PRIIPSCostsResult`
- Decimal precision maintained
- Immutable container
- No derived totals or RIY calculation

**Regulatory Reference:**
- Commission Delegated Regulation (EU) 2017/653, Annex VI/VII
  - Cost calculation and presentation requirements
  - Cost component definitions and breakdown

**Does NOT Include:**
- Transaction cost calculation
- RIY (Reduction in Yield) calculation
- Implicit cost estimation
- Entry or exit cost derivation
- Ongoing charge aggregation
- Market data integration
- Cost calculation or transformation

**Assumptions:**
- All cost values are pre-computed externally
- Costs are stored as decimals (e.g., 0.01 = 1%)
- Methodology version string is arbitrary and extensible (no hardcoded validation)
- Recommended holding period is arbitrary (only > 0 required)

---

## Architecture

All PRIIPs slices follow the same architectural pattern:

### Data Models
- **Input Models** – Minimal, immutable containers for raw input
- **Result Models** – Immutable export-ready containers
- Pydantic v2 with `frozen=True`
- Field-level validators (input), defensive validators (output)

### Engines
- **Stateless** – No I/O, state, or side effects
- **Pure Functions** – Same input → same output
- No market data, database, or reporting dependencies
- Simple pass-through or table lookup only (no calculations)

### Tests
- Comprehensive test coverage
- Regulatory table validation where applicable
- Input validation edge cases
- Immutability verification
- Decimal preservation
- Realistic examples

### Constants
- Regulatory lookup tables (e.g., SRI combination table)
- Class ranges and bounds
- Scenario type names
- Cost component types

---

## Integration Points

PRIIPs results are consumed by:
- **Reporting layer** – Format KID documents, export tables
- **UI layer** – Display risk indicators, scenario tables, cost breakdowns
- **Database layer** – Persist calculation results for audit trail

PRIIPs engines **do NOT** depend on:
- Market data providers
- ETL validation
- Database repositories
- Reporting formatting
- Streamlit UI components

---

## Future Slices (Out of Scope)

The following PRIIPs capabilities are deferred to future slices (v0.4.0+):

### Slice 4: KID Generation
- HTML/PDF document generation
- KID template formatting
- Regulatory compliance validation
- SRI, scenario, cost table integration

### Slice 5: Scenario Calculation
- Performance scenario simulation (stress, unfavourable, moderate, favourable)
- Historical bootstrap or Monte Carlo methods
- Scenario parameter calibration

### Slice 6: Cost Calculation
- Transaction cost calculation
- RIY (Reduction in Yield) computation
- Implicit cost estimation
- Cost aggregation and totaling

---

## Methodology Limitations

### Scope
This implementation provides typed containers and table lookups only.

It is **not** a complete PRIIPs calculation engine. It is a narrow, focused implementation of output packaging and type safety.

### What is Implemented
- ✅ SRI class combination (table lookup)
- ✅ Performance scenario packaging
- ✅ Cost table structure
- ✅ KID-ready export models

### What is NOT Implemented
- ❌ VEV (Volatile-Equivalent VaR) calculation
- ❌ MRM class calculation
- ❌ CRM class calculation
- ❌ Performance scenario simulation
- ❌ Stress return bootstrapping
- ❌ Recommended holding period derivation
- ❌ Cost calculation or aggregation
- ❌ RIY calculation
- ❌ KID document generation

---

## Conventions

### Decimal Precision
- All costs stored as `Decimal`
- No float conversions
- String → Decimal coercion in input models
- Precision preserved through calculation and result

### Cost Sign Convention
- **Positive = Cost** (e.g., 0.01 = 1% cost)
- **Zero = No cost**
- Negative values accepted as pre-computed inputs

### Cost Components
- **Entry cost** – One-off fee on purchase
- **Exit cost** – One-off fee on sale
- **Ongoing cost** – Annual management charge (recurring)
- **Transaction cost** – Estimated cost of portfolio trading
- **Incidental cost** – Miscellaneous fees

### Methodology Version Flexibility
- Version strings are arbitrary and extensible
- No hardcoded validation against approved versions
- Allows future PRIIPs RTS versions (e.g., "2030/9999") without code change

### Recommended Holding Period
- Stored as positive integer (years)
- No enforced maximum (extensible to future products)
- Minimum 1 year (validated in input)

---

## References

### Regulatory
- **Regulation (EU) No 1286/2014** – PRIIPs Regulation (Level 1)
  - Article 8: KID content requirements
- **Commission Delegated Regulation (EU) 2017/653** – PRIIPs RTS (Level 2)
  - Annex II: MRM/CRM combination table (SRI)
  - Annex IV/V: Performance scenarios
  - Annex VI/VII: Cost tables
- **Commission Delegated Regulation (EU) 2021/2268** – RTS amendments
  - Updated PRIIPs methodology and templates

### Repository
- `src/manco_risk/risk/priips/` – Implementation modules
- `tests/test_priips_*.py` – Test suites
- `FEATURE_PARITY_ROADMAP.md` – Feature tracking
