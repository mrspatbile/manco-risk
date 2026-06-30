# Reference Data Conventions

## Purpose

This document defines the structure, conventions, and deferral roadmap for reference data in manco-risk.

Reference data includes fund profiles, risk policies, and scenario definitions that configure how risk calculations are performed.

---

## Folder Structure

### `data/funds/{fund_id}/`

Per-fund configuration.

**Files:**

- `fund_profile.json` — Fund identity, domicile, regulatory classification, asset types, inception date, target NAV
- `risk_policy.json` — VaR framework, backtesting config, stress testing setup, internal limits, liquidity monitoring

**To add a new fund:**

1. Create `data/funds/{new_fund_id}/` folder
2. Add `fund_profile.json` with fund metadata
3. Add `risk_policy.json` with risk management parameters

**Example:**

```
data/funds/UCITS_Balanced/fund_profile.json
data/funds/UCITS_Balanced/risk_policy.json
```

### `data/reference/`

Shared reference data (not fund-specific).

- `historical_scenarios.json` — Historical market shock parameters (2008, 2011, 2020, 2022)

---

## Conventions

### Units and Sign Conventions

See `CONVENTIONS.md` for project-wide rules. Reference:

- **Decimal rates:** `0.05` = 5% (e.g., equity shock, yield shock)
- **Basis points:** stored as integer multiples of 0.01% (e.g., `300` = 300 bps = 3%)
- **Signed decimals:** `-0.3` = loss of 30%; `0.05` = gain of 5%
- **Dates:** ISO 8601 (e.g., `2015-09-01`)
- **Currencies:** 3-letter ISO code (e.g., `EUR`, `USD`)

### Date Conventions

All dates are ISO 8601 format:

- Fund inception: `YYYY-MM-DD`
- Policy effective dates: `YYYY-MM-DD` (if versioned)
- Scenario dates: encoded in name (e.g., `historical_2008_gfc`)

### Naming Conventions

- `fund_id`: stable key, matches folder name. Example: `UCITS_Balanced`, `AIFM_HedgeFund`
- Scenario keys: lowercase with underscores. Example: `historical_2008_gfc`, `historical_2020_covid`

---

## Field Definitions

### `fund_profile.json`

Fund metadata and regulatory classification.

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `schema_version` | string | `"1.0"` | Schema version identifier |
| `fund_id` | string | `"UCITS_Balanced"` | Stable fund identifier; matches folder name |
| `fund_name` | string | `"UCITS Balanced"` | Display name |
| `fund_type` | string | `"UCITS"` or `"AIFM"` | Fund regime |
| `strategy` | string | `"Balanced portfolio of equities and bonds"` | Strategy description |
| `currency` | string | `"EUR"` | Base/reporting currency (3-letter ISO) |
| `domicile` | string | `"Luxembourg"` | Regulatory jurisdiction |
| `regulator` | string | `"CSSF"` | Primary regulator |
| `inception_date` | string | `"2015-09-01"` | Fund inception (ISO 8601) |
| `target_nav_eur` | number | `500000000` | Target NAV (EUR, for metadata only) |
| `redemption_terms` | object | See below | Redemption structure and frequency |
| `regulatory_classification` | object | See below | Regulatory flags (UCITS, AIFM, Annex IV, etc.) |
| `data_model` | object | See below | Asset types and time series frequency |

**`redemption_terms` object:**

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `structure` | string | `"open_ended"` | Fund structure |
| `redemption_frequency` | string | `"daily"` | Redemption frequency |
| `redemption_notice_days` | integer | `0` or `5` | Notice period before redemption |
| `redemption_settlement_days` | integer | `3` or `1` | Settlement lag after redemption |
| `display` | string | `"Daily dealing, T+3 settlement"` | Human-readable summary |

**`regulatory_classification` object:**

Boolean flags indicating regulatory status. Example:

```json
{
  "is_ucits": true,
  "is_aif": false,
  "is_annex_iv_reportable": false,
  "is_priips_kid_required": true,
  "is_sfdr_article_6": null,
  "is_sfdr_article_8": null,
  "is_sfdr_article_9": null
}
```

**`data_model` object:**

Asset types and time series frequency. Example:

```json
{
  "type": "positions_based",
  "asset_types": ["equity", "bond", "etf", "cash"],
  "time_series_frequency": "daily"
}
```

### `risk_policy.json`

Fund-specific risk management parameters. Covers VaR framework, backtesting, stress testing, liquidity monitoring, and internal limits.

Key sections:

- `var_framework` — VaR models, confidence levels, holding periods, lookback windows
- `backtesting` — Observation window, statistical tests
- `leverage_limits_internal` — Gross and commitment leverage caps
- `liquidity_monitoring` — Stress scenarios and redemption paths
- `concentration_limits_internal` — Single issuer/investor thresholds
- `stress_testing` — Historical and custom scenarios
- `attribution_policy` — Risk factor decomposition (if enabled)
- `srri_monitoring` — UCITS risk indicator parameters (if applicable)

See source files for full details.

### `historical_scenarios.json`

Historical market shock definitions indexed by year.

Each entry contains:

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `name` | string | `"GFC 2008 (Sep-Dec 2008)"` | Scenario display name |
| `description` | string | `"Global Financial Crisis: equity crash, credit widening, safe-haven FX flows"` | Context |
| `delta_equity` | number | `-0.4` | Equity return shock (decimal, signed) |
| `delta_y` | number | `-0.01` | Yield shock (decimal, signed) |
| `delta_spread` | number | `0.03` | Credit spread shock (decimal, signed; positive = widening) |
| `fx_shocks` | object | `{"USD": -0.05, "GBP": -0.15}` | Currency pair shocks (decimal, signed) |

**Sign conventions:**

- Equity shock: negative = loss, positive = gain
- Yield shock: negative = decline in rates, positive = rise in rates
- Spread shock: positive = widening (loss for long credit), negative = tightening (gain for long credit)
- FX shock: negative = depreciation, positive = appreciation

---

## Loaders (To Be Implemented)

The following loaders will read reference data files and validate them:

| Loader | Consumes | Validates | Phase |
|--------|----------|-----------|-------|
| FundProfileLoader | `fund_profile.json` | fund_id uniqueness, fund_type enum, dates, currency codes | 1 |
| RiskPolicyLoader | `risk_policy.json` | fund_id exists, param ranges (confidence levels, lookback windows), scenario references | 1 |
| HistoricalScenarioLoader | `historical_scenarios.json` | scenario keys uniqueness, shock ranges, date validity | 1 |

These will be implemented in the next slice.

---

## Deferred to Future Slices

### Phase 2

- **Counterparties** — OTC counterparty data, collateral treatment, haircuts
- **Benchmarks** — Reference portfolio definitions for relative VaR and Annex IV reporting
- **Regulatory frameworks** — UCITS, AIFM Annex IV, PRIIPs field definitions

### Phase 3+

- **Liquidity calibration** — Asset-level TTL bucketing and calibration weights
- **Alternative asset metadata** — PE, infrastructure, real estate position and valuation schemas

### Later Slices

- **Position datasets** — Sample holdings (UCITS_Balanced, AIFM_HedgeFund, others)
- **Market data expansion** — Enhanced price history, FX rates, instrument master

---

## How to Extend

### Add a New Fund

1. Create `data/funds/{fund_id}/` folder
2. Create `fund_profile.json` with fund metadata
3. Create `risk_policy.json` with risk management parameters
4. Update `docs/REFERENCE_DATA.md` with any new conventions used

### Add a New Scenario

1. Add entry to `data/reference/historical_scenarios.json`
2. Use scenario key in fund risk policies (under `stress_testing.most_relevant_historical_scenarios.selected_scenarios`)
3. Ensure all referenced scenarios exist before using them in policies

---

## Validation Rules

When loaders are implemented, they will enforce:

- `fund_id` uniqueness within `fund_profile.json` and consistency across files
- `fund_type` in allowed list: `UCITS`, `AIFM`
- Date formats: ISO 8601, valid dates
- Numeric ranges: e.g., VaR confidence levels in (0, 1)
- Scenario references: all scenarios referenced in policies must exist in scenario files
- Currency codes: 3-letter ISO standard

---

## Links

- `CONVENTIONS.md` — Project-wide conventions (units, dates, currencies, naming)
- `ARCHITECTURE.md` — How reference data flows through modules
- `PROJECT_SPEC.md` — Overall project scope and phases
