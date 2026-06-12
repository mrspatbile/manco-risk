# Runbook

Operational commands for working on `manco-risk`.

## Quick start

```bash
git clone <repo-url>
cd manco-risk
uv sync
uv run pytest
```

All tests should pass before starting a new task.

## Daily development workflow

Run the standard local checks:

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest
```

Run a specific test file:

```bash
uv run pytest tests/risk/test_leverage_limit_monitoring.py
```

Run a specific test method:

```bash
uv run pytest tests/risk/test_leverage_limit_monitoring.py::TestLeverageLimitMonitoring::test_valid_limit
```

## Code quality

Check linting:

```bash
uv run ruff check src tests
```

Auto-fix linting issues:

```bash
uv run ruff check --fix src tests
```

Check formatting:

```bash
uv run ruff format --check src tests
```

Apply formatting:

```bash
uv run ruff format src tests
```

Run type checks:

```bash
uv run mypy src
```

Run tests:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest tests --cov=src --cov-report=term-missing
```

## Before committing

Run the full local check:

```bash
uv run ruff check --fix src tests
uv run ruff format src tests
uv run mypy src
uv run pytest
```

Then review the changes before committing:

```bash
git status
git diff --staged
```

## Dependency management

Install or update the project environment:

```bash
uv sync
```

Add a runtime dependency:

```bash
uv add <package>
```

Add a development dependency:

```bash
uv add --dev <package>
```

Add an optional dependency group:

```bash
uv add --optional <group-name> <package>
```

Do not manually edit `uv.lock`.

## Pre-commit

Install hooks once:

```bash
uv run pre-commit install
```

Run all hooks manually:

```bash
uv run pre-commit run --all-files
```

The pre-commit hook runs automatically before a commit is created.

## Git workflow

Check status:

```bash
git status
```

Review recent commits:

```bash
git log --oneline -5
```

Stage files:

```bash
git add <files>
```

Commit with a clear domain-focused message:

```bash
git commit -m "add leverage limit monitoring framework"
```

Push to the current branch:

```bash
git push
```

Do not force-push unless explicitly required.

## Common Ruff errors

| Error  | Meaning                      | Typical fix                             |
| ------ | ---------------------------- | --------------------------------------- |
| `F401` | unused import                | remove the import                       |
| `F841` | assigned but unused variable | remove or use the variable              |
| `I001` | import order issue           | run `uv run ruff check --fix src tests` |
| `E501` | line too long                | shorten or split the line               |

## Project references

Read these before changing architecture or methodology:

* `CLAUDE.md` — working rules, scope control, commit rules
* `ARCHITECTURE.md` — module boundaries and forbidden patterns
* `meta/project_spec.md` — domain scope and implementation objective
* `meta/conventions.md` — units, signs, dates, naming conventions
* `meta/reg_reference.md` — regulatory and methodology reference material

## Environment

No environment variables are required for local development.

Main local files:

| File/folder      | Purpose                                            |
| ---------------- | -------------------------------------------------- |
| `pyproject.toml` | project metadata, dependencies, tool settings      |
| `uv.lock`        | resolved dependency versions                       |
| `.venv/`         | local virtual environment                          |
| `src/`           | package source code                                |
| `tests/`         | automated tests                                    |
| `meta/`          | methodology, regulatory, and roadmap documentation |

## Notes

* Use `uv` for dependency management.
* Keep business logic in `src/`.
* Keep notebooks and UI thin.
* Run focused tests while developing, then run the full check before committing.
* Keep documentation-only changes separate from implementation changes when practical.
