# claude-templates

Template for new Python projects. Lives at `coding/claude-templates/` alongside project repositories.

## What is in here

- `setup.py` -- run once from inside a new cloned repository to initialise everything
- `CLAUDE.md` -- permanent working rules for Claude Code, with placeholders for project-specific sections
- `pyproject.toml` -- Python 3.13, uv, ruff, mypy, pytest, src-layout, ready to use
- `.pre-commit-config.yaml` -- pre-commit hooks for ruff linting and formatting
- `.github/workflows/tests.yml` -- CI pipeline: ruff lint, ruff format, mypy, pytest
- `.gitignore` -- covers Python artifacts, virtual environments, coverage, OS and IDE files
- `README-template.md` -- becomes the new repository's README.md after setup runs
- `runbook.md` -- day-to-day development commands
- `meta/environment_setup.md` -- explanation of uv, pipx, pre-commit and repository tooling conventions
- `docs/PROJECT_SPEC.md` -- blank specification file with only the disclaimer
- `meta/prompt.txt` -- the first message sent to Claude Code at session start

## How to start a new project

Create and clone the repository:

```bash
cd ~/Documents/coding

gh repo create my-project --public --clone

cd my-project
```

Initialise from the template:

```bash
python ../claude-templates/setup.py
```

The script will:

- copy all template files into the current directory
- rename `README-template.md` to `README.md`
- copy this file to `meta/human_setup.md`
- create `src/package_name/__init__.py` (hyphens become underscores)
- create `tests/test_smoke.py`
- create or update the project environment using `uv sync`
- install the pre-commit hook

## Before the first Claude Code session

Fill these in manually after running `setup.py`:

1. `docs/PROJECT_SPEC.md` -- complete project specification before Claude touches any module
2. `CLAUDE.md` -- project overview, module list, issue references
3. `README.md` -- project description and usage instructions
4. Add project dependencies using:

```bash
uv add <package>
uv add --dev <package>
```

5. Update badge URLs once the repository exists on GitHub

## Environment and tooling

See:

- `runbook.md` for day-to-day commands
- `meta/environment_setup.md` for tooling architecture and rationale

These documents explain:

- uv
- uv.lock
- .venv
- pipx
- pre-commit
- GitHub Actions

## What setup.py does not do

- does not define project-specific dependencies
- does not create the GitHub repository
- does not make git commits
- does not push anything
- does not write project specifications
- does not implement any business logic

## Typical workflow

After initial setup:

```bash
uv sync

uv run ruff check src tests
uv run mypy src
uv run pytest tests
```

Commit changes:

```bash
git add .
git commit -m "meaningful commit message"
git push
```

Create a release:

```bash
git tag v0.1.0
git push origin v0.1.0

gh release create v0.1.0
```


## Updating project instructions

Whenever any of the following files change:

- `CLAUDE.md`
- `docs/PROJECT_SPEC.md`
- `docs/CONVENTIONS.md`

start the next AI session by asking the AI to re-read them.

Recommended prompt:

```text
Please re-read the following documents in full before continuing:

- CLAUDE.md
- docs/PROJECT_SPEC.md
- docs/CONVENTIONS.md

Summarise any changes that affect implementation decisions.

State the current module being worked on.

Confirm your proposed approach before making further changes.
```

This ensures that implementation decisions remain aligned with the latest project rules, conventions, and specifications.