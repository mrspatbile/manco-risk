# runbook.md

## Environment

Use `uv` for project dependency management.

Create or update the project environment:

```bash
uv sync
```

`uv sync` reads `pyproject.toml` and `uv.lock`, creates `.venv` if needed, and installs the project dependencies.

Do not install project dependencies with `pip` unless there is a specific reason.

## Dependency management

Add runtime dependencies:

```bash
uv add <package>
```

Example:

```bash
uv add pandas
```

Add development dependencies:

```bash
uv add --dev <package>
```

Examples:

```bash
uv add --dev pytest
uv add --dev ruff
uv add --dev mypy
uv add --dev pre-commit
```

## Code quality

Check linting:

```bash
uv run ruff check src tests
```

Auto-fix what Ruff can fix:

```bash
uv run ruff check --fix src tests
```

Check formatting:

```bash
uv run ruff format --check src tests
```

Fix formatting:

```bash
uv run ruff format src tests
```

Type check:

```bash
uv run mypy src
```

## Tests

Run all tests:

```bash
uv run pytest tests/
```

Run tests with coverage:

```bash
uv run pytest tests/ -v --cov=src --cov-report=term-missing
```

## Pre-commit

Install the Git pre-commit hook once per repository:

```bash
uv run pre-commit install
```

Run all pre-commit hooks manually:

```bash
uv run pre-commit run --all-files
```

The pre-commit hook currently runs:

```text
ruff-check
ruff-format
```

Do not add slow checks such as the full test suite to pre-commit unless there is a clear reason.

## Git workflow

Check current state:

```bash
git status
```

Stage changes:

```bash
git add <file>
```

Commit changes:

```bash
git commit -m "clear commit message"
```

Pre-commit runs automatically before the commit is created.

## Common Ruff errors

- `F401` unused import: remove the import
- `F841` assigned but unused variable: remove the variable
- `I001` import order: run `uv run ruff check --fix src tests`

## Common commands

```bash
uv sync
uv run ruff check src tests
uv run ruff check --fix src tests
uv run ruff format src tests
uv run mypy src
uv run pytest tests/
uv run pre-commit run --all-files
```

## Mock data

Add the command to generate mock data for this project once defined.

Example placeholder:

```bash
uv run python scripts/generate_mock_data.py
```

## Notes

- `pyproject.toml` defines project dependencies and tool settings.
- `uv.lock` records the exact package versions installed by uv.
- `.venv` contains the project environment.
- `uv run` executes commands inside the project environment.
- `uv add` updates dependencies and the lock file.
- `uv sync` recreates or updates the environment from the lock file.