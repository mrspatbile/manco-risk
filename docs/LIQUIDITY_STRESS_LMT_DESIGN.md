# Liquidity Stress Testing and LMT Calibration Design

**Note:** This is a historical design document created during v0.1.0 planning. It remains the authoritative methodology reference for liquidity risk. Work is now tracked via GitHub Issues: [#6 Migrate liquidity risk analytics](https://github.com/mrspatbile/manco-risk/issues/6) and [#7 Implement LMT simulation engine](https://github.com/mrspatbile/manco-risk/issues/7).

Status: methodology reference  
Project area: liquidity analytics and LMT simulation  
Last reviewed: 2026-06-12

## 1. Design objective

This document translates liquidity regulation and ESMA guidance into implementable Python models. It defines the separation between:

1. liquidity classification;
2. asset liquidation stress;
3. redemption stress;
4. combined redemption plus liquidation stress;
5. liquidity limits;
6. LMT calibration;
7. LMT activation simulation.

The design does not assume a universal regulatory formula. Instead, it makes the manager’s methodology explicit, auditable and testable.

## 2. Core design principles

### 2.1 Separation of concerns

| Layer | Responsibility | Not responsible for |
|---|---|---|
| Liquidity taxonomy | Buckets, asset liquidity categories, LMT names | Stress results |
| Position liquidity classification | Classify each position and assign base assumptions | Redemptions |
| Asset liquidation engine | Compute cash generation, cost and shortfall by horizon | Investor behaviour |
| Redemption stress engine | Compute liability-side cash need | Asset sales |
| Combined stress engine | Match liquidity supply and liquidity demand | LMT calibration decision |
| Limit engine | Compare metrics to thresholds | Selecting calibration methodology |
| LMT calibration engine | Compute tool level/factor/trigger | Pricing assets |
| LMT activation simulator | Compare before/after liquidity state | Legal approval workflow |

### 2.2 Positive loss / cost convention

Use positive magnitudes for:

- liquidation cost;
- redemption amount;
- liquidity shortfall;
- swing factor;
- anti-dilution levy;
- redemption fee;
- deferred redemption amount.

Use signed values only for cash-flow direction where needed.

## 3. Liquidity taxonomy

### 3.1 LiquidityBucket

Suggested enum:

```python
class LiquidityBucket(str, Enum):
    CASH = "CASH"
    T1 = "T1"
    T2_5 = "T2_5"
    T6_10 = "T6_10"
    T11_20 = "T11_20"
    GT20 = "GT20"
    ILLIQUID = "ILLIQUID"
```

### 3.2 LiquidityAssumptionSource

```python
class LiquidityAssumptionSource(str, Enum):
    POLICY_DEFAULT = "POLICY_DEFAULT"
    MANAGER_OVERRIDE = "MANAGER_OVERRIDE"
    MARKET_DATA = "MARKET_DATA"
    VENDOR = "VENDOR"
    REGULATORY = "REGULATORY"
```

### 3.3 LiquidityCostComponent

```python
class LiquidityCostComponent(str, Enum):
    EXPLICIT_TRANSACTION_COST = "EXPLICIT_TRANSACTION_COST"
    BID_ASK_SPREAD = "BID_ASK_SPREAD"
    MARKET_IMPACT = "MARKET_IMPACT"
    TAX_OR_FEE = "TAX_OR_FEE"
    STRESSED_ADD_ON = "STRESSED_ADD_ON"
```

## 4. Position liquidity profile

### 4.1 PositionLiquidityProfile

Suggested fields:

- position_id;
- instrument_id;
- asset_class;
- market_value_base_ccy;
- liquidity_bucket;
- normal_liquidation_horizon_days;
- stressed_liquidation_horizon_days;
- normal_liquidation_cost_bps;
- stressed_liquidation_cost_bps;
- daily_liquidation_capacity_base_ccy;
- assumption_source;
- rationale;
- warning flags.

### 4.2 Validation

- market value can be positive, zero or negative depending on position type, but liquidity analysis should usually consume absolute market value for liquidation exposure;
- liquidation horizons must be non-negative;
- cost bps must be non-negative;
- daily liquidation capacity must be non-negative;
- illiquid positions should have zero or missing daily liquidation capacity with an explicit reason.

## 5. Asset liquidation assumptions

### 5.1 Assumption dimensions

| Dimension | Example |
|---|---|
| horizon | 1 day, 5 days, 10 days, 20 days |
| market condition | normal, stressed, severe |
| liquidation policy | pro-rata, most-liquid-first, least-liquid-first, manager-selected |
| participation rate | 10% ADV for equities, 5% ADV in stress |
| bond sellability | rating, issue size, spread, dealer depth |
| fund-of-funds | underlying dealing frequency |
| derivative close-out | close-out cost, margin liquidity |

### 5.2 Liquidation policy

Supported policies:

1. **Pro-rata liquidation**: sell all assets in proportion to current weights. Useful for anti-dilution calibration because ESMA highlights pro-rata cost as a starting point for estimated liquidity cost.
2. **Most-liquid-first liquidation**: use cash and most liquid assets first. Useful for operational cash-generation testing, but may increase residual portfolio illiquidity.
3. **Least-liquid-first liquidation**: conservative for cost analysis but often unrealistic.
4. **Manager-selected liquidation**: explicit list of positions and amounts, useful for governance/action plans.

### 5.3 Liquidation result

Suggested result fields:

- total_requested_liquidation;
- total_liquidated;
- total_unliquidated;
- total_cost;
- total_cost_bps_nav;
- liquidation_schedule by day;
- position-level liquidation rows;
- warnings.

## 6. Redemption stress design

### 6.1 RedemptionScenario

Fields:

- scenario_id;
- scenario_type;
- redemption_percent_nav;
- redemption_amount_base_ccy;
- investor_group;
- largest_investor_assumption;
- top_investor_assumption;
- margin_call_amount;
- other_liability_outflow;
- settlement_days;
- notice_period_days;
- description.

Scenario types:

- HISTORICAL_PERCENTILE;
- LARGEST_HISTORICAL;
- INVESTOR_CONCENTRATION;
- REGULATORY_OR_DOCUMENT;
- REVERSE_STRESS;
- MANAGER_DEFINED.

### 6.2 Redemption stress result

Fields:

- redemption_amount;
- cash_available;
- liquid_assets_available_by_settlement;
- redemption_coverage_ratio;
- liquidity_shortfall;
- warning status;
- escalation status;
- trigger candidates.

## 7. Combined stress design

### 7.1 Combined stress input

Fields:

- valuation_date;
- fund_id;
- nav;
- position_liquidity_profiles;
- asset_liquidation_assumptions;
- redemption_scenario;
- liquidation_policy;
- stress_market_condition;
- selected_lmts.

### 7.2 Combined stress formula

```text
required_cash = redemption_amount + margin_calls + other_liability_outflows
available_cash = starting_cash + cash_from_asset_liquidation - liquidation_costs
liquidity_shortfall = max(required_cash - available_cash, 0)
redemption_coverage_ratio = available_cash / required_cash
```

If required cash is zero, the coverage ratio should be `None` or a special status, not infinite.

### 7.3 Combined result

Fields:

- required_cash;
- available_cash_before_lmt;
- available_cash_after_lmt;
- liquidation_cost_before_lmt;
- liquidation_cost_after_lmt;
- shortfall_before_lmt;
- shortfall_after_lmt;
- redemption_coverage_ratio_before_lmt;
- redemption_coverage_ratio_after_lmt;
- time_to_meet_redemption;
- LMT activation results;
- warnings.

## 8. LMT calibration instruments

### 8.1 Suspension

Purpose:
Temporary exceptional control when the fund cannot operate normal subscriptions/redemptions fairly or safely.

Activation indicators:

- NAV cannot be calculated reliably;
- severe liquidity shortfall;
- market closure/trading halt;
- severe political/financial crisis;
- cyber incident affecting fund operation;
- fraud or valuation uncertainty;
- natural disaster.

Calibration fields:

- activation_reason;
- review_frequency_days;
- reopening_criteria;
- investor_notification_required;
- NCA_notification_required;
- maximum_review_period if fund documents define one.

### 8.2 Redemption gate

Purpose:
Limit the amount redeemed on a dealing date/window.

Inputs:

- redemption orders;
- NAV;
- liquid assets available;
- shortfall;
- investor concentration;
- fund document gate limit;
- operational ability to defer orders.

Calibration formula examples:

```text
gate_trigger_ratio = redemption_orders / NAV
executable_redemption = min(redemption_orders, available_liquidity_after_costs)
deferred_redemption = redemption_orders - executable_redemption
fund_level_gate_ratio = executable_redemption / redemption_orders
```

Recommended outputs:

- activation_required;
- trigger_metric;
- gate_ratio;
- executable_amount;
- deferred_amount;
- remaining_investor_dilution_before_gate;
- remaining_investor_dilution_after_gate.

### 8.3 Extension of notice period

Purpose:
Extend time available to liquidate assets.

Calibration formula:

```text
required_extension_days = max(0, liquidation_days_needed - current_notice_period_days)
```

Outputs:

- activation_required;
- existing_notice_period_days;
- required_notice_period_days;
- extension_days;
- resulting_shortfall;
- investor impact note.

### 8.4 Redemption fee

Purpose:
Charge redeeming investors to cover predictable liquidity costs.

Formula:

```text
redemption_fee_rate = expected_cost_to_redeeming_investors / redemption_amount
```

Cost stack:

- explicit transaction fees;
- fixed taxes/levies;
- known dealing costs;
- limited stressed add-on if methodology permits.

Outputs:

- fee_rate;
- fee_amount;
- cost_recovered;
- residual_cost;
- whether static fee is sufficient in stress.

### 8.5 Swing pricing

Purpose:
Adjust dealing NAV to pass estimated liquidity costs to transacting investors and protect remaining investors.

Inputs:

- net subscriptions/redemptions;
- swing threshold;
- liquidation-cost estimate;
- spread and market-impact assumptions;
- maximum swing factor;
- full/partial/tiered model.

Formula:

```text
raw_swing_factor = estimated_liquidity_cost / NAV_or_flow_basis
applied_swing_factor = min(raw_swing_factor, maximum_swing_factor) if max exists
```

Outputs:

- swing_triggered;
- raw_swing_factor;
- applied_swing_factor;
- exceeded_maximum_factor;
- cost_transferred_to_transacting_investors;
- residual_dilution.

### 8.6 Dual pricing

Purpose:
Use bid and offer prices to reflect transaction side.

Formula:

```text
bid_nav = mid_nav - sell_cost_adjustment
offer_nav = mid_nav + buy_cost_adjustment
```

Outputs:

- bid_nav;
- offer_nav;
- bid_offer_spread_nav;
- residual market-impact add-on.

### 8.7 Anti-dilution levy

Purpose:
Apply a levy to subscribing/redeeming investors to offset liquidity costs.

Formula:

```text
adl_rate = estimated_liquidity_cost / transacting_flow_amount
adl_amount = adl_rate * transacting_flow_amount
```

Outputs:

- levy_rate;
- levy_amount;
- explicit_cost_component;
- implicit_cost_component;
- residual_cost;
- recalibration_required.

### 8.8 Redemption in kind

Purpose:
Satisfy redemptions by transferring assets instead of cash.

Calibration inputs:

- investor eligibility;
- asset transferability;
- tax/custody constraints;
- pro-rata basket feasibility;
- concentration effects.

Outputs:

- in_kind_eligible;
- asset_basket;
- cash_component;
- fairness warning;
- operational warning.

### 8.9 Side pockets

Purpose:
Segregate illiquid or impaired assets. Treat as a future model layer.

Inputs:

- asset impairment;
- valuation uncertainty;
- sanctions or trapped assets;
- fund document permissions;
- investor communication requirements.

Outputs:

- side_pocket_amount;
- side_pocket_nav_share;
- liquid_pool_nav;
- redemption eligibility impact.

## 9. Calibration of limits

### 9.1 LiquidityLimitDefinition

Fields:

- limit_id;
- metric;
- source;
- limit_type;
- threshold;
- direction;
- description;
- applies_to_fund_type;
- active_from;
- active_to.

Sources:

- REGULATORY;
- REGULATOR_IMPOSED;
- FUND_DOCUMENT;
- INTERNAL;
- LMT_POLICY.

Metrics:

- CASH_RATIO;
- LIQUID_ASSET_RATIO_T1;
- LIQUID_ASSET_RATIO_T5;
- REDEMPTION_COVERAGE_RATIO;
- LIQUIDITY_SHORTFALL;
- TIME_TO_LIQUIDATE_DAYS;
- STRESSED_LIQUIDATION_COST_BPS;
- SWING_FACTOR_REQUIRED;
- ADL_RATE_REQUIRED;
- GATE_TRIGGER_RATIO;
- LARGEST_INVESTOR_COVERAGE_RATIO.

### 9.2 Calibration hierarchy

1. Regulatory/fund document constraints.
2. Board/risk appetite thresholds.
3. Historical internal experience.
4. Peer/market assumptions if approved.
5. Reverse stress test thresholds.
6. LST output distribution.

### 9.3 Warning/escalation/hard limit design

| Level | Example trigger | Action |
|---|---|---|
| Warning | redemption coverage < 150% | risk monitoring |
| Escalation | redemption coverage < 120% | committee review |
| Hard breach | redemption coverage < 100% | action/LMT consideration |
| LMT activation | redemption coverage < 100% or shortfall > 0 | tool simulation/activation workflow |

## 10. Combined test scenarios

### 10.1 Base redemption with normal liquidation assumptions

- Redemption: 5% NAV.
- Liquidation policy: most-liquid-first.
- Market condition: normal.
- Expected result: no shortfall, low cost, no LMT activation.

### 10.2 Severe redemption with stressed spreads

- Redemption: 20% NAV.
- Stressed bid-ask spreads.
- Market impact multiplier: 2x to 4x.
- Expected result: swing pricing/ADL candidate, possible warning/escalation.

### 10.3 Market-wide liquidity shock with redemption pressure

- Redemption: 10% NAV.
- ADV participation halved.
- Bond liquidity capacity reduced.
- Cost add-on applied.
- Expected result: time-to-liquidation increases, possible notice extension or gate.

### 10.4 Investor concentration redemption

- Largest investor redeems full holding.
- Top-5 investor stress optional.
- Expected result: investor concentration warning, gate simulation, ADL/swing comparison.

### 10.5 Fire-sale liquidation scenario

- Liquidation required within settlement period.
- Least-liquid or selected-liquidation policy.
- Expected result: high liquidation cost and dilution; LMT needed if remaining investor dilution exceeds threshold.

### 10.6 LMT activation comparison

Run each combined stress before and after tools:

| Tool | Before metric | After metric |
|---|---|---|
| Gate | full redemption shortfall | reduced executable redemption, deferred balance |
| Notice extension | shortfall by settlement date | additional liquidation time |
| Swing pricing | dilution to remaining investors | cost passed to transacting investors |
| ADL | residual liquidation cost | levy recovery |
| Redemption in kind | cash shortfall | cash need reduced by in-kind basket |
| Suspension | impossible or unfair processing | temporary stop and review status |

## 11. Audit trail

Every stress result and LMT calibration should capture:

- input data date;
- methodology version;
- assumption source;
- scenario ID;
- model parameters;
- limit IDs evaluated;
- LMTs considered;
- LMT selected or rejected;
- explanation;
- warnings;
- approver / committee reference when later persisted.

## 12. Future data contracts

### 12.1 PositionLiquidityProfile

```python
PositionLiquidityProfile(
    position_id: str,
    instrument_id: str,
    asset_class: str,
    market_value_base_ccy: Decimal,
    liquidity_bucket: LiquidityBucket,
    normal_liquidation_horizon_days: int,
    stressed_liquidation_horizon_days: int,
    normal_liquidation_cost_bps: Decimal,
    stressed_liquidation_cost_bps: Decimal,
    daily_liquidation_capacity_base_ccy: Decimal,
    assumption_source: LiquidityAssumptionSource,
    rationale: str | None,
)
```

### 12.2 LiquidityStressScenario

```python
LiquidityStressScenario(
    scenario_id: str,
    redemption_percent_nav: Decimal,
    margin_call_percent_nav: Decimal,
    market_liquidity_shock: str,
    liquidation_policy: LiquidationPolicy,
    stress_cost_multiplier: Decimal,
)
```

### 12.3 LMTCalibrationResult

```python
LMTCalibrationResult(
    lmt_type: LMTType,
    activation_required: bool,
    trigger_metric: str,
    trigger_value: Decimal,
    threshold: Decimal,
    calibrated_level: Decimal | None,
    residual_shortfall: Decimal,
    residual_dilution: Decimal,
    warnings: list[str],
)
```

## 13. Implementation order

1. Taxonomy and buckets.
2. Position liquidity profiles.
3. Liquidation assumptions.
4. Asset liquidation engine.
5. Redemption scenario model.
6. Redemption stress engine.
7. Combined stress engine.
8. Liquidity limits.
9. LMT inventory.
10. LMT calibration engines.
11. LMT activation simulation.
12. Persistence and reporting.
