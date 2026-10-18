# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Pure domain validation and diagnostic projection."""

from __future__ import annotations

from pydantic import JsonValue, ValidationError
from pydantic_core import ErrorDetails

from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId, Diagnostic, DiagnosticPhase


def validation_diagnostics(
    error: ValidationError,
    *,
    prefix: tuple[str | int, ...] = (),
    phase: DiagnosticPhase = DiagnosticPhase.MODEL,
    remediation: str = "Repair the canonical authoring model at the reported path.",
) -> tuple[Diagnostic, ...]:
    return tuple(
        Diagnostic(
            code=AuthoringRuleId.VALIDATION,
            phase=phase,
            message=_validation_message(item),
            path=(*prefix, *(_path_part(part) for part in item.get("loc", ()))),
            expected=_expected(item),
            actual=_actual(item),
            allowed_values=_allowed_values(item),
            remediation=remediation,
        )
        for item in error.errors()
    )


def _validation_message(item: ErrorDetails) -> str:
    """Front the field location in the message so an agent can repair without parsing `path`."""
    loc = item.get("loc", ())
    message = (
        "Input has an unsupported discriminator."
        if item.get("type") == "union_tag_invalid"
        else str(item.get("msg", "invalid authoring intent"))
    )
    location = ".".join(str(part) for part in loc)
    return f"{location}: {message}" if location else message


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
