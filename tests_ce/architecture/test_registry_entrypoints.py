"""Fresh-process probes for cold CLI-to-registry composition."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _cli(cwd: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    return subprocess.run(
        [sys.executable, "-m", "datamimic_ce.interfaces.cli", *arguments],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
    )


def test_cli_entrypoints_resolve_live_registries_outside_checkout(tmp_path: Path) -> None:
    """A cold process must compose the canonical CLI and live registries."""
    valid = tmp_path / "valid.xml"
    unsupported = tmp_path / "unsupported.xml"
    valid.write_text(
        '<setup rngSeed="1"><generate name="things" count="1">'
        '<key name="id" constant="1"/></generate></setup>',
        encoding="utf-8",
    )
    unsupported.write_text('<setup rngSeed="1"><not-registered/></setup>', encoding="utf-8")

    capabilities = _cli(tmp_path, "capabilities", "--full")
    assert capabilities.returncode == 0, capabilities.stderr
    manifest = json.loads(capabilities.stdout)
    assert {"setup", "generate", "key"} <= set(manifest["elements"])
    assert manifest["targets"]

    accepted = _cli(tmp_path, "lint", valid.name, "--format", "json")
    assert accepted.returncode == 0, accepted.stderr
    assert json.loads(accepted.stdout)["ok"] is True

    rejected = _cli(tmp_path, "lint", unsupported.name, "--format", "json")
    assert rejected.returncode == 1
    diagnostics = json.loads(rejected.stdout)["diagnostics"]
    assert any(diagnostic["rule"] == "DM101" for diagnostic in diagnostics)
