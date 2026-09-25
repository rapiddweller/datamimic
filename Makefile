.PHONY: help install test test-unit test-integration test-functional coverage coverage-unit typecheck lint format check architecture-check architecture-cycle-check clean

PACKAGE := datamimic_ce
TESTS := tests_ce
CE_COVERAGE_FILES := $(shell find $(PACKAGE) -type f -name '*.py')

help:
	@echo "Available targets:"
	@echo "  install           Install project dependencies via uv"
	@echo "  test              Run the full test suite"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-functional   Run functional tests only"
	@echo "  coverage          Run tests with coverage report for $(PACKAGE)"
	@echo "  coverage-unit     Run unit tests with complete CE coverage and regression floor"
	@echo "  typecheck         Run mypy against $(PACKAGE)"
	@echo "  lint              Run ruff against $(PACKAGE)"
	@echo "  format            Auto-format code with ruff"
	@echo "  check             Run lint, typecheck, and tests"
	@echo "  architecture-check Validate the physical, dependency, and ArchKeel architecture gates"
	@echo "  architecture-cycle-check Check module imports with pinned Pylint"
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

coverage-unit:
	coverage run --source=$(PACKAGE) -m pytest $(TESTS)/unit_tests -n 0
	@coverage report --format=total --omit='$(PACKAGE)/domains/shared/examples/*.py,$(PACKAGE)/resources/demos/**/*.py,$(PACKAGE)/interfaces/demo.py' --fail-under=65.74 $(CE_COVERAGE_FILES)
	@coverage xml --omit='$(PACKAGE)/domains/shared/examples/*.py,$(PACKAGE)/resources/demos/**/*.py,$(PACKAGE)/interfaces/demo.py' $(CE_COVERAGE_FILES)

typecheck:
	mypy $(PACKAGE)

lint:
	ruff check $(PACKAGE)

format:
	ruff format $(PACKAGE)
	ruff check --fix $(PACKAGE)

check: lint typecheck test

architecture-check: architecture-cycle-check
	pytest -q tests_ce/architecture/test_inner_architecture_target.py
	# ArchKeel ratchets type-only/package SCC edges; Pylint checks executable import cycles.
	uvx --python 3.11 --from archkeel==0.7.0 archkeel validate --baseline known-violations.json --json | python3 -c 'import json, sys; raw = sys.stdin.read(); print(raw, end=""); report = json.loads(raw); measurements = report.get("measurements") or {}; scalars = measurements.get("scalars") or {}; coverage = report.get("coverage") or {}; valid = report.get("exit_code") == 0 and report.get("declared_rules") == "PASS" and report.get("observation_complete") == "PASS" and coverage.get("status") == "PASS" and scalars.get("violations") == 0 and scalars.get("unknown_positions") == 0 and report.get("baseline_new") == 0 and report.get("baseline_resolved") == 0; sys.exit(0 if valid else 1)'

architecture-cycle-check:
	uvx --python 3.11 --from pylint==3.3.7 pylint --disable=all --enable=cyclic-import --persistent=n --score=n datamimic_ce

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
