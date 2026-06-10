# Environment Setup

## Overview

This repository uses a modern Python workflow based on:

- `uv` for dependency management and virtual environments
- `pipx` for global developer tools
- `pre-commit` for automated code quality checks
- `ruff` for linting and formatting
- `mypy` for type checking
- `pytest` for testing

The goal is to keep project dependencies isolated while installing developer tools only once.

---

## Tooling Layers

Think of the setup in three layers:

```text
pipx
    ↓
Global developer tools

uv
    ↓
Project dependency manager

.venv
    ↓
Project environment
```

---

## pipx

`pipx` installs developer tools globally in isolated environments.

Examples:

```bash
pipx install uv
pipx install pre-commit
```

These tools become available from any project.

Check installed tools:

```bash
pipx list
```

---

## uv

`uv` manages:

- dependencies
- lock files
- virtual environments

Create or update the environment:

```bash
uv sync
```

Add runtime dependencies:

```bash
uv add pandas
```

Add development dependencies:

```bash
uv add --dev pytest
```

Run commands inside the project environment:

```bash
uv run pytest
uv run mypy src
uv run ruff check src tests
```

---

## .venv

`uv sync` creates `.venv` automatically if needed.

You normally do not need to create virtual environments manually.

You may activate the environment:

```bash
source .venv/bin/activate
```

but the preferred workflow is:

```bash
uv run pytest
uv run python script.py
```

without manual activation.

---

## pyproject.toml

Defines:

- project metadata
- runtime dependencies
- development dependencies
- tool configuration

Think:

```text
What should be installed?
```

---

## uv.lock

Generated automatically by uv.

Records the exact versions installed.

Think:

```text
What was actually installed?
```

Commit `uv.lock` to Git.

---

## pre-commit

Runs checks before commits are created.

Install hooks:

```bash
uv run pre-commit install
```

Run manually:

```bash
uv run pre-commit run --all-files
```

Current hooks:

```text
ruff-check
ruff-format
```

---

## Why Not Use pip Directly?

Traditional workflow:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Repository workflow:

```bash
uv sync
uv run pytest
```

This reduces setup steps and improves reproducibility.

---

## Typical Workflow

Clone repository:

```bash
git clone <repo>
cd <repo>
```

Create environment:

```bash
uv sync
```

Install pre-commit hooks:

```bash
uv run pre-commit install
```

Run tests:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check src tests
```

Run type checking:

```bash
uv run mypy src
```

---

## Rule of Thumb

Global tools:

```text
uv
pre-commit
```

Install once with:

```bash
pipx install ...
```

Project packages:

```text
pandas
numpy
pytest
ruff
mypy
streamlit
```

Manage with:

```bash
uv add ...
uv add --dev ...
```
