# Liquidity Analytics Methodology

**Document purpose:** Specify the liquidity calculations implemented in `src/manco_risk/risk/liquidity/` for issue #6.

**Status:** Complete implementation with tests and type safety  
**Last reviewed:** 2026-06-30  
**Related design reference:** [LIQUIDITY_STRESS_LMT_DESIGN.md](LIQUIDITY_STRESS_LMT_DESIGN.md) (historical design document)

---

## Overview

This module implements six core liquidity analytics:

1. **Time-to-Liquidate (TTL)** — Estimate position liquidation timeline
2. **Liquidity Bucket Classification** — Classify TTL into risk buckets
3. **Portfolio Liquidity Profile** — Aggregate portfolio by bucket
4. **Redemption Stress** — Test liquidity coverage under redemption shock
5. **Investor Concentration** — Analyze top-N investor exposure
6. **Liquidity-Adjusted VaR** — Add liquidity cost to base VaR

Each calculation is independent, typed, tested, and documented below.

---

## 1. Time-to-Liquidate (TTL)

### Purpose

Estimate how many days are required to liquidate a position at a given market capacity.

Used to:
- Classify positions by liquidity horizon
- Identify positions requiring extended liquidation
- Support liquidity bucket classification

### Inputs

| Input | Type | Unit | Constraints |
|-------|------|------|-------------|
| position_id | int | — | Unique identifier |
| asset_class | str | — | Non-empty |
| market_value | Decimal | EUR | Non-negative |
| liquidation_capacity_per_day | Decimal | EUR/day | Positive |

### Formula

```
days_to_liquidate = market_value / liquidation_capacity_per_day
```

### Units and Conventions

- **Market value**: Decimal in base currency (EUR), non-negative
- **Liquidation capacity**: Decimal in EUR per calendar day, positive
- **TTL result**: Decimal in days (fractional days allowed)
  - Example: `0.5 days` for positions half the daily capacity
  - Example: `2.5 days` for positions 2.5× daily capacity

### Interpretation

- **TTL = 0**: Position can be liquidated same-day
- **TTL = 1**: Position takes one day to liquidate
- **TTL = 2.5**: Position takes 2.5 days to liquidate (fractional acceptable)
- **TTL >> 5**: Position may be considered illiquid depending on bucket scheme

### Implementation

**Module:** `TimeToLiquidateEngine`  
**Input model:** `PositionLiquidityInput`, `LiquidationAssumptionSet`  
**Output model:** `TimeToLiquidateResult`

### Simplifications / Out of Scope

- No market impact modeling (capacity is assumed constant)
- No haircut applied to proceeds (liquidation time only)
- No multi-period effects or contagion
- Assumes positions liquidate independently

---

## 2. Liquidity Bucket Classification

### Purpose

Classify a position's TTL into a predefined liquidity bucket for portfolio segmentation.

Used to:
- Group positions by liquidation horizon
- Support portfolio liquidity profile aggregation
- Identify tail risks and concentration

### Inputs

| Input | Type | Unit |
|-------|------|------|
| days_to_liquidate | Decimal | days |
| bucket_scheme | LiquidityBucketScheme | — |

### Matching Rule

```
For each bucket in bucket_scheme (in order):
  If bucket.min_days <= ttl <= bucket.max_days:
    Return bucket.name
  If bucket.max_days is None (unbounded):
    If ttl >= bucket.min_days:
      Return bucket.name
```

Returns error if TTL does not fall into any bucket.

### Units and Conventions

- **TTL days**: Decimal (from TTL calculation)
- **Bucket min/max**: Integer days (inclusive range)
- **Bucket name**: String identifier (e.g., "T+0", "T+1-5")

### Example Bucket Scheme

```
T+0:     min=0,  max=0   (same-day)
T+1-5:   min=1,  max=5   (1–5 days)
T+5+:    min=6,  max=None (6+ days, unbounded)
```

### Interpretation

- Tight buckets: more granular risk separation
- Loose buckets: simplified portfolio view
- Empty buckets in aggregation: acceptable (report zero)

### Implementation

**Module:** `BucketClassificationEngine`  
**Input models:** `TimeToLiquidateResult`, `LiquidityBucketScheme`  
**Output model:** `LiquidityBucketClassification`

### Simplifications / Out of Scope

- Buckets are fixed at fund level (no dynamic adjustment)
- No interpolation between buckets
- No correlation with market conditions

---

## 3. Portfolio Liquidity Profile

### Purpose

Aggregate position classifications into a portfolio-level liquidity snapshot.

Shows:
- Distribution of positions across liquidity buckets
- Concentration in illiquid positions
- Availability of liquid assets for redemptions

### Inputs

| Input | Type |
|-------|------|
| fund_id | int |
| valuation_date | date |
| classifications | list[LiquidityBucketClassification] |
| bucket_scheme | LiquidityBucketScheme |
| total_portfolio_value | Decimal |

### Calculation

```
For each bucket in bucket_scheme:
  total_market_value = sum(c.market_value for c in classifications if c.bucket_name == bucket)
  position_count = count(c for c in classifications if c.bucket_name == bucket)
  percentage = total_market_value / total_portfolio_value
```

### Output Model

For each bucket:

```python
PortfolioLiquidityBucketSummary(
    bucket_name: str,
    total_market_value: Decimal,
    position_count: int,
    percentage_of_portfolio: Decimal,  # range [0, 1]
)
```

### Units and Conventions

- **Market value**: Decimal EUR, non-negative
- **Percentage**: Decimal in range [0, 1]
  - Example: 0.25 = 25% of portfolio
- **Position count**: Integer, non-negative
- **Sum of percentages**: Must equal 1.0 (±0.0001 tolerance for rounding)

### Interpretation

- High percentage in T+5+: lower liquidity risk in redemption scenarios
- High percentage in T+1-5: moderate buffer for medium-term redemptions
- High percentage in T+0: maximum flexibility for same-day redemptions
- Empty buckets (0%): acceptable if scheme defines them

### Implementation

**Module:** `PortfolioLiquidityProfileEngine`  
**Input models:** `LiquidityBucketClassification` list, `LiquidityBucketScheme`  
**Output model:** `PortfolioLiquidityProfileResult`

### Simplifications / Out of Scope

- No rebalancing optimization
- No liquidity event simulation
- No position-level constraints or locking

---

## 4. Redemption Stress

### Purpose

Test whether available liquid assets can cover a redemption shock.

Identifies:
- Coverage ratio (liquidity available vs. redemption demand)
- Liquidity shortfall (if any)
- Remaining buffer after redemption

### Inputs

| Input | Type | Unit | Constraints |
|-------|------|------|-------------|
| fund_nav | Decimal | EUR | Positive |
| redemption_shock_rate | Decimal | — | [0, 1] (e.g., 0.10 = 10%) |
| liquid_bucket_names | list[str] | — | Non-empty |

### Formulas

```
redemption_amount = fund_nav × redemption_shock_rate

available_liquidity = sum(
    bucket.total_market_value
    for bucket in portfolio_profile.buckets
    if bucket.bucket_name in liquid_bucket_names
)

coverage_ratio = available_liquidity / redemption_amount
  (undefined if redemption_amount = 0; set to 0 in code)

shortfall_amount = max(redemption_amount - available_liquidity, 0)

remaining_buffer = max(available_liquidity - redemption_amount, 0)
```

### Units and Conventions

- **Shock rate**: Decimal [0, 1]
  - 0 = no redemption (coverage = 0, shortfall = 0, buffer = available)
  - 0.10 = 10% of NAV redeemed
  - 1.0 = 100% of NAV redeemed
- **Coverage ratio**: Decimal ≥ 0
  - > 1: sufficient liquidity
  - < 1: shortfall
  - = 1: exact coverage
- **Shortfall / Buffer**: Decimal EUR, non-negative
  - Mutually exclusive: either shortfall > 0 (buffer = 0) or buffer > 0 (shortfall = 0)

### Interpretation

**Coverage ratio > 1.0**
- Sufficient liquid assets to cover redemption
- No gates or swing pricing required (in theory)

**Coverage ratio < 1.0**
- Liquidity shortfall exists
- Fund would need gates, swing pricing, or additional measures
- Shortfall amount = liquidity gap

**Coverage ratio = 0.5**
- 50% of redemption can be met from liquid assets
- 50% would require deferral or tools

### Implementation

**Module:** `RedemptionStressEngine`  
**Input models:** `PortfolioLiquidityProfileResult`, `RedemptionStressAssumption`  
**Output model:** `RedemptionStressResult`

### Simplifications / Out of Scope

- **Asset-side only**: Tests liquidity of positions, not redemption mechanics
- **No gates/swing pricing**: Calculates coverage but does not trigger or simulate gates
- **No redemption queues**: Assumes all redemptions happen simultaneously
- **No contagion**: Fund stress does not affect liquidation capacity
- **Single period**: No multi-day redemption paths or waterfall effects
- **No haircuts applied to coverage**: Haircuts are noted in assumptions but not deducted from coverage

---

## 5. Investor Concentration

### Purpose

Analyze the concentration of NAV across investors.

Identifies:
- Largest single investor exposure
- Top-N investor concentration (e.g., top-1, top-5, top-10)
- Investor count and diversity

Used for:
- Redemption shock sensitivity (largest investor scenario)
- Fund diversification monitoring
- Regulatory reporting (investor limits)

### Inputs

| Input | Type | Unit |
|-------|------|------|
| investor_holdings | list[InvestorHolding] | — |
| fund_nav | Decimal | EUR |
| top_n_levels | list[int] | — |

### Formulas

```
For each investor:
  holding_percentage = investor_nav_amount / fund_nav

Largest investor = investor with max(nav_amount)

For each N in top_n_levels:
  top_n_investors = sorted investors by nav_amount (descending), take first N
  top_n_total = sum(inv.nav_amount for inv in top_n_investors)
  top_n_percentage = top_n_total / fund_nav
```

### Units and Conventions

- **Investor NAV**: Decimal EUR, non-negative
- **Fund NAV**: Decimal EUR, positive (sum of investor holdings typically)
- **Holding percentage**: Decimal [0, 1]
  - 0.05 = 5% of fund
  - 1.0 = sole investor
- **Top-N levels**: List of positive integers
  - Example: [1, 5, 10] calculates top-1, top-5, top-10

### Output Model

```python
InvestorConcentrationResult(
    largest_investor_id: str,
    largest_investor_amount: Decimal,
    largest_investor_percentage: Decimal,
    total_investor_count: int,
    top_n_levels: list[int],
    top_n_investors: dict[int, list[TopNInvestor]],  # e.g., {1: [...], 5: [...]}
)
```

### Interpretation

**Largest investor = 30%**
- Single investor represents significant concentration risk
- Redemption of largest investor would require 30% liquidity

**Top-5 = 60%**
- 60% of NAV held by 5 investors
- Medium concentration risk

**Top-10 = 80%**
- 80% of NAV held by 10 investors
- Moderate diversification

### Implementation

**Module:** `InvestorConcentrationEngine`  
**Input models:** `InvestorHolding` list  
**Output model:** `InvestorConcentrationResult`

### Simplifications / Out of Scope

- **No redemption modeling**: Concentration is a snapshot, not a scenario
- **No correlated redemptions**: Does not model whether large investors might redeem together
- **No behavioral assumptions**: Assumes all investors are equally likely to redeem
- **No multi-fund effects**: Single-fund view only

---

## 6. Liquidity-Adjusted VaR

### Purpose

Add liquidity cost to base VaR to reflect the true cost of closing positions under stress.

Accounts for:
- Bid-ask spreads on liquidation
- Market impact and slippage
- Liquidation horizon costs
- Haircuts on collateral sales

### Inputs

| Input | Type | Unit | Constraints |
|-------|------|------|-------------|
| base_var_amount | Decimal | EUR | Non-negative |
| base_var_rate | Decimal | — | [0, 1] (e.g., 0.05 = 5%) |
| portfolio_value | Decimal | EUR | Positive |
| liquidity_cost_rate | Decimal | — | [0, 1] (e.g., 0.02 = 2%) |

### Formula

```
liquidity_adjustment = portfolio_value × liquidity_cost_rate

liquidity_adjusted_var_amount = base_var_amount + liquidity_adjustment

liquidity_adjusted_var_rate = liquidity_adjusted_var_amount / portfolio_value
```

### Units and Conventions

- **Base VaR amount**: Decimal EUR, non-negative
- **Base VaR rate**: Decimal [0, 1], non-negative
  - 0.05 = 5% VaR
- **Liquidity cost rate**: Decimal [0, 1], non-negative
  - 0.01 = 1% liquidity cost (10 bps)
  - 0.02 = 2% liquidity cost (20 bps)
  - 0.05 = 5% liquidity cost (500 bps) for stressed liquidation
- **Adjustment amount**: Decimal EUR, non-negative
- **Adjusted VaR**: Decimal, same units as base VaR

### Interpretation

**Base VaR 5%, liquidity cost 1% → Adjusted VaR 6%**
- True risk including liquidation cost
- User should hold 6% capital buffer, not 5%

**Base VaR 5%, liquidity cost 0.2% (bid-ask) → Adjusted VaR 5.2%**
- Small adjustment for normal market conditions

**Base VaR 5%, liquidity cost 5% (stressed) → Adjusted VaR 10%**
- Significant adjustment for illiquid portfolio under stress

### Additive Approach

The adjustment is **additive**, not multiplicative:

```
Additive (implemented):
  adjusted_var = base_var + (portfolio × cost_rate)
  
NOT multiplicative:
  adjusted_var ≠ base_var × (1 + cost_rate)
```

This reflects the cost in absolute EUR terms, not a scaling of volatility.

### Implementation

**Module:** `LiquidityAdjustedVaREngine`  
**Input models:** `LiquidityAdjustedVaRAssumption`  
**Output model:** `LiquidityAdjustedVaRResult`

### Simplifications / Out of Scope

- **Simple additive model**: No complex market microstructure
- **No interaction with VaR calculation**: Accepts base VaR as input, does not compute it
- **Constant cost rate**: Does not vary by market condition (use scenarios for that)
- **Portfolio-level only**: Does not disaggregate by position or asset class
- **No correlation with VaR**: Assumes liquidation cost is independent of market shock
- **No connection to historical VaR engines**: Future integration to auto-compute from base VaR

---

## Data Conventions

All liquidity calculations follow project conventions:

| Type | Representation | Range | Example |
|------|---|---|---|
| Rates, percentages | Decimal | [0, 1] | 0.05 = 5% |
| Basis points | int | — | 50 = 50 bps = 0.5% |
| Monetary values | Decimal | ≥ 0 | EUR amounts |
| Days | Decimal | ≥ 0 | 2.5 days |
| Counts | int | ≥ 0 | position_count |

**No raw percentages:** Always use decimals (0.05, not 5).  
**No hardcoded data:** All data loads from CSVs or parameters.  
**No DataFrames at boundaries:** Engines use typed models.  
**Decimal precision:** Preserved throughout; no float conversion.

See `docs/CONVENTIONS.md` for full project data standards.

---

## What Is Not Implemented

The following are **out of scope for issue #6**:

| Feature | Reason | Future Issue |
|---------|--------|---|
| LMT gates | Trigger logic deferred | #7 LMT simulation |
| Swing pricing | Pricing mechanics deferred | #7 LMT simulation |
| Suspension logic | Regulatory workflow deferred | #7 LMT simulation |
| Redemption queues | Multi-period simulation deferred | #7 LMT simulation |
| Multi-period paths | Waterfall scenarios deferred | #7 LMT simulation |
| Contagion stress | Cross-fund effects deferred | Future multi-fund work |
| Annex IV export | Regulatory reporting deferred | #8 or later |
| Streamlit interface | UI deferred | #9 or later |
| Board report formatting | Reporting deferred | #8 or later |

These are designed as separate concerns and can build on this foundation.

---

## Summary

Issue #6 implements a clean, typed foundation for liquidity analytics:

- **TTL calculation** for position-level liquidation timing
- **Bucket classification** for hierarchical risk grouping
- **Portfolio profile** for aggregate portfolio view
- **Redemption stress** for liquidity coverage testing
- **Investor concentration** for redemption risk analysis
- **Liquidity-adjusted VaR** for true risk quantification

All components are:
- ✓ Typed with full type hints
- ✓ Tested (165 tests, all passing)
- ✓ Independent and composable
- ✓ Free of business logic in notebooks or UI
- ✓ Decimal-preserving with no float conversions
- ✓ Documented with formulas and conventions

Related issues (#7 LMT simulation, #8 reporting, #9 UI) can build on these models.
