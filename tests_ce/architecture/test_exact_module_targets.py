"""Require one concrete responsibility declaration per current CE module."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "datamimic_ce"


def _current_modules() -> set[str]:
    return {path.relative_to(PACKAGE).as_posix() for path in PACKAGE.rglob("*.py")}


def _mounted_contracts() -> dict[Path, tuple[str, ...]]:
    result: dict[Path, tuple[str, ...]] = {}

    def visit(path: Path, scopes: tuple[str, ...]) -> None:
        path = path.resolve()
        assert path not in result, f"contract mounted more than once: {path}"
        result[path] = scopes
        contract = json.loads(path.read_text(encoding="utf-8"))
        for component in contract["components"]:
            inside = component.get("inside")
            if inside:
                visit(ROOT / inside, tuple(component["packages"]))

    visit(ROOT / "architecture-contract.json", ("datamimic_ce",))
    return result


def _declared_modules() -> dict[str, list[tuple[Path, str]]]:
    declarations: dict[str, list[tuple[Path, str]]] = {}
    for contract_path in _mounted_contracts():
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        for module in contract.get("declarations", {}).get("modules", []):
            path = module.get("path", "")
            target = path.removeprefix("datamimic_ce/") if path.startswith("datamimic_ce/") else path
            responsibility = module.get("responsibility", "")
            declarations.setdefault(target, []).append((contract_path, responsibility))
    return declarations


def _expected_owner(module: str, mounted: dict[Path, tuple[str, ...]]) -> Path:
    dotted = "datamimic_ce." + module[:-3].replace("/", ".")
    candidates = [
        (max(map(len, scopes)), path)
        for path, scopes in mounted.items()
        if any(dotted == scope or dotted.startswith(scope + ".") for scope in scopes)
    ]
    depth = max(length for length, _ in candidates)
    owners = [path for length, path in candidates if length == depth]
    assert len(owners) == 1, f"module has ambiguous deepest contract owner: {module}"
    return owners[0]


def _check_declarations(
    current: set[str],
    mounted: dict[Path, tuple[str, ...]],
    declarations: dict[str, list[tuple[Path, str]]],
) -> None:
    declared = set(declarations)
    assert declared == current, (
        f"module declarations differ from current Python files: "
        f"missing={sorted(current - declared)}, extra_or_stale={sorted(declared - current)}"
    )

    for target, entries in declarations.items():
        assert len(entries) == 1, f"duplicate module declaration: {target}"
        contract_path, responsibility = entries[0]
        assert responsibility.strip(), f"blank module responsibility: {target}"
        assert responsibility.strip().endswith((".", "!", "?")), f"incomplete module responsibility: {target}"
        assert not any(word in responsibility.casefold() for word in ("todo", "tbd", "placeholder")), (
            f"placeholder module responsibility: {target}"
        )
        assert contract_path == _expected_owner(target, mounted), f"module declared at wrong contract depth: {target}"


def test_every_current_module_has_one_concrete_deepest_contract_declaration() -> None:
    _check_declarations(_current_modules(), _mounted_contracts(), _declared_modules())


def test_module_declaration_gate_rejects_missing_extra_duplicate_and_bad_ownership() -> None:
    current = _current_modules()
    mounted = _mounted_contracts()
    declarations = _declared_modules()

    missing = {target: entries.copy() for target, entries in declarations.items()}
    missing.pop(next(iter(missing)))
    invalid = [missing]

    extra = {target: entries.copy() for target, entries in declarations.items()}
    extra["stale.py"] = [(next(iter(mounted)), "Stale module.")]
    invalid.append(extra)

    duplicate = {target: entries.copy() for target, entries in declarations.items()}
    target = next(iter(duplicate))
    duplicate[target].append(duplicate[target][0])
    invalid.append(duplicate)

    blank = {target: entries.copy() for target, entries in declarations.items()}
    target = next(iter(blank))
    blank[target] = [(blank[target][0][0], " ")]
    invalid.append(blank)

    placeholder = {target: entries.copy() for target, entries in declarations.items()}
    target = next(iter(placeholder))
    placeholder[target] = [(placeholder[target][0][0], "TODO: assign responsibility.")]
    invalid.append(placeholder)

    wrong_depth = {target: entries.copy() for target, entries in declarations.items()}
    target, entries = next(
        (target, entries)
        for target, entries in wrong_depth.items()
        if _expected_owner(target, mounted) != ROOT / "architecture-contract.json"
    )
    wrong_depth[target] = [(ROOT / "architecture-contract.json", entries[0][1])]
    invalid.append(wrong_depth)

    for mutated in invalid:
        try:
            _check_declarations(current, mounted, mutated)
        except AssertionError:
            continue
        raise AssertionError("mutated module declarations unexpectedly passed")
