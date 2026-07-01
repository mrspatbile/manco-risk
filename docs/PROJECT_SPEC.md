# Project Specification

## Project Name

manco-risk

## Objective

Build a modular Python risk analytics repository for AIFM / ManCo workflows, focused on fund risk management, market data ingestion, position validation, risk calculations and reporting outputs.

The repository is intended to become the long-term implementation of the functionality currently demonstrated in fund-risk-workflow, using a cleaner modular architecture, stronger separation of concerns and tested business components.

## Core Architecture

Data flow:

Fund administrator files  
→ ETL and validation  
→ SQLite database  
→ Risk calculation modules  
→ Reporting layer  
→ Notebooks / UI for review only

## Modules

### market_data

Bloomberg-compatible market data interface.

Responsibilities:
- mock Bloomberg client
- price and risk factor retrieval
- yield curve and benchmark data access
- market data schemas

### etl

Data ingestion and validation.

Responsibilities:
- load fund administrator files
- validate positions
- normalise identifiers
- enforce required fields
- create risk-ready datasets

### database

Persistence layer.

Responsibilities:
- SQLite connection
- database models
- data access functions
- schema creation
- data access boundaries

### risk

Risk calculation layer.

Responsibilities:
- fixed-position Historical VaR
- parametric VaR
- Expected Shortfall
- VaR backtesting
- stress testing
- leverage calculations
- liquidity risk analytics
- LMT simulation
- private asset analytics (private equity, infrastructure, real estate, private debt)

### reporting

Reporting layer.

Responsibilities:
- Annex IV-style outputs
- board risk reporting
- summary tables
- export-ready outputs

### ui

Review and demonstration layer.

Responsibilities:
- Streamlit pages
- charts
- dashboard views

No calculation logic should live in the UI.

### notebooks

Demonstration and review only.

Responsibilities:
- explain context
- call package functions
- display outputs
- support interpretation

No business logic should live in notebooks.

## Design Rules

- Keep business logic inside `src/`.
- Keep notebooks thin.
- Keep Streamlit pages thin.
- Each risk calculation must have tests.
- Each database query should be isolated in the database layer.
- Market data access must go through the market data layer.
- ETL should validate data before risk calculation modules consume it.
- Prefer typed inputs and explicit schemas.
- Avoid hidden assumptions inside notebooks.

## Initial Scope

Phase 1:
- project structure
- database layer
- market data access layer
- position ingestion
- fixed-position Historical VaR
- Expected Shortfall
- 1-day VaR backtesting

Phase 2:
- parametric VaR
- Student-t VaR
- stress testing
- leverage
- liquidity profiling

Phase 3:
- LST
- LMT simulation
- Annex IV-style reporting
- board reporting
- Streamlit dashboard

## Out of Scope for Initial Build

- full regulatory reporting engine
- production Bloomberg integration
- full credit spread curve infrastructure
- complete Annex IV XML submission
- vendor-style reporting platform
- production-grade ManCo system

## Non-Functional Requirements

- All calculations must be reproducible.
- All methodologies must be documented.
- All risk calculation modules must be independently testable.
- Market data, ETL, risk and reporting layers must remain decoupled.
- Notebook outputs should be reproducible from package functions alone.

## Current Data Sources

Phase 1:

- Fund administrator exports
- SQLite database
- Mock Bloomberg provider

Production integrations are out of scope.

## Key Methodological Decision

Market risk VaR should be position-based, not based on historical NAV returns.

For a VaR date, the portfolio is fixed at that date and historical market moves are applied to generate a hypothetical P&L distribution.

NAV-return VaR may be used only as a separate fund-level proxy and must be clearly labelled as such.

## VAR Fixed Income Limitation

Initial bond VaR may use duration-based sensitivity to historical yield movements.

Credit spread risk, issuer-specific events and rating migration effects are not explicitly modelled in the initial implementation.

> This repository is a simplified analytical implementation. It is not intended to replicate
> regulatory frameworks or production systems.

---

