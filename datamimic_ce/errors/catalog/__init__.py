# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.errors.catalog.client_errors import ISSUES as _CLIENT_ERRORS
from datamimic_ce.errors.catalog.condition_errors import ISSUES as _CONDITION_ERRORS
from datamimic_ce.errors.catalog.definition import IssueDefinition
from datamimic_ce.errors.catalog.exporter_errors import ISSUES as _EXPORTER_ERRORS
from datamimic_ce.errors.catalog.generator_errors import ISSUES as _GENERATOR_ERRORS
from datamimic_ce.errors.catalog.guidance import (
    FILE_LOOKUP_PATTERN,
    GUIDANCE_COUNT_SCOPE,
    GUIDANCE_EMPTY_VALUE,
    GUIDANCE_FILE_LOOKUP,
    GUIDANCE_IN_DATE_FORMAT,
    GUIDANCE_LOOKUP_POINTER,
    GUIDANCE_OUT_DATE_FORMAT,
    GUIDANCE_SCRIPT_BUILTIN,
    GUIDANCE_VALID_LOCALE,
    GUIDANCE_WHERE_SCOPE,
)
from datamimic_ce.errors.catalog.include_errors import ISSUES as _INCLUDE_ERRORS
from datamimic_ce.errors.catalog.operation_errors import ISSUES as _OPERATION_ERRORS
from datamimic_ce.errors.catalog.parser_errors import ISSUES as _PARSER_ERRORS
from datamimic_ce.errors.catalog.source_errors import ISSUES as _SOURCE_ERRORS
from datamimic_ce.errors.catalog.state_machine_errors import ISSUES as _STATE_MACHINE_ERRORS
from datamimic_ce.errors.catalog.task_errors import ISSUES as _TASK_ERRORS
from datamimic_ce.errors.catalog.warnings import ISSUES as _WARNINGS
from datamimic_ce.errors.codes import ErrorCode, IssueCode, IssueSeverity

ISSUE_DEFINITIONS: list[IssueDefinition] = [
    *_CLIENT_ERRORS,
    *_CONDITION_ERRORS,
    *_EXPORTER_ERRORS,
    *_GENERATOR_ERRORS,
    *_INCLUDE_ERRORS,
    *_OPERATION_ERRORS,
    *_PARSER_ERRORS,
    *_SOURCE_ERRORS,
    *_STATE_MACHINE_ERRORS,
    *_TASK_ERRORS,
    *_WARNINGS,
]

_ISSUE_DEFINITIONS_BY_CODE = {issue.code: issue for issue in ISSUE_DEFINITIONS}


def get_issue_definition(code: IssueCode) -> IssueDefinition:
    return _ISSUE_DEFINITIONS_BY_CODE[code]


ERROR_TEMPLATES: dict[ErrorCode, str] = {
    ErrorCode.INVALID_DATASET: (
        "Dataset '{dataset}' is not supported{entity_clause}. Use a supported 2-letter dataset"
        " code (e.g., US) or remove the dataset attribute to use the default."
    ),
    ErrorCode.INVALID_LOCALE: "Locale {locale_label} is not supported{entity_clause}. {guidance}",
    ErrorCode.DATETIME_CONVERSION_FAILED: (
        "Failed to convert datetime value of <{element_tag}> '{name}'{format_clause}: {cause}{guidance}"
    ),
    ErrorCode.ENTITY_INIT_FAILED: "Can't create entity '{entity}': {cause}",
    ErrorCode.RULE_EVAL_FAILED: "Failed to evaluate {kind} '{expr}' for <{element_tag}>{descriptor}{cause_clause}",
    ErrorCode.INVALID_SOURCE: "Invalid source: {issue}{guidance}",
    ErrorCode.EXPORT_CONFIG: "Invalid exporter configuration: {issue}{guidance}",
    ErrorCode.INCLUDE_ERROR: "Include failed: {issue}{guidance}",
    ErrorCode.GENERATOR_CONFIG: "Invalid generator configuration: {issue}{guidance}",
    ErrorCode.CONDITION_EVAL_FAILED: "Invalid <condition>: {issue}{guidance}",
    ErrorCode.PARSER_VALIDATION: "Descriptor validation error: {issue}{guidance}",
    ErrorCode.CLIENT_CONFIG: "Invalid client configuration: {issue}{guidance}",
    ErrorCode.TASK_CONFIG: "Invalid task configuration: {issue}{guidance}",
    ErrorCode.OPERATION_ERROR: "Operation failed: {issue}{guidance}",
    ErrorCode.RUNTIME_CONFIG: "Invalid runtime configuration: {issue}{guidance}",
}


def invalid_locale_text(locale: str) -> str:
    return ERROR_TEMPLATES[ErrorCode.INVALID_LOCALE].format(
        locale_label=repr(locale),
        entity_clause="",
        guidance=GUIDANCE_VALID_LOCALE,
    )


__all__ = [
    "ErrorCode",
    "IssueCode",
    "IssueSeverity",
    "IssueDefinition",
    "ISSUE_DEFINITIONS",
    "get_issue_definition",
    "invalid_locale_text",
    "ERROR_TEMPLATES",
    "FILE_LOOKUP_PATTERN",
    "GUIDANCE_COUNT_SCOPE",
    "GUIDANCE_EMPTY_VALUE",
    "GUIDANCE_FILE_LOOKUP",
    "GUIDANCE_IN_DATE_FORMAT",
    "GUIDANCE_LOOKUP_POINTER",
    "GUIDANCE_OUT_DATE_FORMAT",
    "GUIDANCE_SCRIPT_BUILTIN",
    "GUIDANCE_WHERE_SCOPE",
    "GUIDANCE_VALID_LOCALE",
]
