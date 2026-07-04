# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
"""Gate: `path/to/file.py:NNN` anchors in docs/internal/review-181.md still
point at a real file and a line within it, and — where the same sentence also
names a backticked python identifier (e.g. `_RUNTIME_HINTS`) — that identifier
still lives near the anchored line. Refactors renumber lines silently; this
catches the anchor drifting without anyone noticing.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "internal" / "review-181.md"

# `path/to/file.py:NNN` — requires a directory component, so a bare `dryrun.py:219`
# (explicitly marked "pre-change" in the doc, i.e. a historical, not current, anchor)
# is deliberately not treated as a checkable anchor.
ANCHOR_RE = re.compile(r"`([\w./]+/[\w.]+\.py):(\d+)`")

# A backticked token that reads as a real python identifier or dotted attribute
# chain (`_RUNTIME_HINTS`, `TaskUtil.create_converter_list`) — not a quoted error
# message (has spaces), a keyword=value (has '='), or a bare filename.
BACKTICK_RE = re.compile(r"`([^`]+)`")
IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
FILE_EXTENSIONS = {"py", "xml", "json", "md", "yaml", "yml", "txt"}
WINDOW_CHARS = 400  # doc characters scanned before/after an anchor for its identifier
LINE_WINDOW = 40  # +/- lines in the source file the identifier must appear within


def _is_identifier_candidate(token: str) -> bool:
    if not IDENTIFIER_RE.fullmatch(token):
        return False
    parts = token.split(".")
    # Reject look-alike filenames such as `test_dryrun.py` (last segment is an extension).
    return not (len(parts) > 1 and parts[-1].lower() in FILE_EXTENSIONS)


def _find_anchors() -> list[tuple[str, int, list[str]]]:
    text = DOC_PATH.read_text()
    anchors = []
    for match in ANCHOR_RE.finditer(text):
        rel_path, line_s = match.group(1), match.group(2)
        window = text[max(0, match.start() - WINDOW_CHARS) : match.end() + WINDOW_CHARS // 2]
        identifiers = [
            tok for tok in BACKTICK_RE.findall(window) if tok != rel_path and _is_identifier_candidate(tok)
        ]
        anchors.append((rel_path, int(line_s), identifiers))
    return anchors


def test_anchor_extraction_finds_a_reasonable_number():
    anchors = _find_anchors()
    # Guard against the regex silently matching nothing (a vacuous, always-green gate).
    assert len(anchors) >= 3, f"only found {len(anchors)} anchors in review-181.md; extraction is likely broken"


def test_anchors_resolve():
    anchors = _find_anchors()
    assert anchors, "no anchors parsed — see previous test"

    for rel_path, line_no, identifiers in anchors:
        target = REPO_ROOT / rel_path
        assert target.is_file(), (
            f"anchor `{rel_path}:{line_no}` in docs/internal/review-181.md drifted: "
            f"{rel_path} no longer exists. Refresh the anchor against the current source."
        )

        source_lines = target.read_text().splitlines()
        assert line_no <= len(source_lines), (
            f"anchor `{rel_path}:{line_no}` in docs/internal/review-181.md drifted: "
            f"{rel_path} only has {len(source_lines)} lines. Refresh the line number "
            f"(e.g. grep the quoted message/identifier in the current file)."
        )

        lo, hi = max(0, line_no - 1 - LINE_WINDOW), min(len(source_lines), line_no + LINE_WINDOW)
        nearby_text = "\n".join(source_lines[lo:hi])
        for identifier in identifiers:
            # A dotted chain like TaskUtil.create_converter_list won't appear verbatim
            # at a call site; its last component (the actual symbol) will.
            symbol = identifier.rsplit(".", 1)[-1]
            assert symbol in nearby_text, (
                f"anchor `{rel_path}:{line_no}` in docs/internal/review-181.md drifted: "
                f"`{identifier}` does not appear within +/-{LINE_WINDOW} lines of {line_no} "
                f"in {rel_path} any more. Refresh the line number to where `{symbol}` "
                f"actually is now (e.g. `grep -n {symbol} {rel_path}`)."
            )
