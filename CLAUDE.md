# CLAUDE.md

## Project overview

manco-risk is a modular Python risk analytics repository for AIFM and ManCo workflows.

The project separates market data, ETL, database access, risk calculations, reporting and UI layers. The first implementation focuses on position-based Historical VaR, Expected Shortfall and VaR backtesting, with later modules covering parametric VaR, stress testing, leverage, liquidity analytics, LST, LMT simulation and Annex IV-style reporting.

The full specification is in `meta/project_spec.md` -- read it before starting any module.

---

## Commit rules

- Do not add co-author attribution in commit messages
- Do not add any Claude or AI references in commit messages
- Use only the repository author identity configured in git
- Commit messages should reflect the domain reasoning behind the change, not just the code change
- Do not commit anything. Give bash commands to stage files and provide commit messages when asked.

Good commit message examples:
- `add cashflow coverage ratio calculation for soft bullet structures`
- `fix haircut schedule lookup -- was matching on asset type only, now includes maturity bucket`
- `add rating downgrade scenario to stress engine`

---

## How we work together

### Session start
At the start of every session, state which module you are working on.
Do not jump to another module unless explicitly instructed.
Confirm the current state of the repo before adding new files.

1. Understand the task first
2. Explain proposed changes before implementing anything
3. Wait for approval
4. Implement in small steps
5. After each step explain what changed and why

### Module sequencing

1. Target architecture and repository structure
2. Market data abstraction layer
3. Database schema and access layer
4. Position ingestion and validation
5. Risk-ready enrichment pipeline
6. Historical VaR, Expected Shortfall and backtesting
7. Parametric VaR and Student-t VaR
8. Stress testing and leverage analytics
9. Liquidity risk, LST and LMT analytics
10. Reporting outputs
11. Streamlit UI
12. Example notebooks and documentation

### Linear issue references

<!-- Fill in issue numbers for this project. Example: -->
<!--
PRJ-101 Domain models and data layer
PRJ-102 Module 1 -- ...
-->

MRS-123  Define target architecture and module boundaries

MRS-124  Set up repository structure and development tooling

MRS-125  Implement market data abstraction layer

MRS-126  Implement mock Bloomberg provider

MRS-127  Define market data schemas and contracts

MRS-128  Design database schema

MRS-129  Implement database access layer

MRS-130  Implement repository/query layer

MRS-131  Implement position ingestion framework

MRS-132  Implement data validation framework

MRS-133  Implement risk-ready enrichment pipeline

MRS-134  Implement Historical VaR engine

MRS-135  Implement Parametric VaR engine

MRS-136  Implement Expected Shortfall engine

MRS-137  Implement VaR backtesting framework

MRS-138  Implement stress testing framework

MRS-139  Implement leverage analytics

MRS-140  Implement liquidity risk analytics

MRS-141  Implement liquidity stress testing

MRS-142  Implement reporting framework

MRS-143  Implement Annex IV reporting outputs

MRS-144  Implement management risk reporting

MRS-145  Implement Streamlit application

MRS-146  Implement dashboard visualisations

MRS-147  Implement automated testing framework

MRS-148  Implement data quality controls

MRS-149  Implement CI/CD workflows

MRS-150  Project documentation

MRS-151  Example notebooks and demonstrations

### Before creating new files
If a pattern already exists in the repo (a base class, a loader, a report format),
follow that pattern. Ask before introducing a new pattern.

### When stuck
If a design decision is ambiguous, ask. Do not invent business logic that is not in the spec
or already present in the codebase.

---

## Code standards

- Python 3.13
- Type hints throughout -- no untyped functions
- Pydantic or dataclasses for all domain objects
- Pydantic v2 syntax throughout -- use `model_config = ConfigDict(...)` not `class Config`
- pathlib for all file paths -- no string path concatenation
- pytest for all tests -- use fixtures
- logging for all runtime messages -- no print statements in production code
- No `from __future__ import annotations`
- No hardcoded datasets -- everything loads from CSV files in data/
- No business logic inside dashboard code
- Custom exceptions for domain errors (see spec for the full list)
- Run `uv ruff check src tests` before marking any task done -- all checks must pass

---

## Data conventions

- Rates, ratios, haircuts: store as `Decimal` (e.g., 0.05 = 5%, 1.5 = 150%)
- Exception: Bloomberg-style market data may follow Bloomberg conventions, such as bond prices quoted as percentages. These conventions should be preserved at ingestion and converted only in clearly documented transformation steps.
- Basis points: store as `int` (e.g., 50 = 50 bps = `0.5%`)
- Never store raw percentages -- convert to decimal or bps at ingestion
- Field naming must make the unit explicit:
  - `haircut_rate: Decimal` (0-1 range, e.g., 0.15)
  - `spread_bps: int` (basis points, e.g., 150)
  - `coverage_ratio: Decimal` (decimal, e.g., 1.25)
  
  ## Numerical data documentation

Document data conventions in three places:

- `meta/conventions.md` -- authoritative reference
- domain models -- field-level units and ranges
- calculation modules -- assumptions and formula documentation

All financial calculations must explicitly state:

- units
- scaling conventions
- sign conventions
- input assumptions

Examples:

- returns stored as decimal (`0.05 = 5%`)
- yields stored as decimal (`0.035 = 3.5%`)
- haircuts stored as decimal (`0.15 = 15%`)
- leverage stored as ratio (`2.5 = 250%`)
- basis points stored as integer (`50 = 50bps`)
- bond prices follow Bloomberg conventions unless transformed
  
 ---

## Architecture rules

- Abstract base classes for all engines and loaders
- Concrete implementations via dependency injection
- Calculations must be independent from visualisation
- Business logic operates on domain entities, not raw DataFrames where practical
- Prefer composition over deep inheritance hierarchies

---

## Sample data rules

- All sample data must be realistic -- no placeholder names like "Entity A"
- Data must cover at least six months of snapshots
- Multiple entities, asset classes, and ratings where relevant
- Distributions should be realistic enough to trigger edge cases


### Scope control

Do not expand scope beyond the current Linear issue.

If a proposed change requires:
- a new data source
- a new architectural component
- a new dependency
- a methodology change

stop and ask before implementing.

Prefer the smallest change that satisfies the current issue.

### Refactoring rules

Do not perform repository-wide refactors unless explicitly requested.

When refactoring:
- preserve behaviour
- add tests first where practical
- explain the migration path before changing interfaces

### Dependency rules

Before adding a dependency:

1. Explain why the standard library is insufficient.
2. Explain alternative packages considered.
3. Wait for approval.

Prefer:
- stdlib
- pandas
- numpy
- scipy
- pydantic

Avoid introducing dependencies for small utilities.

## Prototype Reference Repository

A separate prototype repository exists:

`../manco-risk-mngmt`

This repository may be consulted for:

- domain knowledge
- regulatory references
- methodology research
- example calculations
- sample datasets
- workflow understanding

It must not be treated as an architectural reference.

Do not reproduce:

- notebook-centric implementations
- mixed responsibilities
- calculation logic embedded in notebooks
- direct data manipulation inside reporting code
- architectural shortcuts taken during prototyping

When using the prototype repository:

1. Explain what information is being referenced.
2. Explain what will be reused conceptually.
3. Explain what will be redesigned.
4. Implement according to the architecture defined in this repository.
5. Wait for approval before copying or rewriting substantial functionality.


### Migration Rule

The goal of this repository is not to port the prototype.

The goal is to reimplement selected functionality using the architecture defined in:

- CLAUDE.md
- meta/project_spec.md
- meta/conventions.md

A clean reimplementation is preferred over a direct migration.
