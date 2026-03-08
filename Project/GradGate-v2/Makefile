.PHONY: lint format typecheck test test-cov serve-api install install-dev install-hooks

# ── Setup ────────────────────────────────────────────────────────────────────
install:
	pip install rich

install-dev:
	pip install -r requirements-dev.txt

install-hooks:
	pre-commit install

# ── Quality ──────────────────────────────────────────────────────────────────
lint:
	ruff check .

lint-fix:
	ruff check . --fix

format:
	black .

format-check:
	black --check .

typecheck:
	mypy engine/ display/

# ── Tests ────────────────────────────────────────────────────────────────────
test:
	pytest tests/ -x --ignore=tests/load -q

test-cov:
	pytest tests/ -x --ignore=tests/load \
		--cov=engine --cov=display \
		--cov-report=term-missing -q

# ── Development ──────────────────────────────────────────────────────────────
serve-api:
	uvicorn api.main:app --reload --port 8000

# ── All checks (same as CI) ───────────────────────────────────────────────────
ci: lint format-check typecheck test
