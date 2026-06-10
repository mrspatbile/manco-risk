# Project initialisation script -- run once from the repo root after cloning.
# python ../claude-templates/setup.py

import shutil
import subprocess
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent
PROJECT_DIR = Path.cwd()
PROJECT_NAME = PROJECT_DIR.name
PACKAGE_NAME = PROJECT_NAME.replace("-", "_")

SKIP_AT_ROOT = {"setup.py", "README.md", "README-template.md"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}


def substitute(text: str) -> str:
    return text.replace("{{project_name}}", PROJECT_NAME).replace("{{package_name}}", PACKAGE_NAME)


def copy_template_files() -> None:
    for src in TEMPLATES_DIR.rglob("*"):
        if src.is_dir():
            continue
        if src.name in SKIP_FILES:
            continue
        if src.name in SKIP_AT_ROOT:
            continue

        relative = src.relative_to(TEMPLATES_DIR)
        dest = PROJECT_DIR / relative
        dest.parent.mkdir(parents=True, exist_ok=True)

        content = src.read_text(encoding="utf-8")
        dest.write_text(substitute(content), encoding="utf-8")

        print(f"  copied {relative}")


def copy_readme() -> None:
    src = TEMPLATES_DIR / "README-template.md"
    dest = PROJECT_DIR / "README.md"

    content = src.read_text(encoding="utf-8")
    dest.write_text(substitute(content), encoding="utf-8")

    print("  copied README-template.md -> README.md")


def copy_human_setup() -> None:
    src = TEMPLATES_DIR / "README.md"
    dest = PROJECT_DIR / "meta" / "human_setup.md"
    dest.parent.mkdir(parents=True, exist_ok=True)

    content = src.read_text(encoding="utf-8")
    dest.write_text(substitute(content), encoding="utf-8")

    print("  copied README.md -> meta/human_setup.md")


def copy_self() -> None:
    dest = PROJECT_DIR / "meta" / "setup.py"
    shutil.copy2(Path(__file__), dest)

    print("  copied setup.py -> meta/setup.py")


def create_package() -> None:
    package_dir = PROJECT_DIR / "src" / PACKAGE_NAME
    package_dir.mkdir(parents=True, exist_ok=True)

    init_file = package_dir / "__init__.py"
    init_file.write_text("", encoding="utf-8")

    print(f"  created src/{PACKAGE_NAME}/__init__.py")


def initialise_uv() -> None:
    subprocess.run(["uv", "sync"], check=True)
    print("  synced environment with uv")


def install_pre_commit_hook() -> None:
    subprocess.run(["uv", "run", "pre-commit", "install"], check=True)
    print("  installed pre-commit hook")


def main() -> None:
    print(f"\nInitialising project: {PROJECT_NAME}")
    print(f"Package name:         {PACKAGE_NAME}\n")

    print("Copying template files...")
    copy_template_files()
    copy_readme()
    copy_human_setup()
    copy_self()

    print("\nCreating package structure...")
    create_package()

    print("\nSyncing environment with uv...")
    initialise_uv()

    print("\nInstalling pre-commit hook...")
    install_pre_commit_hook()

    print("\nDone.")
    print("\nNext steps:")
    print("  1. Fill in meta/project_spec.md")
    print("  2. Fill in CLAUDE.md -- project overview, module list, Linear issue numbers")
    print("  3. Add project dependencies with: uv add <package>")
    print("  4. Add dev dependencies with: uv add --dev <package>")
    print("  5. Run: uv run pytest")
    print("  6. Run: uv run ruff check src tests")
    print("  7. Run: uv run mypy src")
    print("  8. Update README.md badge URLs once the repo is on GitHub")
    print("  9. Open Claude Code and send the contents of meta/prompt.txt\n")


if __name__ == "__main__":
    main()
