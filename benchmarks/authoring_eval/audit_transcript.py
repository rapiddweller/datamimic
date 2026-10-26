# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Audit a sub-agent transcript (#412) for forbidden actions; a run with a finding does not count.

    python -m benchmarks.authoring_eval.audit_transcript <transcript.jsonl> --allow <run-dir> --allow <venv> \
        --forbid <repository-root>

The transcript is Claude Code JSONL. Only the tool calls of assistant messages are examined: the brief itself
names the forbidden things. Limit: the shell is read for absolute and ``~`` paths only; relative paths and
paths built by variables or commands are not resolved."""

import argparse
import json
import os
import re
import sys
from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

_SKILL_TOOL = "Skill"
_SHELL_TOOL = "Bash"
_PATH_KEYS = ("file_path", "path", "notebook_path")
_PATTERN_KEYS = ("pattern",)
_AGENTS_FILE = "agents.md"
_SYSTEM_PATHS = (Path("/usr"), Path("/bin"), Path("/dev/null"))
# An absolute or home path in a shell command; a letter, dot or slash before the slash means a relative path or a URL.
_SHELL_PATH = re.compile(r"(?<![\w.:/$~-])(?:~?/)[^\s'\"|;&<>()`$]*")


class FindingKind(StrEnum):
    SKILL = "skill"
    AGENTS_FILE = "agents_file"
    FORBIDDEN_ROOT = "forbidden_root"
    OUTSIDE_ALLOWED = "outside_allowed"


@dataclass(frozen=True)
class Finding:
    line: int
    kind: FindingKind
    tool: str
    detail: str


def _tool_calls(transcript: Path) -> Iterator[tuple[int, str, dict[str, object]]]:
    """(line number, tool name, tool input) for every tool call the agent made."""
    # iterate the file, not str.splitlines(): that also splits on U+2028 and form feeds inside JSON strings
    with transcript.open(encoding="utf-8") as lines:
        for number, text in enumerate(lines, start=1):
            message = json.loads(text).get("message") if text.strip() else None
            if not isinstance(message, dict) or message.get("role") != "assistant":
                continue
            content = message.get("content")
            for block in content if isinstance(content, list) else []:
                if block.get("type") == "tool_use":
                    yield number, block["name"], block["input"]


def _is_path(candidate: str) -> bool:
    """Regex and sed patterns such as /def/,/p/ and the `/>` of XML look like paths; a real path starts in an existing
    top directory."""
    return candidate.startswith("~") or (candidate != "/" and os.path.lexists("/" + candidate.split("/")[1]))


def _paths(tool: str, tool_input: dict[str, object]) -> list[str]:
    if tool == _SHELL_TOOL:
        command = tool_input.get("command")
        return [path for path in _SHELL_PATH.findall(command) if _is_path(path)] if isinstance(command, str) else []
    return [value for key in _PATH_KEYS if isinstance(value := tool_input.get(key), str) and os.path.isabs(value)]


def _scanned_text(tool: str, tool_input: dict[str, object]) -> list[str]:
    keys = ("command",) if tool == _SHELL_TOOL else _PATH_KEYS + _PATTERN_KEYS
    return [value for key in keys if isinstance(value := tool_input.get(key), str)]


def _under(path: str, roots: Sequence[Path]) -> bool:
    # normpath, not realpath: a venv's python is a symlink to a path outside the venv
    candidate = Path(os.path.normpath(os.path.expanduser(path)))
    return any(candidate.is_relative_to(root) for root in roots)


def _spellings(roots: Sequence[Path]) -> list[Path]:
    """Each root as given and with symlinks resolved, because /tmp and /private/tmp name the same place."""
    return [Path(os.path.normpath(root)) for root in roots] + [Path(os.path.realpath(root)) for root in roots]


def audit(transcript: Path, allow: Sequence[Path], forbid: Sequence[Path]) -> list[Finding]:
    allowed = _spellings(allow) + list(_SYSTEM_PATHS)
    forbidden = _spellings(forbid)
    findings = []
    for line, tool, tool_input in _tool_calls(transcript):
        if tool == _SKILL_TOOL:
            findings.append(Finding(line, FindingKind.SKILL, tool, str(tool_input.get("skill", ""))))
        if any(_AGENTS_FILE in text.casefold() for text in _scanned_text(tool, tool_input)):
            findings.append(Finding(line, FindingKind.AGENTS_FILE, tool, "mentions AGENTS.md"))
        for path in _paths(tool, tool_input):
            if _under(path, forbidden):
                findings.append(Finding(line, FindingKind.FORBIDDEN_ROOT, tool, path))
            if not _under(path, allowed):
                findings.append(Finding(line, FindingKind.OUTSIDE_ALLOWED, tool, path))
    return findings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m benchmarks.authoring_eval.audit_transcript")
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--allow", type=Path, action="append", required=True, help="the run directory and the venv")
    parser.add_argument("--forbid", type=Path, action="append", default=[], help="a root the agent must not touch")
    arguments = parser.parse_args(argv)
    findings = audit(arguments.transcript, arguments.allow, arguments.forbid)
    print(json.dumps({"clean": not findings, "findings": [asdict(finding) for finding in findings]}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
