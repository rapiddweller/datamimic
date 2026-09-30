from __future__ import annotations

import copy
import hashlib
import json

import pytest

from datamimic_ce.authoring.adapters.reference import capabilities_manifest
from script.architecture_study import compare_step0


def _projection(content: str) -> dict[str, object]:
    encoded = content.encode("utf-8")
    return {
        "content": content,
        "bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _capabilities(content: object) -> dict[str, object]:
    return _projection(json.dumps(content, sort_keys=True))


def _current_capabilities(version: str) -> dict[str, object]:
    return _capabilities({"schema_version": version, "elements": {"sample": ["stable"]}})


def _projections(capabilities: dict[str, object]) -> dict[str, object]:
    return {
        "capabilities": capabilities,
        "reference_authoring": _projection('{"authoring":"stable"}'),
        "reference_scaffold": _projection('{"scaffold":"stable"}'),
        "compiler": _projection('{"compiler":"stable"}'),
    }


def test_current_capability_projection_accepts_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(compare_step0, "captured_package_version", lambda: "installed-current")
    current = _current_capabilities("installed-current")

    assert compare_step0.capability_projection_equivalent(current, copy.deepcopy(current))


@pytest.mark.parametrize("metadata", ["sha256", "bytes"])
def test_capability_projection_rejects_identical_malformed_metadata(
    metadata: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(compare_step0, "captured_package_version", lambda: "installed-current")
    current = _current_capabilities("installed-current")
    assert compare_step0.capability_projection_equivalent(current, copy.deepcopy(current))
    malformed = copy.deepcopy(current)
    malformed[metadata] = "wrong" if metadata == "sha256" else current["bytes"] + 1

    assert not compare_step0.capability_projection_equivalent(malformed, copy.deepcopy(malformed))


@pytest.mark.parametrize("content", ["not-json", "[]", "null", '"scalar"'])
def test_capability_projection_rejects_invalid_or_non_object_json(content: str) -> None:
    malformed = _projection(content)

    assert not compare_step0.capability_projection_equivalent(malformed, copy.deepcopy(malformed))


def test_capability_projection_rejects_changed_current_content(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(compare_step0, "captured_package_version", lambda: "installed-current")
    before = _current_capabilities("installed-current")
    assert compare_step0.capability_projection_equivalent(before, copy.deepcopy(before))
    changed = _capabilities(
        {"schema_version": "installed-current", "elements": {"sample": ["changed"]}}
    )

    assert not compare_step0.capability_projection_equivalent(before, changed)


def test_projection_comparison_accepts_complete_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(compare_step0, "captured_package_version", lambda: "installed-current")
    before = _projections(_current_capabilities("installed-current"))

    assert compare_step0.projections_equivalent(before, copy.deepcopy(before))


@pytest.mark.parametrize("missing", ["capabilities", "reference_authoring", "reference_scaffold", "compiler"])
def test_projection_comparison_rejects_missing_required_section(
    missing: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(compare_step0, "captured_package_version", lambda: "installed-current")
    before = _projections(_current_capabilities("installed-current"))
    assert compare_step0.projections_equivalent(before, copy.deepcopy(before))
    after = copy.deepcopy(before)
    del after[missing]

    assert not compare_step0.projections_equivalent(before, after)


@pytest.mark.parametrize("changed", ["reference_authoring", "reference_scaffold", "compiler"])
def test_non_capability_projections_remain_byte_exact(
    changed: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(compare_step0, "captured_package_version", lambda: "installed-current")
    before = _projections(_current_capabilities("installed-current"))
    assert compare_step0.projections_equivalent(before, copy.deepcopy(before))
    after = copy.deepcopy(before)
    after[changed] = _projection('{"changed":true}')

    assert not compare_step0.projections_equivalent(before, after)


@pytest.mark.parametrize("version", ["missing", None, "", 123, [], "invented"])
def test_capability_identity_rejects_invalid_or_unrecognized_version(
    version: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(compare_step0, "captured_package_version", lambda: "installed-current")
    content: dict[str, object] = {"elements": {"sample": ["stable"]}}
    if version != "missing":
        content["schema_version"] = version
    projection = _capabilities(content)

    assert not compare_step0.capability_projection_equivalent(projection, copy.deepcopy(projection))


@pytest.mark.parametrize("installed_version", [None, ""])
def test_capability_identity_rejects_unavailable_or_empty_installed_version(
    installed_version: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(compare_step0, "captured_package_version", lambda: installed_version)
    projection = _current_capabilities("installed-current")

    assert not compare_step0.capability_projection_equivalent(projection, copy.deepcopy(projection))


@pytest.mark.parametrize("elements", ["missing", {}, [], None, "not-an-object"])
def test_capability_identity_rejects_missing_or_invalid_elements(
    elements: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(compare_step0, "captured_package_version", lambda: "installed-current")
    content: dict[str, object] = {"schema_version": "installed-current"}
    if elements != "missing":
        content["elements"] = elements
    projection = _capabilities(content)

    assert not compare_step0.capability_projection_equivalent(projection, copy.deepcopy(projection))


def test_full_current_capability_manifest_accepts_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = capabilities_manifest()
    version = manifest["schema_version"]
    assert isinstance(version, str) and version
    assert isinstance(manifest["elements"], dict) and manifest["elements"]
    monkeypatch.setattr(compare_step0, "captured_package_version", lambda: version)
    projection = _capabilities(manifest)

    assert compare_step0.capability_projection_equivalent(projection, copy.deepcopy(projection))


def test_capability_identity_still_requires_byte_exact_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(compare_step0, "captured_package_version", lambda: "installed-current")
    manifest = {"schema_version": "installed-current", "elements": {"sample": ["stable"]}}
    before = _projection(json.dumps(manifest, sort_keys=True))
    after = _projection(json.dumps(manifest, indent=2, sort_keys=True))

    assert compare_step0.capability_projection_equivalent(before, copy.deepcopy(before))
    assert not compare_step0.capability_projection_equivalent(before, after)
