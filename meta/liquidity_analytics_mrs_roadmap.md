# Liquidity Analytics Implementation Roadmap

Status: implementation roadmap  
Project area: liquidity analytics and LMT simulation  
Parent track: liquidity risk analytics  
Last reviewed: 2026-06-12

## 1. Roadmap objective

This roadmap converts the liquidity methodology into implementable MRS issues. The sequence deliberately starts with pure risk-layer models and engines, then adds combined stress, LMT calibration, persistence, and reporting.

The liquidity track should follow the same architecture principles used in VaR, stress testing, leverage, and derivative pricing:

- pure risk engines do not import database or ORM code;
- database persistence is added after pure models are stable;
- reporting is added after persistence;
- limits and LMT calibration are separate from core stress calculations;
- regulation is represented as data and rules, not hidden assumptions.

## 2. Proposed issue sequence

| Issue | Title | Type | Depends on |
|---|---|---|---|
| MRS-173 | Liquidity taxonomy and bucket model | pure models | MRS-172 |
| MRS-174 | Position liquidity classification | pure engine | MRS-173 |
| MRS-175 | Asset liquidation assumptions | pure models | MRS-173 |
| MRS-176 | Time-to-liquidation engine | pure engine | MRS-174, MRS-175 |
| MRS-177 | Redemption scenario model | pure models | MRS-173 |
| MRS-178 | Redemption stress engine | pure engine | MRS-177 |
| MRS-179 | Asset liquidation stress engine | pure engine | MRS-176 |
| MRS-180 | Combined liquidity stress engine | pure engine | MRS-178, MRS-179 |
| MRS-181 | Liquidity limit monitoring | pure engine | MRS-180 |
| MRS-182 | LMT taxonomy and inventory model | pure models | MRS-173 |
| MRS-183 | Anti-dilution levy calibration | pure engine | MRS-179, MRS-182 |
| MRS-184 | Swing pricing calibration | pure engine | MRS-179, MRS-182 |
| MRS-185 | Redemption gate and notice extension calibration | pure engine | MRS-180, MRS-182 |
| MRS-186 | LMT activation simulation | pure engine | MRS-181, MRS-183, MRS-184, MRS-185 |
| MRS-187 | Liquidity persistence layer | database | MRS-180, MRS-186 |
| MRS-188 | Liquidity reporting views | reporting | MRS-187 |

## 3. MRS-173 — Liquidity taxonomy and bucket model

### Objective

Create core liquidity enums and immutable Pydantic models.

### Scope

- LiquidityBucket
- LiquidityCostComponent
- LiquidationPolicy
- LiquidityScenarioType
- LiquidityAssumptionSource
- base position liquidity profile model

### Out of scope

- classification engine;
- stress testing;
- LMT calibration;
- persistence.

### Inputs

- asset class;
- liquidity bucket convention;
- cost component convention.

### Outputs

- importable pure taxonomy models.

### Main files

- `src/manco_risk/risk/liquidity/__init__.py`
- `src/manco_risk/risk/liquidity/enums.py`
- `src/manco_risk/risk/liquidity/models.py`
- `tests/risk/test_liquidity_models.py`

### Tests

- enum value tests;
- model validation;
- frozen model behaviour;
- no database imports.

## 4. MRS-174 — Position liquidity classification

### Objective

Classify positions into liquidity buckets and assign baseline liquidation assumptions.

### Scope

- rule-based classification;
- cash, listed equity, ETF, listed fund, bond, FX and derivative placeholders;
- unsupported asset class warnings;
- manager override support.

### Out of scope

- market-data-driven ADV model;
- bond quote-depth model;
- persistence;
- stress calculations.

### Inputs

- risk-ready position records;
- classification rules;
- optional override assumptions.

### Outputs

- PositionLiquidityProfile list;
- classification warnings.

### Tests

- cash classified as immediate liquidity;
- listed equity classified by rule;
- bond classification by default rule;
- derivatives classified as close-out/margin placeholder;
- unsupported asset class warning;
- override priority.

## 5. MRS-175 — Asset liquidation assumptions

### Objective

Represent liquidation assumptions independent of the classification engine.

### Scope

- normal/stressed liquidation horizon;
- cost bps;
- daily liquidation capacity;
- asset-class defaults;
- scenario overrides.

### Out of scope

- actual liquidation simulation;
- market data provider integration;
- persistence.

### Inputs

- PositionLiquidityProfile;
- assumption tables;
- scenario shock multipliers.

### Outputs

- AssetLiquidationAssumption records.

### Tests

- positive horizons;
- non-negative costs;
- override application;
- stressed multiplier application.

## 6. MRS-176 — Time-to-liquidation engine

### Objective

Compute how many days are needed to liquidate a target amount or percentage of NAV.

### Scope

- daily liquidation schedule;
- position-level liquidation plan;
- pro-rata and most-liquid-first policies;
- cost calculation by day.

### Out of scope

- redemptions;
- LMTs;
- persistence.

### Inputs

- position liquidity profiles;
- liquidation assumptions;
- target liquidation amount;
- liquidation policy.

### Outputs

- liquidation schedule;
- time-to-liquidation;
- liquidation cost;
- residual illiquid amount.

### Tests

- pro-rata liquidation;
- most-liquid-first liquidation;
- insufficient liquidity shortfall;
- cost bps application;
- cash T0 handling.

## 7. MRS-177 — Redemption scenario model

### Objective

Define liability-side redemption scenarios.

### Scope

- normal/elevated/severe redemption scenario;
- historical percentile placeholder;
- investor concentration scenario;
- margin and collateral outflow fields;
- settlement days and notice period.

### Out of scope

- statistical calibration from historical flows;
- investor database;
- persistence.

### Inputs

- NAV;
- redemption percentage or amount;
- investor concentration assumptions.

### Outputs

- RedemptionScenario;
- RedemptionCashNeed.

### Tests

- redemption percent to amount;
- direct amount scenario;
- margin call addition;
- invalid negative redemption rejected;
- zero redemption scenario allowed.

## 8. MRS-178 — Redemption stress engine

### Objective

Compute redemption cash need and standalone redemption coverage.

### Scope

- cash need calculation;
- available cash and short-term liquid asset coverage;
- redemption coverage ratio;
- shortfall calculation.

### Out of scope

- asset liquidation schedule;
- LMT activation;
- persistence.

### Inputs

- redemption scenario;
- cash amount;
- liquid assets by bucket.

### Outputs

- RedemptionStressResult.

### Tests

- full coverage;
- partial coverage;
- zero cash need;
- margin-call-driven shortfall.

## 9. MRS-179 — Asset liquidation stress engine

### Objective

Run standalone asset liquidation stress using liquidation assumptions.

### Scope

- liquidation by horizon;
- cost by position;
- stressed cost multiplier;
- liquidation shortfall.

### Out of scope

- redemption scenario;
- LMTs;
- persistence.

### Inputs

- position profiles;
- liquidation assumptions;
- target liquidation amount;
- scenario.

### Outputs

- AssetLiquidationStressResult.

### Tests

- normal liquidation;
- stressed liquidation;
- cost multiplier;
- liquidation shortfall;
- illiquid position handling.

## 10. MRS-180 — Combined liquidity stress engine

### Objective

Combine redemption pressure and asset liquidation stress.

### Scope

- required cash;
- available cash after liquidation;
- liquidation cost;
- redemption coverage ratio;
- shortfall;
- time to meet redemptions.

### Out of scope

- LMT calibration;
- persistence;
- reporting.

### Inputs

- RedemptionStressResult or scenario;
- AssetLiquidationStressResult or liquidation assumptions;
- NAV;
- settlement horizon.

### Outputs

- CombinedLiquidityStressResult.

### Tests

- no shortfall;
- shortfall;
- liquidation cost impact;
- settlement horizon breach;
- combined warnings.

## 11. MRS-181 — Liquidity limit monitoring

### Objective

Compare liquidity metrics to regulatory, document and internal thresholds.

### Scope

- LiquidityLimitDefinition;
- LiquidityMetricObservation;
- LiquidityLimitCheckResult;
- warning/escalation/breach statuses.

### Out of scope

- LMT activation;
- persistence.

### Inputs

- liquidity metrics from combined stress;
- configured limits.

### Outputs

- limit check results.

### Tests

- warning threshold;
- escalation threshold;
- hard breach;
- missing observation;
- multiple limits for same metric.

## 12. MRS-182 — LMT taxonomy and inventory model

### Objective

Represent available LMTs and fund-level permissions.

### Scope

- LMTType;
- LMTCategory;
- LMTInventoryItem;
- fund-document availability;
- mandatory selected flag;
- normal/stressed use flag.

### Out of scope

- calibration engines;
- activation simulation;
- persistence.

### Inputs

- fund documents;
- selected LMT list;
- permitted tool inventory.

### Outputs

- LMTInventory.

### Tests

- all LMT instruments represented;
- at least two selected LMTs validation optional;
- suspension treated as exceptional;
- side pocket treated as future/exceptional.

## 13. MRS-183 — Anti-dilution levy calibration

### Objective

Calculate ADL rate from estimated liquidity costs.

### Scope

- explicit cost;
- implicit cost;
- market-impact add-on;
- levy rate;
- residual dilution.

### Out of scope

- swing pricing;
- dual pricing;
- legal activation workflow.

### Inputs

- liquidation cost result;
- transacting flow amount;
- ADL policy.

### Outputs

- ADLCalibrationResult.

### Tests

- explicit-only cost;
- explicit + implicit cost;
- zero flow handling;
- max levy cap if configured.

## 14. MRS-184 — Swing pricing calibration

### Objective

Calculate swing factor using estimated liquidity cost.

### Scope

- full swing;
- partial swing;
- tiered swing placeholder;
- maximum swing factor;
- residual cost.

### Out of scope

- NAV production;
- accounting integration.

### Inputs

- net flow;
- NAV;
- estimated liquidity cost;
- swing policy.

### Outputs

- SwingPricingCalibrationResult.

### Tests

- no swing below threshold;
- swing above threshold;
- maximum swing cap;
- residual dilution.

## 15. MRS-185 — Redemption gate and notice extension calibration

### Objective

Calibrate quantity and timing LMTs.

### Scope

- redemption gate ratio;
- executable vs deferred redemption;
- notice extension days;
- investor-level gate flag for eligible AIF profiles.

### Out of scope

- anti-dilution tools;
- suspension;
- persistence.

### Inputs

- combined stress result;
- gate policy;
- notice extension policy.

### Outputs

- GateCalibrationResult;
- NoticeExtensionCalibrationResult.

### Tests

- no gate needed;
- gate needed due to shortfall;
- gate due to redemption threshold;
- notice extension due to TTL gap.

## 16. MRS-186 — LMT activation simulation

### Objective

Compare before/after liquidity metrics after applying one or more LMTs.

### Scope

- selected LMTs;
- activation decisions;
- combined effect simulation;
- residual shortfall;
- residual dilution;
- warnings.

### Out of scope

- legal approval workflow;
- persistence;
- reporting.

### Inputs

- combined stress result;
- LMT inventory;
- calibration results.

### Outputs

- LMTActivationSimulationResult.

### Tests

- gate reduces cash need;
- notice extension improves liquidation capacity;
- swing/ADL reduces dilution;
- combined tools;
- rejected unavailable tool.

## 17. MRS-187 — Liquidity persistence layer

### Objective

Persist liquidity stress and LMT results.

### Scope

- ORM models;
- mappers;
- repositories;
- calculation service.

### Out of scope

- reporting views;
- UI.

### Inputs

- pure result objects.

### Outputs

- database rows linked to CalculationRun.

### Tests

- mapping tests;
- repository tests;
- service success/failure lifecycle.

## 18. MRS-188 — Liquidity reporting views

### Objective

Provide query/reporting outputs for liquidity risk governance.

### Scope

- latest liquidity stress by fund;
- limit status view;
- LMT activation view;
- CSV or structured report data.

### Out of scope

- UI dashboard;
- document generation unless requested.

### Inputs

- persisted liquidity results.

### Outputs

- reporting schemas and repository queries.

### Tests

- latest result selection;
- fund/date query;
- status aggregation.

## 19. Suggested first implementation prompt

Start with MRS-173. Do not start with combined stress or LMT calibration until taxonomy and position liquidity profiles are stable.
