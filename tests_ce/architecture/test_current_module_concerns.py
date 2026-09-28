"""Keep every current CE module and component accountable to one stated concern."""

from __future__ import annotations

import json
from pathlib import Path

from tests_ce.architecture.test_recursive_target_definition import (
    _files_at,
    _source_has_python_code,
    _target_files,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/architecture/inner/structure-review.json"
REVIEW_ROOT = ROOT / "docs/architecture/inner/semantic-review"


def _review_records() -> dict[str, dict]:
    records: dict[str, dict] = {}
    for path in sorted(REVIEW_ROOT.glob("review-*.json")):
        for record in json.loads(path.read_text(encoding="utf-8"))["records"]:
            if record["id"].startswith("module:"):
                assert record["id"] not in records, f"duplicate module concern: {record['id']}"
                records[record["id"]] = record
    return records


def _current_modules() -> set[str]:
    return {path.relative_to(ROOT / "datamimic_ce").as_posix() for path in (ROOT / "datamimic_ce").rglob("*.py")}


def _components() -> list[dict]:
    return [
        component
        for path in [
            ROOT / "architecture-contract.json",
            *sorted((ROOT / "docs/architecture").rglob("architecture-contract.json")),
        ]
        for component in json.loads(path.read_text(encoding="utf-8"))["components"]
    ]


def _ambiguous_targets(manifest: dict) -> set[str]:
    return (
        {target for split in manifest["splits"] for target in split["targets"]}
        | {merge["target"] for merge in manifest["merges"]}
        | {module["target"] for module in manifest["new_modules"]}
    )


def test_current_modules_and_components_have_a_target_and_one_sentence_concern() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source_files = _files_at(manifest["source_commit"])
    target_sources = _target_files(source_files, manifest)
    current = _current_modules()
    assert set(target_sources) == current, (
        "missing or conflicting current-module target mapping: "
        f"missing={sorted(current - set(target_sources))}, stale={sorted(set(target_sources) - current)}"
    )

    records = _review_records()
    assert set(records) == {f"module:{source}" for source in source_files}, "missing source-module concern"
    ambiguous_targets = _ambiguous_targets(manifest)
    overrides = {item["target"]: item["responsibility"] for item in manifest["target_module_concerns"]}
    assert len(overrides) == len(manifest["target_module_concerns"]), "duplicate target-module concern"
    assert ambiguous_targets <= set(overrides), (
        f"missing explicit concern for split, merge, or new target: {sorted(ambiguous_targets - set(overrides))}"
    )
    assert set(overrides) <= set(target_sources), (
        f"concern for absent target module: {sorted(set(overrides) - set(target_sources))}"
    )
    assert len(set(overrides.values())) == len(overrides), "duplicate target-module responsibility"
    for target, sources in target_sources.items():
        if target not in ambiguous_targets:
            assert len(sources) == 1, f"ambiguous target needs an explicit concern: {target}"
        concerns = (
            {overrides[target]}
            if target in ambiguous_targets
            else {records[f"module:{source}"].get("concern", "").strip() for source in sources}
        )
        assert concerns and all(concerns), f"missing or blank current-module concern: {target}"
        assert all(concern.endswith((".", "!", "?")) for concern in concerns), (
            f"incomplete current-module concern: {target}"
        )

    reviewed_packages = {review["path"]: review for review in manifest["package_reviews"]}
    for source in source_files:
        if not source.endswith("__init__.py"):
            continue
        if _source_has_python_code(source, manifest["source_commit"]):
            scope = source.rsplit("/", 1)[0] if "/" in source else "."
            owner = reviewed_packages[scope].get("initializer_owner", "")
            assert owner.strip(), f"missing executable initializer owner: {source}"

    components = _components()
    assert len({component["id"] for component in components}) == len(components), "duplicate component target"
    target_scopes = {"."}
    for target in current:
        parts = target.removesuffix(".py").split("/")
        target_scopes.update("/".join(parts[:index]) for index in range(1, len(parts) + 1))
    for component in components:
        assert component.get("packages"), f"missing component target: {component['id']}"
        for target in component["packages"]:
            scope = target.removeprefix("datamimic_ce").strip(".").replace(".", "/") or "."
            assert scope in target_scopes, f"missing component target: {component['id']} -> {target}"
        responsibilities = component.get("responsibilities", [])
        assert len(responsibilities) == 1, f"component needs one responsibility sentence: {component['id']}"
        responsibility = responsibilities[0]
        assert isinstance(responsibility, str) and responsibility.strip().endswith((".", "!", "?")), (
            f"blank or incomplete component responsibility: {component['id']}"
        )
