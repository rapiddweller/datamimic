"""One owner of the install reference, and the shape of the three plugin manifests."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "plugins/datamimic"
MCP_FILE = PLUGIN / ".mcp.json"
REFERENCE_PATTERN = re.compile(
    r"^datamimic-ce\[mcp\]( @ git\+https://github\.com/rapiddweller/datamimic@[\w./-]+|>=5\.0\.0,<6)$"
)
PYTHON_RANGE_PATTERN = re.compile(r"^>=3\.\d+,<3\.\d+$")


def _entry() -> dict[str, object]:
    return json.loads(MCP_FILE.read_text())["mcpServers"]["datamimic"]


def _args() -> list[str]:
    args = _entry()["args"]
    assert isinstance(args, list)
    return args


def test_mcp_entry_starts_the_stdio_server_through_uvx() -> None:
    entry = _entry()
    assert entry["type"] == "stdio" and entry["command"] == "uvx"
    args = _args()
    assert args[args.index("datamimic-mcp") :] == ["datamimic-mcp", "--transport", "stdio"]
    assert "--workspace-root" not in args
    assert "cwd" not in entry and "env" not in entry


def test_install_reference_and_python_range_have_the_designed_shape() -> None:
    args = _args()
    assert args[0] == "--python" and PYTHON_RANGE_PATTERN.match(args[1]), args[:2]
    assert args[2] == "--from" and REFERENCE_PATTERN.match(args[3]), args[2:4]


def test_install_reference_appears_only_in_the_mcp_file() -> None:
    markers = ("git+https://github.com/rapiddweller/datamimic", "datamimic-ce[")
    offenders = [
        str(path.relative_to(ROOT))
        for path in PLUGIN.rglob("*")
        if path.is_file() and path != MCP_FILE and any(marker in path.read_text(errors="ignore") for marker in markers)
    ]
    assert offenders == []


def test_setup_skill_reads_the_reference_from_the_mcp_file() -> None:
    text = (PLUGIN / "skills/setup-datamimic/SKILL.md").read_text()
    assert "../../.mcp.json" in text
    assert (PLUGIN / "skills/setup-datamimic" / "../../.mcp.json").resolve() == MCP_FILE
    assert "uvx --refresh" in text and "build_protocol" in text


def test_skills_hold_no_stale_pin_workspace_binding_or_mcp_optional_text() -> None:
    for path in PLUGIN.rglob("*.md"):
        text = path.read_text()
        assert ">=5.0.0" not in text, path
        assert "--workspace-root" not in text, path
        assert "optional transport" not in text, path
        assert "child_execution" not in text, path


def test_manifests_share_name_and_version_and_point_at_the_mcp_file() -> None:
    codex = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text())
    claude = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
    assert codex["mcpServers"] == "./.mcp.json" and codex["skills"] == "./skills/"
    assert (PLUGIN / codex["mcpServers"]).resolve() == MCP_FILE
    assert codex["version"] == claude["version"] == "0.4.1"
    assert codex["name"] == claude["name"] == "datamimic"
    assert not (PLUGIN / "plugin.json").exists()
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    assert [item["name"] for item in marketplace["plugins"]] == ["datamimic"]


@pytest.mark.skipif(shutil.which("claude") is None, reason="the claude binary is not installed")
def test_claude_validates_the_plugin() -> None:
    result = subprocess.run(
        ["claude", "plugin", "validate", str(PLUGIN), "--json"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
