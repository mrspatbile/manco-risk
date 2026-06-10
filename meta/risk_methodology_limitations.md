# Risk Methodology Limitations

## Purpose

This note records the known limitations of the first version of the `manco-risk` VaR methodology.

The goal is to keep the implementation honest and avoid presenting a simple equity-like VaR simulator as a universal market risk engine.

## Current Phase 1 scope

The first VaR simulator is limited to equity-like instruments:

- Listed equities
- ETFs
- Listed funds with reliable price history
- Index-like instruments or explicitly mapped proxies
- Base-currency cash

The current portfolio is fixed at valuation date `t`.

Historical shocks are applied to today’s current exposure. Old portfolio compositions are not used.

## Explicitly out of scope

The first version does not cover:

- Derivatives
- Options
- Swaps
- FX forwards
- Futures
- Hedge rolling
- Fixed-income yield-curve revaluation
- Bond aging and roll-down
- Short-maturity fixed income mapped to curve tenors
- Credit spread shocks
- Foreign-currency cash
- Full PRIIPs methodology implementation
- QuantLib integration
- Open Source Risk Engine integration

## Why these limitations matter

A simple historical price-return VaR can be reasonable for listed equities and ETFs.

It is not generally appropriate for instruments whose risk depends on more than a directly observable price return.

Examples:

- A bond’s risk depends on rates, spreads, duration, convexity, maturity, coupon structure, and roll-down.
- A short-maturity Treasury bill should not blindly use the same ISIN price history over a long lookback window.
- An FX forward depends on spot FX, rates, forward points, maturity, and notional.
- An option or structured derivative requires Greeks, pricing models, or full scenario revaluation.
- A hedge may be static or rolled, and the choice materially changes the simulated risk.

## Treatment of cash

Base-currency cash is treated as constant:

```text
cash_return = 0
cash_scenario_pnl = 0
```

This is acceptable for simple base-currency cash.

Foreign-currency cash is not covered in the first version because it introduces FX risk.

Cash equivalents, money-market funds, deposits, and T-bills should not automatically be treated as cash unless the methodology explicitly allows it.

## Missing data limitation

The default policy is strict.

The calculator should fail if a supported non-cash instrument does not have sufficient clean historical data.

The first version should not silently use:

- forward-filled prices
- stale prices
- incomplete series
- unmapped proxies
- old portfolio compositions

Any later use of scenario dropping, proxy mapping, or filling must be documented and reported in a data quality output.

## Hedges

Current hedges should be included as current positions when the methodology supports the hedge instrument type.

For the first version:

- FX forwards and derivatives are out of scope
- hedge rolling is out of scope
- static versus rolling hedge treatment must be documented as a methodology choice before implementation

For 1-day VaR, static hedge treatment is usually the simpler starting point.

For longer horizons, rolling hedge treatment requires an explicit hedge policy model, including rebalance frequency, target hedge ratio, tolerance bands, costs, maturity treatment, and forward points.

## Fixed income

Fixed income is out of scope for the first equity-like simulator.

A more complete implementation should use one or more of:

- yield curve shocks
- spread shocks
- duration/convexity approximation
- mapped benchmark risk factors
- constant-maturity curve nodes
- full pricing revaluation

Short-maturity instruments should not blindly use the same ISIN price history over long lookback windows.

## Derivatives

Derivatives are out of scope.

A more complete implementation requires:

- pricing models
- Greeks approximation
- full revaluation under historical scenarios
- curves, vol surfaces, calendars, schedules, and conventions
- model validation and methodology documentation

External engines such as QuantLib or Open Source Risk Engine may be evaluated later for these purposes.

## PRIIPs

PRIIPs-style methodology may be considered later for simple Category 2 equity-like instruments.

The first implementation should not be described as PRIIPs-compliant unless all relevant requirements are implemented and tested.

PRIIPs methodology is product-disclosure oriented and prescriptive. It should remain separate from the general internal VaR simulator unless explicitly scoped.

## QuantLib and ORE

QuantLib and ORE are not part of the first implementation.

Potential future use cases:

- calendars
- schedules
- day count conventions
- yield curves
- bond pricing
- derivative pricing
- scenario revaluation
- portfolio-level risk analytics

Even if an external engine is used later, the `manco-risk` project should retain:

- fund admin ingestion
- validation
- database records
- methodology records
- calculation run metadata
- audit trail
- result persistence
- reporting workflow

## Current methodology statement

The first VaR simulator should be described as:

```text
A fixed-current-portfolio equity-like VaR simulator using admin market values,
historical price return shocks, strict data quality checks, and positive loss
VaR reporting.
```

It should not be described as:

```text
a universal market risk engine
a derivatives VaR engine
a fixed-income VaR engine
a PRIIPs-compliant calculator
an ORE/QuantLib replacement
```
