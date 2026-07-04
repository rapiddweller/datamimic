# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
"""Gate: every `datamimic ...` / `datamimic-mcp ...` invocation documented in
README.md, AGENTS.md, docs/api/cli.md and docs/mcp_quickstart.md is a real,
runnable CLI command — not just prose that happens to look like one.

Validation is against the live typer apps via CliRunner (no server spawned,
no subprocess): each extracted invocation gets `--help` appended, since Click
validates subcommand/option names before `--help` short-circuits execution
(pinned empirically in test_help_does_not_mask_bad_input below). The one case
where appending `--help` would itself mask the bug — a bare invocation with no
subcommand at all — is invoked as-is instead (see _cli_result).
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from typer.testing import CliRunner

from datamimic_ce.cli import app as cli_app
from datamimic_ce.mcp.cli import app as mcp_app

REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_FILES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "docs" / "api" / "cli.md",
    REPO_ROOT / "docs" / "mcp_quickstart.md",
]
# A real, existing descriptor to stand in for <descriptor.xml>-style placeholders.
REAL_RECIPE = REPO_ROOT / "examples" / "showcase" / "01-banking-core" / "datamimic.xml"

APPS = {"datamimic": cli_app, "datamimic-mcp": mcp_app}
# Lines starting with these are setup/tooling noise, not CLI invocations to validate.
NON_CLI_PREFIXES = ("pip", "python", "claude", "cd", "export")

runner = CliRunner()

FENCE_RE = re.compile(r"```(\w*)\n(.*?)```", re.S)
BRACKET_TOKEN_RE = re.compile(r"^\[.*\]\.{0,3}$")  # Click usage notation: [OPTIONS], [ARGS]...
PLACEHOLDER_RE = re.compile(r"^<(.*)>$")


def _substitute_placeholder(token: str) -> str:
    """Replace a `<...>` placeholder with a real file for descriptor-like args, else a name."""
    m = PLACEHOLDER_RE.match(token)
    if not m:
        return token
    inner = m.group(1).lower()
    if any(hint in inner for hint in ("xml", "descriptor", "path")):
        return str(REAL_RECIPE)
    return "placeholder-name"


def _tokens_from_bash_line(raw_line: str) -> list[str] | None:
    # Strip a trailing "# comment" (a '#' preceded by whitespace or at line start);
    # a bare '#' inside an option value never occurs in this corpus.
    line = re.split(r"(?<!\S)#", raw_line, maxsplit=1)[0].strip()
    if not line:
        return None
    tokens = line.split()
    if tokens[0] in NON_CLI_PREFIXES or tokens[0] not in APPS:
        return None
    args = [_substitute_placeholder(t) for t in tokens[1:] if not BRACKET_TOKEN_RE.match(t)]
    return [tokens[0], *args]


def _iter_command_configs(obj):
    """Walk a parsed JSON mcp config for any {"command": ..., "args": [...]} pair."""
    if isinstance(obj, dict):
        command, args = obj.get("command"), obj.get("args")
        if isinstance(command, str) and isinstance(args, list):
            yield command, [str(a) for a in args]
        for value in obj.values():
            yield from _iter_command_configs(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _iter_command_configs(value)


def _tokens_from_yaml_block(body: str) -> list[str] | None:
    # Small, boring parse: these mcp configs are always flat `command:` + inline-list `args:`.
    command_m = re.search(r"^\s*command:\s*(\S+)", body, re.M)
    args_m = re.search(r"^\s*args:\s*(\[.*\])", body, re.M)
    if not command_m or not args_m:
        return None
    return [command_m.group(1), *ast.literal_eval(args_m.group(1))]


def _extract_commands() -> list[tuple[str, list[str]]]:
    """Return (source_label, tokens) for every documented invocation across DOC_FILES."""
    commands: list[tuple[str, list[str]]] = []
    for path in DOC_FILES:
        text = path.read_text()
        for lang, body in FENCE_RE.findall(text):
            if lang == "bash":
                for raw_line in body.splitlines():
                    tokens = _tokens_from_bash_line(raw_line)
                    if tokens:
                        commands.append((f"{path.name} [bash] `{raw_line.strip()}`", tokens))
            elif lang == "json":
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    continue
                for command, args in _iter_command_configs(data):
                    if command in APPS:
                        commands.append((f"{path.name} [json] {command} {' '.join(args)}", [command, *args]))
            elif lang == "yaml":
                tokens = _tokens_from_yaml_block(body)
                if tokens and tokens[0] in APPS:
                    commands.append((f"{path.name} [yaml] {' '.join(tokens)}", tokens))
    return commands


def _cli_result(app, args: list[str]):
    """Invoke `args` against `app`, appending --help unless that would mask a real error.

    A missing/absent subcommand (empty args, or an option token where a subcommand
    should be) is exactly the case `--help` short-circuits past — so it is invoked
    as literally documented instead.
    """
    if not args or args[0].startswith("-"):
        return runner.invoke(app, args)
    return runner.invoke(app, [*args, "--help"])


def test_help_does_not_mask_bad_input():
    """Empirical precondition for this whole gate, pinned so a Click/Typer upgrade
    that changes this behavior fails loudly instead of silently green-lighting junk."""
    bad_subcommand = runner.invoke(mcp_app, ["badcmd", "--help"])
    assert bad_subcommand.exit_code != 0

    bad_option = runner.invoke(cli_app, ["lint", "--badopt", "--help"])
    assert bad_option.exit_code != 0


def test_mcp_serve_is_a_required_subcommand_regression_pin():
    """Regression pin for the historical collapse bug (fixed via the no-op
    `_root` callback in datamimic_ce/mcp/cli.py): a single-command Typer app
    with no callback collapses so the subcommand name becomes optional. That
    silently broke every `datamimic-mcp serve ...` doc and MCP client config
    the day a second command was ever added, and reverting the callback would
    silently do it again."""
    current_form = runner.invoke(mcp_app, ["serve", "--transport", "stdio", "--help"])
    assert current_form.exit_code == 0

    old_collapsed_form = runner.invoke(mcp_app, ["--transport", "stdio"])
    assert old_collapsed_form.exit_code != 0

    bare_no_subcommand = runner.invoke(mcp_app, [])
    assert bare_no_subcommand.exit_code != 0


def test_documented_commands_are_real():
    commands = _extract_commands()
    # Guard against the extractor silently matching nothing (a vacuous, always-green gate).
    assert len(commands) >= 20, f"only found {len(commands)} documented commands; extraction is likely broken"

    failures = []
    for label, tokens in commands:
        app = APPS[tokens[0]]
        result = _cli_result(app, tokens[1:])
        if result.exit_code != 0:
            last_line = result.output.strip().splitlines()[-1] if result.output.strip() else "<no output>"
            failures.append(f"{label} -> exit {result.exit_code}: {last_line}")

    assert not failures, "documented command(s) do not run against the real CLI:\n" + "\n".join(failures)


def test_real_execution_smoke():
    """A few documented commands are cheap enough to actually run (no servers)."""
    version = runner.invoke(cli_app, ["version"])
    assert version.exit_code == 0
    assert "DATAMIMIC version" in version.output

    caps = runner.invoke(cli_app, ["capabilities"])
    assert caps.exit_code == 0
    manifest = json.loads(caps.output)
    for key in ("elements", "generators", "entities", "converters", "targets", "distributions"):
        assert key in manifest

    # 01-banking-core carries two known DM315 (WARNING) hints; warnings alone don't
    # fail lint's default --fail-on=error threshold.
    lint = runner.invoke(cli_app, ["lint", str(REAL_RECIPE)])
    assert lint.exit_code == 0, lint.output
