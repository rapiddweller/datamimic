"""Keep complete-assignment and forbidden-dependency rules on their owner packages."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

RULE_SCOPES = {
    "architecture-contract.json": {
        "TASKS-NO-CLIENTS": "datamimic_ce.engine.runtime.tasks",
    },
    "docs/architecture/inner/dsl/model/architecture-contract.json": {
        "MODEL-ASSIGNMENT": "datamimic_ce.engine.dsl.model",
    },
    "docs/architecture/inner/runtime/tasks/architecture-contract.json": {
        "TASKS-ASSIGNMENT": "datamimic_ce.engine.runtime.tasks",
    },
    "docs/architecture/inner/runtime/tasks/generate/architecture-contract.json": {
        "GENERATE-ASSIGNMENT": "datamimic_ce.engine.runtime.tasks.generate",
    },
    "docs/architecture/inner/dsl/parsers/architecture-contract.json": {
        "PARSERS-ASSIGNMENT": "datamimic_ce.engine.dsl.parsers",
    },
}


def test_architecture_rules_cover_their_complete_owner_packages() -> None:
    for relative_path, expected_rules in RULE_SCOPES.items():
        contract = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
        rules = {rule["id"]: rule for rule in contract["rules"]}
        for rule_id, expected_source in expected_rules.items():
            assert rules[rule_id]["source"] == expected_source, rule_id
