"""Keep the recursive architecture target defined as the CE tree changes."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "datamimic_ce"
MANIFEST = ROOT / "docs/architecture/inner/structure-review.json"


def _files_at(commit: str) -> set[str]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "--name-only", commit, "--", "datamimic_ce"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return {
        path.removeprefix("datamimic_ce/")
        for raw in result.stdout.split(b"\0")
        if raw
        for path in [raw.decode()]
        if path.endswith(".py")
    }


def _current_files() -> set[str]:
    return {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*.py")
    }


def _scopes(files: set[str]) -> set[str]:
    result = {"."}
    for file in files:
        parent = PurePosixPath(file).parent
        while str(parent) != ".":
            result.add(parent.as_posix())
            parent = parent.parent
    return result


def _children(scope: str, files: set[str]) -> set[str]:
    prefix = "" if scope == "." else scope + "/"
    children = set()
    for file in files:
        if file.startswith(prefix):
            remainder = file[len(prefix) :]
            if "/" in remainder:
                children.add(remainder.split("/", 1)[0])
            elif remainder != "__init__.py":
                children.add(remainder)
    return children


def _source_has_python_code(source: str, commit: str) -> bool:
    result = subprocess.run(
        ["git", "show", f"{commit}:datamimic_ce/{source}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return _has_python_code(ast.parse(result.stdout, filename=source).body)


def _has_python_code(body: list[ast.stmt]) -> bool:
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    return any(not isinstance(statement, ast.Pass) for statement in body)


def _target_implementation_issues(
    targets: dict[str, set[str]], package: Path, source_commit: str
) -> list[str]:
    issues: list[str] = []
    for target, sources in targets.items():
        path = package / target
        if not path.is_file():
            continue
        if target == "__init__.py":
            if _has_python_code(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)).body):
                issues.append("root initializer must remain empty")
            continue
        requires_code = not sources or any(_source_has_python_code(source, source_commit) for source in sources)
        if requires_code and not _has_python_code(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)).body):
            issues.append(f"placeholder target module: {target}")
    return issues


def _target_files(files: set[str], manifest: dict) -> dict[str, set[str]]:
    relocations = manifest["relocations"]
    package_relocations = manifest["package_relocations"]
    split_items = manifest["splits"]
    initializer_removals = manifest["removed_initializers"]
    module_removals = manifest["removed_modules"]
    merge_items = manifest["merges"]
    new_modules = manifest["new_modules"]
    file_moves = {item["source"]: item["target"] for item in relocations}
    package_moves = {item["source"].rstrip("/"): item["target"].rstrip("/") for item in package_relocations}
    splits = {item["source"]: item for item in split_items}
    removed_initializers = {item["source"]: item for item in initializer_removals}
    removed_modules = {item["source"]: item for item in module_removals}
    merges = {source: item for item in merge_items for source in item["sources"]}
    assert len(file_moves) == len(relocations) and set(file_moves) <= files, "invalid file relocation selector"
    assert len(package_moves) == len(package_relocations) and set(package_moves) <= _scopes(files), (
        "invalid package relocation selector"
    )
    assert len(splits) == len(split_items) and set(splits) <= files, "invalid split selector"
    assert len(removed_initializers) == len(initializer_removals) and set(removed_initializers) <= files, (
        "invalid initializer removal selector"
    )
    assert len(removed_modules) == len(module_removals) and set(removed_modules) <= files, (
        "invalid module removal selector"
    )
    assert len(merges) == sum(len(item["sources"]) for item in merge_items) and set(merges) <= files, (
        "invalid merge selector"
    )
    selectors = [set(file_moves), set(splits), set(removed_initializers), set(removed_modules), set(merges)]
    assert sum(map(len, selectors)) == len(set().union(*selectors)), "a source has multiple selectors"
    assert all(
        not any(source == package or source.startswith(package + "/") for package in package_moves)
        for source in set().union(*selectors)
    ), "a source cannot use both a package and direct selector"
    assert not any(
        first != second and second.startswith(first + "/") for first in package_moves for second in package_moves
    ), "nested package relocation selectors"
    for source, item in removed_initializers.items():
        assert source.endswith("/__init__.py") and item.get("reason")
        assert not _source_has_python_code(source, manifest["source_commit"]), source
    for source, item in removed_modules.items():
        assert source.endswith(".py") and not source.endswith("/__init__.py") and item.get("reason")
    for item in merge_items:
        assert item.get("reason") and item["sources"] and len(set(item["sources"])) == len(item["sources"])
        _assert_target_path(item["target"])
    assert len({item["target"] for item in new_modules}) == len(new_modules), "duplicate new module target"
    for item in new_modules:
        assert item.get("reason")
        _assert_target_path(item["target"])

    output: dict[str, set[str]] = {}
    split_destinations: set[str] = set()
    ordinary_destinations: dict[str, set[str]] = {}
    assert len({item["target"] for item in merge_items}) == len(merge_items), "duplicate merge target"
    merge_destinations = {
        PurePosixPath(item["target"]).as_posix(): set(item["sources"])
        for item in merge_items
    }

    for source in files:
        if source in removed_initializers or source in removed_modules:
            continue
        if source in splits:
            split = splits[source]
            assert split.get("reason") and split["targets"], f"split requires targets and a reason: {source}"
            assert len(set(split["targets"])) == len(split["targets"])
            targets = split["targets"]
            split_destinations.update(PurePosixPath(target).as_posix() for target in targets)
        elif source in merges:
            targets = [merges[source]["target"]]
        elif source in file_moves:
            targets = [file_moves[source]]
        else:
            matches = [package for package in package_moves if source == package or source.startswith(package + "/")]
            if matches:
                package = max(matches, key=len)
                targets = [package_moves[package] + source[len(package) :]]
            else:
                targets = [source]
        if source not in splits:
            ordinary_target = PurePosixPath(targets[0]).as_posix()
            ordinary_destinations.setdefault(ordinary_target, set()).add(source)
        for target in targets:
            _assert_target_path(target)
            path = PurePosixPath(target)
            output.setdefault(path.as_posix(), set()).add(source)

    for item in new_modules:
        target = PurePosixPath(item["target"]).as_posix()
        assert target not in output, f"new module target conflicts with mapped source: {target}"
        output[target] = set()

    collisions = {target: sources for target, sources in output.items() if len(sources) > 1}
    assert all(
        (
            sources == merge_destinations.get(target)
            or (target in split_destinations and len(ordinary_destinations.get(target, set())) <= 1)
        )
        for target, sources in collisions.items()
    ), f"unexplained target collisions: {collisions}"
    return output


def _assert_target_path(target: str) -> None:
    path = PurePosixPath(target)
    assert not path.is_absolute() and ".." not in path.parts and path.suffix == ".py", target


def _contracts() -> dict[str, list[set[str]]]:
    root = ROOT / "architecture-contract.json"
    active: set[Path] = set()
    mounted: set[Path] = set()
    layouts: dict[str, list[set[str]]] = {}

    def visit(path: Path, *, inside: bool = False, mount_scopes: tuple[str, ...] = ("datamimic_ce",)) -> None:
        path = path.resolve()
        assert path.is_relative_to(ROOT.resolve()) and path.is_file(), path
        assert path not in active, f"inside contract cycle: {path}"
        if inside:
            assert path not in mounted, f"duplicate inside mount: {path}"
            mounted.add(path)
        active.add(path)
        contract = json.loads(path.read_text(encoding="utf-8"))
        assert contract.get("schema_version") == "2.1.0"
        for rule in contract["rules"]:
            if rule["kind"] == "root_layout":
                root = rule["root"]
                assert any(root == scope or root.startswith(scope + ".") for scope in mount_scopes), (path, root)
                scope = root.removeprefix("datamimic_ce").strip(".").replace(".", "/") or "."
                layouts.setdefault(scope, []).append(set(rule["allowed_children"]))
        for component in contract["components"]:
            if component.get("inside"):
                visit(ROOT / component["inside"], inside=True, mount_scopes=tuple(component["packages"]))
        active.remove(path)

    visit(root)
    inner_root = ROOT / "docs/architecture/inner"
    declared = {path.resolve() for path in inner_root.rglob("architecture-contract.json")}
    assert mounted == declared, "every inner contract must be reachable exactly once from the root"

    contract = json.loads(root.read_text(encoding="utf-8"))
    root_kinds = {rule["kind"] for rule in contract["rules"]}
    assert {"complete_assignment", "complete_requires", "interface_boundary", "root_layout"} <= root_kinds
    assert any(rule["kind"] == "no_component_cycles" and rule.get("level") == "module" for rule in contract["rules"])
    for path in mounted:
        contract = json.loads(path.read_text(encoding="utf-8"))
        if len(contract["components"]) > 1:
            kinds = {rule["kind"] for rule in contract["rules"]}
            assert {"complete_assignment", "complete_requires", "interface_boundary", "no_component_cycles"} <= kinds
    return layouts


def _check_layouts(layouts: dict[str, list[set[str]]], targets: set[str], excluded: set[str]) -> None:
    target_scopes = _scopes(targets)
    expected_scopes = target_scopes
    assert set(layouts) == expected_scopes, (
        "layout roots must cover existing target scopes, not vanished or future paths"
    )
    for scope in expected_scopes:
        declarations = layouts.get(scope, [])
        assert len(declarations) == 1, f"{scope}: expected exactly one root_layout, got {len(declarations)}"
        allowed = declarations[0]
        children = _children(scope, targets | excluded)
        expected = {
            "datamimic_ce."
            + (scope.replace("/", ".") + "." if scope != "." else "")
            + (child[:-3] if child.endswith(".py") else child)
            for child in children
        }
        assert allowed == expected, (
            f"{scope}: root_layout children differ: missing={expected - allowed}, extra={allowed - expected}"
        )


def _physical_target_issues(current: set[str], targets: dict[str, set[str]]) -> list[str]:
    expected = set(targets)
    issues: list[str] = []
    if missing := sorted(expected - current):
        issues.append(f"missing target modules: {missing}")
    if legacy := sorted(current - expected):
        issues.append(f"legacy or unowned modules: {legacy}")
    return issues


def test_recursive_target_definition_covers_sources_and_mounts() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["format_version"] == 1
    assert manifest["editions"] == {"ce": "datamimic_ce", "ee": "datamimic_ee"}
    assert re.fullmatch(r"[0-9a-f]{40}", manifest["source_commit"])
    assert manifest["scope"].strip()
    assert all(item.get("prefix") and item.get("reason") for item in manifest["exclusions"])

    all_files = _files_at(manifest["source_commit"])
    exclusions = manifest["exclusions"]
    files = {file for file in all_files if not any(file.startswith(item["prefix"]) for item in exclusions)}
    reviews = manifest["package_reviews"]
    reviewed = {item["path"]: item for item in reviews}
    assert len(reviewed) == len(reviews) and set(reviewed) == _scopes(files)
    for scope, review in reviewed.items():
        assert review["disposition"] in {"retain", "regroup", "relocate", "dissolve"}
        assert review.get("target") and review.get("rationale")
        assert set(review["direct_children"]) == _children(scope, files), scope
        init = "__init__.py" if scope == "." else f"{scope}/__init__.py"
        if init in files and _source_has_python_code(init, manifest["source_commit"]):
            assert review.get("initializer_owner"), init

    targets = _target_files(files, manifest)
    retained = {item["path"] for item in manifest["retained_over_seven"]}
    target_scopes = _scopes(set(targets))
    assert retained == {scope for scope in target_scopes if len(_children(scope, set(targets))) > 7}
    assert all(item.get("reason") for item in manifest["retained_over_seven"])
    excluded_files = {file for file in all_files - files}
    layouts = _contracts()
    _check_layouts(layouts, set(targets), excluded_files)


def test_recursive_target_definition_rejects_mapping_and_layout_false_greens(tmp_path: Path) -> None:
    files = {"a.py", "b.py", "split.py"}
    manifest: dict = {
        "relocations": [{"source": source, "target": "target.py"} for source in ("a.py", "b.py")],
        "package_relocations": [],
        "splits": [{"source": "split.py", "targets": ["target.py"], "reason": "named split"}],
        "removed_initializers": [],
        "removed_modules": [],
        "merges": [],
        "new_modules": [],
    }
    with pytest.raises(AssertionError, match="collisions"):
        _target_files(files, manifest)
    manifest["relocations"] = []
    manifest["splits"][0]["targets"] = []
    with pytest.raises(AssertionError, match="split requires"):
        _target_files({"split.py"}, manifest)

    target_manifest: dict = json.loads(MANIFEST.read_text(encoding="utf-8"))
    all_files = _files_at(target_manifest["source_commit"])
    excluded = {p for p in all_files if any(p.startswith(x["prefix"]) for x in target_manifest["exclusions"])}
    targets = _target_files(all_files - excluded, target_manifest)
    layouts = _contracts()
    mutated = {scope: [children.copy() for children in entries] for scope, entries in layouts.items()}
    mutated.pop(next(iter(mutated)))
    with pytest.raises(AssertionError, match="layout roots"):
        _check_layouts(mutated, set(targets), excluded)
    mutated = {scope: [children.copy() for children in entries] for scope, entries in layouts.items()}
    mutated[next(iter(mutated))].append(mutated[next(iter(mutated))][0].copy())
    with pytest.raises(AssertionError, match="exactly one root_layout"):
        _check_layouts(mutated, set(targets), excluded)

    bad_source = {
        "relocations": [{"source": "missing.py", "target": "target.py"}],
        "package_relocations": [],
        "splits": [],
        "removed_initializers": [],
        "removed_modules": [],
        "merges": [],
        "new_modules": [],
    }
    with pytest.raises(AssertionError, match="file relocation selector"):
        _target_files({"source.py"}, bad_source)

    merge = {
        "relocations": [],
        "package_relocations": [],
        "splits": [],
        "removed_initializers": [],
        "removed_modules": [{"source": "removed.py", "reason": "obsolete"}],
        "merges": [{"sources": ["context.py", "setup.py"], "target": "context.py", "reason": "one owner"}],
        "new_modules": [{"target": "boundary.py", "reason": "new boundary"}],
    }
    assert _target_files({"context.py", "setup.py", "removed.py"}, merge) == {
        "context.py": {"context.py", "setup.py"},
        "boundary.py": set(),
    }
    merge["merges"][0]["sources"].append("missing.py")
    with pytest.raises(AssertionError, match="merge selector"):
        _target_files({"context.py", "setup.py", "removed.py"}, merge)
    merge["merges"][0]["sources"] = ["context.py", "setup.py"]
    merge["new_modules"][0]["target"] = "context.py"
    with pytest.raises(AssertionError, match="new module target conflicts"):
        _target_files({"context.py", "setup.py", "removed.py"}, merge)
    merge["new_modules"][0]["target"] = "boundary.py"
    merge["removed_modules"][0]["source"] = "missing.py"
    with pytest.raises(AssertionError, match="module removal selector"):
        _target_files({"context.py", "setup.py", "removed.py"}, merge)

    source = next(
        path
        for path in _files_at(target_manifest["source_commit"])
        if _source_has_python_code(path, target_manifest["source_commit"])
    )
    placeholder = tmp_path / "target.py"
    placeholder.write_text('"""Not implemented."""\npass\n', encoding="utf-8")
    assert _target_implementation_issues(
        {"target.py": {source}}, tmp_path, target_manifest["source_commit"]
    ) == ["placeholder target module: target.py"]
    placeholder.write_text("value = 1\n", encoding="utf-8")
    assert not _target_implementation_issues({"target.py": {source}}, tmp_path, target_manifest["source_commit"])
    root_initializer = tmp_path / "__init__.py"
    root_initializer.write_text("", encoding="utf-8")
    assert not _target_implementation_issues(
        {"__init__.py": {"__init__.py"}}, tmp_path, target_manifest["source_commit"]
    )
    root_initializer.write_text("load_dotenv()\n", encoding="utf-8")
    assert _target_implementation_issues(
        {"__init__.py": {"__init__.py"}}, tmp_path, target_manifest["source_commit"]
    ) == ["root initializer must remain empty"]

    with pytest.raises(AssertionError, match="missing target modules"):
        assert not _physical_target_issues({"legacy.py"}, {"target.py": {"source.py"}})
    with pytest.raises(AssertionError, match="legacy or unowned modules"):
        assert not _physical_target_issues({"target.py", "legacy.py"}, {"target.py": {"source.py"}})
