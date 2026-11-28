.PHONY: help install install-pre-commit test test-unit test-architecture test-integration test-benchmarks test-functional coverage coverage-unit coverage-unit-run coverage-unit-report typecheck lint format check architecture-check architecture-definition-check architecture-revision architecture-report architecture-validation-receipt architecture-cycle-check installed-authoring-check agent-plugin-check agent-plugin-package clean

PYTHON ?= python
INSTALLED_AUTHORING_ARGS ?=
AGENT_PLUGIN_ARCHIVE ?= test-artifacts/agent-plugin/datamimic.zip

PACKAGE := datamimic_ce
TESTS := tests_ce
AUTOMATIC_TESTS := $(addprefix $(TESTS)/,unit_tests integration_tests architecture functional_tests conformance scenarios api_tests factory_tests)
CE_COVERAGE_FILES := $(shell find $(PACKAGE) -type f -name '*.py')
COVERAGE_OMIT := $(PACKAGE)/resources/examples/*.py,$(PACKAGE)/resources/demos/**/*.py,$(PACKAGE)/interfaces/demo.py
UNIT_TEST_ARGS ?= $(TESTS)/unit_tests
ARCHKEEL_REVISION := f08ebe1826ff54df8d46045a4d96174c87cf1e58
ARCHKEEL_PYTHON := 3.11.12
ARCHKEEL := ARCHKEEL_BUNDLE_NATIVE=1 ARCHKEEL_NO_INIT=1 uvx --python $(ARCHKEEL_PYTHON) --from 'git+https://github.com/rapiddweller/archkeel@$(ARCHKEEL_REVISION)' archkeel
ARCHITECTURE_DIR := test-artifacts/architecture/ce-recursive-target

help:
	@echo "Available targets:"
	@echo "  install           Install project dependencies via uv"
	@echo "  installed-authoring-check  Check an installed wheel in an isolated workspace"
	@echo "  agent-plugin-check  Check native plugin metadata and contained skill resources"
	@echo "  agent-plugin-package  Build the separate agent plugin ZIP"
	@echo "  test              Run automatic test lanes"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests only (benchmarks excluded)"
	@echo "  test-benchmarks   Run the POSIX-only authoring eval oracle"
	@echo "  test-functional   Run functional tests only"
	@echo "  coverage          Run tests with coverage report for $(PACKAGE)"
	@echo "  coverage-unit     Run unit tests with complete CE coverage and regression floor"
	@echo "  typecheck         Run mypy against $(PACKAGE)"
	@echo "  lint              Run ruff against $(PACKAGE)"
	@echo "  format            Auto-format code with ruff"
	@echo "  check             Run lint, typecheck, and tests"
	@echo "  test-architecture Run the whole tests_ce/architecture folder (no file is excluded)"
	@echo "  install-pre-commit Install the git hook: ruff format, ruff check and mypy on datamimic_ce"
	@echo "  architecture-check Validate the physical, dependency, and ArchKeel architecture gates"
	@echo "  architecture-definition-check Validate recursive target coverage and move-map consistency"
	@echo "  architecture-report Generate the current ArchKeel HTML and JSON report"
	@echo "  architecture-cycle-check Check module imports with pinned Pylint"
	@echo "  clean             Remove caches and build artifacts"

install:
	uv sync

installed-authoring-check:
	$(PYTHON) -I "$(CURDIR)/script/check_installed_authoring.py" $(INSTALLED_AUTHORING_ARGS)

agent-plugin-check:
	$(PYTHON) -m pytest -q tests_ce/unit_tests/test_docs/test_agent_plugin.py

agent-plugin-package: agent-plugin-check
	mkdir -p "$(dir $(AGENT_PLUGIN_ARCHIVE))"
	cd plugins && $(PYTHON) -m zipfile -c "$(abspath $(AGENT_PLUGIN_ARCHIVE))" datamimic

install-pre-commit:
	uv tool install --quiet pre-commit
	"$$(uv tool dir --bin)/pre-commit" install

test:
	pytest -q $(AUTOMATIC_TESTS)

test-unit:
	pytest -q $(TESTS)/unit_tests

test-architecture:
	pytest -q $(TESTS)/architecture

test-integration:
	pytest -q $(TESTS)/integration_tests

test-benchmarks:
	pytest -q $(TESTS)/nightly_tests/test_benchmarks

test-functional:
	pytest -q $(TESTS)/functional_tests

coverage:
	coverage run -m pytest $(AUTOMATIC_TESTS)
	coverage report --include="$(PACKAGE)/*"
	coverage html --include="$(PACKAGE)/*"

coverage-unit: coverage-unit-run coverage-unit-report

# CI runs this once per shard (UNIT_TEST_ARGS, COVERAGE_FILE) and combines the data files before the report.
coverage-unit-run:
	coverage run --source=$(PACKAGE) -m pytest $(UNIT_TEST_ARGS) -n 0 --durations=20

coverage-unit-report:
	@coverage report --format=total --omit='$(COVERAGE_OMIT)' --fail-under=65.74 $(CE_COVERAGE_FILES)
	@coverage xml --omit='$(COVERAGE_OMIT)' $(CE_COVERAGE_FILES)

typecheck:
	mypy $(PACKAGE)

lint:
	ruff check $(PACKAGE)

format:
	ruff format $(PACKAGE)
	ruff check --fix $(PACKAGE)

check: lint typecheck test

architecture-definition-check:
	uvx --python 3.11 --from pytest==8.3.5 pytest -q tests_ce/architecture/test_recursive_target_definition.py tests_ce/architecture/test_current_module_concerns.py tests_ce/architecture/test_exact_module_targets.py tests_ce/architecture/test_registry_entrypoints.py::test_registry_owns_exact_initializer_and_keeps_package_selector tests_ce/architecture/test_public_api_contract_ownership.py::test_existing_entrypoints_have_explicit_inner_public_decisions

# The result is one line of ~140 KB; keep it out of the job log, where it buries the reason a later step fails.
architecture-report:
	mkdir -p $(ARCHITECTURE_DIR)
	rm -f $(ARCHITECTURE_DIR)/architecture.json $(ARCHITECTURE_DIR)/architecture.report.html
	@$(ARCHKEEL) report --output $(ARCHITECTURE_DIR)/architecture.json --format json; status=$$?; case "$$status" in 0|1|2) ;; *) exit "$$status";; esac; test -s $(ARCHITECTURE_DIR)/architecture.json
	@$(ARCHKEEL) report --output $(ARCHITECTURE_DIR)/architecture.report.html; status=$$?; case "$$status" in 0|1|2) ;; *) exit "$$status";; esac; test -s $(ARCHITECTURE_DIR)/architecture.report.html

architecture-revision:
	@printf '%s\n' '$(ARCHKEEL_REVISION)'

architecture-validation-receipt:
	mkdir -p $(ARCHITECTURE_DIR)
	rm -f $(ARCHITECTURE_DIR)/validation.json
	@$(ARCHKEEL) validate --json > $(ARCHITECTURE_DIR)/validation.json; status=$$?; case "$$status" in 0|1|2) ;; *) exit "$$status";; esac; test -s $(ARCHITECTURE_DIR)/validation.json

architecture-check: architecture-validation-receipt architecture-cycle-check architecture-definition-check
	uvx --python 3.11 --from pytest==8.3.5 pytest -q tests_ce/architecture/test_inner_architecture_target.py
	$(PYTHON) script/architecture_study/archkeel_status.py $(ARCHITECTURE_DIR)/validation.json --gate

architecture-cycle-check:
	uvx --python 3.11 --from pylint==3.3.7 pylint --disable=all --enable=cyclic-import --persistent=n --score=n datamimic_ce

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
