## MRS-138 — Equity-like stress testing engine

### Goal

Implement Phase 1 stress testing for equity-like investment fund portfolios.

The engine should apply deterministic shocks to the current risk-ready portfolio and produce:

- stressed market value
- stressed NAV
- stressed P&L
- percentage loss
- scenario metadata for audit and methodology documentation

This is an internal AIFM-style portfolio stress engine. It is not a PRIIPs RTS scenario engine and not a full ESMA liquidity stress-testing module.

---

## Regulatory interpretation

### AIFMD / ESMA

For AIFMD / ESMA fund stress testing:

- stress testing is required
- most market shock sizes are manager-defined
- the AIFM must document methodology, assumptions, scenario severity, frequency, and governance
- historical, hypothetical, and reverse stress scenarios are acceptable
- liquidity stress testing is separate and should be implemented later

### PRIIPs

PRIIPs stress scenarios are different:

- PRIIPs scenarios are disclosure calculations
- PRIIPs RTS methodology is more prescriptive
- PRIIPs should be implemented as a separate engine later
- PRIIPs stress scenarios should not be mixed into the internal AIFM stress engine

---

## Phase 1 scope

Included:

- equity-like instruments
- ETFs
- listed funds
- index-like positions
- base-currency cash unchanged
- deterministic parallel equity shocks
- historical stress windows using price returns
- user-defined hypothetical shocks
- reverse stress to NAV loss threshold
- pure risk engine
- tests

Out of scope for Phase 1:

- bonds
- fixed-income curve shocks
- clean / dirty bond valuation
- credit spread shocks
- derivatives
- FX forwards
- foreign-currency cash
- liquidity stress testing
- redemption shocks
- investor concentration shocks
- LMT activation
- PRIIPs RTS stress scenarios
- persistence / service integration unless added as a later step

Bonds are excluded from Phase 1 because they require a different methodology:

- clean price versus dirty price treatment
- accrued interest
- yield curve shocks
- spread shocks
- modified duration
- spread duration
- maturity buckets / curve vertices
- rating / issuer / sector spread buckets
- potentially QuantLib / ORE-style repricing

Bonds should be added later in a separate fixed-income stress module.

---

## Step 1 — Pure hypothetical equity shock engine

Create a pure stress-testing engine that applies a single shock to all equity-like market values.

Supported asset classes:

- `EQUITY`
- `ETF`
- `LISTED_FUND`
- `INDEX`
- `CASH`

Cash treatment:

- base-currency cash is unchanged
- cash stressed value equals current value
- cash P&L equals zero

Shock treatment:

```text
equity_like_stressed_value = current_market_value * (1 + shock_rate)
position_pnl = stressed_market_value - current_market_value
portfolio_pnl = sum(position_pnl)
stressed_nav = current_nav + portfolio_pnl
loss_pct_nav = max(0, -portfolio_pnl / current_nav)
```

Initial scenarios:

| Scenario code | Scenario name | Shock |
|---|---|---:|
| `EQ_PARALLEL_10` | Equity parallel shock -10% | `-0.10` |
| `EQ_PARALLEL_20` | Equity parallel shock -20% | `-0.20` |
| `EQ_PARALLEL_30` | Equity parallel shock -30% | `-0.30` |
| `EQ_PARALLEL_40` | Equity parallel shock -40% | `-0.40` |
| `USER_DEFINED` | User-defined equity shock | configurable |

Models:

- `StressScenario`
- `StressScenarioInput`
- `StressPositionResult`
- `StressScenarioResult`

Tests:

- -10% equity shock
- -20% equity shock
- cash unchanged
- mixed equity / cash portfolio
- positive shock produces gain and zero loss percentage
- unsupported asset class rejected
- shocked market values calculated correctly
- portfolio stressed NAV calculated correctly
- loss percentage calculated as positive loss magnitude

---

## Step 2 — Reverse stress engine

Implement reverse stress to calculate the parallel equity shock required to reach a target NAV loss.

Input:

- risk-ready portfolio
- target loss percentage, e.g. `0.10`, `0.20`, `0.30`

Formula:

```text
target_loss_amount = NAV * target_loss_percentage
required_shock = -target_loss_amount / equity_like_market_value
```

Cash remains unchanged, so portfolios with more cash require a larger equity shock to reach the same NAV loss.

Output:

- target loss percentage
- required shock
- stressed NAV
- stressed P&L
- feasibility flag

Tests:

- 10% NAV loss threshold
- 20% NAV loss threshold
- portfolio with cash requires larger equity shock
- no equity exposure rejected or marked infeasible
- required shock capped or flagged if below -100%

---

## Step 3 — Historical stress window engine

Reuse existing price-to-return logic to calculate historical stress shocks for named windows.

Initial historical windows:

| Scenario code | Scenario name | Window |
|---|---|---|
| `HIST_GFC` | Global financial crisis | 2008-2010 |
| `HIST_EU_DEBT` | European debt crisis | 2010-2012 |
| `HIST_COVID` | Covid sell-off | Feb-Mar 2020 |
| `HIST_RATE_2022_PROXY` | 2022 listed-risk-asset drawdown | 2022 |

Phase 1 implementation:

- accept historical price points
- convert prices to returns
- calculate scenario P&Ls using the current portfolio
- report worst loss in the selected window
- do not fetch market data inside the pure engine

Tests:

- historical window with known price path
- worst P&L selected
- missing data rejected
- cash unchanged
- scenario date / window metadata preserved

---

## Step 4 — Persistence and service integration

Only after pure engines are complete:

- add ORM / repository support if schema exists
- add mapper
- add service
- persist scenario name, scenario type, source, shock rate, stressed NAV, P&L, loss percentage, and run metadata

Persistence fields should include:

- fund id
- valuation date
- calculation run id
- scenario code
- scenario name
- scenario type
- scenario source
- shock rate
- stressed NAV
- stressed P&L
- loss percentage
- number of positions stressed
- number of positions excluded
- created timestamp

---

## Later module — Fixed-income stress testing

Bonds should be added later as a separate module.

Reason:

Equity stress can use direct market-value shocks, but fixed-income stress needs curve / spread methodology.

Future fixed-income stress scope:

- clean price versus dirty price convention
- accrued interest
- dirty value for NAV / P&L impact
- clean price for market quote reference
- modified duration shocks
- spread-duration shocks
- yield curve vertices
- credit spread buckets
- maturity buckets
- rating / issuer / sector spread shocks
- QuantLib / ORE-style full repricing as a later phase

Safe implementation rule:

```text
Use dirty value for NAV and P&L impact.
Keep clean price for market quote / reference.
```

Possible fixed-income approximation:

```text
rate_pnl ≈ -modified_duration * yield_shock * dirty_market_value
credit_pnl ≈ -spread_duration * spread_shock * dirty_market_value
stressed_dirty_value = current_dirty_value + rate_pnl + credit_pnl
```

---

## Acceptance criteria

- Pure hypothetical stress engine implemented and tested.
- Reverse stress engine implemented and tested.
- Historical window stress engine implemented and tested.
- Cash remains unchanged.
- Equity-like shocks apply to current portfolio market values.
- Unsupported asset classes fail explicitly.
- Stress results use project sign conventions:
  - P&L is signed
  - losses are negative
  - percentage loss is positive
- PRIIPs logic is not mixed into this module.
- Liquidity stress testing is not mixed into this module.
- Fixed-income stress testing is deferred to a later module.
