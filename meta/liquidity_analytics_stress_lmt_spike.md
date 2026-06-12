# Liquidity Analytics, Stress Testing, and LMT Methodology Spike

Status: methodology spike  
Project area: liquidity risk analytics for ManCo / investment fund workflows  
Target implementation track: MRS-172 onward  
Scope: UCITS and open-ended AIFs, with AIFMD references where useful  
Last reviewed: 2026-06-12

## 1. Executive conclusion

The liquidity analytics module should be built as a fund-level asset-liability liquidity framework. It should not be a single stress-test formula. It should combine:

1. **Asset-side liquidity analytics**: liquidity buckets, time-to-liquidation, liquidation cost, market impact, liquidation shortfall, forced-sale price impact.
2. **Liability-side liquidity analytics**: redemption scenarios, investor concentration, dealing frequency, notice period, settlement cycle, margin calls, collateral calls, subscription/redemption netting.
3. **Combined liquidity stress tests**: redemption pressure plus stressed asset liquidation assumptions.
4. **Liquidity Management Tool simulation**: gates, notice-period extensions, redemption fees, swing pricing, dual pricing, anti-dilution levy, redemption in kind, suspension, and side pockets.
5. **Limit and calibration layer**: regulatory/document constraints, internal warning thresholds, escalation thresholds, LMT activation thresholds, and post-action residual-risk checks.

The regulatory framework requires liquidity risk management, periodic liquidity stress testing, tool selection, calibration, activation, and governance. It does **not** prescribe a universal quantitative model. Therefore the implementation should encode explicit methodology assumptions instead of pretending that one regulatory formula exists.

## 2. Regulatory source hierarchy

### 2.1 Primary legislation and core rules

| Source | Relevance for implementation |
|---|---|
| AIFMD Article 16 | Requires liquidity management systems and regular stress tests under normal and exceptional liquidity conditions for relevant AIFs. Also requires consistency between investment strategy, liquidity profile, and redemption policy. |
| AIFMD Level 2 Regulation (EU) 231/2013 | Provides operating-condition detail for liquidity systems, monitoring, limits, and stress tests. The implementation should treat this as the operational anchor for AIF liquidity risk controls. |
| UCITS Directive 2009/65/EC and Commission Directive 2010/43/EU | Require risk-management processes and define UCITS liquidity risk as the risk that a position cannot be sold, liquidated, or closed at limited cost in an adequately short timeframe while preserving redemption ability. |
| Commission Delegated Regulation (EU) 2016/438 | UCITS depositary Level 2 regulation. It is not a liquidity-stress methodology regulation, but it is relevant for cash-flow oversight, segregation, safekeeping, and governance context. |
| CSSF Circular 16/644 | Luxembourg UCITS depositary guidance. It clarifies depositary organisational duties and therefore matters for operational control context, but it should not be treated as a quantitative liquidity model. |
| Directive (EU) 2024/927 | AIFMD II / UCITS amendments introducing a harmonised LMT framework and ESMA mandates for LMT selection and calibration. |
| ESMA 2020 liquidity stress testing guidelines | Practical supervisory framework for liquidity stress testing in UCITS and AIFs. |
| ESMA 2026 LMT guidelines | Current guidance on the selection, activation, calibration, and deactivation of LMTs for UCITS and open-ended AIFs. |

### 2.2 What is prescribed versus manager methodology

| Area | Regulatory prescription | Manager methodology |
|---|---|---|
| Liquidity risk management | Required | Model design, data sources, assumptions, thresholds |
| Liquidity stress testing | Required | Scenarios, shocks, liquidation policy, frequency beyond minimum/guidance |
| Fund strategy vs redemption terms | Must be consistent | Quantitative consistency metrics and governance evidence |
| LMT availability | Harmonised list and minimum selection rules | Tool selection per fund profile, activation thresholds, calibration levels |
| Anti-dilution tools | Should reflect estimated cost of liquidity | Cost model, market impact model, spread assumptions, pro-rata vs selected liquidation |
| Redemption gates and notice extensions | Tool characteristics and governance expectations | Trigger thresholds, duration, release policy, investor-level or fund-level design |
| Suspension | Exceptional, temporary | Trigger escalation, valuation handling, reopening criteria |
| Side pockets | Exceptional circumstances | Eligibility, segregation, valuation, investor treatment, future phase |

## 3. 2026 ESMA LMT framework

The 2026 ESMA LMT guidelines are the main current source for selection and calibration of LMTs for UCITS and open-ended AIFs. They state that the primary responsibility for liquidity risk management and for LMT selection, calibration, activation, and deactivation remains with the fund manager. They also say selected LMTs should enable effective liquidity-risk management under normal and stressed market conditions.

The harmonised LMT list includes:

1. suspension of subscriptions, repurchases and redemptions;
2. redemption gates;
3. extension of notice periods;
4. redemption fees;
5. swing pricing;
6. dual pricing;
7. anti-dilution levy;
8. redemption in kind;
9. side pockets.

For the minimum mandatory LMT selection, the amended UCITS and AIFMD frameworks focus on tools in the annex lists. ESMA states that managers should consider the merit of selecting at least one quantitative-based LMT, such as redemption gates or notice-period extension, and at least one anti-dilution tool, such as redemption fees, swing pricing, dual pricing, or anti-dilution levy.

### 3.1 LMT taxonomy for implementation

| Category | LMT | Primary purpose | Model output |
|---|---|---|---|
| Exceptional control | Suspension | Stop subscriptions/redemptions temporarily in exceptional circumstances | suspension_status, reason, review_date, reopening_criteria |
| Quantity restriction | Redemption gate | Limit executable redemption amount over a dealing date/window | executable_redemption, deferred_redemption, gate_ratio |
| Timing restriction | Extension of notice period | Give more time to liquidate assets orderly | revised_liquidation_horizon, revised_shortfall |
| Cost allocation | Redemption fee | Charge redeeming investors a predefined or dynamic fee | fee_rate, cost_recovered, residual_dilution |
| NAV adjustment | Swing pricing | Adjust dealing NAV to reflect liquidity costs | swing_factor, swung_nav, residual_dilution |
| Bid/offer valuation | Dual pricing | Use subscription/redemption price basis reflecting spreads | bid_nav, offer_nav, dilution_transfer |
| Cost allocation | Anti-dilution levy | Charge entry/exit levy reflecting trading costs | levy_rate, levy_amount, residual_cost |
| In-kind settlement | Redemption in kind | Satisfy redemptions by transferring assets | in_kind_assets, cash_shortfall, concentration impact |
| Segregation | Side pocket | Segregate illiquid/impaired assets | side_pocket_nav, liquid_pool_nav, redemption eligibility |

### 3.2 Selection factors from ESMA 2026

The implementation should allow a manager to document LMT selection with the following factors:

- fund legal structure, including ETF or master-feeder features;
- investment strategy and investment policy;
- dealing terms: notice period, lock-up, settlement period, redemption policy, dealing frequency;
- liquidity profile of assets;
- anticipated liquidity demands, redemptions, margin calls and other liability-side risks;
- impact of activating the tool on liquidity profile;
- liquidity stress-testing results;
- investor-base concentration and distribution policy;
- operational feasibility and implementation barriers.

These inputs should become explicit model fields in later implementation issues rather than free text only.

## 4. UCITS liquidity risk and UCITS II / amended UCITS context

The UCITS implementation should treat the following as base rules:

1. UCITS liquidity risk means the risk that a position cannot be sold, liquidated, or closed at limited cost in an adequately short timeframe and that the UCITS cannot comply with redemption obligations.
2. UCITS management companies need a liquidity-risk management process and should ensure the liquidity profile of investments is appropriate to the redemption policy.
3. The 2024 UCITS amendments introduce the LMT framework and give ESMA a mandate for selection and calibration guidelines, now reflected in the 2026 ESMA LMT guidelines.

The user referred to “UCITS 2”. In this project documentation, use the safer term **amended UCITS framework / UCITS Directive amendments under Directive (EU) 2024/927**. Avoid calling it “UCITS II” unless the repo glossary deliberately uses that shorthand.

### 4.1 Commission Delegated Regulation 2016/438 and CSSF Circular 16/644

These 2016 materials matter for governance but not for the core quantitative stress formula:

- Commission Delegated Regulation (EU) 2016/438 supplements UCITS depositary obligations.
- CSSF Circular 16/644 clarifies depositary organisational requirements in Luxembourg.
- For this project, they inform audit trail, cash-flow oversight, safekeeping context, escalation evidence, and data availability, but they do not prescribe time-to-liquidation formulas, redemption-shock percentiles, or swing-factor calibration.

## 5. Liquidity analytics building blocks

### 5.1 Position liquidity classification

Each position should be classified by liquidity characteristics:

| Field | Example | Purpose |
|---|---|---|
| asset_class | Equity, Bond, ETF, Listed Fund, Cash, FX, Derivative | Rule selection |
| liquidity_bucket | T0, T1, T2_5, T6_10, T11_20, GT20, ILLIQUID | Reporting and limits |
| liquidation_horizon_days | 1, 5, 10, 20, 60 | Stress and gap analysis |
| liquidation_cost_bps | 5, 25, 75, 250 | LMT calibration |
| stressed_liquidation_cost_bps | 20, 100, 300 | Stressed LMT calibration |
| adv_participation_rate | 10% | Equity/ETF liquidation capacity |
| bid_ask_spread_bps | 10 | Dilution cost estimate |
| market_impact_bps | 20 | Swing/ADL calculation |
| valuation_confidence | high / medium / low | Suspension / side-pocket trigger support |

### 5.2 Liquidity buckets

Suggested default buckets:

| Bucket | Definition | Use |
|---|---|---|
| CASH | Cash and cash equivalents available immediately | redemption coverage |
| T1 | Sale/settlement within one business day | high liquidity |
| T2_5 | Liquid within 2 to 5 business days | weekly liquidity |
| T6_10 | Liquid within 6 to 10 business days | short liquidation window |
| T11_20 | Liquid within 11 to 20 business days | monthly stress |
| GT20 | More than 20 days | illiquidity warning |
| ILLIQUID | No reliable liquidation horizon | LMT and escalation trigger |

### 5.3 Asset liquidation capacity

For each position:

```text
sellable_value_by_day = min(position_value, daily_liquidation_capacity * liquidation_days)
```

Daily liquidation capacity can be defined by asset class:

- cash: full amount T0;
- listed equities/ETFs: ADV × participation rate × stressed price haircut;
- bonds: trader quote depth, issue size share, rating bucket and spread shock assumptions;
- funds: underlying dealing frequency and redemption notice;
- derivatives: close-out liquidity, collateral/margin call liquidity and counterparty terms;
- private assets: manager-specified liquidation profile or illiquid bucket.

### 5.4 Liquidation cost

Suggested cost stack:

```text
liquidation_cost = explicit_cost + half_spread_or_full_spread + market_impact + taxes_or_fees + stressed_add_on
```

For anti-dilution tools, ESMA 2026 gives useful implementation principles: estimated cost of liquidity should include explicit transaction costs and may include implicit transaction costs, including significant market impact, and the starting point can be a pro-rata slice of all portfolio assets unless that is not a fair estimate.

## 6. Liability-side liquidity analytics

### 6.1 Redemption scenarios

| Scenario | Redemption shock | Use |
|---|---:|---|
| Normal | Historical 50th or 75th percentile | ordinary monitoring |
| Elevated | Historical 90th or 95th percentile | warning threshold |
| Severe | Historical 99th percentile or largest historical redemption | escalation threshold |
| Extreme | investor concentration redemption | LMT activation |
| Reverse | redemption amount that breaches coverage or TTL limit | governance and contingency planning |

### 6.2 Investor concentration

A practical model should store:

- largest investor share;
- top-5 investor share;
- investor type: retail, institutional, nominee, fund platform, feeder, internal fund;
- redemption notice terms by investor class;
- historical subscription/redemption behaviour;
- concentration-based stress assumptions.

### 6.3 Liability-side additional demands

The model should support more than investor redemptions:

- margin calls;
- collateral calls;
- unsettled trades;
- financing maturities;
- fund-level expenses and fees;
- FX settlement needs;
- distributions.

## 7. Standalone and combined liquidity stress tests

### 7.1 Standalone asset liquidation stress

Measures how much of the portfolio can be liquidated over a horizon and at what cost, without a redemption shock.

Outputs:

- liquidation schedule;
- value liquidated by day;
- residual illiquid amount;
- liquidation cost;
- weighted average liquidation horizon;
- percentage of NAV liquid within each bucket.

### 7.2 Standalone redemption stress

Measures redemption pressure without changing asset liquidity assumptions.

Outputs:

- redemption amount;
- cash coverage;
- liquid-asset coverage;
- uncovered redemption;
- investor concentration driver;
- warning/escalation status.

### 7.3 Combined redemption + liquidation stress

The combined test is the central test for ManCo workflows:

```text
available_liquidity_after_costs >= redemption_cash_need + margin_calls + other_liability_outflows
```

Outputs:

- redemption coverage ratio;
- liquidity shortfall;
- time-to-meet-redemption;
- liquidation cost paid by fund if no LMT;
- dilution borne by remaining investors if no LMT;
- LMT recommendation status.

### 7.4 Reverse liquidity stress

Reverse liquidity stress finds the redemption shock or market liquidity shock that creates a breach:

- redemption amount that exhausts liquid assets within settlement period;
- spread shock that makes swing factor exceed maximum policy threshold;
- investor concentration redemption that triggers gate;
- market-impact multiplier that creates NAV dilution beyond internal tolerance.

## 8. Liquidity Management Tool calibration

### 8.1 Calibration principle

LMT calibration should be a separate layer from stress testing:

```text
stress_engine_output -> lmt_calibration_engine -> lmt_activation_decision -> residual_liquidity_metrics
```

This separation is important because a stress test can show a shortfall without automatically deciding which tool must be used. The decision depends on fund documents, legal authority, governance, investor treatment, operational feasibility, and regulatory notification requirements.

### 8.2 LMT inventory

Each fund should have an LMT inventory:

| Field | Description |
|---|---|
| fund_id | Fund |
| lmt_type | gate, notice extension, swing pricing, ADL, etc. |
| available_in_documents | Whether permitted by prospectus/fund rules |
| selected_as_mandatory_lmt | Whether part of minimum LMT selection |
| normal_market_use | Whether used under normal conditions |
| stressed_market_use | Whether used under stressed conditions |
| activation_metric | redemption %, net flow %, liquidity cost %, TTL, shortfall |
| warning_threshold | internal pre-alert |
| activation_threshold | formal activation level |
| deactivation_threshold | recovery / reopening condition |
| maximum_level | maximum factor/gate/fee if defined |
| governance_body | board, conduct committee, risk committee |
| notification_required | NCA/investor notification flag |

### 8.3 Calibration by LMT

#### Redemption gates

Calibration metrics:

- redemption orders as % NAV;
- redemption orders as % liquid assets;
- investor concentration trigger;
- projected liquidation shortfall;
- time-to-liquidation beyond redemption settlement date.

Possible thresholds:

| Level | Example |
|---|---:|
| warning | redemptions > 5% NAV |
| escalation | redemptions > 10% NAV or liquid-asset coverage < 125% |
| activation | redemptions > 15% NAV or shortfall > 0 |

#### Notice-period extension

Calibration metrics:

- days needed for orderly liquidation;
- settlement deadline gap;
- portion of NAV liquid by current redemption date;
- stressed time-to-liquidation.

Formula:

```text
required_notice_extension_days = max(0, time_to_liquidate_required_assets - current_notice_period_days)
```

#### Redemption fee

Calibration metrics:

- fixed explicit transaction cost;
- taxes/fees;
- predictable costs;
- stressed add-on if methodology allows.

Formula:

```text
redemption_fee_rate = estimated_redemption_related_cost / redemption_amount
```

#### Swing pricing

Calibration metrics:

- net flow as % NAV;
- estimated liquidity cost of pro-rata liquidation;
- bid-ask spread;
- market impact;
- swing threshold and factor.

Formula:

```text
swing_factor = min(max_swing_factor, estimated_liquidity_cost / NAV_or_flow_basis)
```

The implementation should support both full swing and partial swing with a single or tiered swing factor.

#### Dual pricing

Calibration metrics:

- bid-ask spread of underlying assets;
- subscription/redemption side;
- explicit cost add-on;
- market-impact add-on if relevant.

Outputs:

- bid NAV;
- offer NAV;
- spread transfer to transacting investors.

#### Anti-dilution levy

Calibration metrics:

- explicit costs;
- implicit costs;
- bid-ask spread;
- market impact;
- investor concentration;
- fund flow direction and size.

Formula:

```text
adl_rate = estimated_cost_of_liquidity / subscription_or_redemption_amount
```

#### Redemption in kind

Calibration metrics:

- investor type and eligibility;
- asset transferability;
- custody/settlement ability;
- fairness to remaining investors;
- concentration risk of assets transferred.

#### Suspension

Calibration metrics:

- valuation uncertainty;
- trading venue closure;
- severe liquidity failure;
- fraud/cyber/natural disaster;
- inability to compute NAV or meet redemptions fairly.

Suspension should be modelled as exceptional and temporary, with review and reopening criteria.

#### Side pockets

Side pockets should be a later-phase model. Triggers may include asset impairment, valuation uncertainty, sanctions, market closure, or trapped assets.

## 9. Limit monitoring and calibration of limits

### 9.1 Limit types

| Limit type | Purpose |
|---|---|
| Regulatory/document hard limit | Cannot be breached without formal action |
| Internal hard limit | Board/risk policy limit |
| Escalation threshold | Requires committee review/action |
| Warning threshold | Pre-alert to risk/portfolio management |
| LMT activation threshold | Tool-specific trigger |
| Deactivation threshold | Recovery threshold for tool removal |

### 9.2 Core liquidity metrics

| Metric | Definition |
|---|---|
| cash_ratio | cash / NAV |
| liquid_asset_ratio_T1 | assets liquid within 1 day / NAV |
| liquid_asset_ratio_T5 | assets liquid within 5 days / NAV |
| redemption_coverage_ratio | available liquidity / stressed redemptions |
| liquidity_shortfall | stressed redemptions - available liquidity |
| time_to_liquidate_nav_pct | days to liquidate required NAV percentage |
| weighted_average_liquidation_days | weighted liquidity horizon |
| stressed_liquidation_cost_bps | cost / NAV |
| dilution_cost_to_remaining_investors | uncompensated cost if no ADT |
| largest_investor_redemption_coverage | coverage if largest investor redeems |
| gate_trigger_ratio | redemptions / NAV or / liquid assets |
| swing_factor_required | estimated liquidity cost ratio |
| adl_required_rate | estimated cost allocated to transacting investors |

### 9.3 Calibration approach

A practical model should calibrate thresholds using:

- fund documents and permitted tools;
- redemption frequency and settlement cycle;
- historical fund flows;
- investor concentration;
- liquidity bucket distribution;
- liquidation cost distribution;
- historical market stress events;
- LST outputs;
- operational lead times;
- governance body tolerance.

## 10. Data architecture implications

### 10.1 Core input tables/models later

- LiquidityBucketDefinition
- PositionLiquidityProfile
- AssetLiquidationAssumption
- RedemptionScenario
- InvestorConcentrationProfile
- LiquidityStressScenario
- LiquidityStressResult
- LMTDefinition
- LMTCalibrationRule
- LMTActivationResult
- LiquidityLimitDefinition
- LiquidityLimitCheckResult

### 10.2 Separation of modules

- `risk/liquidity` should contain pure engines and Pydantic models.
- `database` should contain persistence later.
- `reporting` should contain reporting views later.
- `ui` should not be part of the first implementation phase.

## 11. Proposed first implementation sequence

1. Liquidity taxonomy and buckets.
2. Position liquidity classification.
3. Asset liquidation assumptions.
4. Time-to-liquidation engine.
5. Redemption scenarios.
6. Redemption stress engine.
7. Asset liquidation stress engine.
8. Combined liquidity stress engine.
9. Liquidity limits.
10. LMT taxonomy and inventory.
11. LMT calibration engines.
12. LMT activation simulation.

## 12. Sources

- ESMA, Guidelines on liquidity management tools of UCITS and open-ended AIFs, ESMA34-671404336-1364, 2026.
- ESMA, Guidelines on liquidity stress testing in UCITS and AIFs, ESMA34-39-897.
- Directive (EU) 2024/927 amending AIFMD and UCITS Directive.
- Directive 2011/61/EU, Article 16.
- Commission Delegated Regulation (EU) No 231/2013, Articles 46-49.
- Directive 2009/65/EC and Commission Directive 2010/43/EU.
- Commission Delegated Regulation (EU) 2016/438.
- CSSF Circular 16/644.
- CSSF Working Paper, Liquidity Stress Test for Luxembourg Investment Funds: the Time to Liquidation Approach, 2023.
- Roncalli et al., Liquidity Stress Testing in Asset Management, Parts 1-3, 2021.
