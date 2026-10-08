"""Keep command entrypoints and Python API declarations at the right contract scope."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _read_contract(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _component(contract: dict, component_id: str) -> dict:
    return next(component for component in contract["components"] if component["id"] == component_id)


def test_cli_and_mcp_remain_commands_without_component_local_public_apis() -> None:
    root = _read_contract(ROOT / "architecture-contract.json")
    commands = {command["id"]: command["command"] for command in root["declarations"]["public_commands"]}
    assert commands == {"CMD-DATAMIMIC": "datamimic", "CMD-MCP": "datamimic-mcp"}

    interfaces = _read_contract(ROOT / "docs/architecture/inner/interfaces/architecture-contract.json")
    assert _component(interfaces, "TRANSPORT-CLI").get("public", []) == []
    assert _component(interfaces, "TRANSPORT-MCP").get("public", []) == []


def test_client_lookup_is_declared_at_io_boundary_and_owned_by_clients() -> None:
    symbol = "datamimic_ce.engine.io.clients.client:ClientLookup"
    root = _read_contract(ROOT / "architecture-contract.json")
    assert _component(root, "COMP-IO")["public"].count(symbol) == 1
    assert symbol not in root["declarations"]["public_api"]
    assert all(symbol not in component["public"] for component in root["components"] if component["id"] != "COMP-IO")
    io = _read_contract(ROOT / "docs/architecture/inner/io/architecture-contract.json")
    assert symbol.split(":", 1)[0] in _component(io, "IO-CLIENTS")["public"]


def test_generate_domain_is_root_public_api_and_domain_api_sibling_stays_public() -> None:
    symbol = "datamimic_ce.domains.facade:generate_domain"
    return_alias = "datamimic_ce.domains.domain_core.contracts.json_types:JsonObject"
    root = _read_contract(ROOT / "architecture-contract.json")
    assert root["declarations"]["public_api"].count(symbol) == 1
    assert root["declarations"]["public_api"].count(return_alias) == 1
    assert all(symbol not in component.get("public", []) for component in root["components"])

    domains = _read_contract(ROOT / "docs/architecture/inner/domains/architecture-contract.json")
    assert all(symbol not in component.get("public", []) for component in domains["components"])

    sibling_api = _component(domains, "DOMAINS-API")["public"]
    assert "datamimic_ce.domains.api" in sibling_api
    assert "datamimic_ce.domains.api:AddressService" in sibling_api


def test_inherited_domain_service_models_are_declared_at_domains_boundaries() -> None:
    models = {
        "datamimic_ce.domains.shared.models.address:Address",
        "datamimic_ce.domains.shared.models.city:City",
        "datamimic_ce.domains.shared.models.company:Company",
        "datamimic_ce.domains.shared.models.country:Country",
        "datamimic_ce.domains.shared.models.person:Person",
        "datamimic_ce.domains.healthcare.models.patient:Patient",
    }
    root = _read_contract(ROOT / "architecture-contract.json")
    root_domains = _component(root, "COMP-DOMAINS")["public"]
    assert all(root_domains.count(symbol) == 1 for symbol in models)
    assert models.isdisjoint(root["declarations"]["public_api"])

    domains = _read_contract(ROOT / "docs/architecture/inner/domains/architecture-contract.json")
    shared_models = {
        "datamimic_ce.domains.shared.models.address:Address",
        "datamimic_ce.domains.shared.models.city:City",
        "datamimic_ce.domains.shared.models.company:Company",
        "datamimic_ce.domains.shared.models.country:Country",
        "datamimic_ce.domains.shared.models.person:Person",
    }
    shared_public = _component(domains, "DOMAINS-SHARED")["public"]
    assert all(shared_public.count(symbol) == 1 for symbol in shared_models)
    assert _component(domains, "DOMAINS-HEALTHCARE")["public"].count(
        "datamimic_ce.domains.healthcare.models.patient:Patient"
    ) == 1
    assert models.isdisjoint(_component(domains, "DOMAINS-API")["public"])


def test_demographic_profile_records_are_owned_by_domains_not_global_public_api() -> None:
    symbols = {
        "datamimic_ce.domains.shared.demographics.profile:DemographicAgeBand",
        "datamimic_ce.domains.shared.demographics.profile:DemographicConditionRate",
    }
    root = _read_contract(ROOT / "architecture-contract.json")
    root_domains = _component(root, "COMP-DOMAINS")["public"]
    assert all(root_domains.count(symbol) == 1 for symbol in symbols)
    assert symbols.isdisjoint(root["declarations"]["public_api"])


def test_statement_branch_and_memstore_manager_are_root_component_declarations() -> None:
    owners = {
        "COMP-DSL": "datamimic_ce.engine.dsl.statements.base.composite_statement:ConditionBranchStatement",
        "COMP-RUNTIME": "datamimic_ce.engine.runtime.storage.memstore_manager:MemstoreManager",
    }
    root = _read_contract(ROOT / "architecture-contract.json")
    assert set(owners.values()).isdisjoint(root["declarations"]["public_api"])
    for owner_id, symbol in owners.items():
        assert _component(root, owner_id)["public"].count(symbol) == 1
        assert all(
            symbol not in component.get("public", [])
            for component in root["components"]
            if component["id"] != owner_id
        )

    dsl = _read_contract(ROOT / "docs/architecture/inner/dsl/statements/architecture-contract.json")
    assert owners["COMP-DSL"] in _component(dsl, "STATEMENTS-BASE")["public"]
    runtime = _read_contract(ROOT / "docs/architecture/inner/runtime/architecture-contract.json")
    assert "datamimic_ce.engine.runtime.storage.memstore_manager" in _component(runtime, "RUNTIME-STORAGE")[
        "public"
    ]


def test_finance_model_api_types_are_declared_at_their_owning_boundaries() -> None:
    model_symbols = {
        "datamimic_ce.domains.finance.models.bank:Bank",
        "datamimic_ce.domains.finance.generators.bank_account_generator:BankAccountGenerator",
    }
    contract_symbols = {
        f"datamimic_ce.domains.finance.contracts:{name}"
        for name in (
            "BankAccountData",
            "CurrencyData",
            "GeneratedTransactionData",
            "TransactionData",
            "TransactionTypeData",
        )
    }
    symbols = model_symbols | contract_symbols
    root = _read_contract(ROOT / "architecture-contract.json")
    root_domains = _component(root, "COMP-DOMAINS")["public"]
    assert all(root_domains.count(symbol) == 1 for symbol in symbols)
    assert symbols.isdisjoint(root["declarations"]["public_api"])
    assert all(
        symbols.isdisjoint(component.get("public", []))
        for component in root["components"]
        if component["id"] != "COMP-DOMAINS"
    )

    domains = _read_contract(ROOT / "docs/architecture/inner/domains/architecture-contract.json")
    finance = _component(domains, "DOMAINS-FINANCE")["public"]
    assert all(finance.count(symbol) == 1 for symbol in symbols)
    assert all(
        symbols.isdisjoint(component.get("public", []))
        for component in domains["components"]
        if component["id"] != "DOMAINS-FINANCE"
    )

    inner = _read_contract(ROOT / "docs/architecture/inner/domains/finance/architecture-contract.json")
    contracts = _component(inner, "FINANCE-CONTRACTS")["public"]
    assert all(contracts.count(symbol) == 1 for symbol in contract_symbols)
    assert all(
        contract_symbols.isdisjoint(component.get("public", []))
        for component in inner["components"]
        if component["id"] != "FINANCE-CONTRACTS"
    )
    assert "contracts" in {
        entry["component"] for entry in _component(inner, "FINANCE-MODELS")["requires"]
    }


def test_demographic_context_is_runtime_owned_and_not_root_public() -> None:
    from datamimic_ce.engine.runtime import api as runtime_api
    from datamimic_ce.engine.runtime.contexts.demographic_context import DemographicContext

    assert "DemographicContext" in runtime_api.__all__
    assert runtime_api.DemographicContext is DemographicContext

    runtime_api_module = "datamimic_ce.engine.runtime.api"
    context_module = "datamimic_ce.engine.runtime.contexts.demographic_context"
    root = _read_contract(ROOT / "architecture-contract.json")
    runtime = _component(root, "COMP-RUNTIME")["public"]
    assert runtime_api_module in runtime
    assert context_module not in root["declarations"]["public_api"]
    assert all(
        runtime_api_module not in component.get("public", [])
        and context_module not in component.get("public", [])
        for component in root["components"]
        if component["id"] != "COMP-RUNTIME"
    )

    inner = _read_contract(ROOT / "docs/architecture/inner/runtime/architecture-contract.json")
    runtime_api = _component(inner, "RUNTIME-API")["public"]
    runtime_contexts = _component(inner, "RUNTIME-CONTEXTS")["public"]
    assert runtime_api_module in runtime_api
    assert context_module in runtime_contexts
    assert all(
        runtime_api_module not in component.get("public", [])
        and context_module not in component.get("public", [])
        for component in inner["components"]
        if component["id"] not in {"RUNTIME-API", "RUNTIME-CONTEXTS"}
    )


def test_facade_records_keep_their_existing_owner_modules() -> None:
    from datamimic_ce.engine.dsl.api import TimeSeriesNamespace
    from datamimic_ce.engine.runtime.api import DemographicContext

    assert TimeSeriesNamespace.__module__ == "datamimic_ce.engine.dsl.model.generation.timeseries"
    assert DemographicContext.__module__ == "datamimic_ce.engine.runtime.contexts.demographic_context"


def test_state_machine_definition_is_generation_contract_owned() -> None:
    from datamimic_ce.domains import api
    from datamimic_ce.domains.domain_core.contracts import generation

    symbol = "datamimic_ce.domains.domain_core.contracts.generation:StateMachineDef"
    assert api.StateMachineDef is generation.StateMachineDef

    domains = _read_contract(ROOT / "docs/architecture/inner/domains/architecture-contract.json")
    core = _component(domains, "DOMAINS-CORE")["public"]
    assert core.count(symbol) == 1
    assert all(
        symbol not in component.get("public", [])
        for component in domains["components"]
        if component["id"] != "DOMAINS-CORE"
    )


def test_existing_entrypoints_have_explicit_inner_public_decisions() -> None:
    root = _read_contract(ROOT / "architecture-contract.json")
    tasks = _read_contract(ROOT / "docs/architecture/inner/runtime/tasks/architecture-contract.json")
    shared = _read_contract(ROOT / "docs/architecture/inner/domains/shared/architecture-contract.json")
    healthcare = _read_contract(ROOT / "docs/architecture/inner/domains/healthcare/architecture-contract.json")
    authoring = _read_contract(ROOT / "docs/architecture/inner/authoring/architecture-contract.json")

    assert _component(tasks, "TASKS-REGISTRY")["public"] == []

    assert _component(shared, "SHARED-USE-CASES")["public"] == [
        "datamimic_ce.domains.shared.use_cases.address_api:AddressRequest",
        "datamimic_ce.domains.shared.use_cases.address_api:generate",
        "datamimic_ce.domains.shared.use_cases.person_api:PersonRequest",
        "datamimic_ce.domains.shared.use_cases.person_api:generate",
    ]
    assert _component(healthcare, "HEALTHCARE-USE-CASES")["public"] == [
        "datamimic_ce.domains.healthcare.use_cases.doctor_api:DoctorRequest",
        "datamimic_ce.domains.healthcare.use_cases.doctor_api:generate",
        "datamimic_ce.domains.healthcare.use_cases.patient_api:PatientRequest",
        "datamimic_ce.domains.healthcare.use_cases.patient_api:generate",
    ]

    api = _component(authoring, "AUTHORING-API")
    assert api["packages"] == ["datamimic_ce.authoring.api"]
    assert api["exact_modules"] == ["datamimic_ce.authoring"]
    assert api["public"] == ["datamimic_ce.authoring.api"]
    assert _component(root, "COMP-AUTHORING")["public"] == [
        "datamimic_ce.authoring.api",
        "datamimic_ce.authoring.contracts",
        "datamimic_ce.authoring.spec:LeafFieldKind",
    ]


def test_domains_initializer_has_one_exact_owner_without_widening_api_selector() -> None:
    module = "datamimic_ce.domains"
    domains = _read_contract(ROOT / "docs/architecture/inner/domains/architecture-contract.json")
    api = _component(domains, "DOMAINS-API")

    assert api["packages"] == ["datamimic_ce.domains.api"]
    assert api["exact_modules"] == [module]
    assert [
        component["id"]
        for component in domains["components"]
        if module in component.get("exact_modules", [])
        or any(
            module == package or module.startswith(f"{package}.")
            for package in component.get("packages", [])
        )
    ] == ["DOMAINS-API"]


@pytest.mark.parametrize(
    ("path", "owner_id", "root", "package_selector", "child_owners"),
    [
        (
            "docs/architecture/inner/runtime/architecture-contract.json",
            "RUNTIME-API",
            "datamimic_ce.engine.runtime",
            ["datamimic_ce.engine.runtime.api"],
            {
                "datamimic_ce.engine.runtime.contracts": "RUNTIME-CONTRACTS",
                "datamimic_ce.engine.runtime.storage": "RUNTIME-STORAGE",
                "datamimic_ce.engine.runtime.logging": "RUNTIME-LOGGING",
                "datamimic_ce.engine.runtime.process_titles": "RUNTIME-LOGGING",
                "datamimic_ce.engine.runtime.contexts": "RUNTIME-CONTEXTS",
                "datamimic_ce.engine.runtime.tasks": "RUNTIME-TASKS",
                "datamimic_ce.engine.runtime.lifecycle": "RUNTIME-LIFECYCLE",
                "datamimic_ce.engine.runtime.scripting": "RUNTIME-EVALUATION",
            },
        ),
        (
            "docs/architecture/inner/domains/finance/architecture-contract.json",
            "FINANCE-MODELS",
            "datamimic_ce.domains.finance",
            [
                "datamimic_ce.domains.finance.models",
            ],
            {
                "datamimic_ce.domains.finance.models": "FINANCE-MODELS",
                "datamimic_ce.domains.finance.generators": "FINANCE-GENERATORS",
                "datamimic_ce.domains.finance.contracts": "FINANCE-CONTRACTS",
                "datamimic_ce.domains.finance.services": "FINANCE-SERVICES",
                "datamimic_ce.domains.finance.luhn": "FINANCE-ALGORITHMS",
            },
        ),
        (
            "docs/architecture/inner/domains/healthcare/architecture-contract.json",
            "HEALTHCARE-SERVICES",
            "datamimic_ce.domains.healthcare",
            [
                "datamimic_ce.domains.healthcare.services",
            ],
            {
                "datamimic_ce.domains.healthcare.models": "HEALTHCARE-MODELS",
                "datamimic_ce.domains.healthcare.generators": "HEALTHCARE-GENERATORS",
                "datamimic_ce.domains.healthcare.services": "HEALTHCARE-SERVICES",
                "datamimic_ce.domains.healthcare.use_cases": "HEALTHCARE-USE-CASES",
            },
        ),
        (
            "docs/architecture/inner/io/exporters/architecture-contract.json",
            "EXPORTERS-REGISTRY",
            "datamimic_ce.engine.io.exporters",
            [
                "datamimic_ce.engine.io.exporters.registry",
            ],
            {
                "datamimic_ce.engine.io.exporters.core": "EXPORTERS-CORE",
                "datamimic_ce.engine.io.exporters.formats": "EXPORTERS-FORMATS",
                "datamimic_ce.engine.io.exporters.database": "EXPORTERS-DATABASE",
                "datamimic_ce.engine.io.exporters.memory": "EXPORTERS-MEMORY",
                "datamimic_ce.engine.io.exporters.diagnostics": "EXPORTERS-DIAGNOSTICS",
                "datamimic_ce.engine.io.exporters.registry": "EXPORTERS-REGISTRY",
                "datamimic_ce.engine.io.exporters.lifecycle": "EXPORTERS-LIFECYCLE",
                "datamimic_ce.engine.io.exporters.session": "EXPORTERS-SESSION",
            },
        ),
        (
            "docs/architecture/inner/domains/shared/converters/architecture-contract.json",
            "CONVERTERS-BASE",
            "datamimic_ce.domains.shared.converters",
            [
                "datamimic_ce.domains.shared.converters.base",
            ],
            {
                "datamimic_ce.domains.shared.converters.base": "CONVERTERS-BASE",
                "datamimic_ce.domains.shared.converters.text": "CONVERTERS-TEXT",
                "datamimic_ce.domains.shared.converters.temporal": "CONVERTERS-TEMPORAL",
                "datamimic_ce.domains.shared.converters.privacy": "CONVERTERS-PRIVACY",
                "datamimic_ce.domains.shared.converters.structural": "CONVERTERS-STRUCTURAL",
            },
        ),
        (
            "docs/architecture/inner/io/architecture-contract.json",
            "IO-API",
            "datamimic_ce.engine.io",
            ["datamimic_ce.engine.io.api"],
            {
                "datamimic_ce.engine.io.contracts": "IO-CONTRACTS",
                "datamimic_ce.engine.io.clients": "IO-CLIENTS",
                "datamimic_ce.engine.io.connection_config": "IO-CONNECTION-CONFIG",
                "datamimic_ce.engine.io.data_sources": "IO-SOURCES",
                "datamimic_ce.engine.io.exporters": "IO-EXPORTERS",
                "datamimic_ce.engine.io.files": "IO-FILES",
            },
        ),
    ],
)
def test_initializers_have_exact_existing_owners(
    path: str,
    owner_id: str,
    root: str,
    package_selector: list[str],
    child_owners: dict[str, str],
) -> None:
    contract = _read_contract(ROOT / path)
    owner = _component(contract, owner_id)

    assert owner["packages"] == package_selector
    assert owner.get("exact_modules") == [root]
    assert [
        component["id"]
        for component in contract["components"]
        if root in component.get("exact_modules", [])
        or any(root == package or root.startswith(f"{package}.") for package in component.get("packages", []))
    ] == [owner_id]

    for child, expected_owner in child_owners.items():
        assert [
            component["id"]
            for component in contract["components"]
            if child in component.get("exact_modules", [])
            or any(child == package or child.startswith(f"{package}.") for package in component.get("packages", []))
        ] == [expected_owner]

def test_model_util_stays_inside_dsl_model_boundary() -> None:
    from datamimic_ce.engine.dsl import api as dsl_api
    from datamimic_ce.engine.dsl.model import validation

    model_util = "datamimic_ce.engine.dsl.model.validation:ModelUtil"
    validation_names = {
        "check_constraints",
        "check_exist_count",
        "check_is_digit_or_script",
        "check_min_max_count",
        "check_weights_require_values",
    }
    validation_symbols = {
        f"datamimic_ce.engine.dsl.model.validation:{name}" for name in validation_names
    }

    model = _read_contract(ROOT / "docs/architecture/inner/dsl/model/architecture-contract.json")
    assert model_util in _component(model, "MODEL-VALIDATION")["public"]

    dsl = _read_contract(ROOT / "docs/architecture/inner/dsl/architecture-contract.json")
    parent_public = _component(dsl, "DSL-MODELS")["public"]
    assert model_util not in parent_public
    assert {symbol for symbol in parent_public if symbol.startswith("datamimic_ce.engine.dsl.model.validation:")} == (
        validation_symbols
    )

    assert set(dsl_api.__all__) >= validation_names
    assert "ModelUtil" not in dsl_api.__all__
    assert not hasattr(dsl_api, "ModelUtil")
    assert dsl_api.check_constraints is validation.check_constraints
    assert dsl_api.check_exist_count is validation.check_exist_count
    assert dsl_api.check_is_digit_or_script is validation.check_is_digit_or_script
    assert dsl_api.check_min_max_count is validation.check_min_max_count
    assert dsl_api.check_weights_require_values is validation.check_weights_require_values
