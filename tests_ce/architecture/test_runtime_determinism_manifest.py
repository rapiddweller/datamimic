from __future__ import annotations

from pathlib import Path

import pytest

from tests_ce.architecture.runtime_determinism_manifest import (
    EXPECTED_ENTITY_REPLAY_HASH,
    EXPECTED_FACADE_CONTENT_HASHES,
    EXPECTED_LITERAL_REPLAY_HASH,
    UTF8_PROBE_HASH,
    RuntimeDeterminismManifest,
    _compare_command,
    compare_manifests,
)


def _manifest() -> RuntimeDeterminismManifest:
    return {
        "facade_hashes": dict(EXPECTED_FACADE_CONTENT_HASHES),
        "entity_replay_hash": EXPECTED_ENTITY_REPLAY_HASH,
        "literal_replay_hash": EXPECTED_LITERAL_REPLAY_HASH,
        "coverage": {
            "Facade API": "4/4",
            "Entities": "23/23 (selected attributes)",
            "Literal generators": (
                "34/35 (SequenceTableGenerator covered by external-service DSL tests; "
                "excluded from this byte hash: DB state)"
            ),
            "Dynamic seeded Safe Globals": "16 representative paths (datetime, fake, pd, random, uuid)",
            "UTF-8 probe": "1 (canonical UTF-8 probe)",
        },
        "utf8_probe_hash": UTF8_PROBE_HASH,
    }


def test_identical_manifests_pass_cross_job_comparison() -> None:
    assert compare_manifests({"ubuntu-py311": _manifest(), "windows-py311": _manifest()}) == ()


def test_different_manifest_fails_cross_job_comparison() -> None:
    changed = _manifest()
    changed["facade_hashes"]["person"] = "different"
    errors = compare_manifests({"ubuntu-py311": _manifest(), "windows-py311": changed})
    assert "windows-py311: actual hashes differ from ubuntu-py311" in errors
    assert "person: actual hash does not match committed golden" not in errors


def test_different_literal_replay_hash_fails_cross_job_comparison() -> None:
    changed = _manifest()
    changed["literal_replay_hash"] = "different"
    errors = compare_manifests({"ubuntu-py311": _manifest(), "windows-py311": changed})
    assert "windows-py311: actual hashes differ from ubuntu-py311" in errors
    assert "replay_all_seeded.xml hash does not match the committed golden" not in errors


def test_different_entity_replay_hash_fails_cross_job_comparison() -> None:
    changed = _manifest()
    changed["entity_replay_hash"] = "different"
    errors = compare_manifests({"ubuntu-py311": _manifest(), "windows-py311": changed})
    assert "windows-py311: actual hashes differ from ubuntu-py311" in errors
    assert "seed_in_setup.xml hash does not match the committed golden" not in errors


def test_missing_manifest_count_writes_failure_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    assert _compare_command(tmp_path, expected_count=2) == 1
    assert "expected 2 manifests, found 0" in summary.read_text(encoding="utf-8")
