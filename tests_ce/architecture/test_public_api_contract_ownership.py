"""Keep command entrypoints and Python API declarations at the right contract scope."""

from __future__ import annotations

import json
from pathlib import Path

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
