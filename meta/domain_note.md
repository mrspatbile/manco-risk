Working module: **domain model / pre-database design for MRS-128**.

Below is the first domain-modelling note for `manco-risk`.

# Domain modelling note before database schema design

## 1. Purpose

The purpose of this step is to define the business model before designing SQLite tables, ETL contracts or risk engines.

The main design rule is:

```text
Source data, methodology settings, calculation outputs and reporting fields must not be mixed.
```

This follows the project architecture, where ETL validates data, the database stores clean data and snapshots, risk modules calculate results, reporting formats outputs, and UI/notebooks remain thin review layers.  

The regulatory research also makes the same point: the database must be more detailed than the regulatory report, and regulatory reporting should be an output layer rather than the operating data model. 

---

# 2. Domain boundaries

The platform should be split into these conceptual domains.

## A. Fund master domain

Purpose: store stable fund-level identity, legal structure and reporting scope.

Likely entities:

```text
AIFM
Fund
ShareClass
FundRegime
ReportingObligation
```

Examples of concepts:

```text
fund name
domicile
base currency
AIF / UCITS / MMF / ELTIF classification
open-ended / closed-ended flag
AIFM authorisation status
reporting frequency
share class currency
redemption frequency
notice period
lock-up period
```

Classification:

```text
mostly source data and reference data
some regulatory classification
some fund-level settings
```

Do not mix this with risk calculation outputs.

---

## B. Instrument and issuer domain

Purpose: describe what the fund holds.

Likely entities:

```text
Instrument
Issuer
SecurityIdentifier
InstrumentClassification
```

Examples of concepts:

```text
ISIN
ticker
asset class
currency
issuer LEI
issuer country
sector
maturity date
coupon rate
modified duration
spread duration
derivative flag
SFT flag
securitisation flag
```

Classification:

```text
source data
market data reference data
regulatory reference classification where applicable
```

This domain should support market risk, concentration, liquidity, leverage and reporting, but should not contain report-specific fields.

The current market data design already introduces typed models such as `InstrumentInfo`, `Price`, `PriceHistory` and `FXRate`, which gives a useful starting point for this domain. 

---

## C. Position domain

Purpose: store holdings at a valuation date.

Likely entities:

```text
PositionSnapshot
Position
PositionValuation
```

Examples of concepts:

```text
fund
valuation date
instrument
quantity
market value
currency
local market value
base currency market value
NAV percentage
cost value
price source
source file
```

Classification:

```text
source data
validated ETL output
accounting / administrator data
```

Position records should not become a dumping ground for:

```text
VaR result
ES result
leverage ratio
Annex IV field
liquidity bucket result
stress test result
reporting rank
```

Those belong to calculation output or reporting layers.

---

## D. Market data domain

Purpose: expose prices, FX rates, curves and instrument metadata through provider interfaces.

Likely entities or concepts:

```text
MarketDataProvider
Price
PriceHistory
FXRate
InstrumentInfo
MarketDataAdjustment
```

Classification:

```text
market data source
provider-normalised reference data
provider-specific adjustment
```

Provider-specific corrections belong in the market data layer, not in ETL, risk, reporting or UI. The architecture file is explicit that provider anomalies and documented overrides should be handled before downstream modules consume the data. 

---

## E. NAV and accounting snapshot domain

Purpose: store fund-level accounting values used as denominators and reconciliation anchors.

Likely entities:

```text
NAVSnapshot
AUMSnapshot
FundFlow
```

Examples of concepts:

```text
NAV
GAV
AUM
subscriptions
redemptions
share class NAV
valuation date
accounting source
```

Classification:

```text
source data
administrator/accounting data
some derived accounting outputs
```

Important distinction:

```text
NAV is source/accounting data for many risk calculations.
VaR as % NAV is a risk output.
```

---

## F. Methodology domain

Purpose: store choices that affect calculations.

Likely entities:

```text
RiskMethodology
VaRMethodology
LeverageFramework
LiquidityFramework
ValuationPolicy
LMTFramework
RiskLimitFramework
```

Examples of concepts:

```text
VaR confidence level
VaR holding period
VaR observation window
fixed-position VaR flag
gross leverage method
commitment leverage method
hedging treatment
netting treatment
liquidity bucket scheme
LST scenario assumptions
collateral haircut methodology
risk limit thresholds
valuation methodology
```

Classification:

```text
fund methodology setting
internal risk configuration
regulatory-methodology selector
versioned configuration
```

This domain is central because many values are not directly “regulatory fields”. The regulatory file separates prescribed rules from framework-required but fund-defined variables, such as liquidity buckets, LST assumptions, LMT thresholds, AIF counterparty limits and valuation methodology. 

---

## G. Calculation run domain

Purpose: store reproducible calculation events and their outputs.

Likely entities:

```text
RiskCalculationRun
HistoricalVaRResult
ExpectedShortfallResult
BacktestResult
StressTestResult
LeverageResult
LiquidityBucketResult
ConcentrationResult
CounterpartyExposureResult
```

Examples of concepts:

```text
calculation date
as-of date
input snapshot
methodology version
engine version
result value
confidence level
holding period
lookback period
P&L distribution reference
exceptions count
breach flag
```

Classification:

```text
derived output
calculation snapshot
lineage object
```

The project already states that all calculations must be reproducible and methodologies documented. 

---

## H. Counterparty, derivative, collateral and SFT domain

Purpose: model exposures that are not fully captured by plain long-only positions.

Likely entities:

```text
Counterparty
DerivativePosition
SFTPosition
CollateralBalance
MarginBalance
ClearingRelationship
```

Examples of concepts:

```text
counterparty LEI
counterparty type
OTC derivative exposure
clearing status
CCP LEI
notional
market value
delta-adjusted exposure
collateral type
collateral value
haircut
reuse flag
margin type
hedging flag
currency hedging flag
leverage contribution
```

Classification:

```text
source data
regulatory reference data
methodology input
calculation output depending on field
```

This is one of the areas where the prototype seems to have accumulated ad hoc fields. In the new model, these concepts should be separated carefully:

```text
counterparty identity ≠ counterparty exposure result
collateral balance ≠ collateral haircut methodology
hedging flag from source ≠ hedging eligibility for commitment leverage
leverage contribution ≠ source position field
```

---

## I. Liquidity and LMT domain

Purpose: support liquidity profiling, LST and liquidity management tools.

Likely entities:

```text
LiquidityFramework
LiquidityBucketScheme
LiquidityBucketResult
LiquidityStressScenario
LiquidityStressTestResult
LMTReferenceData
FundLMTSelection
LMTActivationEvent
```

Examples of concepts:

```text
redemption terms
asset liquidity methodology
liquidity bucket definition
time to liquidate
investor redemption bucket
selected LMT
activation threshold
activation status
swing pricing factor
redemption gate threshold
anti-dilution levy rate
```

Classification:

```text
methodology setting
regulatory reference data
operational event
derived output
```

Liquidity buckets should be child rows or repeated outputs, not scalar fields on a fund or position. The regulatory file explicitly recommends bucket-style output tables for liquidity and investor redemption profiles. 

---

## J. Reporting and regulatory metadata domain

Purpose: define regulatory schemas and store filing outputs.

Likely entities:

```text
RegulationSource
RegulatoryRequirement
VariableDefinition
AllowedValueSet
ValidationRule
ReportSchemaVersion
RegulatoryFiling
ReportingFieldValue
RepeatedBlockValue
SubmissionFeedback
```

Examples of concepts:

```text
Annex IV field definition
XML tag
allowed value
mandatory status
conditionality rule
schema version
CSSF guidance version
submitted value
validation result
regulator feedback
```

Classification:

```text
regulatory metadata
reporting schema
filing snapshot
submission workflow
```

Important rule:

```text
Annex IV field definitions do not belong inside Position, Fund or Instrument tables.
```

Annex IV should consume source data and calculation outputs, then produce filing values.

---

## K. Audit and lineage domain

Purpose: make every reported or calculated value traceable.

Likely concepts:

```text
source_snapshot_id
calculation_run_id
methodology_version_id
as_of_date
period_start
period_end
override_flag
override_reason
approver_id
evidence_uri
schema_version
submission_id
regulator_feedback_id
```

Classification:

```text
lineage
audit
governance
control evidence
```

This should be designed early because it affects most domains. Retrofitting lineage later usually causes messy schema changes.

---

# 3. Field classification rules

Before any field enters the database design, it should be classified.

## Rule 1: Source data

A field is source data if it comes from an administrator file, accounting system, fund document, market data provider, investor register or legal reference.

Examples:

```text
position quantity
instrument ISIN
market value
NAV
fund domicile
share class currency
redemption notice period
counterparty LEI
collateral balance
```

Store it with source snapshot information.

---

## Rule 2: Reference data

A field is reference data if it defines stable categories, codes, allowed values or classification schemes.

Examples:

```text
asset class
currency
country code
fund regime
LMT type
SFDR Article 6 / 8 / 9
Annex IV allowed value
EMIR action type
SFTR action type
```

Store it separately from transactional records.

---

## Rule 3: Methodology setting

A field is a methodology setting if the fund, ManCo or calculation framework chooses it and it affects outputs.

Examples:

```text
VaR confidence level
VaR lookback window
liquidity bucket scheme
counterparty internal limit
collateral haircut methodology
hedging eligibility rule
LMT activation threshold
valuation technique
```

Store it as versioned configuration, not as a plain attribute.

---

## Rule 4: Internal risk limit

A field is an internal limit if it expresses a monitoring threshold rather than a measured exposure.

Examples:

```text
issuer exposure limit
counterparty exposure limit
liquidity warning threshold
leverage internal limit
concentration alert level
```

Store it separately from the measured result.

---

## Rule 5: Calculation input

A field is a calculation input if it is consumed by a risk engine.

Examples:

```text
position market value
instrument duration
historical prices
FX rates
NAV
methodology parameters
collateral haircut rate
netting eligibility
```

Some calculation inputs are source fields, some are methodology fields.

---

## Rule 6: Derived output

A field is derived if the platform calculates it.

Examples:

```text
VaR
Expected Shortfall
gross leverage ratio
commitment leverage ratio
issuer exposure percentage
counterparty exposure percentage
liquidity bucket percentage
time to liquidate
stress loss
backtesting exception
```

Store derived outputs in calculation result tables with run metadata.

---

## Rule 7: Reporting field

A field is a reporting field if it exists because a regulatory or management report requires a submitted/displayed value.

Examples:

```text
Annex IV XML field
AIFM reporting block value
board report table value
CSSF filing status
```

Do not store reporting fields as if they were operating source data.

---

## Rule 8: Filing snapshot

A field is a filing snapshot if it is the exact value submitted or prepared for submission.

Examples:

```text
submitted Annex IV value
report period
schema version
validation status
submission timestamp
correction flag
regulator rejection reason
```

Store it separately from source data and calculation outputs.

---

# 4. Proposed conceptual entity catalogue

This is not a database schema. This is the domain entity map.

## Phase 1 core entities

These are the entities needed for position-based Historical VaR, Expected Shortfall and backtesting.

```text
Fund
ShareClass
Instrument
Issuer
PositionSnapshot
Position
NAVSnapshot
MarketDataSnapshot
PriceHistory
FXRate
RiskMethodology
RiskCalculationRun
HistoricalVaRResult
ExpectedShortfallResult
BacktestResult
```

Phase 1 should stay narrow because the project spec defines Phase 1 around database layer, market data abstraction, position ingestion, fixed-position Historical VaR, ES and 1-day VaR backtesting. 

---

## Phase 2 entities

These support leverage, liquidity and stress testing.

```text
StressScenario
StressTestResult
LeverageFramework
LeverageCalculationResult
LiquidityFramework
LiquidityBucketScheme
LiquidityBucketResult
ConcentrationLimit
ConcentrationResult
Counterparty
CounterpartyExposureResult
```

---

## Phase 3 entities

These support LST, LMT, Annex IV, board reporting and richer supervisory reporting.

```text
DerivativePosition
SFTPosition
CollateralBalance
InvestorHolding
InvestorLiquidityTerms
FundFlow
LMTReferenceData
FundLMTSelection
LMTActivationEvent
RegulationSource
RegulatoryRequirement
VariableDefinition
AllowedValueSet
ValidationRule
ReportSchemaVersion
RegulatoryFiling
ReportingFieldValue
RepeatedBlockValue
SubmissionFeedback
```

---

## Later specialised domains

These are important but should not block the first database design unless they are part of the near-term scope.

```text
PrivateAssetPosition
PortfolioCompany
PrivateAssetValuation
ValuationInputSet
ValuationScenario
ValuationGovernanceEvent
ESGProfile
PAIIndicator
TaxonomyMetric
PRIIPsCalculation
EMIRReport
SFTRReport
MiFIRTransactionReport
BreachEvent
```

---

# 5. Phase 1 minimum model

For the first database and ETL design, I would limit the core model to this:

```text
Fund
Instrument
Issuer
PositionSnapshot
Position
NAVSnapshot
RiskMethodology
RiskCalculationRun
HistoricalVaRResult
ExpectedShortfallResult
BacktestResult
```

Market data can remain provider-based initially, because MRS-125 is already focused on a CSV-backed market data abstraction rather than full production storage. 

## Phase 1 should support

```text
one fund or multiple funds
positions by valuation date
instrument metadata
market value in native and/or base currency
NAV denominator
historical price retrieval
FX retrieval
fixed-position Historical VaR
Expected Shortfall
1-day backtesting
calculation reproducibility
```

## Phase 1 should not yet try to fully support

```text
Annex IV XML generation
full leverage reporting
full collateral model
full derivative trade lifecycle
full LMT framework
SFDR / Taxonomy
PRIIPs
EMIR / SFTR
private asset valuation governance
regulator feedback workflow
```

Those should be anticipated, not fully built.

---

# 6. Granularity decisions to make before schema design

These are the key questions that must be answered before creating tables.

## Fund

Granularity:

```text
one row per fund
```

Open question:

```text
Should NAV live directly on Fund?
```

Recommendation:

```text
No. NAV changes by date, so it belongs in NAVSnapshot.
```

---

## PositionSnapshot

Granularity:

```text
one row per fund per valuation date per source file or load batch
```

Purpose:

```text
groups all positions from the same administrator extract
supports lineage
supports reloads and corrections
```

---

## Position

Granularity:

```text
one row per fund, valuation date, instrument and position source line
```

Open question:

```text
Should Position store liquidity bucket?
```

Recommendation:

```text
Only if the bucket comes directly from the source file as a source classification. If calculated by the platform, it belongs in LiquidityBucketResult.
```

---

## Instrument

Granularity:

```text
one row per security / instrument identifier
```

Open question:

```text
Should duration be stored on Instrument?
```

Recommendation:

```text
Static terms can belong to Instrument, but market-sensitive values such as modified duration may need an as-of date or market data source if they change over time.
```

This matters because Phase 1 bond VaR may use duration-based sensitivity, and the project specification explicitly notes that initial bond VaR may use duration-based sensitivity to historical yield movements. 

---

## NAVSnapshot

Granularity:

```text
one row per fund or share class per valuation date
```

Purpose:

```text
denominator for VaR as % NAV
reconciliation anchor
reporting source
```

---

## RiskMethodology

Granularity:

```text
one row per methodology version
```

Possible scope:

```text
methodology applies globally
methodology applies per fund
methodology applies per risk engine
```

Recommendation:

```text
Allow fund-specific methodology versions, even if Phase 1 starts with one default methodology.
```

---

## RiskCalculationRun

Granularity:

```text
one row per calculation execution
```

Purpose:

```text
links input snapshot, methodology version, market data window and output results
```

This should be created before result entities, otherwise reproducibility becomes weak.

---

## HistoricalVaRResult

Granularity:

```text
one row per calculation run per fund, and possibly per share class or portfolio slice later
```

Should store:

```text
VaR value
confidence level used
holding period
lookback window
result currency or percentage basis
calculation run link
```

Should not store:

```text
raw source positions
raw price histories
reporting-only labels
```

---

# 7. Prototype field inventory method

The prototype inventory should come after the above model is accepted.

For each prototype field, classify it using this template:

```text
prototype field name:
prototype location:
business meaning:
field family:
    source data / reference data / methodology setting / internal limit /
    calculation input / derived output / reporting field / audit field
regulatory source:
    Level 1 / delegated regulation / RTS / ITS / ESMA guidance /
    CSSF implementation / fund methodology / internal / none
recommended treatment:
    keep / rename / derive / move to methodology / move to result /
    move to reporting / drop / unclear
target conceptual entity:
notes:
```

This prevents “field copying” from the old repository.

---

# 8. Specific risks to avoid during the prototype inventory

## Risk 1: treating all prototype fields as requirements

A field in the prototype means only:

```text
the prototype once needed it
```

It does not mean:

```text
the field is regulatory
the field belongs in the database
the field should be stored as source data
the field belongs in Phase 1
```

---

## Risk 2: treating Annex IV as the data model

Annex IV is an output. It should not define the internal operating model.

The regulatory research says Annex IV consumes positions, instruments, derivatives, SFTs, collateral, counterparty exposures, NAV snapshots, investor data, liquidity terms, stress testing results and leverage calculations, and then submits aggregated supervisory report fields. 

---

## Risk 3: storing derived values as source fields

Avoid storing these directly on source tables:

```text
VaR
Expected Shortfall
gross leverage ratio
commitment leverage ratio
issuer exposure percentage
counterparty exposure percentage
liquidity bucket percentage
stress loss
backtesting exception
Annex IV submitted value
```

They need calculation run lineage.

---

## Risk 4: methodology hidden inside attributes

Avoid fields such as:

```text
is_hedging
is_nettable
collateral_haircut
liquidity_bucket
leverage_treatment
```

unless their meaning is clear.

Better classification:

```text
source hedging flag
methodology hedging eligibility
calculated leverage treatment
reported leverage contribution
```

These are different concepts.

---

# 9. Recommended next action

The next concrete step should be:

```text
Create a prototype field inventory, but classify every field against this domain model.
```

The inventory should not ask:

```text
Do we copy this field?
```

It should ask:

```text
What business concept does this field represent?
Is it source data, methodology, output or reporting?
Where should this concept live in the new model?
Should it be Phase 1 or deferred?
```

After that, the database schema can be designed with much lower risk.

My recommendation for the next working sequence is:

```text
1. Freeze this conceptual domain model as the working baseline.
2. Inventory prototype fields.
3. Classify prototype fields using the field classification template.
4. Produce a Phase 1 entity and field list.
5. Only then design the SQLite schema.
```

So the immediate next deliverable should be:

```text
prototype_field_inventory.md
```

with classification, not schema.
