# Prototype Field Inventory Method

Project: `manco-risk`  
Context: pre-database domain modelling before MRS-128  
Purpose: classify fields from the prototype repository `../manco-risk-mngmt` without copying its architecture.

---

## 1. Objective

This document defines the method for reviewing fields found in the prototype repository before designing the database schema for `manco-risk`.

The goal is not to migrate the prototype field-by-field.

The goal is to identify business concepts, classify them correctly, and decide whether they belong in the new domain model.

The inventory must distinguish:

- source data
- reference data
- regulatory metadata
- methodology settings
- internal risk limits
- calculation inputs
- derived outputs
- reporting fields
- filing snapshots
- audit and lineage fields

A field must not be treated as regulatory only because it exists in the prototype.

---

## 2. Guiding principle

The prototype is evidence, not authority.

A prototype field means only that the prototype once used that field. It does not prove that the field is:

- regulatory
- mandatory
- correctly named
- correctly located
- source data
- suitable for the new database
- required in Phase 1

Each field must be reclassified against the new architecture and domain model.

---

## 3. Working assumptions

The new project follows a layered architecture:

```text
Fund administrator files
→ ETL and validation
→ SQLite database
→ Risk engines
→ Reporting layer
→ Notebooks / UI for review only
```

The database must support source data, methodology versioning, calculation reproducibility and reporting lineage.

The database must not be designed as a flat collection of Annex IV, regulatory or prototype fields.

---

## 4. Field classification categories

Each prototype field must be assigned one primary category.

### 4.1 Source data

Data received from an administrator file, accounting extract, market data provider, investor register, fund document or other operational source.

Examples:

- quantity
- market value
- NAV
- ISIN
- counterparty LEI
- collateral balance
- redemption notice period

### 4.2 Reference data

Stable or semi-stable classification data, code lists or allowed values.

Examples:

- asset class
- currency
- country code
- fund regime
- instrument type
- LMT type
- SFDR article classification

### 4.3 Regulatory metadata

Versioned regulatory source, article, field definition, XML tag, validation rule, allowed value or reporting schema item.

Examples:

- Annex IV XML tag
- ESMA field name
- CSSF schema version
- allowed value list
- conditionality rule

### 4.4 Methodology setting

A fund, ManCo or engine-level choice that affects how calculations are performed.

Examples:

- VaR confidence level
- VaR lookback period
- leverage method
- hedging eligibility rule
- liquidity bucket scheme
- LST scenario configuration
- collateral haircut methodology

### 4.5 Internal risk limit

A monitoring threshold or control level defined internally.

Examples:

- issuer exposure limit
- counterparty limit
- liquidity warning threshold
- leverage alert threshold
- concentration limit

### 4.6 Calculation input

A value consumed by a calculation engine. A calculation input may also be source data or methodology data, so the inventory should record both the business meaning and the role in calculations.

Examples:

- position market value
- modified duration
- historical return series
- FX rate
- NAV denominator
- haircut rate

### 4.7 Derived output

A value calculated by the platform.

Examples:

- VaR
- Expected Shortfall
- gross leverage ratio
- commitment leverage ratio
- issuer exposure percentage
- counterparty exposure percentage
- liquidity bucket percentage
- stress loss
- backtesting exception

Derived outputs should generally link to a calculation run.

### 4.8 Reporting field

A value prepared for a management, board, investor or regulatory report.

Examples:

- Annex IV field value
- board report metric
- reporting block rank
- report display label

Reporting fields should not be stored as operating source data.

### 4.9 Filing snapshot

The exact value, status or metadata related to a regulatory submission.

Examples:

- submitted value
- schema version
- validation status
- submission timestamp
- correction flag
- regulator feedback message

### 4.10 Audit and lineage field

A field used to trace, approve, override or evidence a value.

Examples:

- source snapshot ID
- calculation run ID
- methodology version ID
- override flag
- override reason
- approver
- evidence link

---

## 5. Regulatory authority classification

If a field has a regulatory or supervisory basis, classify the source precisely.

Use one of:

- Level 1 directive or regulation
- delegated regulation
- RTS
- ITS
- ESMA guideline
- ESMA technical guidance
- CSSF implementation or circular
- Luxembourg law
- fund documentation
- internal risk policy
- industry best practice
- not regulatory
- unclear

Do not classify a field as regulatory until the source is identified.

---

## 6. Inventory template

Use this template for each prototype field.

```text
prototype_field_name:
prototype_location:
prototype_context:
example_values:

business_meaning:

primary_classification:
    source data / reference data / regulatory metadata / methodology setting /
    internal risk limit / calculation input / derived output / reporting field /
    filing snapshot / audit and lineage / unclear

secondary_role_if_any:
    source data / calculation input / reporting input / derived output / none

regulatory_authority_classification:
    Level 1 / delegated regulation / RTS / ITS / ESMA guideline /
    ESMA technical guidance / CSSF implementation / Luxembourg law /
    fund documentation / internal risk policy / industry best practice /
    not regulatory / unclear

source_reference:
    document / article / annex / field name / internal policy / unknown

recommended_treatment:
    keep / rename / move to methodology / move to calculation result /
    move to reporting schema / move to filing snapshot / derive, do not store /
    keep as audit field / drop / unclear

target_domain:
    fund master / instrument and issuer / position / market data /
    NAV and accounting / methodology / calculation run /
    counterparty-derivative-collateral-SFT / liquidity-LMT /
    reporting-regulatory metadata / audit-lineage / deferred

target_entity_candidate:

phase:
    Phase 1 / Phase 2 / Phase 3 / later / not in scope / unclear

notes:

open_questions:
```

---

## 7. Recommended inventory table columns

For a spreadsheet or markdown table, use these columns:

| Column | Purpose |
|---|---|
| `prototype_field_name` | Original field name |
| `prototype_location` | File, notebook, class, function, CSV or report where found |
| `prototype_context` | How the field is used in the prototype |
| `example_values` | Representative values if available |
| `business_meaning` | Plain-English meaning |
| `primary_classification` | Main field category |
| `secondary_role` | Calculation input, reporting input or none |
| `regulatory_authority_classification` | Exact regulatory or non-regulatory category |
| `source_reference` | Source document, article, field, policy or unknown |
| `recommended_treatment` | Keep, rename, move, derive, drop, unclear |
| `target_domain` | New conceptual domain |
| `target_entity_candidate` | Candidate new entity |
| `phase` | Phase 1, Phase 2, Phase 3, later, not in scope |
| `notes` | Design notes |
| `open_questions` | Questions to resolve before schema design |

---

## 8. Treatment decision rules

### 8.1 Keep

Use when the field is a valid source, reference, methodology, output or reporting concept and fits the new architecture.

### 8.2 Rename

Use when the concept is valid but the prototype name is vague, misleading or lacks unit clarity.

Examples:

- `spread` → `spread_bps` if stored in basis points
- `haircut` → `haircut_rate` if stored as decimal
- `mv` → `market_value`

### 8.3 Move to methodology

Use when the field represents a choice, assumption, calibration or rule.

Examples:

- liquidity bucket definitions
- hedging eligibility logic
- collateral haircut rule
- VaR lookback period

### 8.4 Move to calculation result

Use when the field is produced by a calculation.

Examples:

- VaR
- Expected Shortfall
- leverage ratio
- stress loss
- exposure percentage

### 8.5 Move to reporting schema

Use when the field exists because a report or regulatory template requires it.

Examples:

- Annex IV field name
- XML tag
- validation code
- report block name

### 8.6 Move to filing snapshot

Use when the field records what was submitted or validated for a reporting period.

Examples:

- submitted value
- submission status
- rejection message
- correction flag

### 8.7 Derive, do not store as source

Use when the value can be recomputed from source data and methodology.

Examples:

- issuer exposure percentage
- portfolio liquidity bucket percentage
- leverage ratio
- VaR as percentage of NAV

### 8.8 Drop

Use when the field is prototype-specific, duplicated, unused, misleading or not part of the new scope.

### 8.9 Unclear

Use when the business meaning or source cannot be established.

No unclear field should enter the database schema without resolution.

---

## 9. Domain mapping guide

### 9.1 Fund master

Use for:

- fund identity
- AIFM identity
- fund regime
- domicile
- base currency
- legal structure
- open-ended or closed-ended status
- reporting obligation
- share class terms

Do not use for:

- NAV by date
- risk result
- reporting field value

### 9.2 Instrument and issuer

Use for:

- ISIN
- ticker
- issuer
- asset class
- country
- sector
- maturity
- coupon
- duration if reference-date treatment is clear

Do not use for:

- position market value
- VaR contribution
- reporting aggregation rank

### 9.3 Position

Use for:

- fund holdings by valuation date
- quantity
- market value
- exposure amount if sourced or directly validated
- source file linkage

Do not use for:

- VaR
- ES
- leverage ratio
- Annex IV field values
- calculated liquidity bucket outputs

### 9.4 NAV and accounting

Use for:

- NAV snapshot
- AUM snapshot
- GAV snapshot
- subscriptions
- redemptions

Do not use for:

- VaR output
- leverage output
- reporting XML field values

### 9.5 Methodology

Use for:

- VaR methodology
- leverage methodology
- liquidity methodology
- valuation policy
- internal limits
- LMT calibration rules

Do not use for:

- measured results
- raw positions

### 9.6 Calculation run

Use for:

- calculation execution metadata
- input snapshot links
- methodology version links
- VaR result
- ES result
- backtesting result
- leverage result
- stress result
- liquidity bucket result

Do not use for:

- source positions
- regulatory field definitions

### 9.7 Counterparty, derivative, collateral and SFT

Use for:

- derivative trade or position data
- counterparty identity
- clearing status
- notional
- collateral balances
- SFT records
- margin records

Separate source attributes from calculated exposures and leverage treatment.

### 9.8 Reporting and regulatory metadata

Use for:

- regulation source
- field definition
- allowed values
- validation rules
- report schema version
- reporting field mapping
- filing value
- submission feedback

Do not use for:

- operating source data
- raw holdings

### 9.9 Audit and lineage

Use for:

- source snapshot
- calculation run
- methodology version
- override evidence
- approval information
- submission link

This should be available across domains, not added late as a reporting patch.

---

## 10. Phase classification guide

### Phase 1

Include only fields needed for:

- fund identity
- instrument metadata
- position ingestion
- NAV snapshots
- market data access
- fixed-position Historical VaR
- Expected Shortfall
- 1-day backtesting
- calculation reproducibility

### Phase 2

Include fields needed for:

- parametric VaR
- Student-t VaR
- stress testing
- leverage analytics
- liquidity profiling
- concentration monitoring

### Phase 3

Include fields needed for:

- liquidity stress testing
- LMT simulation
- Annex IV-style reporting
- management risk reporting
- Streamlit dashboard support

### Later

Use for specialised domains such as:

- full Annex IV XML submission
- EMIR reporting
- SFTR reporting
- PRIIPs
- SFDR and Taxonomy
- private asset valuation governance
- regulator feedback workflow
- AML / KYC

---

## 11. Initial priority groups for prototype review

Review prototype fields in this order:

1. fund and share class fields
2. instrument and issuer fields
3. position fields
4. NAV and accounting fields
5. market data fields
6. VaR and ES fields
7. backtesting fields
8. leverage fields
9. liquidity fields
10. counterparty fields
11. derivative fields
12. collateral fields
13. hedging fields
14. reporting fields
15. regulatory fields
16. audit, override and manual adjustment fields

This order keeps Phase 1 concepts first and prevents Annex IV or late prototype additions from dominating the schema.

---

## 12. Red flags during inventory

Flag any prototype field that meets one of these patterns:

- field name has no unit where unit matters
- field stores a percentage as `5` instead of `0.05`
- field mixes source and calculated values
- field has unclear date basis
- field has unclear fund or share class scope
- field looks like an Annex IV field inside a source table
- field stores a derived result without calculation metadata
- field stores a methodology choice without versioning
- field stores a manual override without reason or approval evidence
- field name includes vague words such as `flag`, `type`, `value`, `amount`, `ratio` without context
- field appears in notebooks only
- field is hardcoded in a calculation
- field controls logic but is not documented

---

## 13. Output of the inventory exercise

The output should be a classified inventory with three sections.

### 13.1 Accepted Phase 1 concepts

Fields or concepts ready to support the Phase 1 database schema.

### 13.2 Deferred concepts

Fields or concepts that are valid but belong to Phase 2, Phase 3 or later.

### 13.3 Rejected or unresolved concepts

Fields that should be dropped, renamed later or investigated further.

No unresolved concept should be added to the database schema.

---

## 14. Suggested working prompt for Claude Code

Use this prompt when asking Claude Code to inspect the prototype repository.

```text
Inspect the prototype repository `../manco-risk-mngmt` for data fields only.

Do not propose code changes.
Do not design the database schema.
Do not infer that a field is regulatory because it exists in the prototype.
Do not copy prototype architecture.

Create a field inventory using the template in `prototype_field_inventory.md`.

For each field, capture:
- original field name
- location
- usage context
- business meaning
- example values if available
- primary classification
- regulatory authority classification
- recommended treatment
- target conceptual domain
- target entity candidate
- phase
- notes and open questions

Pay special attention to fields related to:
- counterparty
- collateral
- leverage
- hedging
- liquidity
- regulatory reporting
- derived outputs stored as source data

Return the result as a markdown table grouped by domain.
```

---

## 15. Decision gate before database schema design

Database schema design should start only after these checks are complete:

- Phase 1 entity list is agreed
- Phase 1 field list is agreed
- each field has a classification
- derived outputs are separated from source data
- reporting fields are separated from operating data
- methodology settings are versioned conceptually
- lineage requirements are known
- unresolved prototype fields are either deferred or excluded

