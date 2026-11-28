# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Pure domain validation and diagnostic projection."""

from __future__ import annotations

import re

from pydantic import JsonValue, ValidationError
from pydantic_core import ErrorDetails

from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId, Diagnostic, DiagnosticLocation, DiagnosticPhase
from datamimic_ce.authoring.domain.expectations import expectation_repair


def validation_diagnostics(
    error: ValidationError,
    *,
    prefix: tuple[str | int, ...] = (),
    phase: DiagnosticPhase = DiagnosticPhase.MODEL,
    remediation: str = "Repair the canonical authoring model at the reported path.",
) -> tuple[Diagnostic, ...]:
    diagnostics = []
    for item in error.errors():
        path = (*prefix, *(_path_part(part) for part in item.get("loc", ())))
        diagnostics.append(
            Diagnostic(
                code=AuthoringRuleId.VALIDATION,
                phase=phase,
                message=_validation_message(item),
                path=path,
                location=_syntax_location(item, prefix),
                expected=_expected(item),
                actual=_actual(item),
                allowed_values=_allowed_values(item),
                # A malformed expectation gets the shape of its kind; the path holds field names only.
                remediation=expectation_repair(path) or _syntax_remediation(item, prefix) or remediation,
            )
        )
    return tuple(diagnostics)


def _syntax_remediation(item: ErrorDetails, prefix: tuple[str | int, ...]) -> str | None:
    if item.get("type") != "json_invalid":
        return None
    source = f" of {prefix[0]}" if prefix else ""
    return f"Fix the JSON syntax{source} at the reported position."


def _syntax_location(item: ErrorDetails, prefix: tuple[str | int, ...]) -> DiagnosticLocation | None:
    if item["type"] != "json_invalid":
        return None
    # pydantic-core renders the parser position at the end of the JSON syntax error.
    match = re.search(r" at line (\d+) column (\d+)$", item["msg"])
    if match is None:
        return None
    return DiagnosticLocation(
        file=prefix[0] if prefix and isinstance(prefix[0], str) else None,
        line=int(match[1]),
        column=int(match[2]),
    )


def _validation_message(item: ErrorDetails) -> str:
    match item.get("type"):
        case "union_tag_invalid":
            return "Input has an unsupported discriminator."
        case "json_invalid":
            return "Input is not valid JSON."
        case _:
            return str(item.get("msg", "Invalid authoring intent."))


def _path_part(value: object) -> str | int:
    return value if isinstance(value, str | int) else str(value)


def _allowed_values(item: ErrorDetails) -> tuple[JsonValue, ...] | None:
    """Return only structured validator facts; never parse Pydantic message text."""
    context = item.get("ctx") or {}
    context_key = "expected_tags" if item.get("type") == "union_tag_invalid" else "expected"
    raw_values = context.get(context_key)
    if item.get("type") in {"union_tag_invalid", "enum", "literal_error", "authoring_enum"} and isinstance(
        raw_values, list | tuple
    ):
        values = tuple(value for value in raw_values if isinstance(value, str | int | float | bool) or value is None)
        return values or None
    return None


def _expected(item: ErrorDetails) -> JsonValue | None:
    allowed = _allowed_values(item)
    if allowed is not None:
        return list(allowed)
    context = item.get("ctx") or {}
    for key in ("expected", "ge", "gt", "le", "lt", "min_length", "max_length"):
        value = context.get(key)
        if value is not None and isinstance(value, str | int | float | bool):
            return value
    return None


def _actual(item: ErrorDetails) -> JsonValue | None:
    # Validation inputs can contain profile credentials and tokens.
    return None
