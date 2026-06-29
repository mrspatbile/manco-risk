# CLAUDE.md

## Project overview

manco-risk is a modular Python risk analytics repository for AIFM and ManCo workflows.

The project separates market data, ETL, database access, risk calculations, reporting and UI layers. The first implementation focuses on position-based Historical VaR, Expected Shortfall and VaR backtesting, with later modules covering parametric VaR, stress testing, leverage, liquidity analytics, LST, LMT simulation and Annex IV-style reporting.

The full specification is in `meta/project_spec.md` -- read it before starting any module.

---

## New session checklist

At the start of a new Claude session:

1. Read `CLAUDE.md`.
2. Read `ARCHITECTURE.md`.
3. Read `meta/project_spec.md`.
4. Read `meta/conventions.md`.
5. Check the current repository state:

   ```bash
   git status --short
   git log --oneline -5
````

6. State:

   * current GitHub issue and relevant Feature Parity Roadmap milestone
   * latest relevant commits
   * files likely to be touched
   * proposed first step

Do not implement until the user approves the proposed first step.

---

## Commit rules

* Do not add co-author attribution in commit messages.
* Do not add any Claude or AI references in commit messages.
* Use only the repository author identity configured in git.
* Commit messages should reflect the domain reasoning behind the change, not just the code change.
* Do not commit anything. Give bash commands to stage files and provide commit messages when asked.

Good commit message examples:

* `add cashflow coverage ratio calculation for soft bullet structures`
* `fix haircut schedule lookup -- was matching on asset type only, now includes maturity bucket`
* `add rating downgrade scenario to stress engine`

---

## How we work together

### Session start

At the start of every session, state which module you are working on.

Do not jump to another module unless explicitly instructed.

Confirm the current state of the repo before adding new files.

1. Understand the task first.
2. Explain proposed changes before implementing anything.
3. Wait for approval.
4. Implement in small steps.
5. After each step explain what changed and why.

---

## Planning and Issue Workflow

**Goal:** Feature parity with `fund-risk-workflow`.

**Reference:** The Feature Parity Roadmap (`meta/feature_parity_roadmap.md`) is the master planning document. All work aligns with capabilities and milestones defined there.

### Starting a new task

1. Check the Feature Parity Roadmap to identify the capability gap.
2. Locate or create the corresponding GitHub issue.
3. Review the issue description, labels, and milestone.
4. Read from:
   * `CLAUDE.md`
   * `ARCHITECTURE.md`
   * `meta/project_spec.md`
   * `meta/conventions.md`
   * the GitHub issue description
   * `git log --oneline -5`
   * `git status --short`

5. Only read additional meta documents if relevant:
   * prototype review: `meta/prototype_field_inventory.md`
   * regulatory design: `meta/reg_reference.md`
   * database design: `meta/domain_note.md`
   * market data work: `meta/market_data_design.md`

6. Propose the approach before implementing.

Do not require long prior conversation history. The issue description plus repository files are the source of truth.

---

## Before creating new files

If a pattern already exists in the repo, for example a base class, a loader, a report format or a database helper, follow that pattern.

Ask before introducing a new pattern.

## When stuck

If a design decision is ambiguous, ask.

Do not invent business logic that is not in the spec or already present in the codebase.

---

## Code standards

* Python 3.13
* Type hints throughout -- no untyped functions
* Pydantic or dataclasses for all domain objects
* Pydantic v2 syntax throughout -- use `model_config = ConfigDict(...)` not `class Config`
* pathlib for all file paths -- no string path concatenation
* pytest for all tests -- use fixtures
* logging for all runtime messages -- no print statements in production code
* No `from __future__ import annotations`
* No hardcoded datasets -- everything loads from CSV files in data/
* No business logic inside dashboard code
* Custom exceptions for domain errors, see the spec for the full list
* Run `uv run ruff check src tests` before marking any task done
* Run `uv run mypy src` before marking implementation tasks done
* Run `uv run pytest` before marking implementation tasks done

---

## Data conventions

* Rates, ratios, haircuts: store as `Decimal`, for example `0.05 = 5%`, `1.5 = 150%`
* Exception: Bloomberg-style market data may follow Bloomberg conventions, such as bond prices quoted as percentages. These conventions should be preserved at ingestion and converted only in clearly documented transformation steps.
* Basis points: store as `int`, for example `50 = 50 bps = 0.5%`
* Never store raw percentages -- convert to decimal or bps at ingestion
* Field naming must make the unit explicit:

  * `haircut_rate: Decimal` for 0-1 range, for example `0.15`
  * `spread_bps: int` for basis points, for example `150`
  * `coverage_ratio: Decimal`, for example `1.25`

### Numerical data documentation

Document data conventions in three places:

* `meta/conventions.md` -- authoritative reference
* domain models -- field-level units and ranges
* calculation modules -- assumptions and formula documentation

All financial calculations must explicitly state:

* units
* scaling conventions
* sign conventions
* input assumptions

Examples:

* returns stored as decimal, for example `0.05 = 5%`
* yields stored as decimal, for example `0.035 = 3.5%`
* haircuts stored as decimal, for example `0.15 = 15%`
* leverage stored as ratio, for example `2.5 = 250%`
* basis points stored as integer, for example `50 = 50bps`
* bond prices follow Bloomberg conventions unless transformed

---

## Architecture rules

See `ARCHITECTURE.md` for the complete target structure, module responsibilities, dependency rules, and forbidden patterns.

Key principles:

* Abstract base classes for all engines and loaders
* Concrete implementations via dependency injection
* Calculations must be independent from visualisation
* Business logic operates on domain entities, not raw DataFrames where practical
* Prefer composition over deep inheritance hierarchies

---

## Sample data rules

* All sample data must be realistic -- no placeholder names like "Entity A"
* Data must cover at least six months of snapshots
* Multiple entities, asset classes, and ratings where relevant
* Distributions should be realistic enough to trigger edge cases

---

## Scope control

Scope is controlled by the active GitHub issue. Do not expand beyond it.

If a proposed change requires:

* a new data source
* a new architectural component
* a new dependency
* a methodology change
* a significant expansion of capability scope

stop and ask before implementing.

Prefer the smallest change that satisfies the current issue. Check the Feature Parity Roadmap to confirm alignment before proposing scope changes.

---

## Refactoring rules

Do not perform repository-wide refactors unless explicitly requested.

When refactoring:

* preserve behaviour
* add tests first where practical
* explain the migration path before changing interfaces

---

## Dependency rules

Before adding a dependency:

1. Explain why the standard library is insufficient.
2. Explain alternative packages considered.
3. Wait for approval.

Prefer:

* stdlib
* pandas
* numpy
* scipy
* pydantic

Avoid introducing dependencies for small utilities.

### Dependency management

Use `uv` for dependency management.

* Add runtime dependencies with `uv add <package>`.
* Add development dependencies with `uv add --dev <package>`.
* Do not manually edit dependency entries in `pyproject.toml`.
* Do not manually edit `uv.lock`.
* After dependency changes, run `uv lock` only if needed to resync the lockfile.

---

## Prototype Reference Repository

A separate prototype repository exists:

`../manco-risk-mngmt`

This repository may be consulted for:

* domain knowledge
* regulatory references
* methodology research
* example calculations
* sample datasets
* workflow understanding

It must not be treated as an architectural reference.

Before using the prototype repository, read and follow:

* `meta/prototype_field_inventory.md`

The prototype field inventory is mandatory when reviewing fields, schemas, reports, calculations or sample datasets from the prototype.

Do not infer regulatory requirements from the prototype.

Do not assume a field is regulatory simply because it exists in the prototype.

Every prototype field or concept considered for reuse must be classified as one of:

* source data
* reference data
* fund methodology setting
* internal risk limit
* calculation input
* derived output
* reporting field
* filing snapshot
* audit / lineage field
* out of scope
* unclear

Do not reproduce:

* notebook-centric implementations
* mixed responsibilities
* calculation logic embedded in notebooks
* direct data manipulation inside reporting code
* architectural shortcuts taken during prototyping
* derived values stored as source data
* reporting fields mixed with calculation inputs
* regulatory concepts mixed with methodology choices
* ad hoc counterparty, leverage, collateral or hedging fields without classification

When using the prototype repository:

1. Explain what information is being referenced.
2. Classify the relevant prototype fields or concepts using `meta/prototype_field_inventory.md`.
3. Explain what will be reused conceptually.
4. Explain what will be redesigned.
5. Implement according to the architecture defined in this repository.
6. Wait for approval before copying or rewriting substantial functionality.

### Prototype inspection scope

When inspecting `../manco-risk-mngmt`, start with a lightweight structure map.

For the first pass, do not read `.ipynb` notebooks unless explicitly instructed.

First inspect:

* Python source files
* CSV / Excel sample input files
* configuration files
* markdown documentation
* schema-like files
* lightweight reporting templates or generated output samples

Skip in the first pass:

* `.ipynb` files
* notebook checkpoint folders
* cached files
* generated charts
* large output files
* virtual environments
* `__pycache__`
* `.pytest_cache`
* `.mypy_cache`
* old build artifacts

The goal of the first pass is to identify candidate files for controlled field inventory, not to understand every prototype experiment.

---

## Migration rule

The goal of this repository is not to port the prototype.

The goal is to reimplement selected functionality using the architecture defined in:

* `ARCHITECTURE.md`
* `CLAUDE.md`
* `meta/project_spec.md`
* `meta/conventions.md`
* `meta/reg_reference.md`
* `meta/prototype_field_inventory.md`

A clean reimplementation is preferred over a direct migration.


