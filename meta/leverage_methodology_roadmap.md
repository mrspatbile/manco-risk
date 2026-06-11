# Leverage methodology roadmap

Project: `manco-risk`  
File: `meta/leverage_methodology_roadmap.md`  
Purpose: define the regulatory, methodology, data-model, implementation, and reporting roadmap for fund leverage analytics.

---

## 1. Executive design decision

Leverage must be designed as three separate layers:

1. **Exposure source layer**  
   Identifies where exposure comes from: physical instruments, cash, borrowing, securities financing transactions, derivatives, embedded leverage, and look-through structures.

2. **Regulatory aggregation method layer**  
   Applies the calculation method: AIFMD gross method, AIFMD commitment method, and later UCITS global exposure methods.

3. **Limit monitoring layer**  
   Checks calculated metrics against regulatory, regulator-imposed, fund-document, and internal limits.

The calculation engine must not decide whether a fund breaches a limit. It calculates exposure and leverage. A separate limit-monitoring layer consumes those metrics and applies the relevant thresholds.

This separation is important because:

- general AIFMD does not impose one universal leverage cap for all AIFs;
- loan-originating AIFs under AIFMD II have specific hard leverage caps;
- UCITS has a separate global-exposure regime, not an AIFMD leverage-ratio regime;
- fund-specific prospectus or offering-document limits may be stricter than regulation;
- internal risk limits may be warning or escalation thresholds rather than legal hard limits.

---

## 2. Regulatory source hierarchy

### 2.1 AIFMD Level 1 and AIFMD II

AIFMD defines leverage broadly as any method by which an AIFM increases the exposure of an AIF, whether through borrowing of cash or securities, leverage embedded in derivatives, or any other means.

For general AIFs, AIFMD requires leverage calculation, disclosure, risk management, and regulatory reporting. It does **not** impose one universal EU leverage cap for every AIF.

AIFMD II / Directive (EU) 2024/927 introduces specific rules for loan-originating AIFs, including hard leverage caps calculated using the commitment method:

- **175% of NAV** for open-ended loan-originating AIFs;
- **300% of NAV** for closed-ended loan-originating AIFs.

These caps are not general AIFMD leverage limits for all funds. They apply to the loan-originating AIF regime.

### 2.2 AIFMD Level 2 Regulation 231/2013

The core calculation framework for AIFMD leverage is in Commission Delegated Regulation (EU) No 231/2013, especially:

- Article 6 — general provisions on leverage calculation;
- Article 7 — gross method;
- Article 8 — commitment method;
- Articles 9 to 11 — additional commitment-method rules, including conversion, netting, hedging, and exposure increase.

These are the primary references for the AIFMD leverage calculation engine.

### 2.3 ESMA AIFMD reporting and leverage-risk material

ESMA material is relevant for reporting, systemic-risk monitoring, data consistency, and leverage-risk supervision. It does not replace the Level 2 gross and commitment calculation rules.

For this project, ESMA material supports the need to keep:

- leverage by method;
- exposure by source;
- borrowing separated from derivatives;
- SFT exposure separated from derivatives;
- fund-specific limits separated from regulatory hard caps;
- reporting-ready fields that can later support Annex IV or integrated reporting.

### 2.4 ESMA 2026 integrated reporting direction

The ESMA 2026 integrated funds reporting direction reinforces that future supervisory reporting will require structured information on fund characteristics, exposures, assets, risk profile, leverage, and stress-test results.

This supports a source-first design. The system should not produce only one leverage number. It must keep enough fields to explain how the leverage number was produced and where the leverage comes from.

### 2.5 UCITS global exposure

UCITS should not be mixed into the AIFMD leverage engine.

UCITS has a separate **global exposure** framework. UCITS global exposure may be calculated using the commitment approach, relative VaR, absolute VaR, or advanced risk measurement methods.

For this project:

- UCITS commitment/global exposure may later reuse derivative exposure conversion models;
- UCITS VaR approaches belong to a later UCITS risk-limit/global-exposure module;
- UCITS VaR is not AIFMD leverage and should not be implemented inside the AIFMD leverage engine.

---

## 3. Main methodology principle

Leverage should not be implemented as separate asset-class systems for gross and commitment methods.

Instead:

1. Each position or financing arrangement produces one or more **exposure source records**.
2. The **gross method** aggregates absolute exposure values with gross-method exclusions.
3. The **commitment method** starts from the same exposure source base, then applies eligible conversion, netting, hedging, and offset rules.
4. Limit monitoring checks the resulting metrics against regulatory, regulator-imposed, fund-document, and internal limits.

This avoids duplicating asset-class logic and keeps the system ready for Annex IV, integrated reporting, and management reporting.

---

## 4. Exposure source taxonomy

The leverage module must classify exposure by source before calculating method-level leverage.

Recommended `LeverageSource` values:

```text
PHYSICAL_SECURITY_EXPOSURE
CASH
DIRECT_BORROWING
REINVESTED_BORROWING
DERIVATIVE_COMMITMENT
SFT_REPO
SFT_REVERSE_REPO
SECURITIES_LENDING
EMBEDDED_DERIVATIVE
CONTROLLED_STRUCTURE
FUND_LOOK_THROUGH
SHAREHOLDER_LOAN
OTHER
```

### Source definitions

| Source | Meaning | Phase |
|---|---|---|
| `PHYSICAL_SECURITY_EXPOSURE` | Exposure from physical securities: equities, bonds, ETFs, listed funds, index-like physical holdings | Phase 1 |
| `CASH` | Cash and cash equivalents; important for exclusions and borrowing checks | Phase 1 |
| `DIRECT_BORROWING` | Borrowing of cash or securities that creates balance-sheet leverage | Later |
| `REINVESTED_BORROWING` | Borrowing that has been invested and increases market exposure | Later |
| `DERIVATIVE_COMMITMENT` | Exposure from derivatives converted into equivalent underlying or commitment exposure | Later |
| `SFT_REPO` | Repo-generated exposure | Later |
| `SFT_REVERSE_REPO` | Reverse repo-generated exposure | Later |
| `SECURITIES_LENDING` | Securities-lending exposure | Later |
| `EMBEDDED_DERIVATIVE` | Leverage embedded in structured instruments | Later |
| `CONTROLLED_STRUCTURE` | Exposure through controlled structures requiring look-through | Later |
| `FUND_LOOK_THROUGH` | Exposure through target funds or fund-of-fund structures | Later |
| `SHAREHOLDER_LOAN` | Loan-originating AIF shareholder loans, tracked separately for AIFMD II checks | Later |
| `OTHER` | Explicit fallback; should require reason text | Later |

---

## 5. Asset and exposure treatment matrix

This table is the roadmap for how asset classes and leverage sources should be treated. Phase 1 implements only the physical and cash rows, but the full taxonomy is defined upfront.

| Asset / source | AIFMD gross method | AIFMD commitment method | UCITS global exposure | Phase |
|---|---|---|---|---|
| Equity | Absolute market exposure | Physical exposure; no netting unless part of eligible hedge logic later | Not derivative global exposure by itself | Phase 1 |
| Bond | Absolute market exposure | Physical exposure; no netting unless part of eligible hedge logic later | Not derivative global exposure by itself | Phase 1 |
| ETF | Absolute market exposure; look-through later if needed | Physical exposure or look-through later | Depends on UCITS classification / embedded leverage | Phase 1 / later look-through |
| Listed fund | Absolute market exposure; look-through later if needed | Physical exposure or look-through later | Depends on UCITS classification / embedded leverage | Phase 1 / later look-through |
| Index-like physical holding | Absolute market exposure | Physical exposure | Depends on instrument type | Phase 1 |
| Base-currency cash | Excluded if qualifying cash/cash equivalent under gross method | Generally zero exposure unless connected to borrowing/reinvestment | Not global exposure by itself | Phase 1 |
| Non-base-currency cash | FX exposure issue; not simple cash treatment | FX exposure issue | FX exposure issue | Later / explicit unsupported in Phase 1 |
| Direct borrowing, unreinvested | Track separately; not automatically market exposure if cash remains cash and conditions are met | Track separately | UCITS borrowing rules separate from global exposure | Later |
| Direct borrowing, reinvested | Include exposure generated by reinvestment | Include exposure generated by reinvestment | Depends on UCITS context | Later |
| Repo | Include relevant SFT exposure | Include relevant SFT exposure, with method-specific rules | UCITS EPM / counterparty framework | Later |
| Reverse repo | Include relevant SFT exposure | Include relevant SFT exposure, with method-specific rules | UCITS EPM / counterparty framework | Later |
| Securities lending | Include relevant exposure | Include relevant exposure | UCITS EPM / counterparty framework | Later |
| Futures | Convert to equivalent underlying exposure | Convert to commitment exposure; netting/hedging later | Commitment conversion / VaR framework | Later |
| Options | Convert using option methodology, likely delta-adjusted exposure | Convert using commitment rules; netting/hedging later | Commitment conversion / VaR framework | Later |
| Swaps | Convert to equivalent underlying/notional exposure | Convert to commitment exposure | Commitment conversion / VaR framework | Later |
| FX forwards | Convert to currency exposure | Netting/hedging where eligible | UCITS FX derivative rules | Later |
| Embedded derivatives | Extract embedded derivative exposure | Convert embedded derivative commitment exposure | UCITS embedded derivative rules | Later |
| Controlled structures | Look-through where required | Look-through where required | UCITS look-through where applicable | Later |
| Target funds | Market value first; look-through later where needed | Market value first; look-through later where needed | UCITS look-through where applicable | Later |

---

## 6. AIFMD gross method design

The gross method should be implemented as an aggregation method over exposure source records.

Phase 1 gross method:

```text
physical securities exposure = abs(market_value_base_ccy)
qualifying base-currency cash exposure = 0
unsupported sources = explicit unsupported record or error, depending on selected strictness

gross_exposure = sum(included gross exposure sources)
gross_leverage_ratio = gross_exposure / NAV
```

Later gross method additions:

```text
derivatives converted to equivalent underlying exposure
reinvested borrowing exposure
SFT exposure
embedded derivative exposure
look-through exposure where required
```

The gross method must not apply commitment-method netting or hedging reductions.

---

## 7. AIFMD commitment method design

The commitment method should also be implemented as an aggregation method over exposure source records, but with an additional rule layer.

Phase 1 commitment method for physical instruments:

```text
physical securities exposure = abs(market_value_base_ccy)
qualifying base-currency cash exposure = 0
commitment_exposure = sum(physical exposure sources)
commitment_leverage_ratio = commitment_exposure / NAV
```

Later commitment method additions:

```text
derivative conversion to equivalent underlying / commitment exposure
eligible netting rules
eligible hedging rules
offset rules
reinvested borrowing treatment
SFT treatment
embedded derivative treatment
```

The commitment method must keep an audit trail of:

```text
raw exposure before reduction
converted exposure
netting reduction
hedging reduction
offset reduction
final commitment exposure
reason / rule reference for each reduction
```

---

## 8. General AIFMD leverage limits

For general AIFMD funds, the base calculation engine should not apply one fixed regulatory leverage cap.

General AIFMD requirements are primarily:

```text
calculate gross leverage
calculate commitment leverage
disclose expected maximum leverage where required
monitor leverage and risks
report leverage and exposure to regulators
support NCA/regulator-imposed limits where applicable
```

Therefore:

```text
general AIFMD leverage calculation = metric production
general AIFMD limit checking = separate limit-monitoring layer
```

---

## 9. Loan-originating AIF hard leverage caps

AIFMD II introduces specific leverage caps for loan-originating AIFs.

These are not general AIF leverage caps. They apply to loan-originating AIFs and should be implemented in the limit-monitoring layer.

Recommended inputs:

```text
is_loan_originating_aif: bool
fund_liquidity_structure: OPEN_ENDED | CLOSED_ENDED
is_shareholder_loan_only: bool
shareholder_loan_notional_base_ccy: Decimal | None
fund_capital_base_ccy: Decimal | None
commitment_leverage_ratio: Decimal
```

Recommended limit rules:

```text
open-ended loan-originating AIF:
    commitment leverage hard cap = 175% of NAV

closed-ended loan-originating AIF:
    commitment leverage hard cap = 300% of NAV
```

Shareholder-loan exceptions should be tracked separately and must not be hard-coded into the base leverage engine.

---

## 10. UCITS global exposure and limits

UCITS should be implemented later as a separate global-exposure module.

UCITS is not AIFMD leverage. UCITS has a global-exposure framework that may use:

```text
commitment approach
relative VaR approach
absolute VaR approach
advanced risk measurement methods
```

For this roadmap:

- UCITS commitment/global exposure may reuse derivative exposure conversion models;
- UCITS VaR approaches should remain out of the leverage engine;
- UCITS VaR belongs to a later UCITS global-exposure / risk-limit module;
- UCITS temporary borrowing limits should be tracked separately from derivative global exposure.

Do not implement UCITS VaR inside the AIFMD leverage module.

---

## 11. Limit monitoring framework

Limit monitoring must be separate from leverage calculation.

### 11.1 Limit source

Recommended `LimitSource` values:

```text
REGULATORY
REGULATOR_IMPOSED
FUND_DOCUMENT
INTERNAL
```

Definitions:

| Source | Meaning | Example |
|---|---|---|
| `REGULATORY` | A hard rule directly from law or regulation | Loan-originating AIF leverage cap of 175% / 300% |
| `REGULATOR_IMPOSED` | Specific restriction imposed by the CSSF or another NCA on this fund or manager | CSSF imposes a custom leverage cap |
| `FUND_DOCUMENT` | Limit in prospectus, offering memorandum, LPA, fund rules, constitutional documents, or investor documents | “Commitment leverage may not exceed 250%” |
| `INTERNAL` | ManCo, board, investment committee, or risk-policy monitoring threshold | Warning at 180%, escalation at 200% |

Do not split `PROSPECTUS`, `FUND_POLICY`, `BOARD_LIMIT`, `RISK_POLICY`, and `INTERNAL_MONITORING` in Phase 1. They are too granular and can be represented by `FUND_DOCUMENT` or `INTERNAL`.

### 11.2 Limit type

Recommended `LimitType` values:

```text
HARD_LIMIT
WARNING_THRESHOLD
ESCALATION_THRESHOLD
```

Definitions:

| Type | Meaning |
|---|---|
| `HARD_LIMIT` | Breach requires formal action or creates non-compliance |
| `WARNING_THRESHOLD` | Early warning before a hard limit is reached |
| `ESCALATION_THRESHOLD` | Requires escalation or review, even if not a legal breach |

### 11.3 Limit metric

Recommended `LimitMetric` values:

```text
AIFMD_GROSS_LEVERAGE
AIFMD_COMMITMENT_LEVERAGE
LOAN_ORIGINATING_AIF_COMMITMENT_LEVERAGE
UCITS_GLOBAL_EXPOSURE
UCITS_TEMPORARY_BORROWING
DIRECT_BORROWING
DERIVATIVE_EXPOSURE
SFT_EXPOSURE
```

Examples:

```text
REGULATORY / HARD_LIMIT / LOAN_ORIGINATING_AIF_COMMITMENT_LEVERAGE / 175%
REGULATORY / HARD_LIMIT / LOAN_ORIGINATING_AIF_COMMITMENT_LEVERAGE / 300%
REGULATOR_IMPOSED / HARD_LIMIT / AIFMD_COMMITMENT_LEVERAGE / 160%
FUND_DOCUMENT / HARD_LIMIT / AIFMD_COMMITMENT_LEVERAGE / 250%
INTERNAL / WARNING_THRESHOLD / AIFMD_GROSS_LEVERAGE / 180%
INTERNAL / ESCALATION_THRESHOLD / DIRECT_BORROWING / 50%
```

---

## 12. Annex IV and integrated reporting field preview

The leverage model should already prepare for reporting, even if Annex IV output is implemented later.

### 12.1 Fund-level fields

```text
fund_id
valuation_date
reporting_date
base_currency
nav
fund_type
is_aif
is_ucits
is_loan_originating_aif
fund_liquidity_structure
is_open_ended
is_closed_ended
```

### 12.2 Method-level leverage fields

```text
leverage_method
raw_exposure
excluded_exposure
net_exposure_after_exclusions
commitment_exposure_before_reductions
netting_reduction
hedging_reduction
offset_reduction
final_exposure
leverage_ratio
calculation_status
methodology_version
```

### 12.3 Source-level fields

```text
source
source_exposure
source_exposure_pct_nav
source_included_in_gross
source_included_in_commitment
source_exclusion_reason
source_methodology_note
```

### 12.4 Position-level fields

```text
position_id
isin
instrument_name
asset_class
instrument_type
currency
market_value_base_ccy
absolute_market_value_base_ccy
source
gross_exposure
commitment_exposure
included_in_method
exclusion_reason
unsupported_reason
```

### 12.5 Borrowing fields

```text
borrowing_id
borrowing_type
borrowing_currency
borrowing_amount_base_ccy
is_reinvested
reinvested_amount_base_ccy
is_temporary
maturity_date
borrowing_purpose
borrowing_source
included_in_gross
included_in_commitment
```

### 12.6 Derivative fields

```text
derivative_id
underlying_asset_class
underlying_identifier
notional_base_ccy
market_value_base_ccy
delta
conversion_method
equivalent_underlying_exposure
commitment_exposure
netting_set_id
hedging_set_id
netting_reduction
hedging_reduction
final_commitment_exposure
```

### 12.7 SFT fields

```text
sft_id
sft_type
counterparty_id
collateral_value_base_ccy
cash_leg_value_base_ccy
security_leg_value_base_ccy
reinvestment_flag
reinvested_collateral_value_base_ccy
sft_exposure_base_ccy
included_in_gross
included_in_commitment
```

### 12.8 Limit-monitoring fields

```text
limit_id
limit_source
limit_type
limit_metric
limit_value
limit_currency
limit_ratio
measured_value
headroom
breach_flag
warning_flag
escalation_flag
breach_amount
breach_date
reference_document
rule_reference
```

---

## 13. Recommended model API roadmap

### 13.1 Phase 1 pure leverage taxonomy and source model

```text
LeverageMethod
LeverageSource
LimitSource
LimitType
LimitMetric
UnsupportedLeverageExposure
LeverageExposureSourceRecord
LeveragePositionContribution
LeverageSourceContribution
LeverageInput
LeverageMethodResult
LeverageResult
```

### 13.2 Later source records

```text
BorrowingRecord
DerivativeExposureRecord
SFTExposureRecord
EmbeddedDerivativeRecord
LookThroughExposureRecord
LeverageLimitRule
LeverageLimitCheckResult
```

---

## 14. Implementation issue sequence

Parent issue:

```text
MRS-139 — Implement leverage analytics
```

Child issues:

```text
MRS-157 — Leverage taxonomy and exposure source model
MRS-158 — Physical instrument leverage exposure
MRS-159 — Cash and cash-equivalent leverage treatment
MRS-160 — Direct borrowing leverage source
MRS-161 — Securities financing transaction leverage source
MRS-162 — Derivative exposure conversion model
MRS-163 — AIFMD gross and commitment aggregation engines
MRS-164 — Leverage persistence and reporting views
MRS-165 — UCITS global exposure support
MRS-166 — Leverage limit monitoring framework
```

---

## 15. Phase 1 implementation scope

Start with MRS-157 only.

MRS-157 should implement:

```text
pure enums
pure Pydantic models
validation rules
unsupported exposure tracking
source taxonomy
limit taxonomy
no calculation engine
no persistence
no reporting output
```

MRS-158 and MRS-159 should then implement physical instruments and cash treatment as exposure-source logic, not as separate gross/commitment engines.

MRS-163 should implement the AIFMD gross and commitment aggregation engines once the source exposure layer is available.

---

## 16. Key implementation constraints

```text
risk engines must remain pure
no ORM imports in risk modules
no database imports in risk modules
use Decimal for monetary values and ratios
leverage exposure is a positive magnitude
leverage ratio = exposure / NAV
unsupported exposure must be explicit
regulatory calculation and limit monitoring must remain separate
UCITS VaR must not be mixed into AIFMD leverage
loan-originating AIF hard caps belong to limit monitoring, not base exposure calculation
```

---

## 17. References

Primary sources to use when implementing calculation rules:

1. Directive 2011/61/EU (AIFMD).
2. Commission Delegated Regulation (EU) No 231/2013, Articles 6 to 11.
3. Directive (EU) 2024/927 (AIFMD II / UCITS amendments), especially loan-originating AIF provisions.
4. ESMA AIFMD reporting guidance and reporting templates.
5. ESMA final report on integrated collection of funds data, 2026.
6. ESMA / CESR Guidelines on Risk Measurement and the Calculation of Global Exposure and Counterparty Risk for UCITS.
7. ESMA UCITS VaR material, for future UCITS global exposure work only.

