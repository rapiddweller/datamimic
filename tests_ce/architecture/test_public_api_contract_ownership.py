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
