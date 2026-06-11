# Leverage Methodology Roadmap

Project: `manco-risk`  
Purpose: design and implement leverage analytics for AIFM / ManCo risk workflows with clear separation between exposure source, regulatory aggregation method, reporting, and limit monitoring.

This document is a methodology and implementation roadmap. It is not legal advice. Regulatory interpretation must be reviewed before production use.

---

## 1. Design principles

### 1.1 Source-first, method-second

Leverage must be implemented in layers.

1. **Exposure source layer**: identifies where exposure comes from.
2. **Regulatory aggregation layer**: applies AIFMD gross, AIFMD commitment, and later UCITS global exposure rules.
3. **Reporting layer**: explains total leverage by method, source, position, and reporting category.
4. **Limit monitoring layer**: checks calculated metrics against regulatory, regulator-imposed, fund-document, and internal limits.

This prevents the code from mixing four different questions:

- What exposure exists?
- Which exposure is included in a specific method?
- Where does the leverage come from?
- Is the fund breaching a limit?

### 1.2 Calculation and limit monitoring must remain separate

The leverage engines calculate metrics. They do not decide whether the fund is compliant.

Limit monitoring consumes calculated metrics and compares them against:

- hard regulatory limits;
- limits specifically imposed by the CSSF / NCA / regulator;
- limits written in fund documents;
- internal monitoring thresholds.

This matters because general AIFMD has no single EU-wide hard leverage cap for every AIF, while AIFMD II introduces specific hard caps for loan-originating AIFs.

### 1.3 Fair value and leverage exposure are different

For derivatives, two values must be modelled separately:

- **Fair value / mark-to-market**: used for NAV.
- **Regulatory exposure**: used for leverage, such as notional, equivalent underlying exposure, or delta-adjusted exposure.

Example:

```text
Option fair value: EUR 50,000
Option equivalent underlying / delta-adjusted exposure: EUR 1,000,000
```

The NAV uses EUR 50,000. Leverage uses the exposure measure, not the fair value.

### 1.4 Gross and commitment should reuse the same exposure source base

The difference between AIFMD gross and AIFMD commitment should not be implemented by creating separate asset-class treatment systems.

The correct structure is:

```text
source exposure layer
    physical instruments
    cash / cash equivalents
    direct borrowing
    reinvested borrowing
    SFTs
    derivatives
    embedded leverage / look-through

aggregation method layer
    AIFMD gross
    AIFMD commitment
    UCITS global exposure later
```

Gross method aggregates absolute exposure with gross-method exclusions. Commitment method starts from source exposure and applies conversion, netting, hedging, and offset rules where eligible.

---

## 2. Regulatory source map

### 2.1 AIFMD and AIFMD Level 2

Core sources:

- Directive 2011/61/EU (AIFMD), especially leverage definition, risk management, disclosure, reporting, and Article 25 supervisory powers.
- Commission Delegated Regulation (EU) No 231/2013, Articles 6 to 11.

Key Level 2 concepts:

- Article 6: leverage is exposure divided by NAV; AIFMs calculate exposure under both gross and commitment methods.
- Article 7: gross method.
- Article 8: commitment method.
- Article 9: methods of increasing exposure.
- Article 10: derivative conversion methodologies.
- Article 11: duration netting rules for interest-rate derivatives.

Implementation implication:

- AIFMD leverage engines must produce at least gross leverage and commitment leverage.
- Source decomposition must be retained for reporting and audit.
- General AIFMD calculation does not itself set one hard leverage cap for all AIFs.

### 2.2 AIFMD II / loan-originating AIFs

Directive (EU) 2024/927 introduced a specific leverage limit regime for loan-originating AIFs.

For a loan-originating AIF, the leverage ratio is calculated using the commitment method and is capped at:

- **175% of NAV** for open-ended loan-originating AIFs;
- **300% of NAV** for closed-ended loan-originating AIFs.

The same regime provides that borrowing arrangements fully covered by contractual capital commitments from investors are not treated as exposure for this ratio, and the loan-originating AIF cap does not apply where lending activity consists solely of shareholder loans and their notional value does not exceed 150% of the AIF's capital.

Implementation implication:

- Do not bake loan-originating AIF caps into the base AIFMD leverage calculation engine.
- Create a separate limit monitoring layer that can apply this cap only when fund classification requires it.
- Future fund-level fields must include loan-originating status, open-ended/closed-ended status, capital, shareholder-loan-only flag, shareholder-loan notional, and contractual capital commitment coverage.

### 2.3 ESMA 2026 integrated reporting direction

ESMA's 2026 final report on integrated fund data confirms the direction of travel: reporting should be more integrated across AIFMD and UCITS, with supervisory data covering fund characteristics, exposures, assets, risk profile, leverage and stress testing.

Implementation implication:

- The leverage model must preserve source-level and method-level audit fields.
- Do not store only one leverage number.
- Reporting views should be built from structured components: source exposure, method result, limit check, and fund classification.

### 2.4 UCITS global exposure

UCITS global exposure is not the same as AIFMD leverage.

UCITS global exposure can be measured using:

- commitment approach;
- relative VaR approach;
- absolute VaR approach;
- other recognised advanced risk measurement methods.

UCITS global exposure must be calculated at least daily, and method selection depends on the investment strategy and derivative complexity.

Implementation implication:

- UCITS global exposure is a later module.
- UCITS derivative commitment conversion may reuse derivative exposure source models.
- UCITS VaR is not part of the AIFMD leverage engine.
- UCITS VaR should be handled in a later UCITS risk-limit / global-exposure module, not mixed into AIFMD leverage.

---

## 3. Exposure source taxonomy

The source layer identifies where exposure comes from. It does not decide the final regulatory method result.

### 3.1 Core source categories

```text
PHYSICAL_INSTRUMENT
CASH_AND_CASH_EQUIVALENT
DIRECT_BORROWING
REINVESTED_BORROWING
SFT_REPO
SFT_REVERSE_REPO
SECURITIES_LENDING
DERIVATIVE
EMBEDDED_DERIVATIVE
FUND_LOOK_THROUGH
CONTROLLED_STRUCTURE
OTHER
```

### 3.2 Exposure treatment values

```text
INCLUDED
EXCLUDED
UNSUPPORTED
PENDING_METHOD_RULE
```

Meanings:

- `INCLUDED`: exposure is included in the source base.
- `EXCLUDED`: exposure is explicitly excluded, with reason.
- `UNSUPPORTED`: source exists but calculation is not supported yet.
- `PENDING_METHOD_RULE`: source is identified, but final treatment depends on the later gross/commitment/UCITS method.

---

## 4. Asset and source treatment roadmap

| Source / asset type | Source engine | Source-layer output | AIFMD gross later | AIFMD commitment later | UCITS later |
|---|---|---|---|---|---|
| Equity | Physical instrument | absolute market value | included | included | physical context, not derivative global exposure |
| Bond | Physical instrument | absolute market value | included | included | physical context |
| ETF / listed fund | Physical instrument / look-through later | absolute market value | included unless look-through policy says otherwise | included unless look-through policy says otherwise | depends on UCITS/layered exposure policy |
| Index holding | Physical instrument if physical/index-like holding | absolute market value | included | included | context-specific |
| Base-currency cash | Cash engine | raw value tracked, exposure zero | excluded if qualifying cash/cash equivalent | zero in Phase 1 | not global exposure |
| Non-base currency cash | Cash engine | unsupported / warning in Phase 1 | later FX treatment | later FX treatment | later FX treatment |
| Direct borrowing, not reinvested | Borrowing engine | direct borrowing source | method-specific treatment later | method-specific treatment later | borrowing limits separate |
| Reinvested borrowing | Borrowing engine | reinvested borrowing source | included as exposure created by reinvestment | included/conservative until rules mature | separate from UCITS global exposure |
| Repo | SFT engine | repo source | included by method rule | included/conservative until rules mature | EPM/SFT treatment later |
| Reverse repo | SFT engine | reverse repo source | included by method rule | included/conservative until rules mature | later |
| Securities lending | SFT engine | securities-lending source | included by method rule | included/conservative until rules mature | later |
| Future / forward | Derivative engine | provided notional/equivalent underlying | included using source exposure | included/conversion then reductions | UCITS commitment later |
| Option / warrant | Derivative engine | delta-adjusted exposure if available | included using source exposure | included/conversion then reductions | UCITS commitment or VaR later |
| Swap | Derivative engine | notional/equivalent exposure | included using source exposure | included/conversion then reductions | UCITS commitment or VaR later |
| FX forward | Derivative engine | currency exposure | included using source exposure | currency hedging reductions possible | UCITS FX derivative treatment later |
| Embedded derivative | Embedded derivative source later | separate exposure source | included when quantified | included/conversion rules | UCITS embedded derivative rules later |
| Fund look-through | Look-through source later | underlying exposure | method-specific | method-specific | important for UCITS later |

---

## 5. Derivative roadmap: valuation vs exposure

### 5.1 Generic derivative model

The project already has a generic derivative record model from MRS-162. It should remain generic and QuantLib-ready.

Core concepts:

```text
DerivativeValuation
- fair_value_base_ccy
- valuation_source
- pricing_model
- valuation_date

DerivativeExposure
- notional_base_ccy
- equivalent_underlying_exposure_base_ccy
- delta_adjusted_exposure_base_ccy
- exposure_source
```

Exposure selection for the source engine:

1. use delta-adjusted exposure if available;
2. else use equivalent underlying exposure if available;
3. else use notional if available;
4. if none exists, record unsupported exposure and warning.

### 5.2 Linear interest-rate derivatives

A specific model will be needed for automatic interest-rate duration netting.

Possible future model:

```python
class LinearInterestRateDerivativeRecord(BaseModel):
    derivative_id: str
    currency: str
    underlying_curve: str
    maturity_date: date
    pay_receive_direction: str
    notional_base_ccy: Decimal
    fair_value_base_ccy: Decimal
    modified_duration: Decimal | None
    duration_equivalent: Decimal | None
    exposure_base_ccy: Decimal
```

This is mainly for linear instruments:

- interest-rate swaps;
- FRAs;
- interest-rate futures;
- bond futures;
- forward-starting swaps.

The maturity bucket should normally be derived from valuation date and maturity date, not stored as a permanent static attribute.

```text
remaining maturity = maturity_date - valuation_date
maturity bucket = methodology bucket rule applied to remaining maturity
```

### 5.3 Non-linear interest-rate derivatives

Non-linear derivatives need more than maturity and duration.

Examples:

- swaptions;
- caps;
- floors;
- bond options;
- callable structures;
- structured notes with optionality.

Possible future model:

```python
class NonLinearInterestRateDerivativeRecord(BaseModel):
    derivative_id: str
    currency: str
    underlying_curve: str
    maturity_date: date
    option_type: str
    strike: Decimal
    exercise_style: str
    fair_value_base_ccy: Decimal
    delta: Decimal | None
    gamma: Decimal | None
    vega: Decimal | None
    delta_adjusted_exposure_base_ccy: Decimal | None
    pricing_model: str | None
```

For non-linear derivatives, QuantLib or another pricing engine becomes relevant because the fund may need fair value, delta, gamma, vega, volatility inputs, curves, fixing data and exercise-style treatment.

### 5.4 QuantLib roadmap

QuantLib should not be mandatory for the current AIFMD aggregation pass. It should be introduced as a later pricing/analytics layer.

Recommended future issues:

```text
MRS-167 — Interest-rate derivative duration-netting model
MRS-168 — QuantLib derivative pricing and Greeks spike
MRS-169 — QuantLib-backed derivative valuation and exposure conversion
```

Rationale:

- AIFMD leverage exposure is not the same as fair value.
- QuantLib helps produce fair values, deltas and sensitivities.
- Regulatory exposure conversion still needs rule-specific logic.
- The system must support provided exposures before pricing infrastructure is complete.

---

## 6. AIFMD gross method roadmap

### 6.1 Core behaviour

AIFMD gross leverage engine consumes source results and produces:

```text
LeverageMethodResult(method=AIFMD_GROSS)
```

Formula:

```text
gross leverage = gross exposure / NAV
```

### 6.2 Source input policy

The gross engine should aggregate source-layer gross exposures, subject to gross-method exclusions.

Initial approach:

- physical instruments: included;
- qualifying base-currency cash: excluded because the cash engine outputs zero gross exposure;
- reinvested borrowing: included;
- direct borrowing: consumed according to source-layer output and later refined;
- SFTs: included based on SFT source output;
- derivatives: included based on derivative source output;
- unsupported exposures: passed through;
- warnings: propagated.

### 6.3 Audit requirements

The gross method result must preserve:

- total gross exposure;
- leverage ratio;
- source contributions;
- position contributions where available;
- excluded exposure with reason;
- unsupported exposure with reason;
- warnings.

---

## 7. AIFMD commitment method roadmap

### 7.1 Core behaviour

AIFMD commitment engine consumes the same source results and produces:

```text
LeverageMethodResult(method=AIFMD_COMMITMENT)
```

Formula:

```text
commitment leverage = final commitment exposure / NAV
```

Where:

```text
final commitment exposure = base exposure before reductions - eligible reductions
```

### 7.2 Conservative base exposure

Initial commitment base exposure policy:

- use `commitment_exposure` where source engines provide it;
- if `commitment_exposure` is None, use `gross_exposure` conservatively;
- qualifying cash contributes zero;
- derivatives use provided source exposure until richer conversion rules exist;
- SFTs and borrowing use source-layer exposure conservatively until more specific rules are added.

### 7.3 Netting and hedging reductions

Commitment reductions should be explicit records, not inferred automatically from weak signals.

A reduction model should include:

```text
CommitmentReduction
- reduction_id
- reduction_type
- source_position_id
- source_derivative_id
- target_position_id
- target_derivative_id
- underlying_identifier
- asset_class
- reduction_amount
- reason
- is_regulatory_eligible
```

Reduction types:

```text
NETTING
HEDGING
CURRENCY_HEDGING
OTHER
```

Rules for MRS-163:

- Eligible reductions reduce commitment exposure.
- Ineligible reductions are ignored but audited.
- A hedge flag alone is not enough to reduce exposure.
- A same-underlying relationship is needed for simple netting.
- Highly correlated assets or same issuer alone should not be treated as identical underlying.
- Reductions cannot take exposure below zero.
- Article 11 interest-rate duration netting should remain out of scope unless explicit interest-rate derivative netting fields are introduced.

### 7.4 Audit requirements

The commitment method must retain:

- base exposure before reductions;
- total eligible reductions;
- final exposure;
- applied reductions;
- ignored reductions;
- reason for every ignored reduction;
- leverage ratio;
- source contributions;
- unsupported exposures;
- warnings.

If `LeverageMethodResult` is insufficient, create a wrapper:

```text
AIFMDCommitmentLeverageResult
- method_result
- base_exposure_before_reductions
- total_reductions
- final_exposure
- applied_reductions
- ignored_reductions
```

---

## 8. UCITS global exposure roadmap

UCITS should be implemented separately from AIFMD leverage.

### 8.1 UCITS commitment approach

UCITS commitment approach converts financial derivative positions into the market value of equivalent positions in the underlying assets. It is a global-exposure method, not an AIFMD leverage method.

Implementation later:

- derivative conversion models;
- UCITS-specific netting and hedging rules;
- ongoing/daily calculation support;
- global exposure limits;
- audit trail.

### 8.2 UCITS VaR approaches

UCITS VaR is not leverage.

It is a global-exposure / risk-measurement method for UCITS, generally relevant for complex derivative strategies.

It should be a later module, using the VaR infrastructure where appropriate.

---

## 9. Limit monitoring roadmap

Limits should be a separate module from leverage calculation.

### 9.1 Limit source taxonomy

Keep Phase 1 simple:

```text
REGULATORY
REGULATOR_IMPOSED
FUND_DOCUMENT
INTERNAL
```

Meanings:

- `REGULATORY`: hard rule directly from law or regulation.
- `REGULATOR_IMPOSED`: specific restriction imposed by CSSF, NCA or regulator.
- `FUND_DOCUMENT`: prospectus, offering memorandum, LPA, fund rules, constitutional documents.
- `INTERNAL`: internal ManCo/risk policy thresholds.

### 9.2 Limit type taxonomy

```text
HARD_LIMIT
WARNING_THRESHOLD
ESCALATION_THRESHOLD
```

### 9.3 Limit metrics

Potential metrics:

```text
AIFMD_GROSS_LEVERAGE
AIFMD_COMMITMENT_LEVERAGE
LOAN_ORIGINATING_AIF_COMMITMENT_LEVERAGE
UCITS_GLOBAL_EXPOSURE
DIRECT_BORROWING
DERIVATIVE_EXPOSURE
SFT_EXPOSURE
```

### 9.4 Examples

```text
REGULATORY / HARD_LIMIT / LOAN_ORIGINATING_AIF_COMMITMENT_LEVERAGE / 175%
REGULATORY / HARD_LIMIT / LOAN_ORIGINATING_AIF_COMMITMENT_LEVERAGE / 300%
FUND_DOCUMENT / HARD_LIMIT / AIFMD_COMMITMENT_LEVERAGE / 250%
INTERNAL / WARNING_THRESHOLD / AIFMD_GROSS_LEVERAGE / 180%
REGULATOR_IMPOSED / HARD_LIMIT / AIFMD_COMMITMENT_LEVERAGE / 160%
```

---

## 10. Annex IV / integrated reporting field preview

The leverage data model should be ready for later Annex IV / integrated reporting views.

### 10.1 Fund classification fields

Future fields:

```text
fund_id
fund_name
base_currency
valuation_date
nav
fund_type
is_aif
is_ucits
is_loan_originating_aif
is_open_ended
is_closed_ended
is_feeder
is_fund_of_funds
is_shareholder_loan_only
fund_capital
```

### 10.2 Method result fields

```text
calculation_date
method
nav
total_exposure
leverage_ratio
base_exposure_before_reductions
total_reductions
final_exposure
```

### 10.3 Source contribution fields

```text
source
raw_exposure
gross_exposure
commitment_exposure
treatment
exclusion_reason
unsupported_reason
percentage_of_nav
```

### 10.4 Borrowing fields

```text
borrowing_id
currency
amount_base_ccy
purpose
treatment
is_temporary
is_secured
reinvested_amount_base_ccy
is_fully_covered_by_contractual_capital_commitments
```

### 10.5 SFT fields

```text
sft_id
sft_type
currency
market_value_base_ccy
cash_collateral_base_ccy
securities_collateral_base_ccy
reinvested_cash_collateral_base_ccy
treatment
```

### 10.6 Derivative fields

```text
derivative_id
derivative_type
payoff_type
underlying_identifier
underlying_asset_class
currency
fair_value_base_ccy
valuation_source
pricing_model
notional_base_ccy
equivalent_underlying_exposure_base_ccy
delta_adjusted_exposure_base_ccy
exposure_source
is_hedge
hedge_group_id
```

### 10.7 Commitment reduction fields

```text
reduction_id
reduction_type
source_position_id
source_derivative_id
target_position_id
target_derivative_id
underlying_identifier
asset_class
reduction_amount
reason
is_regulatory_eligible
applied_or_ignored
ignored_reason
```

### 10.8 Limit monitoring fields

```text
limit_id
limit_source
limit_type
limit_metric
threshold
observed_value
headroom
breach_flag
warning_flag
escalation_flag
as_of_date
```

---

## 11. Implementation issue sequence

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
MRS-162 — Derivative valuation and exposure model
MRS-163 — AIFMD gross and commitment aggregation engines
MRS-164 — Leverage persistence and reporting views
MRS-165 — UCITS global exposure support
MRS-166 — Leverage limit monitoring framework
```

Future derivative-specific issues:

```text
MRS-167 — Interest-rate derivative duration-netting model
MRS-168 — QuantLib derivative pricing and Greeks spike
MRS-169 — QuantLib-backed derivative valuation and exposure conversion
```

---

## 12. Current implementation status

Completed:

```text
MRS-157 — Leverage taxonomy and exposure source model
MRS-158 — Physical instrument leverage exposure
MRS-159 — Cash and cash-equivalent leverage treatment
MRS-160 — Direct borrowing leverage source
MRS-161 — Securities financing transaction leverage source
MRS-162 — Derivative valuation and exposure model
```

Next:

```text
MRS-163 — AIFMD gross and commitment aggregation engines
```

MRS-163 should implement:

- AIFMD gross leverage result;
- AIFMD commitment leverage result;
- explicit commitment reduction records;
- conservative same-underlying netting only when provided and eligible;
- explicit hedging reductions only when provided and eligible;
- no automatic Article 11 duration netting yet;
- no QuantLib;
- no persistence;
- no limit monitoring.

---

## 13. References

- Directive 2011/61/EU (AIFMD).
- Commission Delegated Regulation (EU) No 231/2013, Articles 6 to 11.
- Directive (EU) 2024/927 (AIFMD II / UCITS amendments).
- ESMA Final Report on the integrated collection of funds' data, 4 May 2026.
- CESR/ESMA Guidelines on Risk Measurement and the Calculation of Global Exposure and Counterparty Risk for UCITS, CESR/10-788.
