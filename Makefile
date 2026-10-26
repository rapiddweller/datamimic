.PHONY: help install test test-unit test-integration test-functional coverage coverage-unit typecheck lint format check architecture-check architecture-definition-check architecture-version architecture-report architecture-validation-receipt architecture-cycle-check installed-authoring-check agent-plugin-check agent-plugin-package clean

PYTHON ?= python
INSTALLED_AUTHORING_ARGS ?=
AGENT_PLUGIN_ARCHIVE ?= test-artifacts/agent-plugin/datamimic.zip

PACKAGE := datamimic_ce
TESTS := tests_ce
CE_COVERAGE_FILES := $(shell find $(PACKAGE) -type f -name '*.py')
ARCHKEEL_SOURCE := archkeel==4.0.1
# The independent receipt includes the exact Python runtime.
ARCHKEEL_PYTHON := 3.11.12
ARCHITECTURE_DIR := test-artifacts/architecture/ce-recursive-target
# Empty by default. CI sets --substance-only for fork pull requests, which cannot record the review.
COMPLETION_GATE_FLAGS ?=

help:
	@echo "Available targets:"
	@echo "  install           Install project dependencies via uv"
	@echo "  installed-authoring-check  Check an installed wheel in an isolated workspace"
	@echo "  agent-plugin-check  Check native plugin metadata and contained skill resources"
	@echo "  agent-plugin-package  Build the separate agent plugin ZIP"
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
	@coverage report --format=total --omit='$(PACKAGE)/resources/examples/*.py,$(PACKAGE)/resources/demos/**/*.py,$(PACKAGE)/interfaces/demo.py' --fail-under=65.74 $(CE_COVERAGE_FILES)
	@coverage xml --omit='$(PACKAGE)/resources/examples/*.py,$(PACKAGE)/resources/demos/**/*.py,$(PACKAGE)/interfaces/demo.py' $(CE_COVERAGE_FILES)

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
	uvx --python $(ARCHKEEL_PYTHON) --from '$(ARCHKEEL_SOURCE)' archkeel report --output $(ARCHITECTURE_DIR)/architecture.json --json > $(ARCHITECTURE_DIR)/report.stdout.json

architecture-version:
	@version="$$(uvx --python $(ARCHKEEL_PYTHON) --from '$(ARCHKEEL_SOURCE)' archkeel --version)" && test "$$version" = 'archkeel $(patsubst archkeel==%,%,$(ARCHKEEL_SOURCE))' && printf '%s\n' "$${version#archkeel }"

architecture-validation-receipt:
	mkdir -p $(ARCHITECTURE_DIR)
	# Preserve exit-2 diagnostics for the independently reviewed completion policy.
	@uvx --python $(ARCHKEEL_PYTHON) --from '$(ARCHKEEL_SOURCE)' archkeel validate --baseline known-violations.json --json > $(ARCHITECTURE_DIR)/validation.json; status=$$?; test "$$status" -eq 0 || test "$$status" -eq 2

architecture-check: architecture-cycle-check architecture-definition-check
	uvx --python 3.11 --from pytest==8.3.5 pytest -q tests_ce/architecture/test_inner_architecture_target.py tests_ce/architecture/test_completion_gate.py
	# ArchKeel ratchets type-only/package SCC edges; Pylint checks executable import cycles.
	$(MAKE) architecture-validation-receipt architecture-report
	uvx --python $(ARCHKEEL_PYTHON) --from '$(ARCHKEEL_SOURCE)' archkeel report --input $(ARCHITECTURE_DIR)/architecture.json --only architecture --full --json > $(ARCHITECTURE_DIR)/completion.json
	uvx --python 3.11 --from pytest==8.3.5 python tests_ce/architecture/completion_gate.py $(COMPLETION_GATE_FLAGS) $(ARCHITECTURE_DIR)/validation.json $(ARCHITECTURE_DIR)/completion.json docs/architecture/refactoring-study/experiment-2/completion-unknowns.json

architecture-cycle-check:
	uvx --python 3.11 --from pylint==3.3.7 pylint --disable=all --enable=cyclic-import --persistent=n --score=n datamimic_ce

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
