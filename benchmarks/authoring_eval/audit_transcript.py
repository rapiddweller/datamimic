# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Audit a sub-agent transcript (#412) for forbidden actions; a run with a finding does not count.

    python -m benchmarks.authoring_eval.audit_transcript <transcript.jsonl> --allow <run-dir> \
        --allow <venv>/bin/datamimic --forbid <repository-root> [--canary <token>]

The transcript is Claude Code JSONL. The tool calls of assistant messages are examined: a tool outside the
allowlist, a path outside the allowed roots, a mention of AGENTS.md. The canary token is searched in every line,
tool results included. An absolute ``Glob`` pattern is checked from its root. Limit: the shell is read for absolute
and ``~/`` paths only; relative paths, globs, a bare ``~`` or ``/``, and paths built by variables or commands are not
resolved (README, "Void runs")."""

import argparse
import json
import os
import re
import sys
from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

# The only tools a subject gets; the runner passes the same set to `claude --tools`.
ALLOWED_TOOLS = ("Bash", "Read", "Write", "Edit", "Glob", "Grep")
_SHELL_TOOL = "Bash"
_GLOB_TOOL = "Glob"
_PATH_KEYS = ("file_path", "path", "notebook_path")
_PATTERN_KEYS = ("pattern",)
_AGENTS_FILE = "agents.md"
_SYSTEM_PATHS = (Path("/usr"), Path("/bin"), Path("/dev/null"))
# An absolute or home path in a shell command; a letter, dot or slash before the slash means a relative path or a URL.
_SHELL_PATH = re.compile(r"(?<![\w.:/$~-])(?:~?/)[^\s'\"|;&<>()`$]*")
_GLOB_CHAR = re.compile(r"[*?[{]")


class FindingKind(StrEnum):
    TOOL = "tool"
    AGENTS_FILE = "agents_file"
    FORBIDDEN_ROOT = "forbidden_root"
    OUTSIDE_ALLOWED = "outside_allowed"
    CANARY = "canary"
    UNREADABLE = "unreadable"  # a line that is not one JSON object can hide a tool call


@dataclass(frozen=True)
class Finding:
    line: int
    kind: FindingKind
    tool: str
    detail: str


def records(transcript: Path) -> Iterator[tuple[int, dict[str, Any] | None]]:
    """(line number, record) for every line that is not blank; the record is None when the line is not a JSON object."""
    # iterate the file, not str.splitlines(): that also splits on U+2028 and form feeds inside JSON strings.
    # errors="replace": a broken byte must not lose the report.
    with transcript.open(encoding="utf-8", errors="replace") as lines:
        for number, text in enumerate(lines, start=1):
            if not text.strip():
                continue
            try:
                record = json.loads(text)
            except ValueError:
                record = None
            yield number, record if isinstance(record, dict) else None


def tool_calls(transcript: Path) -> Iterator[tuple[int, str, dict[str, object]]]:
    """(line number, tool name, tool input) for every tool call the agent made."""
    for number, record in records(transcript):
        message = record.get("message") if record else None
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        content = message.get("content")
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                yield number, block["name"], block["input"]


def _is_path(candidate: str) -> bool:
    """Regex and sed patterns such as /def/,/p/, the `/>` of XML and Python's `//` look like paths; a real path starts
    in an existing top directory. POSIX reads `//etc` as `/etc`."""
    top = candidate.lstrip("/").split("/")[0]
    return candidate.startswith("~") or (top != "" and os.path.lexists("/" + top))


def _glob_root(pattern: str) -> str:
    """The directory a glob pattern searches: up to the last slash before the first glob character. After a glob
    character, `..` can climb anywhere (`**` can match no directory), so that pattern searches from /."""
    glob = _GLOB_CHAR.search(pattern)
    if glob is None:
        return pattern
    if ".." in Path(pattern[glob.start() :]).parts:
        return "/"
    return pattern[: glob.start()].rsplit("/", 1)[0] or "/"


def _paths(tool: str, tool_input: dict[str, object]) -> list[str]:
    if tool == _SHELL_TOOL:
        command = tool_input.get("command")
        return [path for path in _SHELL_PATH.findall(command) if _is_path(path)] if isinstance(command, str) else []
    paths = [value for key in _PATH_KEYS if isinstance(value := tool_input.get(key), str)]
    if tool == _GLOB_TOOL and isinstance(pattern := tool_input.get("pattern"), str) and _absolute(pattern):
        paths.append(_glob_root(pattern))
    return [path for path in paths if _absolute(path)]


def _absolute(path: str) -> bool:
    """A relative path resolves in the run directory (or in the Glob path); ~ is the home directory."""
    return os.path.isabs(path) or path.startswith("~")


def _scanned_text(tool: str, tool_input: dict[str, object]) -> list[str]:
    keys = ("command",) if tool == _SHELL_TOOL else _PATH_KEYS + _PATTERN_KEYS
    return [value for key in keys if isinstance(value := tool_input.get(key), str)]


def _under(path: str, roots: Sequence[Path]) -> bool:
    # normpath, not realpath: a venv's python is a symlink to a path outside the venv
    # normpath keeps a leading double slash (POSIX), so //usr and /usr would differ
    candidate = (
        Path("/" + os.path.normpath(os.path.expanduser(path)).lstrip("/"))
        if path.startswith("/")
        else Path(os.path.normpath(os.path.expanduser(path)))
    )
    return any(candidate.is_relative_to(root) for root in roots)


def spellings(roots: Sequence[Path]) -> list[Path]:
    """Each root as given and with symlinks resolved, because /tmp and /private/tmp name the same place."""
    return [Path(os.path.normpath(root)) for root in roots] + [Path(os.path.realpath(root)) for root in roots]


def audit(transcript: Path, allow: Sequence[Path], forbid: Sequence[Path], canary: str | None = None) -> list[Finding]:
    allowed = spellings(allow) + list(_SYSTEM_PATHS)
    forbidden = spellings(forbid)
    findings = [
        Finding(number, FindingKind.UNREADABLE, "", "line is not a JSON object")
        for number, record in records(transcript)
        if record is None
    ]
    for line, tool, tool_input in tool_calls(transcript):
        if tool not in ALLOWED_TOOLS:
            findings.append(Finding(line, FindingKind.TOOL, tool, "tool outside the allowlist"))
        if any(_AGENTS_FILE in text.casefold() for text in _scanned_text(tool, tool_input)):
            findings.append(Finding(line, FindingKind.AGENTS_FILE, tool, "mentions AGENTS.md"))
        for path in _paths(tool, tool_input):
            if _under(path, forbidden):
                findings.append(Finding(line, FindingKind.FORBIDDEN_ROOT, tool, path))
            if not _under(path, allowed):
                detail = f"{path}: an access attempt outside the allowed roots, also if it does not exist"
                findings.append(Finding(line, FindingKind.OUTSIDE_ALLOWED, tool, detail))
    with transcript.open(encoding="utf-8", errors="replace") as lines:
        findings += [
            Finding(number, FindingKind.CANARY, "", "canary token in the transcript")
            for number, text in enumerate(lines, start=1)
            if canary and canary in text
        ]
    return findings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m benchmarks.authoring_eval.audit_transcript")
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--allow", type=Path, action="append", required=True, help="the run dir, <venv>/bin/datamimic")
    parser.add_argument("--forbid", type=Path, action="append", default=[], help="a root the agent must not touch")
    parser.add_argument("--canary", help="a token that only a leaked instruction file holds")
    arguments = parser.parse_args(argv)
    findings = audit(arguments.transcript, arguments.allow, arguments.forbid, arguments.canary)
    print(json.dumps({"clean": not findings, "findings": [asdict(finding) for finding in findings]}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
