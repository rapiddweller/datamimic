# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Release versions agree across the tag, wheel and both plugin manifests."""

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

from script import prepare_plugin_release
from script.prepare_plugin_release import MANIFESTS, MCP_FILE, check_published, prepare, verify


@pytest.fixture(autouse=True)
def _offline_prepare(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(prepare_plugin_release, "check_published", lambda wheel, tag: None)


def _manifests(root: Path, version: str) -> None:
    for relative in MANIFESTS:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"name": "datamimic", "version": version}), encoding="utf-8")
    mcp = root / MCP_FILE
    mcp.write_text(
        json.dumps({"mcpServers": {"datamimic": {"args": ["--from", f"datamimic-ce[mcp]=={version}"]}}}),
        encoding="utf-8",
    )


def _wheel(root: Path, version: str, *, name: str = "datamimic-ce") -> Path:
    wheel = root / "package.whl"
    with ZipFile(wheel, "w") as archive:
        archive.writestr("package.dist-info/METADATA", f"Name: {name}\nVersion: {version}\n")
    return wheel


def test_prepare_sets_both_versions_and_preserves_other_fields(tmp_path: Path) -> None:
    _manifests(tmp_path, "0.4.0")

    prepare(tmp_path, _wheel(tmp_path, "5.0.0"), "5.0.0")

    for path in MANIFESTS:
        assert json.loads((tmp_path / path).read_text(encoding="utf-8")) == {
            "name": "datamimic",
            "version": "5.0.0",
        }
    args = json.loads((tmp_path / MCP_FILE).read_text())["mcpServers"]["datamimic"]["args"]
    assert args == ["--from", "datamimic-ce[mcp]==5.0.0"]


@pytest.mark.parametrize("version", ["", "5.0", "05.0.0", "5.0.0rc1", "v5.0.0"])
def test_prepare_rejects_invalid_versions_before_writing(tmp_path: Path, version: str) -> None:
    _manifests(tmp_path, "0.4.0")

    with pytest.raises(ValueError):
        prepare(tmp_path, _wheel(tmp_path, "5.0.0"), version)

    assert all(json.loads((tmp_path / path).read_text())["version"] == "0.4.0" for path in MANIFESTS)


def test_prepare_rejects_a_different_wheel_before_writing(tmp_path: Path) -> None:
    _manifests(tmp_path, "0.4.0")
    with pytest.raises(ValueError, match="Release versions differ"):
        prepare(tmp_path, _wheel(tmp_path, "5.0.1"), "5.0.0")
    assert all(json.loads((tmp_path / path).read_text())["version"] == "0.4.0" for path in MANIFESTS)


def test_release_gate_accepts_matching_wheel_tag_and_manifests(tmp_path: Path) -> None:
    _manifests(tmp_path, "5.0.0")
    verify(tmp_path, _wheel(tmp_path, "5.0.0"), "5.0.0")


@pytest.mark.parametrize(
    "wheel_version,tag,manifest",
    [
        ("5.0.1", "5.0.0", "5.0.0"),
        ("5.0.0", "5.0.1", "5.0.0"),
        ("5.0.0", "5.0.0", "4.3.0"),
        ("5.0.0", "v5.0.0", "5.0.0"),
    ],
)
def test_release_gate_rejects_mismatches(tmp_path: Path, wheel_version: str, tag: str, manifest: str) -> None:
    _manifests(tmp_path, manifest)
    with pytest.raises(ValueError):
        verify(tmp_path, _wheel(tmp_path, wheel_version), tag)


def test_release_gate_rejects_a_different_package(tmp_path: Path) -> None:
    _manifests(tmp_path, "5.0.0")
    with pytest.raises(ValueError, match="not datamimic-ce"):
        verify(tmp_path, _wheel(tmp_path, "5.0.0", name="other"), "5.0.0")


@pytest.mark.parametrize("manifest", MANIFESTS)
def test_release_gate_rejects_either_stale_manifest(tmp_path: Path, manifest: Path) -> None:
    _manifests(tmp_path, "5.0.0")
    (tmp_path / manifest).write_text('{"version": "4.3.0"}', encoding="utf-8")

    with pytest.raises(ValueError, match="Plugin versions or source differ"):
        verify(tmp_path, _wheel(tmp_path, "5.0.0"), "5.0.0")


def test_release_commands_prepare_and_verify(tmp_path: Path) -> None:
    _manifests(tmp_path, "0.4.0")
    script = tmp_path / "script" / "prepare_plugin_release.py"
    script.parent.mkdir()
    shutil.copyfile(Path(__file__).resolve().parents[3] / "script" / script.name, script)
    wheel = _wheel(tmp_path, "5.0.0")

    prepare(tmp_path, wheel, "5.0.0")
    subprocess.run([sys.executable, str(script), "verify", str(wheel), "5.0.0"], check=True)
    rejected = subprocess.run([sys.executable, str(script), "verify", str(wheel), "5.0.1"], capture_output=True)

    assert rejected.returncode != 0


def test_release_gate_rejects_a_stale_server_source(tmp_path: Path) -> None:
    _manifests(tmp_path, "5.0.0")
    path = tmp_path / MCP_FILE
    path.write_text('{"mcpServers": {"datamimic": {"args": ["--from", "datamimic-ce[mcp]==4.3.0"]}}}', encoding="utf-8")
    with pytest.raises(ValueError, match="Plugin versions or source differ"):
        verify(tmp_path, _wheel(tmp_path, "5.0.0"), "5.0.0")


def test_prepare_reports_a_partial_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _manifests(tmp_path, "0.4.0")
    original = os.replace

    def fail_second(source, destination):
        if destination == tmp_path / MANIFESTS[1]:
            raise OSError("disk full")
        return original(source, destination)

    wheel = _wheel(tmp_path, "5.0.0")
    monkeypatch.setattr(os, "replace", fail_second)
    with pytest.raises(OSError, match="files already updated.*Check all three"):
        prepare(tmp_path, wheel, "5.0.0")
    assert json.loads((tmp_path / MANIFESTS[0]).read_text())["version"] == "5.0.0"
    assert json.loads((tmp_path / MANIFESTS[1]).read_text())["version"] == "0.4.0"


@pytest.mark.parametrize("args", [[], ["--from"], ["--from", "one", "--from", "two"]])
def test_prepare_rejects_an_ambiguous_server_source_before_writing(tmp_path: Path, args: list[str]) -> None:
    _manifests(tmp_path, "0.4.0")
    (tmp_path / MCP_FILE).write_text(json.dumps({"mcpServers": {"datamimic": {"args": args}}}), encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one --from"):
        prepare(tmp_path, _wheel(tmp_path, "5.0.0"), "5.0.0")
    assert all(json.loads((tmp_path / path).read_text())["version"] == "0.4.0" for path in MANIFESTS)


@pytest.mark.parametrize("valid", [True, False])
def test_pypi_check_requires_a_matching_unyanked_wheel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid: bool
) -> None:
    wheel = _wheel(tmp_path, "5.0.0")
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    release = {"urls": [{"filename": wheel.name, "digests": {"sha256": digest}, "yanked": not valid}]}
    monkeypatch.setattr(
        prepare_plugin_release, "urlopen", lambda url, timeout: io.BytesIO(json.dumps(release).encode())
    )
    if valid:
        check_published(wheel, "5.0.0")
    else:
        with pytest.raises(ValueError, match="available file on PyPI"):
            check_published(wheel, "5.0.0")


def test_pypi_check_rejects_changed_wheel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wheel = _wheel(tmp_path, "5.0.0")
    release = {"urls": [{"filename": wheel.name, "digests": {"sha256": "wrong"}, "yanked": False}]}
    monkeypatch.setattr(
        prepare_plugin_release, "urlopen", lambda url, timeout: io.BytesIO(json.dumps(release).encode())
    )
    with pytest.raises(ValueError, match="available file on PyPI"):
        check_published(wheel, "5.0.0")
