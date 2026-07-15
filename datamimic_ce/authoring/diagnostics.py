# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Diagnostic contract ("diagnostics v1") shared by the CLI and the MCP tools."""

from typing import TypeAlias

from pydantic import BaseModel, Field

from datamimic_ce.model.constraints import RuleSeverity

# Backwards-compatible public name; the enum itself is owned by the rule SPOT.
Severity: TypeAlias = RuleSeverity


class Diagnostic(BaseModel):
    """One finding, always actionable: what is wrong AND what to do differently."""

    rule: str  # e.g. "DM301"
    severity: Severity
    message: str
    fix_hint: str  # never empty — the agent's next edit
    element: str  # tag, e.g. "generate"
    path: str  # lxml getpath, e.g. "/setup/generate[2]/key[3]"
    name: str | None = None  # name/id attribute of the element, if present
    line: int | None = None
    docs: str | None = None  # e.g. "reference://element/generate" — resolvable via the reference tool


class LintResult(BaseModel):
    ok: bool  # True when no ERROR diagnostics (warnings/hints allowed)
    file: str | None = None
    counts: dict[str, int] = Field(default_factory=dict)  # per-severity totals (pre-truncation)
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    truncated: int = 0  # diagnostics dropped beyond the caller's cap

    @classmethod
    def from_diagnostics(
        cls, diagnostics: list[Diagnostic], *, file: str | None = None, max_diagnostics: int | None = None
    ) -> "LintResult":
        counts: dict[str, int] = {}
        for diag in diagnostics:
            counts[diag.severity.value] = counts.get(diag.severity.value, 0) + 1
        kept = diagnostics if max_diagnostics is None else diagnostics[:max_diagnostics]
        return cls(
            ok=counts.get(Severity.ERROR.value, 0) == 0,
            file=file,
            counts=counts,
            diagnostics=kept,
            truncated=len(diagnostics) - len(kept),
        )

    def summary(self) -> str:
        parts = [
            f"{self.counts.get(sev.value, 0)} {sev.value}{'s' if self.counts.get(sev.value, 0) != 1 else ''}"
            for sev in Severity
            if self.counts.get(sev.value, 0)
        ]
        return ", ".join(parts) if parts else "no findings"


def _diagnostic_dicts(diagnostics: list[Diagnostic], detailed: bool) -> list[dict[str, object]]:
    """Serialize diagnostics to dicts, optionally filtering to concise fields.

    Args:
        diagnostics: List of Diagnostic objects
        detailed: If True, return full diagnostic dicts; if False, only concise fields

    Returns:
        List of diagnostic dicts (rule, severity, line, message, fix_hint when detailed=False)
    """
    concise_fields = ("rule", "severity", "line", "message", "fix_hint")
    out: list[dict[str, object]] = []
    for diag in diagnostics:
        data: dict[str, object] = diag.model_dump()
        msg = data.get("message", "")
        if isinstance(msg, str):
            data["message"] = msg[:300]  # truncate long messages
        if not detailed:
            data = {key: data[key] for key in concise_fields if key in data}
        out.append(data)
    return out
