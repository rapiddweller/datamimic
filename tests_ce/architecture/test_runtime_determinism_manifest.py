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
            "Dynamic seeded Safe Globals": "27 representative paths (datetime, fake, math, np, pd, random, uuid)",
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


def test_literal_replay_golden_covers_unique_draws_across_automatic_pages() -> None:
    import hashlib

    from tests_ce.integration_tests.test_determinism_seed_scenarios.test_determinism_seed_scenarios import (
        _run_in_fresh_process,
        canonical_result_bytes,
    )

    result = _run_in_fresh_process("replay_all_seeded.xml")
    # The 41-column literal product automatically splits five rows into pages of three.
    # A page restart previously repeated C in row five rather than exhausting A..E once.
    assert [row["unique_values"] for row in result["literal"]] == ["E", "C", "D", "A", "B"]
    assert hashlib.sha256(canonical_result_bytes(result)).hexdigest() == EXPECTED_LITERAL_REPLAY_HASH
