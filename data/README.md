# Data Layer

## Folder Structure

### `funds/`

Per-fund configuration and metadata.

Each fund has its own folder:

```
funds/
  UCITS_Balanced/
    fund_profile.json      Fund identity, regime, currency, inception, NAV
    risk_policy.json       Fund-specific risk management parameters
  AIFM_HedgeFund/
    fund_profile.json
    risk_policy.json
```

To add a new fund:
1. Create `funds/{fund_id}/` folder
2. Add `fund_profile.json` (fund identity and regime)
3. Add `risk_policy.json` (risk framework, VaR parameters, stress scenarios)

See `docs/REFERENCE_DATA.md` for field definitions and conventions.

### `reference/`

Shared reference data used across funds.

- `historical_scenarios.json` — Historical market shock definitions (2008, 2011, 2020, 2022)

### `market_data/`

Market data files (prices, FX rates, instrument definitions).

See `market_data/` folder for details.

---

## Deferred to Later Slices

The following are **not** included in this slice and will be added when needed:

- Position datasets (sample holdings)
- Expanded market data
- Counterparty data
- Liquidity calibration
- Benchmark portfolios
- Regulatory frameworks

See `docs/REFERENCE_DATA.md` for the full deferral roadmap.
