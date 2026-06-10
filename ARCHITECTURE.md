# Architecture

## Target Package Structure

```
src/manco_risk/
├── common/              Shared types, exceptions, utilities
├── market_data/         Market data abstraction and providers
├── etl/                 Data ingestion and validation
├── database/            SQLite persistence and query layer
├── risk/                Risk calculation engines
├── reporting/           Report generation and output formatting
└── ui/                  Streamlit application (presentation layer only)
```

## Module Responsibilities

### `common/`
**Responsibilities:**
- Custom exceptions for domain errors
- Shared type definitions and enums
- Constants and configuration schemas
- Utility functions with no domain logic

**Must not contain:**
- Market data fetching
- Database queries
- Risk calculations
- Validation logic specific to positions or market data

**Example:** `exceptions.py` defines `InvalidPositionError`, `InsufficientMarketDataError`

---

### `market_data/`
**Responsibilities:**
- Abstract Bloomberg-style market data interface
- Mock Bloomberg provider implementation
- Price, yield curve, and benchmark retrieval
- Market data schemas and validation

**Imports from:**
- `common/`

**Must not contain:**
- Database queries or schema design
- Position validation logic
- Risk calculations
- ETL or data transformation beyond market data normalization

---

### `etl/`
**Responsibilities:**
- Load fund administrator files
- Validate position data
- Normalize identifiers (ISIN, LEI, etc.)
- Enforce required fields
- Create risk-ready position datasets

**Imports from:**
- `common/`, `market_data/`, `database/`

**Must not contain:**
- Risk calculations
- Report formatting
- Hardcoded datasets (all data from CSV files in `data/`)

---

### `database/`
**Responsibilities:**
- SQLite connection management
- Database schema definition
- Repository/query functions
- Data access boundaries

**Imports from:**
- `common/`

**Must not contain:**
- Business logic or validation (those belong in `etl/` or `risk/`)
- Report generation
- Risk calculations

**Example:** `repositories.py` defines `PositionRepository.find_by_date(date)` — not `calculate_var_for_date(date)`

---

### `risk/`
**Responsibilities:**
- Historical VaR calculations
- Parametric VaR and Student-t VaR
- Expected Shortfall
- Backtesting frameworks
- Stress testing
- Leverage and liquidity analytics
- LMT simulation

**Imports from:**
- `common/`, `market_data/`, `etl/`, `database/`

**Must not contain:**
- UI or visualization code
- Report formatting
- Database schema decisions
- Raw file I/O (use `database/` and `etl/`)

**Boundary:** Risk engines operate on position and market data objects; they return typed calculation results. They do not know about reports or UI.

---

### `reporting/`
**Responsibilities:**
- Format risk calculations into reports
- Generate Annex IV-style outputs
- Create board risk reporting tables
- Prepare export-ready formats
- Aggregate results for presentation

**Imports from:**
- `common/`, `risk/`, `database/`

**Must not contain:**
- Risk calculations (use `risk/`)
- Database queries directly (use `database/`)
- UI-specific code (Streamlit, charts)
- Persistent transformations that belong in `etl/`

**Example:** Reporting takes a `HistoricalVaRResult` object and formats it as a table; it does not calculate VaR.

---

### `ui/`
**Responsibilities:**
- Streamlit pages and dashboards
- Display results from `reporting/`
- Call reporting and application service functions
- User interaction and navigation

**Imports from:**
- `common/`, `reporting/`

**Must not contain:**
- Risk calculations
- Data transformations or business logic
- Database queries (go through `reporting/` or `database/`)
- Raw data manipulation

**Boundary:** UI calls `reporting.generate_report()` and displays the result. It does not call `risk.calculate_var()` directly.

---

## Dependency Graph

```
common/                  (no dependencies)
  ↑
  ├─ market_data/
  ├─ etl/              ← market_data/, database/
  └─ database/

  ↑
  ├─ risk/             ← market_data/, etl/, database/
  
  ↑
  ├─ reporting/        ← risk/, database/
  
  ↑
  └─ ui/               ← reporting/
```

**Rule:** Modules may only import from modules listed above them or on the same level. No reverse dependencies.

---

## Forbidden Patterns

The following patterns are explicitly forbidden:

1. **Business logic in UI or notebooks**
   - ❌ `ui/pages/dashboard.py` performs calculations
   - ✅ `risk/engines/var.py` performs calculations; `ui/` calls `reporting.get_var_summary()`

2. **Calculations split across modules**
   - ❌ `etl/` computes interim volatility; `risk/` computes VaR from that
   - ✅ `etl/` validates and enriches positions; `risk/` uses enriched positions to calculate VaR

3. **Direct UI calls to risk engines**
   - ❌ `ui/pages/dashboard.py` imports `from manco_risk.risk import HistoricalVaR`
   - ✅ `ui/pages/dashboard.py` imports `from manco_risk.reporting import get_portfolio_summary`

4. **Database schema decisions in risk engines**
   - ❌ `risk/engines/var.py` calls `database.insert_result()`
   - ✅ `reporting/var_report.py` formats results; persistent storage handled by tests/workflows

5. **Market data integration in database layer**
   - ❌ `database/schema.py` defines Bloomberg price storage
   - ✅ `market_data/` provides prices; `etl/` enriches positions with them; `database/` stores enriched positions

6. **Hardcoded datasets**
   - ❌ `market_data/mock.py` returns hard-coded price dictionaries
   - ✅ `market_data/mock.py` loads prices from CSV files in `data/`

7. **Raw DataFrames as module boundaries**
   - ❌ `risk/` accepts `pd.DataFrame` and returns `pd.DataFrame`
   - ✅ `risk/` accepts typed position objects; returns typed `HistoricalVaRResult`

---

## Extension Points

These modules have defined extension points for future implementations:

- **`market_data/`** — Implement new providers (e.g., production Bloomberg) by subclassing the abstract market data interface.
- **`risk/`** — Add new risk engines (parametric VaR, stress testing) as new subclasses following the established interface.
- **`reporting/`** — Add new report types without modifying `risk/` or `ui/`.
- **`services/`** — (Future) Application services that orchestrate multi-module workflows. Create only when needed.

---

## Data Flow

```
Fund files
    ↓
[etl] — validates, normalizes, enriches (calls market_data)
    ↓
[database] — stores enriched positions
    ↓
[risk] — reads positions and market data, calculates risk metrics
    ↓
[reporting] — formats results into human-readable reports
    ↓
[ui] — displays reports and enables interaction
```

Each step is independent and testable in isolation.
