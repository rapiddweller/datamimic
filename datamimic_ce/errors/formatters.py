# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from __future__ import annotations

import string

from datamimic_ce.errors.catalog import (
    ERROR_TEMPLATES,
    GUIDANCE_EMPTY_VALUE,
    GUIDANCE_IN_DATE_FORMAT,
    GUIDANCE_OUT_DATE_FORMAT,
    GUIDANCE_VALID_LOCALE,
    ErrorCode,
    IssueCode,
    get_issue_definition,
)
from datamimic_ce.errors.codes import IssueSeverity
from datamimic_ce.errors.context import DescriptorLocation
from datamimic_ce.errors.context.descriptor_identity import logical_descriptor_name
from datamimic_ce.errors.descriptor_contracts import DescriptorCarrierLike, DescriptorRootLike

DEFAULT_LOGGER_NAME = "DATAMIMIC"


def _sentence(text: str | None) -> str:
    if not text:
        return ""
    trimmed = str(text).strip()
    if not trimmed:
        return ""
    if trimmed[-1] in ".!?":
        return trimmed
    return f"{trimmed}."


def _format_issue(issue: str) -> str:
    # WHY: centralized normalization keeps user messages consistent and avoids duplication.
    return _sentence(issue) or "Unknown issue."


def _format_guidance(guidance: str | None) -> str:
    sentence = _sentence(guidance)
    return f" {sentence}" if sentence else ""


def code_prefix(error_code: ErrorCode, issue_code: IssueCode | None = None) -> str:
    # WHY: surface stable identifiers in logs for support, analytics, and UX mapping.
    if issue_code:
        return f"[{error_code.value}/{issue_code.value}] "
    return f"[{error_code.value}] "


def _cause_clause(cause: str | None) -> str:
    if not cause:
        return ""
    trimmed = str(cause).strip()
    return f": {trimmed}" if trimmed else ""


def _template_fields(template: str) -> set[str]:
    fields: set[str] = set()
    for _, field_name, _, _ in string.Formatter().parse(template):
        if not field_name:
            continue
        base = field_name.split(".", 1)[0].split("[", 1)[0]
        if base:
            fields.add(base)
    return fields


def element_label(
    *,
    element_tag: str | None = None,
    element_name: str | None = None,
    fallback: str = "element",
) -> str:
    if element_tag and element_name:
        return f"<{element_tag}> '{element_name}'"
    if element_tag:
        return f"<{element_tag}>"
    if element_name:
        return f"element '{element_name}'"
    return fallback


def issue_text(code: IssueCode, **kwargs: object) -> str:
    # WHY: catalog lookups centralize issue metadata and avoid legacy dicts.
    template = get_issue_definition(code).template
    # WHY: fail fast on template/kwargs drift to keep error messages consistent (SPOT).
    # WHY: runtime validation is intentional; unit tests act as the compile-time guard.
    expected = _template_fields(template)
    provided = set(kwargs.keys())
    missing = sorted(expected - provided)
    extra = sorted(provided - expected)
    if missing or extra:
        raise ValueError(
            f"IssueCode {code} template mismatch: missing={missing or '[]'}, "
            f"extra={extra or '[]'}, template='{template}'"
        )
    return template.format(**kwargs)


def _resolve_guidance(code: IssueCode, guidance: str | None) -> str | None:
    if get_issue_definition(code).severity is IssueSeverity.WARNING:
        raise ValueError(f"{code} is a WARNING-severity issue; use task_warning instead.")
    if guidance is None:
        return get_issue_definition(code).guidance
    return guidance


def descriptor_hint(
    ctx: DescriptorCarrierLike | DescriptorRootLike | None = None,
    descriptor_name: str | None = None,
) -> str:
    """Return a descriptor hint for user-facing error messages."""
    name = descriptor_name
    if name is None and isinstance(ctx, DescriptorCarrierLike):
        root = ctx.root
        name = root.descriptor_name if isinstance(root, DescriptorRootLike) else None
    if name is None and isinstance(ctx, DescriptorRootLike):
        name = ctx.descriptor_name
    if not isinstance(name, str):
        name = None
    if name is None:
        from datamimic_ce.errors.context.descriptor_identity import get_descriptor_name

        name = get_descriptor_name()
    name = logical_descriptor_name(name)
    return f" in descriptor '{name}'" if name else ""


def descriptor_hint_if_missing(
    message: str,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
) -> str:
    """Return a descriptor hint unless the message already contains one."""
    hint = descriptor_hint(ctx, descriptor_name)
    if not hint:
        return ""
    # Retain exported presentation deduplication; factories attach their own context directly.
    if message.rstrip(".!?:; ").endswith(hint):
        return ""
    return hint


def format_descriptor_location(location: DescriptorLocation | None) -> str:
    """Return normalized parse-location text for user-facing parser errors."""
    if location is None:
        return ""
    rendered = location.format().strip()
    return f" at {rendered}" if rendered else ""


def rule_error_message(
    expr: str,
    *,
    element_tag: str,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    kind: str = "condition",
    err_message: str | None = None,
    cause: str | None = None,
) -> str:
    """Format a user-facing rule evaluation message with descriptor context."""
    hint = descriptor_hint(ctx, descriptor_name)
    template = ERROR_TEMPLATES[ErrorCode.RULE_EVAL_FAILED]
    message = template.format(
        kind=kind,
        expr=expr,
        element_tag=element_tag,
        descriptor=hint,
        cause_clause=_cause_clause(cause),
    )
    return f"{code_prefix(ErrorCode.RULE_EVAL_FAILED)}{message}"


def datetime_conversion_message(
    *,
    element_tag: str,
    name: str,
    in_fmt: str | None,
    out_fmt: str | None,
    cause: str,
    input_empty: bool = False,
) -> str:
    fmt_parts: list[str] = []
    if in_fmt:
        fmt_parts.append(f"inDateFormat='{in_fmt}'")
    if out_fmt:
        fmt_parts.append(f"outDateFormat='{out_fmt}'")
    format_clause = f" ({', '.join(fmt_parts)})" if fmt_parts else ""

    guidance_parts: list[str] = []
    if in_fmt:
        guidance_parts.append(GUIDANCE_IN_DATE_FORMAT)
    if out_fmt and not in_fmt:
        guidance_parts.append(GUIDANCE_OUT_DATE_FORMAT)
    if input_empty:
        guidance_parts.append(GUIDANCE_EMPTY_VALUE)
    guidance = f" {' '.join(guidance_parts)}" if guidance_parts else ""

    template = ERROR_TEMPLATES[ErrorCode.DATETIME_CONVERSION_FAILED]
    message = template.format(
        element_tag=element_tag,
        name=name,
        format_clause=format_clause,
        cause=cause,
        guidance=guidance,
    )
    return f"{code_prefix(ErrorCode.DATETIME_CONVERSION_FAILED)}{message}"


def dataset_message(*, dataset: str | None, entity: str | None = None) -> str:
    entity_clause = f" for entity '{entity}'" if entity else ""
    template = ERROR_TEMPLATES[ErrorCode.INVALID_DATASET]
    message = template.format(dataset=dataset, entity_clause=entity_clause)
    return f"{code_prefix(ErrorCode.INVALID_DATASET)}{message}"


def locale_message(*, locale: str | None, entity: str | None = None) -> str:
    entity_clause = f" for entity '{entity}'" if entity else ""
    prefix = code_prefix(ErrorCode.INVALID_LOCALE)
    if locale is None or (isinstance(locale, str) and not locale.strip()):
        # WHY: empty locale errors should be explicit and actionable.
        return f"{prefix}Locale is empty{entity_clause}. {GUIDANCE_VALID_LOCALE}"
    locale_label = f"'{locale}'"
    template = ERROR_TEMPLATES[ErrorCode.INVALID_LOCALE]
    message = template.format(locale_label=locale_label, entity_clause=entity_clause, guidance=GUIDANCE_VALID_LOCALE)
    return f"{prefix}{message}"


def entity_init_error_message(*, var_name: str, entity: str, cause: str) -> str:
    template = ERROR_TEMPLATES[ErrorCode.ENTITY_INIT_FAILED]
    message = template.format(entity=entity, cause=cause)
    return f"{code_prefix(ErrorCode.ENTITY_INIT_FAILED)}Failed to execute <variable> '{var_name}': {message}"


def invalid_source_message(*, code: IssueCode, guidance: str | None = None, **kwargs: object) -> str:
    template = ERROR_TEMPLATES[ErrorCode.INVALID_SOURCE]
    issue = issue_text(code, **kwargs)
    guidance = _resolve_guidance(code, guidance)
    message = template.format(issue=_format_issue(issue), guidance=_format_guidance(guidance))
    return f"{code_prefix(ErrorCode.INVALID_SOURCE, code)}{message}"


def export_config_message(*, code: IssueCode, guidance: str | None = None, **kwargs: object) -> str:
    template = ERROR_TEMPLATES[ErrorCode.EXPORT_CONFIG]
    issue = issue_text(code, **kwargs)
    guidance = _resolve_guidance(code, guidance)
    message = template.format(issue=_format_issue(issue), guidance=_format_guidance(guidance))
    return f"{code_prefix(ErrorCode.EXPORT_CONFIG, code)}{message}"


def include_message(*, code: IssueCode, guidance: str | None = None, **kwargs: object) -> str:
    template = ERROR_TEMPLATES[ErrorCode.INCLUDE_ERROR]
    issue = issue_text(code, **kwargs)
    guidance = _resolve_guidance(code, guidance)
    message = template.format(issue=_format_issue(issue), guidance=_format_guidance(guidance))
    return f"{code_prefix(ErrorCode.INCLUDE_ERROR, code)}{message}"


def generator_config_message(
    *, code: IssueCode | None = None, reason: str | None = None, guidance: str | None = None, **kwargs: object
) -> str:
    template = ERROR_TEMPLATES[ErrorCode.GENERATOR_CONFIG]
    if code is None:
        if reason is None or not reason.strip() or guidance is not None or kwargs:
            raise ValueError("A constructor error requires only a non-empty reason, without issue fields or guidance")
        issue = reason
    else:
        if reason is not None:
            raise ValueError("A catalog error cannot also specify a constructor reason")
        issue = issue_text(code, **kwargs)
        guidance = _resolve_guidance(code, guidance)
    message = template.format(issue=_format_issue(issue), guidance=_format_guidance(guidance))
    return f"{code_prefix(ErrorCode.GENERATOR_CONFIG, code)}{message}"


def condition_evaluation_message(*, code: IssueCode, guidance: str | None = None, **kwargs: object) -> str:
    template = ERROR_TEMPLATES[ErrorCode.CONDITION_EVAL_FAILED]
    issue = issue_text(code, **kwargs)
    guidance = _resolve_guidance(code, guidance)
    message = template.format(issue=_format_issue(issue), guidance=_format_guidance(guidance))
    return f"{code_prefix(ErrorCode.CONDITION_EVAL_FAILED, code)}{message}"


def parser_validation_message(
    *, code: IssueCode, guidance: str | None = None, location: DescriptorLocation | None = None, **kwargs: object
) -> str:
    template = ERROR_TEMPLATES[ErrorCode.PARSER_VALIDATION]
    issue = issue_text(code, **kwargs)
    guidance = _resolve_guidance(code, guidance)
    message = template.format(
        issue=_format_issue(issue),
        guidance=_format_guidance(guidance),
    )
    message = f"{message}{format_descriptor_location(location)}"
    return f"{code_prefix(ErrorCode.PARSER_VALIDATION, code)}{message}"


def client_config_message(*, code: IssueCode, guidance: str | None = None, **kwargs: object) -> str:
    template = ERROR_TEMPLATES[ErrorCode.CLIENT_CONFIG]
    issue = issue_text(code, **kwargs)
    guidance = _resolve_guidance(code, guidance)
    message = template.format(issue=_format_issue(issue), guidance=_format_guidance(guidance))
    return f"{code_prefix(ErrorCode.CLIENT_CONFIG, code)}{message}"


def runtime_config_message(*, code: IssueCode, guidance: str | None = None, **kwargs: object) -> str:
    template = ERROR_TEMPLATES[ErrorCode.RUNTIME_CONFIG]
    issue = issue_text(code, **kwargs)
    guidance = _resolve_guidance(code, guidance)
    message = template.format(issue=_format_issue(issue), guidance=_format_guidance(guidance))
    return f"{code_prefix(ErrorCode.RUNTIME_CONFIG, code)}{message}"


def task_config_message(*, code: IssueCode, guidance: str | None = None, **kwargs: object) -> str:
    template = ERROR_TEMPLATES[ErrorCode.TASK_CONFIG]
    issue = issue_text(code, **kwargs)
    guidance = _resolve_guidance(code, guidance)
    message = template.format(issue=_format_issue(issue), guidance=_format_guidance(guidance))
    return f"{code_prefix(ErrorCode.TASK_CONFIG, code)}{message}"


def warning_message(*, code: IssueCode, **kwargs: object) -> str:
    """Render a WARNING-severity issue: ``[Wxxx] <templated text>`` (no error-category framing)."""
    return f"[{code.value}] {issue_text(code, **kwargs)}"


def operation_message(*, code: IssueCode, guidance: str | None = None, **kwargs: object) -> str:
    template = ERROR_TEMPLATES[ErrorCode.OPERATION_ERROR]
    issue = issue_text(code, **kwargs)
    guidance = _resolve_guidance(code, guidance)
    message = template.format(issue=_format_issue(issue), guidance=_format_guidance(guidance))
    return f"{code_prefix(ErrorCode.OPERATION_ERROR, code)}{message}"


def invalid_locale_message(locale: str) -> str:
    return locale_message(locale=locale)
