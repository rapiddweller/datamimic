# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Architecture debt budget.

The architecture contract (``architecture-contract.json`` and its inside contracts) accepts a few
component edges as debt: they exist today but contradict the target. ``archkeel validate`` allows a
declared edge as a whole, so a new import over a debt edge would still pass. This gate freezes the
exact imports per debt edge in ``architecture_debt_budget.json``: a new one fails, and a removed one
must be dropped from the budget, so the budget can only shrink.

The budget's keys are the debt edges; adding debt is a deliberate edit of that file. After removing
debt, rewrite the imports of the existing edges with::

    python tests_ce/architecture/test_architecture_debt_budget.py
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "datamimic_ce"
BUDGET = Path(__file__).with_name("architecture_debt_budget.json")


def _levels() -> list[dict[str, str]]:
    """One package -> component mapping per contract level (level 1, then each inside)."""
    outer = json.loads((REPO / "architecture-contract.json").read_text(encoding="utf-8"))
    levels = [{package: component["label"] for component in outer["components"] for package in component["packages"]}]
    for component in outer["components"]:
        if "inside" in component:
            inner = json.loads((REPO / component["inside"]).read_text(encoding="utf-8"))
            levels.append(
                {
                    package: f"{component['label']}.{sub['label']}"
                    for sub in inner["components"]
                    for package in sub["packages"]
                }
            )
    return levels


def _owner(module: str, level: dict[str, str]) -> str | None:
    matches = [package for package in level if module == package or module.startswith(package + ".")]
    return level[max(matches, key=len)] if matches else None


def _imports() -> list[tuple[str, str]]:
    """(source module, imported target) for every absolute import of the package."""
    found: list[tuple[str, str]] = []
    for path in sorted(PACKAGE.rglob("*.py")):
        module = ".".join(path.relative_to(REPO).with_suffix("").parts).removesuffix(".__init__")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found += [(module, alias.name) for alias in node.names if alias.name.startswith("datamimic_ce.")]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and (node.module or "").startswith("datamimic_ce."):
                found += [(module, f"{node.module}:{alias.name}") for alias in node.names]
    return found


def _crossings() -> dict[str, set[str]]:
    """Every import that crosses two components, keyed by edge, on every contract level."""
    crossings: dict[str, set[str]] = {}
    for level in _levels():
        for source, target in _imports():
            source_component = _owner(source, level)
            target_component = _owner(target.split(":")[0], level)
            if source_component and target_component and source_component != target_component:
                crossings.setdefault(f"{source_component} -> {target_component}", set()).add(f"{source} -> {target}")
    return crossings


def _budget() -> dict[str, list[str]]:
    return json.loads(BUDGET.read_text(encoding="utf-8"))


def test_debt_edges_do_not_grow() -> None:
    observed = _crossings()
    new = {edge: sorted(observed.get(edge, set()) - set(allowed)) for edge, allowed in _budget().items()}
    new = {edge: imports for edge, imports in new.items() if imports}
    assert not new, (
        "New imports over architecture debt edges. Import through an allowed edge, or remove the debt:\n"
        + json.dumps(new, indent=2)
    )


def test_debt_budget_has_no_stale_imports() -> None:
    observed = _crossings()
    stale = {edge: sorted(set(allowed) - observed.get(edge, set())) for edge, allowed in _budget().items()}
    stale = {edge: imports for edge, imports in stale.items() if imports}
    assert not stale, (
        "Debt imports that no longer exist; shrink the budget with "
        "`python tests_ce/architecture/test_architecture_debt_budget.py`:\n" + json.dumps(stale, indent=2)
    )


if __name__ == "__main__":
    current = _crossings()
    rewritten = {edge: sorted(current.get(edge, set())) for edge in _budget()}
    BUDGET.write_text(json.dumps(rewritten, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {BUDGET}: {sum(map(len, rewritten.values()))} imports on {len(rewritten)} debt edges")
