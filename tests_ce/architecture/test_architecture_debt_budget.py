# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Architecture debt budget.

``architecture-contract.json`` and its inside contracts describe the target architecture. Where the
code still contradicts it, ``archkeel report`` records violations, and that red report is expected.
This gate keeps the known violations from growing: each is frozen in ``architecture_debt_budget.json``
by a key that survives unrelated edits (rules | source module -> imported symbol). A new violation
fails; a removed one must be dropped from the budget, so the budget only shrinks. The contract must
otherwise be valid: ``archkeel validate`` may report violated rules, nothing else.

After removing debt, rewrite the budget with::

    python tests_ce/architecture/test_architecture_debt_budget.py
"""

from __future__ import annotations

import functools
import json
import subprocess
import sys
from pathlib import Path

from archkeel.ir.codec import decode_canonical_model

REPO = Path(__file__).resolve().parents[2]
BUDGET = Path(__file__).with_name("architecture_debt_budget.json")
ARCHKEEL = Path(sys.executable).with_name("archkeel")


def _archkeel(command: str) -> dict:
    completed = subprocess.run(
        [str(ARCHKEEL), command, "--json"], cwd=REPO, capture_output=True, text=True, encoding="utf-8", check=False
    )
    return json.loads(completed.stdout)


def _import_key(data: dict) -> str:
    symbol = data["symbol"]
    return f"{data['source_module']} -> {data['target_module']}" + (f":{symbol}" if symbol else "")


@functools.cache
def _violations() -> frozenset[str]:
    report = _archkeel("report")
    assert report["observation_complete"] == "PASS", report["diagnostics"]
    model = decode_canonical_model(json.loads((REPO / report["artifact"]).read_text(encoding="utf-8")))
    imports = {record["id"]: record["data"] for record in model["imports"]}
    keys: set[str] = set()
    for violation in model["violations"]:
        rules = "+".join(sorted(violation["rule_ids"]))
        linked = [imports[fact_id] for fact_id in violation["fact_ids"] if fact_id in imports]
        if linked:
            keys |= {f"{rules} | {_import_key(data)}" for data in linked}
        else:
            keys.add(f"{rules} | {' '.join(sorted(violation['subjects']))}")
    return frozenset(keys)


def test_contract_is_valid_apart_from_known_violations() -> None:
    codes = {diagnostic["code"] for diagnostic in _archkeel("validate")["diagnostics"]}
    assert codes <= {"rule.violated"}, codes


def test_architecture_debt_does_not_grow() -> None:
    new = sorted(_violations() - set(json.loads(BUDGET.read_text(encoding="utf-8"))))
    assert not new, "New architecture violations; fix the code instead:\n" + "\n".join(new)


def test_architecture_debt_budget_has_no_resolved_entries() -> None:
    resolved = sorted(set(json.loads(BUDGET.read_text(encoding="utf-8"))) - _violations())
    assert not resolved, (
        "Resolved architecture violations are still in the budget; shrink it with "
        "`python tests_ce/architecture/test_architecture_debt_budget.py`:\n" + "\n".join(resolved)
    )


if __name__ == "__main__":
    current = sorted(_violations())
    BUDGET.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {BUDGET}: {len(current)} known architecture violations")
