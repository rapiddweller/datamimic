.PHONY: help install test test-unit test-integration test-functional coverage typecheck lint format check architecture-check clean

PACKAGE := datamimic_ce
TESTS := tests_ce

help:
	@echo "Available targets:"
	@echo "  install           Install project dependencies via uv"
	@echo "  test              Run the full test suite"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-functional   Run functional tests only"
	@echo "  coverage          Run tests with coverage report for $(PACKAGE)"
	@echo "  typecheck         Run mypy against $(PACKAGE)"
	@echo "  lint              Run ruff against $(PACKAGE)"
	@echo "  format            Auto-format code with ruff"
	@echo "  check             Run lint, typecheck, and tests"
	@echo "  architecture-check Validate the architecture contract with ArchKeel 0.6.1"
	@echo "  clean             Remove caches and build artifacts"

install:
	uv sync

test:
	pytest -q

test-unit:
	pytest -q $(TESTS)/unit_tests

test-integration:
	pytest -q $(TESTS)/integration_tests

test-functional:
	pytest -q $(TESTS)/functional_tests

coverage:
	coverage run -m pytest $(TESTS)
	coverage report --include="$(PACKAGE)/*"
	coverage html --include="$(PACKAGE)/*"

typecheck:
	mypy $(PACKAGE)

lint:
	ruff check $(PACKAGE)

format:
	ruff format $(PACKAGE)
	ruff check --fix $(PACKAGE)

check: lint typecheck test

architecture-check:
	uvx --python 3.11 --from archkeel==0.6.1 archkeel validate --baseline known-violations.json --json | python3 -c 'import json, sys; raw = sys.stdin.read(); print(raw, end=""); report = json.loads(raw); measurements = report.get("measurements") or {}; scalars = measurements.get("scalars") or {}; coverage = report.get("coverage") or {}; valid = report.get("exit_code") == 0 and report.get("declared_rules") == "PASS" and report.get("observation_complete") == "PASS" and coverage.get("status") == "PASS" and scalars.get("violations") == 0 and scalars.get("unknown_positions") == 0 and report.get("baseline_new") == 0 and report.get("baseline_resolved") == 0; sys.exit(0 if valid else 1)'

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
