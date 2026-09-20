from __future__ import annotations

from pathlib import Path

import pytest

from tests_ce.architecture.facade_hash_manifest import (
    EXPECTED_CONTENT_HASHES,
    UTF8_PROBE_HASH,
    FacadeHashManifest,
    _compare_command,
    compare_manifests,
)


def _manifest() -> FacadeHashManifest:
    return {"facade_hashes": dict(EXPECTED_CONTENT_HASHES), "utf8_probe_hash": UTF8_PROBE_HASH}


def test_identical_manifests_pass_cross_job_comparison() -> None:
    assert compare_manifests({"ubuntu-py311": _manifest(), "windows-py311": _manifest()}) == ()


def test_different_manifest_fails_cross_job_comparison() -> None:
    changed = _manifest()
    changed["facade_hashes"]["person"] = "different"
    errors = compare_manifests({"ubuntu-py311": _manifest(), "windows-py311": changed})
    assert "windows-py311: actual hashes differ from ubuntu-py311" in errors
    assert "person: actual hash does not match committed golden" not in errors


def test_missing_manifest_count_writes_failure_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    assert _compare_command(tmp_path, expected_count=2) == 1
    assert "expected 2 manifests, found 0" in summary.read_text(encoding="utf-8")
