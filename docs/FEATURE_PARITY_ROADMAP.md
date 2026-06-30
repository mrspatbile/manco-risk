# Feature Parity Roadmap

**Roadmap created:** 2026-06-29  
**Last reviewed:** 2026-06-29  
**`manco-risk` version assumed:** 0.1.0  
**Purpose:** Track what remains before `manco-risk` can replace `fund-risk-workflow`.

---

## Purpose

`fund-risk-workflow` = **output reference** (what users see and need)  
`manco-risk` = **architecture reference** (how it should be built)

**Goal:** Recreate the same or better business outputs from `fund-risk-workflow` using the cleaner architecture of `manco-risk`.

Feature parity means:
1. **Capability parity**: same calculations, workflows, methodology coverage, regulatory outputs.
2. **Presentation parity**: same or better plots, tables, reports, notebook storytelling, visual quality.

Feature parity does **not** mean copying notebook code, exploratory architecture, or moving business logic into notebooks.

---

## Migration Rules

- Do not copy notebook-centric architecture.
- Do not move business logic into notebooks, Streamlit, or reporting layers.
- Preserve or improve the visual/reporting quality of `fund-risk-workflow`.
- Reimplement selected functionality through typed models, validation, services, tests, and documented methodology.
- Track both calculation capability and presentation capability separately.
- Exclude exploratory-only workflows and temporary implementation shortcuts.
- Refer to `ARCHITECTURE.md` for module responsibilities and dependency rules.

---

## Status Legend

| Status | Definition |
|--------|-----------|
| **Complete** | Implemented, tested, documented; ready for use. |
| **Partial** | Some functionality exists; key pieces missing. |
| **In Progress** | Actively tracked in an open GitHub issue. |
| **Missing** | Required for parity but not yet implemented. |
| **Deferred** | Valid capability; planned for a later milestone. |
| **Excluded** | Not worth migrating, or conflicts with new architecture. |

---

## Foundational Prerequisites

These must reach feature parity before dependent workflows can be marked complete:

- **Market data ingestion**: CSV loaders, market data schema, historical data storage.
- **Position validation**: Position schema, ingestion rules, exception reporting.
- **Reference data schemas**: Fund profiles, counterparties, benchmarks, scenarios, ratings.
- **Database access layer**: Repository abstractions, schema definitions, migrations.
- **Sample datasets**: Synthetic fund data covering multiple asset classes and rating profiles.

Dependent workflows (VaR, leverage, reporting, etc.) can only reach "Complete" when their foundational dependencies are "Complete" or "In Progress" (with no blockers).

---

## 1. Foundation

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Architecture & modules | — | — | — | — | v0.1.0 | #1 | Complete. See `ARCHITECTURE.md`. |
| Project tooling (uv, pytest, mypy, ruff) | — | — | — | — | v0.1.0 | #2 | Complete. |
| Issue template & delivery guidelines | — | — | — | — | v0.1.0 | #3 | Complete. |
| Feature parity roadmap | — | — | — | — | v0.1.0 | #4 | In progress (this document). |

---

## 2. Data and Reference Data

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Market data loaders (CSV) | Complete | — | — | — | v0.2.0 | TBD | CSV provider implemented; real market data needed. |
| Mock Bloomberg API | Missing | — | — | — | v0.2.0 | TBD | fund-risk-workflow has 39KB mock provider; needed for testing. |
| Position specifications & validation | Complete | — | — | — | v0.2.0 | TBD | Schema and validator complete in manco-risk. |
| Fund profiles & metadata | Missing | — | — | — | v0.2.0 | TBD | Name, strategy, geography, base currency; reference data service. |
| Risk policies & limits | Missing | — | — | — | v0.2.0 | TBD | VaR limits, leverage caps, concentration thresholds. |
| Investor data | Missing | — | — | — | v0.3.0 | TBD | Subscriptions, redemptions, concentration. |
| Counterparty data | Missing | — | — | — | v0.3.0 | TBD | Ratings, exposure limits, haircuts, collateral. |
| Benchmark data & definitions | Missing | — | — | — | v0.2.0 | TBD | Indices, weights, returns. |
| Historical scenarios (market shocks) | Missing | Complete | — | — | v0.2.0 | TBD | 2008, 2020, 2011, 2022 scenarios; fund-risk-workflow has templates. |
| AIFM Hedge Fund sample data | Missing | — | — | — | v0.2.0 | TBD | ~200 positions, equities/FX/derivatives. |
| UCITS Balanced sample data | Missing | — | — | — | v0.2.0 | TBD | ~100 positions, bonds/equities. |
| PE Fund sample data | Missing | — | — | — | v0.2.0 | TBD | Cash flows, valuations, multiples. |
| Infrastructure sample data | Missing | — | — | — | v0.2.0 | TBD | Assets, covenants, debt structures. |
| Real Estate sample data | Missing | — | — | — | v0.2.0 | TBD | Properties, rental income, LTV. |

---

## 3. Configuration & Methodology

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Risk policy templates | Missing | — | — | — | v0.2.0 | TBD | Equity, fixed income, alternatives, multi-asset. |
| Scenario configuration (stress, reverse stress) | Missing | — | — | — | v0.2.0 | TBD | Editable scenario definitions and results. |
| Methodology assumptions documentation | Missing | — | — | — | v0.2.0 | TBD | VaR lookback, confidence levels, scaling factors. |
| Fund setup workflow | Missing | Complete | — | Partial | v0.2.0 | TBD | Create fund, load positions, set policies, validate. |

---

## 4. Market Risk

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Historical VaR (single-period) | Complete | — | — | — | v0.2.0 | TBD | Empirical quantile; 95%/99% confidence; 1-day horizon. Tested and persisted. |
| Expected Shortfall (historical) | Complete | — | — | — | v0.2.0 | TBD | CVaR; tail mean; invariant (ES ≥ VaR) enforced. |
| Expected Shortfall (parametric) | Missing | — | — | — | v0.2.0 | TBD | Not yet implemented for normal or Student-t distributions. |
| Parametric VaR (normal) | Complete | — | — | — | v0.2.0 | TBD | Delta-normal with z-score quantile from scipy.stats.NormalDist(). Tested. |
| Parametric VaR (Student-t) | Missing | — | — | — | v0.2.0 | TBD | Not implemented; would use scipy.stats.t.ppf(). Deferred to v0.2.0+. |
| Scenario P&L (equity) | Complete | — | — | — | v0.2.0 | TBD | Historical returns × position market value. Position and portfolio level. |
| Scenario P&L (fixed-income) | Partial | — | — | — | v0.2.0 | TBD | Available via stress engine only (duration-based PnL), not direct generation. |
| Scenario P&L (derivatives) | Missing | — | — | — | v0.3.0 | TBD | Not yet implemented; deferred to Phase 2. |
| VaR backtesting framework | Complete | — | — | — | v0.2.0 | TBD | Traffic light, exception tracking, statistical tests. |
| Kupiec test (POF) | Complete | — | — | — | v0.2.0 | TBD | Proportion of failures test. |
| Christoffersen test (independence) | Complete | — | — | — | v0.2.0 | TBD | Cluster independence in exceptions. |
| Equity stress scenarios | Complete | — | — | — | v0.2.0 | TBD | Deterministic shocks; position-level and portfolio P&L. Tested. |
| Fixed-income stress scenarios | Complete | — | — | — | v0.2.0 | TBD | Duration-based pricer; rate and credit spread shocks. Tested. |
| Historical stress scenarios (2008, 2020, etc.) | Complete | Partial | — | — | v0.2.0 | TBD | Engine complete (selects worst P&L from window). Data missing (shock parameters). |
| Reverse stress testing (equity) | Complete | — | — | Partial | v0.2.0 | TBD | Calculates required shock to reach target loss; feasibility checks. Tested. |
| Reverse stress testing (fixed-income) | Missing | — | — | — | v0.3.0 | TBD | Not yet implemented; would extend reverse equity pattern. |
| Combined multi-factor stress | Complete | — | — | — | v0.2.0 | TBD | Orchestrates equity + FI engines; handles None scenarios gracefully. Tested. |
| VaR charts & backtesting visuals | Missing | — | Complete | — | v0.2.0 | TBD | Distribution plots, traffic light, exception timeline. |

---

## 5. Liquidity Risk

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Time-to-liquidate (TTL) bucketing | Missing | — | — | — | v0.3.0 | TBD | Asset liquidity classification (T+0, T+1–5, T+5+, illiquid). |
| Liquidity calibration weights | Missing | — | — | — | v0.3.0 | TBD | Asset-level liquidity adjustment factors. |
| Liquidity stress scenarios | Missing | — | — | — | v0.3.0 | TBD | Redemption shock, contagion, fire sales. |
| Redemption stress testing | Missing | — | — | — | v0.3.0 | TBD | Fund-level redemption pathways under stress. |
| Investor concentration analysis | Missing | Complete | — | — | v0.3.0 | TBD | Top-N investor exposure; single largest. |
| Liquidity-adjusted VaR (LVar) | Missing | — | — | — | v0.3.0 | TBD | VaR incorporating bid-ask spreads, market depth. |
| Liquidity profile (AIFMD buckets) | Missing | Complete | — | — | v0.3.0 | TBD | Redemption frequency, notice period, gate provisions. |
| Liquidity charts & distribution | Missing | — | Complete | — | v0.3.0 | TBD | TTL bucket stacked bars, stress outcomes waterfall. |

---

## 6. Liquidity Management Tools (LMT)

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Redemption gates (trigger logic) | Missing | — | — | — | v0.3.0 | TBD | Gate trigger conditions, gate horizon definition. |
| Swing pricing (threshold & rate) | Missing | — | — | — | v0.3.0 | TBD | Swing threshold % NAV, swing rate application. |
| Subscription/redemption suspension | Missing | — | — | — | v0.3.0 | TBD | Suspension conditions and timeline. |
| Contagion switch (cross-fund) | Missing | — | — | — | v0.4.0 | TBD | Multi-fund stress linkage; LMT triggers. |
| LMT trigger analysis | Missing | Complete | — | — | v0.3.0 | TBD | When gates/swing/suspension activated; scenarios. |
| Backlog tracking & analysis | Missing | Complete | — | — | v0.3.0 | TBD | Redemption queues, timing impact on NAV. |
| 12-month redemption path projection | Missing | Complete | Complete | — | v0.3.0 | TBD | Scenarios and stress outcomes. |
| Largest investor scenario | Missing | Complete | Complete | — | v0.3.0 | TBD | Single large redemption impact on liquidity. |
| LMT simulation engine | Missing | Complete | — | Partial | v0.3.0 | TBD | Orchestrate gates, swing, suspension decisions. |

---

## 7. Leverage

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| AIFMD gross leverage | Complete | — | — | — | v0.2.0 | TBD | Sum of notionals, absolute value method. EU231/2013. |
| AIFMD commitment leverage | Complete | — | — | — | v0.2.0 | TBD | Commitment approach, netting rules. EU231/2013. |
| UCITS commitment approach | Complete | — | — | — | v0.2.0 | TBD | Derivative-based commitment exposure; 100% NAV limit. |
| UCITS absolute VaR monitoring | Missing | — | — | — | v0.3.0 | TBD | VaR-based global exposure; 20% NAV threshold. |
| UCITS relative VaR monitoring | Missing | — | — | — | v0.3.0 | TBD | VaR vs. benchmark approach; Annex II. |
| Derivative notional exposure | Complete | — | — | — | v0.2.0 | TBD | Notional, delta, delta-plus methods. |
| Borrowing treatment | Complete | — | — | — | v0.2.0 | TBD | Direct borrowings, interest rate exposure. |
| Securities Financing Transactions (SFT) | Complete | — | — | — | v0.2.0 | TBD | Repos, reverse repos, securities lending. |
| Interest-rate duration netting | Complete | — | — | — | v0.2.0 | TBD | Offsetting long/short IR positions. |
| Granular leverage breakdown | Missing | Complete | — | — | v0.3.0 | TBD | By asset class, counterparty, instrument type. |
| Leverage limit monitoring | Complete | — | — | — | v0.2.0 | TBD | Vs. policy limits; UCITS only. AIFMD monitoring TBD. |
| Leverage charts & trend analysis | Missing | — | Complete | — | v0.3.0 | TBD | Time series vs. policy cap; limit exceedance flags. |

---

## 8. UCITS Monitoring

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Commitment approach global exposure | Complete | — | — | — | v0.2.0 | TBD | Derivative-based; 100% NAV limit. (See Section 7.) |
| Absolute VaR monitoring | Missing | Complete | — | — | v0.3.0 | TBD | VaR-based global exposure; 20% of NAV threshold. |
| Relative VaR monitoring | Missing | Complete | — | — | v0.3.0 | TBD | VaR vs. benchmark VaR; Annex II. |
| SRRI calculation | Missing | Complete | — | — | v0.3.0 | TBD | Synthetic Risk and Reward Indicator; 7-point scale. |
| Stress scenarios (Annex II) | Missing | Complete | — | — | v0.3.0 | TBD | Eight regulatory scenarios defined by ESMA. |
| Concentration checks (10% rule) | Missing | Complete | — | — | v0.3.0 | TBD | Single issuer, asset class limits. |
| Borrowing checks (10% rule) | Missing | Complete | — | — | v0.3.0 | TBD | Maximum 10% of NAV borrowing. |
| OTC counterparty checks | Missing | Complete | — | — | v0.3.0 | TBD | Credit quality, 5% single counterparty limit. |
| UCITS monitoring summary | Missing | Complete | Complete | — | v0.3.0 | TBD | Breach flags, limit exceedance, stress outcomes. |

---

## 9. PRIIPs / KID

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| SRRI (Summary Risk Indicator) | Missing | Complete | — | — | v0.4.0 | TBD | 7-point scale from volatility/VaR; EU PRIIPs. |
| Performance scenario outputs | Missing | Complete | — | — | v0.4.0 | TBD | Favorable/moderate/unfavorable; 1Y/3Y/recommendation horizon. |
| Cost table structure | Missing | Complete | — | — | v0.4.0 | TBD | One-off and ongoing costs; KID template. |
| KID-ready output objects | Missing | Complete | — | — | v0.4.0 | TBD | Export-ready data model for KID generation. |
| KID visualization & formatting | Missing | — | Complete | — | v0.4.0 | TBD | Regulatory-compliant KID layout. |

---

## 10. AIFMD Annex IV Reporting

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Fund identification & summary | Missing | Complete | — | — | v0.3.0 | TBD | ISIN, manager, strategy, AUM, start date. |
| Asset breakdown table | Missing | Complete | — | — | v0.3.0 | TBD | By asset class, geography, sector. |
| Risk measures section | Missing | Complete | — | — | v0.3.0 | TBD | VaR, ES, stress outcomes; regulatory format. |
| Leverage section | Missing | Complete | — | — | v0.3.0 | TBD | Gross, commitment, concentration; Art. 7–8. |
| Liquidity profile | Missing | Complete | — | — | v0.3.0 | TBD | Redemption frequency, notice period, gates. |
| Counterparty register | Missing | Complete | — | — | v0.3.0 | TBD | Concentration by counterparty, collateral. |
| Export-ready Annex IV tables | Missing | Complete | — | — | v0.3.0 | TBD | PDF or regulatory filing format (CSSF quarterly). |
| Annex IV tables in notebook | Missing | — | Complete | — | v0.3.0 | TBD | HTML/table display for review. |

---

## 11. Management Reporting

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Fund summary dashboard | Missing | Complete | Complete | — | v0.2.0 | TBD | AUM, NAV, YTD return, key metrics snapshot. |
| Market risk summary | Missing | Complete | Complete | — | v0.2.0 | TBD | VaR, ES, top risks, stress outcomes. |
| Stress scenario summary | Missing | Complete | Complete | — | v0.2.0 | TBD | P&L outcomes under scenarios vs. policy limits. |
| Liquidity summary | Missing | Complete | Complete | — | v0.3.0 | TBD | TTL profile, redemption capacity, stress outcomes. |
| Leverage summary | Missing | Complete | Complete | — | v0.3.0 | TBD | Gross, commitment, by asset class/counterparty. |
| Exception & breach summary | Missing | Complete | — | — | v0.2.0 | TBD | Policy breaches, data quality gaps, validation issues. |
| Board-style report layout | Missing | Complete | Complete | — | v0.3.0 | TBD | Multi-page PDF, consistent branding, charts & tables. |

---

## 12. Performance Attribution

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| P&L attribution framework | Missing | — | — | — | v0.3.0 | TBD | Position-level, holding period attribution. |
| Equity / rates / FX / credit / residual decomposition | Missing | Complete | — | — | v0.3.0 | TBD | Risk factor breakdown by position. |
| Attribution charts & waterfall | Missing | — | Complete | — | v0.3.0 | TBD | Contribution waterfall, segment analysis. |

---

## 13. ESG

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| ESG score aggregation | Missing | Complete | — | — | v0.4.0 | TBD | Fund-level weighted by NAV/market value. |
| Controversy flags | Missing | Complete | — | — | v0.4.0 | TBD | Count, severity, remediation status by position. |
| Carbon metrics (Scope 1–3) | Missing | Complete | — | — | v0.4.0 | TBD | Intensity, absolute, pathway alignment. |
| Derivative look-through | Missing | — | — | — | v0.4.0 | TBD | ESG attribution for synthetic exposures. |
| ESG charts & scorecards | Missing | — | Complete | — | v0.4.0 | TBD | Fund score gauge, peer comparison, controversy heatmap. |

---

## 14. Alternative Assets (Private Equity, Infrastructure, Real Estate, Private Debt)

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| PE IRR & multiple tracking | Missing | Complete | — | — | v0.4.0 | TBD | DPI, RVPI, TVPI, XIRR; vintage cohorts. |
| PME (Public Market Equivalent) | Missing | Complete | — | — | v0.4.0 | TBD | Long-Nickels method vs. benchmark indices. |
| PE cash flow modeling | Missing | — | — | — | v0.4.0 | TBD | Distributions, reinvestments, projections. |
| PE cash flow visuals | Missing | — | Complete | — | v0.4.0 | TBD | Cumulative, vintage cohorts, KPI timeline. |
| Infrastructure DSCR & LTV | Missing | Complete | — | — | v0.4.0 | TBD | Debt service coverage, leverage ratios; covenant tracking. |
| Infrastructure duration & convexity | Missing | Complete | — | — | v0.4.0 | TBD | Inflation sensitivity, interest rate impact. |
| Real estate valuation stress | Missing | Complete | — | — | v0.4.0 | TBD | Property value decline, rental income compression. |
| Real estate LTV & leverage stress | Missing | Complete | Complete | — | v0.4.0 | TBD | Occupancy shock, interest rate impact on debt. |
| Private debt loan monitoring | Missing | Complete | — | — | v0.4.0 | TBD | Covenant compliance tracking, loan health KPIs. |
| Alternative assets charts | Missing | — | Complete | — | v0.4.0 | TBD | PE cash waterfall, infrastructure DSCR trend, RE stress outcomes. |

---

## 15. Audit & Lineage

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Calculation lineage tracking | Missing | Complete | — | — | v0.3.0 | TBD | What data, parameters, model version produced a result. |
| Data provenance logging | Missing | Complete | — | — | v0.3.0 | TBD | Source, snapshot timestamp, data freshness, chain of custody. |
| Model version & assumption history | Missing | Complete | — | — | v0.3.0 | TBD | Track changes to VaR model, haircuts, scenarios over time. |
| Audit trail export | Missing | Complete | — | — | v0.3.0 | TBD | Exportable proof for regulatory defense (CSSF, ESMA). |

---

## 16. Data Quality & Exception Reporting

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Position validation exceptions | Complete | Complete | — | — | v0.2.0 | TBD | Missing fields, out-of-range values; detailed error list. |
| Market data freshness & gaps | Missing | Complete | — | — | v0.2.0 | TBD | Stale prices, missing tickers, lookback gaps. |
| Reference data mismatch | Missing | Complete | — | — | v0.2.0 | TBD | Rating downgrades, haircut mismatches, fallback usage. |
| Calculation exception report | Missing | Complete | — | — | v0.2.0 | TBD | NaN results, convergence failures, warnings, assumptions. |
| Data quality dashboard | Missing | — | Complete | — | v0.2.0 | TBD | Exception count, severity, trending over time. |

---

## 17. Monitoring & Alerting

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Policy limit monitoring | Missing | Complete | Complete | — | v0.3.0 | TBD | Real-time vs. fund-level thresholds (VaR, leverage, etc.). |
| Regulatory limit monitoring | Missing | Complete | Complete | — | v0.3.0 | TBD | AIFMD (gross/commitment), UCITS (20%, concentration), PRIIPs. |
| Exception threshold alerting | Missing | — | — | — | v0.2.0 | TBD | Data quality, calculation errors; escalation logic. |
| Dashboard real-time refresh | Missing | Complete | Complete | — | v0.3.0 | TBD | Fund summary, risk metrics, alert status; streaming updates. |
| Alert rule engine | Missing | Complete | — | — | v0.3.0 | TBD | Configurable trigger conditions, notification channels. |

---

## 18. Fund Setup & Configuration

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Fund profile creation | Missing | Complete | — | — | v0.2.0 | TBD | Name, strategy, base currency, domicile, inception date. |
| Risk policy template selection | Missing | Complete | — | — | v0.2.0 | TBD | Equity, fixed income, multi-asset presets. |
| Position load & validation workflow | Complete | Complete | — | Partial | v0.2.0 | TBD | CSV import, schema check, exception handling, enrichment. |
| Reference data provisioning | Missing | Complete | — | — | v0.2.0 | TBD | Counterparties, benchmarks, scenarios, ratings. |
| Scenario & stress configuration | Missing | Complete | — | — | v0.2.0 | TBD | Add/edit market shocks, parameters, thresholds. |
| Fund setup wizard | Missing | — | Complete | — | v0.2.0 | TBD | Streamlined onboarding UX for new funds. |

---

## 19. Multi-Fund Rollup (ManCo Portfolio)

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Consolidated AUM & NAV | Missing | Complete | — | — | v0.4.0 | TBD | Across all funds in ManCo; base currency conversion. |
| Aggregated risk metrics (VaR rollup) | Missing | Complete | — | — | v0.4.0 | TBD | Portfolio-level VaR; correlation adjustments. |
| Consolidated leverage checks | Missing | Complete | — | — | v0.4.0 | TBD | Intra-group limits, regulatory consolidation. |
| Consolidated UCITS compliance | Missing | Complete | — | — | v0.4.0 | TBD | Aggregate VaR, concentration, borrowing. |
| Contagion & correlation stress | Missing | Complete | Complete | — | v0.4.0 | TBD | Multi-fund redemption scenarios, fund-fund linkage. |
| ManCo-level reporting | Missing | Complete | Complete | — | v0.4.0 | TBD | Consolidated risk, regulatory, audit reporting. |
| Fund comparison dashboard | Missing | — | Complete | — | v0.4.0 | TBD | Peer risk metrics, peer benchmarking. |

---

## 20. Applications & Demos

| Capability | Engine | Reporting | Visualization | Notebook/Demo | Milestone | Issue | Notes |
|-----------|--------|-----------|----------------|---------------|-----------|-------|-------|
| Core risk analytics demo | — | — | — | Missing | v0.2.0 | TBD | Walkthrough of VaR, ES, backtesting on hedge fund sample. |
| Liquidity and LMT demo | — | — | — | Missing | v0.3.0 | TBD | Redemption stress, gate/swing scenarios. |
| UCITS monitoring demo | — | — | — | Missing | v0.3.0 | TBD | SRRI, limit checks, stress scenarios, KID output. |
| Reporting & audit demo | — | — | — | Missing | v0.3.0 | TBD | Annex IV generation, board report, lineage. |
| Alternative assets demo (PE, infra, RE) | — | — | — | Missing | v0.4.0 | TBD | PE cash flows, infrastructure DSCR, real estate stress. |
| ESG & sustainability demo | — | — | — | Missing | v0.4.0 | TBD | ESG scoring, carbon metrics, controversy monitoring. |
| Multi-fund rollup demo | — | — | — | Missing | v0.4.0 | TBD | Consolidated reporting, peer comparison. |
| Streamlit review interface | — | Complete | Complete | — | v0.5.0 | TBD | Multi-fund dashboard, filter/drill-down, export, real-time alerts. |
| Example CSV data files | — | — | — | — | v0.2.0 | TBD | Sample positions, market data, fund definitions for all asset classes. |

---

## Presentation Parity Tracking

Track important plot and report families from `fund-risk-workflow`. A beautiful output must not be abandoned merely because it came from a notebook.

| Visual Family | Source Workflow | Required? | Complexity (1–5) | Target Layer | Status | Notes |
|---------------|-----------------|-----------|------------------|--------------|--------|-------|
| VaR & ES distribution (histogram, violin, time series) | Historical VaR | Yes | 2 | notebook/dashboard | Missing | Show return distribution, VaR/ES levels, backtest exceptions. |
| VaR backtesting report & traffic light | Backtesting | Yes | 3 | reporting/dashboard | Missing | Exception timeline, green/yellow/red zones, POF test. |
| Stress scenario P&L waterfall | Stress testing | Yes | 3 | reporting/dashboard | Missing | Contribution by asset class, top losers, scenario parameters. |
| Equity/rates/FX/credit factor decomposition | Stress testing | Yes | 3 | reporting/dashboard | Missing | Breakdown of portfolio shock by risk factor. |
| Liquidity bucket stacked bar chart | Liquidity risk | Yes | 2 | reporting/dashboard | Missing | TTL distribution: T+0, T+1–5, T+5+, illiquid. |
| Redemption stress impact chart | LMT simulation | Yes | 3 | reporting/dashboard | Missing | NAV impact across shock levels; gate/swing triggers. |
| Leverage trend + policy cap line chart | Leverage monitoring | Yes | 2 | reporting/dashboard | Missing | Time series vs. policy cap; limit breaches. |
| Leverage breakdown (by source, asset class) | Leverage monitoring | Yes | 2 | reporting/dashboard | Missing | Pie chart, stacked bar by derivative/borrowing/SFT. |
| NAV evolution, returns, drawdown | Fund summary | Yes | 2 | reporting/dashboard | Missing | Multi-panel: NAV curve, cumulative returns, max drawdown. |
| P&L attribution waterfall | Attribution | Yes | 3 | reporting/dashboard | Missing | Contribution by risk factor (equity/rates/FX/credit). |
| ESG score gauge/scorecard | ESG summary | Yes | 2 | reporting/dashboard | Missing | Fund score gauge, peer/policy comparison. |
| PE cash flow waterfall & cumulative | Alternative assets | Yes | 3 | reporting/dashboard | Missing | Distributions, reinvestments, valuation gains; vintage cohorts. |
| PE IRR & multiples table | Alternative assets | Yes | 2 | reporting/dashboard | Missing | DPI, RVPI, TVPI, PME; vintage and aggregate. |
| Infrastructure DSCR trend | Infrastructure | Yes | 2 | reporting/dashboard | Missing | Debt service coverage ratio; covenant level overlay. |
| Infrastructure LTV evolution | Infrastructure | Yes | 2 | reporting/dashboard | Missing | Leverage ratio over time; stress outcomes. |
| Real estate occupancy & rental stress | Real estate | Yes | 3 | reporting/dashboard | Missing | Occupancy scenario impact, rental income P&L. |
| Annex IV identification & summary tables | Regulatory | Yes | 2 | reporting/PDF export | Missing | Fund info, AUM, strategy, inception, ISIN. |
| Annex IV asset breakdown table | Regulatory | Yes | 2 | reporting/PDF export | Missing | By asset class, geography, sector; percentages. |
| Annex IV risk measures & leverage tables | Regulatory | Yes | 2 | reporting/PDF export | Missing | VaR, ES, leverage detail (gross, commitment, netting). |
| Annex IV liquidity buckets table | Regulatory | Yes | 2 | reporting/PDF export | Missing | Redemption frequency, notice, liquidity profile. |
| Board risk summary tables & charts | Management reporting | Yes | 3 | reporting/PDF export | Missing | Multi-page, consistent branding, KPIs, exceptions. |
| UCITS compliance matrix/dashboard | UCITS monitoring | Yes | 2 | reporting/dashboard | Missing | Checks (absolute VaR, concentration, borrowing), vs. limits. |
| KID-style tables (SRI, scenarios, costs) | PRIIPs | Yes | 2 | reporting/PDF export | Missing | Regulatory template format; SRI scale, performance scenarios. |
| Counterparty register table | Risk management | Yes | 2 | reporting/PDF export | Missing | Counterparty, exposure, collateral, haircut. |
| Data quality exception log | Operations | Yes | 1 | reporting/dashboard | Missing | Position validation, market data gaps, reference data issues. |

---

## Excluded from Migration

These exist in `fund-risk-workflow` but should not be migrated:

- **Exploratory notebooks** without operational value or clear outputs.
- **Notebook-only glue code** and compatibility wrappers.
- **Duplicate helpers** or redundant implementations.
- **Temporary shortcuts** taken during prototyping (e.g., hardcoded parameters).
- **Deprecated methodologies** superseded by the spec.
- **Ad hoc transformations** inside notebook cells that lack documentation.

**Important:** Exclude the notebook implementation, not the output. A beautiful plot created in a notebook belongs in the roadmap; the notebook code may be discarded.

---

## Retirement Checklist

### v0.2.0 — Core Risk Analytics (Calculation Substantially Complete)

**What's Complete in manco-risk (v0.1.0):**
- ✓ Historical VaR (empirical quantile; 95%/99%, 1-day horizon)
- ✓ Historical Expected Shortfall (CVaR; ES ≥ VaR invariant)
- ✓ Parametric VaR (normal distribution; z-score based)
- ✓ Scenario P&L generation (equity)
- ✓ Equity, fixed-income, combined stress engines (deterministic)
- ✓ Reverse stress testing (equity; feasibility checks)
- ✓ VaR backtesting framework (alignment, breach counts, regulatory metrics)
- ✓ Kupiec POF test (unconditional coverage; LR-based)
- ✓ Christoffersen test (independence + conditional; UC+Ind+CC)
- ✓ AIFMD gross and commitment leverage
- ✓ UCITS 20% rule (commitment method)
- ✓ Position loader, validator, enricher
- ✓ CSV market data provider
- ✓ Full ORM persistence with CalculationRun audit trail

**Still Missing (Blocking v0.2.0 release):**
- Parametric ES (normal and Student-t)
- Student-t VaR
- Scenario P&L for fixed-income and derivatives (direct generation)
- Reverse stress testing for fixed-income
- Historical scenario data (2008, 2020, 2011, 2022 shock parameters)
- Sample fund datasets (AIFM, UCITS for testing)
- VaR and backtesting charts and tables (reporting layer)
- Fund summary dashboard (reporting layer)
- Mock Bloomberg provider (for testing)

**Can retire `fund-risk-workflow` for:** Core VaR and stress calculations. Reporting, visualization, and demo workflows still needed.

---

### v0.3.0 — Regulatory Reporting & Monitoring

**What's Complete in manco-risk:**
- ✓ UCITS commitment method (20% rule)
- ✓ Leverage limit monitoring (partial)
- ✓ Position enrichment and validation

**Remaining work for v0.3.0:**
- Implement AIFMD Annex IV reporting tables (fund ID, assets, risk, leverage, liquidity).
- Implement UCITS-specific modules (SRRI, absolute/relative VaR, concentration, borrowing checks).
- Implement liquidity analytics (TTL buckling, stress testing, redemption analysis).
- Implement LMT simulation engine (gates, swing pricing, suspension).
- Implement Annex IV and board report PDF export.
- Implement fund setup workflow (policy templates, scenario configuration).
- Implement monitoring and alerting infrastructure.
- Create demo notebooks: UCITS, Annex IV, liquidity, LMT.
- Create counterparty register and exception reporting tables.

**Can retire `fund-risk-workflow` for:** Leverage, basic UCITS compliance, Annex IV quarterly reporting, board summaries.

---

### v0.4.0 — Alternative Assets & Advanced Reporting

**Remaining work for v0.4.0:**
- Implement PE analytics (IRR, DPI, RVPI, TVPI, PME; cash flow models).
- Implement infrastructure analytics (DSCR, LTV, duration, covenant monitoring).
- Implement real estate stress (occupancy, rental income, LTV).
- Implement private debt loan/covenant monitoring.
- Implement PRIIPs KID outputs (SRRI, performance scenarios, cost tables).
- Implement performance attribution (factor decomposition, P&L bridge).
- Implement ESG analytics (score aggregation, carbon metrics, controversies).
- Implement audit and lineage tracking.
- Implement data quality and exception dashboards.
- Create demo notebooks: alternative assets, attribution, ESG, PRIIPs.

**Can retire `fund-risk-workflow` for:** Alternative asset workflows, ESG reporting, attribution analysis, KID/PRIIPs outputs.

---

### v0.5.0 — Applications & Multi-Fund

**Remaining work for v0.5.0:**
- Build Streamlit review interface (multi-fund, filter, drill-down, export).
- Implement multi-fund consolidation (AUM, risk metrics, leverage rollup).
- Implement contagion and correlation stress (multi-fund scenarios).
- Implement ManCo-level reporting and monitoring.
- Implement fund comparison dashboard.
- Production readiness: logging, monitoring, error handling, CI/CD.
- Deploy and migrate live funds to manco-risk.
- Create demo notebook: multi-fund rollup, portfolio management.

**Can retire `fund-risk-workflow` for:** Complete replacement. All outputs, workflows, and applications available in `manco-risk`.

---

## Summary by Capability Status

**Complete (Ready to use in manco-risk v0.1.0):**
- Historical VaR (empirical quantile)
- Historical Expected Shortfall (CVaR; tail mean)
- Parametric VaR (normal distribution)
- Scenario P&L (equity)
- VaR backtesting framework (alignment, breach detection, regulatory counts)
- Kupiec POF test (unconditional coverage)
- Christoffersen test (independence + conditional coverage)
- Equity stress scenarios (deterministic shocks)
- Fixed-income stress scenarios (duration-based)
- Combined multi-asset stress (equity + FI orchestration)
- Reverse stress testing (equity; find required shock for target loss)
- AIFMD gross and commitment leverage
- UCITS commitment method (20% rule)
- Derivative exposure conversion (delta, gamma, vega)
- Position validation and enrichment
- CSV market data ingestion
- Database persistence with CalculationRun audit trail

**Partial (Foundation in place, key pieces missing):**
- Expected Shortfall (historical only; parametric ES not yet implemented)
- Scenario P&L (equity only; FI via stress engine only, derivatives deferred)
- Leverage monitoring (UCITS method complete; AIFMD monitoring engine planned for v0.3.0)
- Historical stress scenarios (engine complete; market shock data missing)
- Data quality reporting (validation layer complete; market data and reference data checks planned for v0.2.0)

**Not yet implemented in roadmap (Planned for v0.2.0–v0.3.0):**
- Sample datasets (all fund types)
- Mock Bloomberg market data provider for testing
- Annex IV regulatory reporting (49KB regulatory engine from fund-risk-workflow)
- UCITS SRRI and absolute/relative VaR monitoring
- Liquidity analytics (TTL bucketing, calibration, stress testing)
- LMT simulation engine (gates, swing pricing, suspension)
- Board and management reporting
- VaR/leverage/stress/liquidity visualization (30 visual families)
- Demo notebooks (core analytics, UCITS, liquidity, reporting)
- Fund setup workflow and policy template selection
- Monitoring and alerting infrastructure

**Not yet implemented in roadmap (Planned for v0.4.0+):**
- PE analytics (IRR, DPI, RVPI, TVPI, PME, cash flow models)
- Infrastructure analytics (DSCR, LTV, duration, covenant monitoring)
- Real estate stress testing (occupancy, rental income, LTV scenarios)
- Private debt loan and covenant monitoring
- PRIIPs KID outputs (SRRI, performance scenarios, cost tables)
- Performance attribution (factor decomposition)
- ESG analytics (score aggregation, carbon metrics, controversy tracking)
- Audit and lineage tracking
- Streamlit review interface
- Multi-fund consolidation and ManCo reporting

---

## Next Steps

1. Inspect `../fund-risk-workflow` to populate missing issue numbers and refine capability descriptions.
2. Assign ownership (optional, for living-document maintenance).
3. Track updates with "last reviewed" date as milestones complete.
4. Use this roadmap to gate new work and keep scope focused.
5. Review quarterly or when a milestone completes.
