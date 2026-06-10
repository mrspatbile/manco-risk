# Equity Historical VaR Methodology

## Purpose

This note defines the first version of the VaR methodology for the `manco-risk` project.

The purpose is not to build a universal institutional VaR engine. The first implementation is a transparent VaR simulator for equity-like portfolios, using the current portfolio as of the valuation date and applying historical price shocks to that fixed portfolio.

## Scope

The methodology applies to:

- Listed equities
- ETFs
- Listed funds with reliable price history
- Index-like instruments or explicit index proxies
- Base-currency cash

The methodology does not apply to derivatives, bonds, FX forwards, or instruments requiring model revaluation.

## Core principle

VaR is calculated on the current fixed portfolio at valuation date `t`.

The simulator does not use old portfolio compositions.

The core workflow is:

```text
current fixed portfolio at valuation date t
+ historical price return shocks
+ current admin market values
= scenario P&Ls

scenario P&Ls
= VaR input distribution
```

The current admin market value and NAV are the source of truth for today’s exposure.

## Supported position treatment

### Equity-like instruments

For each supported non-cash position:

```text
scenario_pnl = current_market_value * historical_return
```

Where:

- `current_market_value` is the admin market value at valuation date `t`
- `historical_return` is the historical price return for the mapped instrument or proxy
- Scenario P&L is signed:
  - positive = gain
  - negative = loss

Portfolio scenario P&L is:

```text
portfolio_scenario_pnl = sum(position_scenario_pnl)
```

### Base-currency cash

Base-currency cash is treated as constant:

```text
cash_return = 0
cash_scenario_pnl = 0
```

Cash reduces portfolio VaR mechanically because it forms part of NAV but does not generate simulated market loss.

Foreign-currency cash is not covered in the first version because it introduces FX risk.

## Data quality and missing data

The default policy is strict.

The simulator should not silently fill missing prices or broken time series.

For supported non-cash positions, the scenario generator requires:

- admin market value
- positive historical prices
- no duplicate price dates
- sufficient price observations for the selected method
- a continuous enough trading-date series for the selected observation interval

Weekends and market holidays are not treated as missing observations.

For 1-day historical VaR, returns are computed between consecutive available trading observations.

For holding-period VaR, the observation interval should be based on trading observations unless a different methodology is explicitly documented.

Default missing-data handling:

```text
STRICT:
fail the calculation if any supported non-cash position lacks sufficient historical data
```

Potential future options:

```text
DROP_SCENARIO:
drop scenario dates where one or more instruments lack data, with full disclosure

PROXY:
use an explicitly mapped proxy or benchmark

FORWARD_FILL:
not default; only allowed for documented short gaps if the methodology permits it
```

## VaR methodologies planned for the equity-like simulator

### 1. Historical 1-day VaR with square-root-of-time scaling

Compute 1-day historical scenario P&Ls, calculate 1-day VaR, and scale to a longer horizon:

```text
VaR_h = VaR_1d * sqrt(h)
```

This assumes stable volatility and independent returns. It is simple and useful for comparison, but it is a modelling assumption.

### 2. Historical holding-period VaR

Compute direct holding-period historical returns:

```text
return_s,h = price_s / price_(s-h) - 1
```

Then apply those holding-period shocks to today’s fixed current market values.

This avoids square-root scaling but produces fewer effective observations and may use overlapping windows.

### 3. Parametric normal VaR

Estimate the portfolio return or P&L distribution and apply a normal distribution quantile.

This is simple and transparent, but normal tails may understate risk for equity-like portfolios.

### 4. Parametric Student-t VaR

Estimate or set a Student-t distribution and apply a Student-t left-tail quantile.

This can better reflect fat-tailed equity return behaviour, but fitting degrees of freedom can be unstable and must be controlled.

### 5. Variance-covariance VaR

Use asset-level return series, current portfolio weights, and a covariance matrix:

```text
portfolio_variance = w.T @ Cov @ w
portfolio_volatility = sqrt(portfolio_variance)
```

Then apply a distribution quantile, typically normal or Student-t.

This is closer to a risk-factor covariance approach.

### 6. PRIIPs-style Category 2 VaR / VEV

A PRIIPs-style method may be added for simple equity-like instruments.

This should be treated separately from the general VaR simulator because PRIIPs is prescriptive and product-disclosure oriented.

Do not label results as PRIIPs-compliant until the relevant RTS details are implemented and tested, including data frequency, holding period, Cornish-Fisher/tail correction where applicable, VEV conversion, and MRM class mapping.

## Historical VaR aggregation convention

Historical VaR is based on scenario P&Ls.

The aggregation engine consumes clean scenario P&Ls and does not handle missing prices.

P&Ls are sorted from worst loss to best gain. VaR is reported as a positive loss magnitude.

If the selected scenario P&L is negative:

```text
var_value = abs(selected_pnl)
```

If the selected scenario P&L is positive or zero:

```text
var_value = 0
```

VaR as a percentage of NAV is:

```text
var_pct_nav = var_value / NAV_t
```

## Implementation boundary

The VaR aggregation engine and the scenario generation layer must remain separate.

The VaR aggregation engine:

- receives clean scenario P&Ls
- sorts losses
- selects the quantile
- reports positive VaR loss magnitude

The scenario generation layer:

- validates price histories
- maps instruments to price/proxy histories
- computes historical shocks
- generates position-level and portfolio-level scenario P&Ls
- reports data quality decisions

## Current assumptions

- Portfolio is fixed at valuation date `t`
- Admin market values are the current exposure source of truth
- NAV at valuation date `t` is used for VaR percentage calculation
- Cash in base currency is constant
- Only equity-like instruments are supported in the first version
- Unsupported instruments should cause the calculation to fail unless explicitly excluded by methodology

---

## Method limitations


| Method | Main use | Main limitation |
|---|---|---|
| Historical 1-day VaR with square-root-of-time scaling | Simple benchmark for longer horizons based on 1-day VaR. | - Assumes independent returns and stable volatility; <br> - can understate risk during volatility clustering, jumps, or stressed markets. |
| Historical holding-period VaR | Direct simulation of the selected holding-period move, such as 20 trading days. | - Produces fewer observations and may rely on overlapping windows; <br> - results can be sensitive to the lookback period. |
| Parametric normal VaR | Fast and transparent VaR based on mean and volatility. | - Assumes normally distributed returns; <br> - can underestimate equity/ETF tail losses. |
| Parametric Student-t VaR | Parametric VaR with fatter tails than the normal distribution. | - Calibration can be unstable; <br> - fitted degrees of freedom may change materially with sample period and outliers. |
| Variance-covariance VaR | Efficient portfolio VaR using weights, volatilities, and correlations. | - Depends heavily on covariance estimates; <br> - correlations may break down in stress periods and the method is linear. |
| PRIIPs-style Category 2 VaR / VEV | Regulatory-style disclosure metric for simple products with suitable price history. | - Prescriptive and disclosure-oriented; <br> - should not be called PRIIPs-compliant unless the full RTS methodology is implemented and tested. |