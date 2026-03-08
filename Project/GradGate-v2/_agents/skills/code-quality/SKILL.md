---
name: code-quality
description: Run linting, formatting, type-checking, and tests on a Python project. Also compacts/cleans code by auto-fixing style issues and removing dead imports.
---

# Code Quality & Compaction Skill

This skill runs a full code quality pass on a Python project using **ruff**, **black**, **mypy**, and **pytest**. It also performs code compaction by auto-fixing lint violations and formatting.

## Prerequisites

The following tools must be installed before running this skill:

```bash
pip install ruff black mypy pytest pytest-cov
```

Or, if the project has a `requirements-dev.txt`:

```bash
pip install -r requirements-dev.txt
```

## Steps

### 1. Auto-fix lint issues (compaction)

Ruff auto-fixes safe issues: unused imports, unsorted imports, deprecated syntax, etc.

```bash
ruff check . --fix
```

> Fixes applied in-place. Review with `git diff` afterwards.

### 2. Auto-format code (style normalization)

Black enforces consistent formatting — line length, quotes, spacing:

```bash
black .
```

> All files reformatted to 100-char line length (as configured in `pyproject.toml`).

### 3. Lint check (verify no remaining issues)

After auto-fixes, verify nothing is left:

```bash
ruff check .
```

Expected output: no errors. If issues remain, they require manual review.

### 4. Type check

Run mypy on the core engine and API packages:

```bash
mypy engine/ display/
```

After Phase 2+:

```bash
mypy engine/ display/ api/
```

Expected: 0 errors. Warnings about missing stubs for third-party packages are OK to ignore.

### 5. Run tests

```bash
pytest tests/ -x --ignore=tests/load -q
```

- `-x`: stop at first failure
- `--ignore=tests/load`: skip load tests (those need a running server)
- `-q`: quiet output

For coverage:

```bash
pytest tests/ -x --ignore=tests/load --cov=engine --cov=display --cov-report=term-missing -q
```

### 6. Full quality pass (all steps in one shot)

```bash
ruff check . --fix && black . && ruff check . && mypy engine/ display/ && pytest tests/ -x --ignore=tests/load -q
```

Or via Makefile (if available):

```bash
make lint-fix   # ruff --fix
make format     # black
make lint       # ruff check (verify)
make typecheck  # mypy
make test       # pytest
```

## What Gets Fixed Automatically

| Issue | Tool | Action |
|---|---|---|
| Unused imports | ruff | Auto-removed |
| Unsorted imports | ruff | Auto-sorted |
| Deprecated syntax (e.g. `Union[X,Y]` → `X \| Y`) | ruff | Auto-upgraded |
| Inconsistent quotes, spacing, line breaks | black | Auto-formatted |
| Lines too long (> 100 chars) | black | Auto-wrapped |

## What Requires Manual Attention

| Issue | Tool | Action needed |
|---|---|---|
| Type errors | mypy | Fix in code |
| Logic bugs | pytest | Fix in code |
| Remaining lint errors after `--fix` | ruff | Review and fix manually |

## When to Run This Skill

- **Before committing** any new code
- **After merging** a large diff
- **When onboarding** to a messy codebase
- **Before a demo / submission** to ensure clean output

## Notes for GradGate

- Config lives in `pyproject.toml` at the repo root
- Target Python version: 3.11+
- Mypy scope: `engine/` and `display/` (add `api/` after Phase 2)
- Tests live in `tests/` — load tests in `tests/load/` are excluded from the default run
