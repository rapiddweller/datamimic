"""Keep flow semantic leaves mounted and explicitly assigned."""

from __future__ import annotations

import json
from pathlib import Path

from datamimic_ce.engine.dsl.model.registry import get_valid_children
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import (
    EL_EXECUTE,
    EL_GENERATE,
    EL_NESTED_KEY,
    EL_SETUP,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/architecture/inner/runtime/tasks/flow/architecture-contract.json"


def test_flow_contract_mounts_five_semantic_leaves() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert {component["label"] for component in contract["components"]} == {
        "branches", "loops", "assertion", "diagnostics", "script-execution",
    }
    assert all(component["requires"] == [] for component in contract["components"])
    assert {rule["kind"] for rule in contract["rules"]} >= {
        "complete_assignment", "complete_requires", "interface_boundary",
    }

    tasks = json.loads(
        (ROOT / "docs/architecture/inner/runtime/tasks/architecture-contract.json").read_text(encoding="utf-8")
    )
    flow = next(component for component in tasks["components"] if component["id"] == "TASKS-FLOW")
    assert flow["inside"] == "docs/architecture/inner/runtime/tasks/flow/architecture-contract.json"
    assert not any("IfElseBaseTask" in item for item in flow["public"])


def test_execute_scope_is_setup_and_nested_key_only() -> None:
    assert EL_EXECUTE in get_valid_children(EL_SETUP)
    assert EL_EXECUTE in get_valid_children(EL_NESTED_KEY)
    assert EL_EXECUTE not in get_valid_children(EL_GENERATE)
