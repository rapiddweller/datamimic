# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""DM4xx — cross-statement rules: references between elements the engine only
checks at runtime (unknown targets) or not at all (duplicate names)."""

import ast
from collections.abc import Iterable
from dataclasses import dataclass

from lxml import etree

from datamimic_ce.authoring.diagnostics import Diagnostic
from datamimic_ce.authoring.rule_catalog import authoring_rule_definition
from datamimic_ce.authoring.rules.base import LintContext, Rule
from datamimic_ce.constants.element_constants import (
    EL_DATABASE,
    EL_ELEMENT,
    EL_GENERATE,
    EL_ID,
    EL_INCLUDE,
    EL_ITERATE,
    EL_KEY,
    EL_MEMSTORE,
    EL_MONGODB,
    EL_NESTED_KEY,
    EL_REFERENCE,
    EL_VARIABLE,
)
from datamimic_ce.constants.exporter_constants import (
    EXPORTER_CONSOLE_EXPORTER,
    EXPORTER_LOG_EXPORTER,
    EXPORTER_TEST_RESULT_EXPORTER,
)
from datamimic_ce.enums.operation_enums import ExportOperation
from datamimic_ce.exporters.exporter_util import ExporterUtil, buffered_exporter_names
from datamimic_ce.model.constraints import (
    DynamicSourceKind,
    SourceFileFormat,
    source_allows_client,
    source_allows_memstore,
    source_dynamic_kind,
    source_file_format,
    source_file_format_for,
    supported_source_file_formats,
)

_GENERATES = (EL_GENERATE, EL_ITERATE)
_SOURCE_READERS = (*_GENERATES, EL_VARIABLE, EL_NESTED_KEY, EL_KEY, EL_ID, EL_ELEMENT, EL_REFERENCE)
_STATIC_TARGETS = {
    *buffered_exporter_names(),
    EXPORTER_CONSOLE_EXPORTER,
    EXPORTER_LOG_EXPORTER,
    EXPORTER_TEST_RESULT_EXPORTER,
}
# Dotted <clientId>.<op> write operations, derived from the engine's own enum so
# this rule cannot drift from what the exporter boundary accepts (SPOT).
_CLIENT_OPERATIONS = {op.value for op in ExportOperation}


def _declared_ids(ctx: LintContext) -> tuple[set[str], set[str]]:
    """(client ids, memstore ids) declared in the descriptor."""
    clients = {el.get("id") for el in ctx.iter(EL_DATABASE, EL_MONGODB) if el.get("id")}
    memstores = {el.get("id") for el in ctx.iter(EL_MEMSTORE) if el.get("id")}
    return {c for c in clients if c}, {m for m in memstores if m}


def _is_python_source_expression(source: str) -> bool:
    """Mirror VariableTask's lazy ``evaluate_python_expression`` syntax gate."""
    try:
        ast.parse(source, mode="eval")
    except SyntaxError:
        return False
    return True


@dataclass(frozen=True)
class _SourceDiagnostic:
    evidence: str
    fix_context: str


def _source_is_declared(
    source: str,
    element_tag: str,
    source_type: str | None,
    clients: set[str],
    memstores: set[str],
) -> bool:
    return (
        source_file_format_for(element_tag, source, source_type) is not None
        or (source in clients and source_allows_client(element_tag, source_type))
        or (source in memstores and source_allows_memstore(element_tag, source_type))
    )


def _dynamic_source_is_valid(
    source: str,
    element_tag: str,
    source_type: str | None,
) -> bool:
    dynamic_kind = source_dynamic_kind(element_tag, source_type)
    if dynamic_kind is DynamicSourceKind.BRACED_EXPRESSION:
        return source.startswith("{") and source.endswith("}")
    if dynamic_kind is DynamicSourceKind.PYTHON_EXPRESSION:
        return _is_python_source_expression(source)
    return False


def _unsupported_file_source_diagnostic(
    element_tag: str,
    source_type: str | None,
    known_format: SourceFileFormat,
) -> _SourceDiagnostic:
    supported = supported_source_file_formats(element_tag, source_type)
    allowed = ", ".join(file_format.value for file_format in supported) if supported else "no file formats"
    return _SourceDiagnostic(
        evidence=(
            f'<{element_tag}> type="{source_type}" does not support source suffix '
            f"'{known_format.value}' (allowed: {allowed})"
        ),
        fix_context=f"Use a source format supported by <{element_tag}> or another source element.",
    )


def _unknown_source_diagnostic(
    source: str,
    element_tag: str,
    source_type: str | None,
    clients: set[str],
    memstores: set[str],
) -> _SourceDiagnostic | None:
    known_format = source_file_format(source)
    if known_format is not None:
        return _unsupported_file_source_diagnostic(element_tag, source_type, known_format)
    if _dynamic_source_is_valid(source, element_tag, source_type):
        return None
    valid_ids: set[str] = set()
    if source_allows_client(element_tag, source_type):
        valid_ids.update(clients)
    if source_allows_memstore(element_tag, source_type):
        valid_ids.update(memstores)
    declared = f" Valid ids: {', '.join(sorted(valid_ids))}." if valid_ids else ""
    fix_context = f"Declare an allowed source id or select a supported file format.{declared}"
    if source_allows_memstore(element_tag, source_type):
        fix_context += f' For memory input add <memstore id="{source}"/> above its users.'
    return _SourceDiagnostic(
        evidence=f'<{element_tag}> source="{source}" is not a supported file or source id',
        fix_context=fix_context,
    )


class UnknownTarget(Rule):
    definition = authoring_rule_definition("DM401")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        clients, memstores = _declared_ids(ctx)
        for element in ctx.iter(*_GENERATES):
            target_attr = element.get("target")
            if not target_attr:
                continue
            try:
                # SPOT: the exact parser the engine uses (AST-based, param-safe)
                parsed = ExporterUtil.parse_function_string(target_attr)
            except ValueError as err:
                yield ctx.diag(UnknownTarget, element, evidence=f"target parser returned: {err}")
                continue
            for entry in parsed:
                name = entry["function_name"]
                base = name.split(".", 1)[0]
                if "." in name:
                    if base not in clients:
                        yield ctx.diag(
                            UnknownTarget,
                            element,
                            evidence=f"target '{name}' references undeclared client '{base}'",
                            fix_context=f'Declare <mongodb id="{base}"/> or <database id="{base}" .../>.',
                        )
                    else:
                        operation = name.split(".", 1)[1]
                        if operation not in _CLIENT_OPERATIONS:
                            yield ctx.diag(
                                UnknownTarget,
                                element,
                                evidence=f"operation '{operation}' in target '{name}' is unknown",
                                fix_context=f"Client operations: {', '.join(sorted(_CLIENT_OPERATIONS))}; "
                                "plain clientId inserts.",
                            )
                elif name not in _STATIC_TARGETS and name not in clients and name not in memstores:
                    valid = sorted(_STATIC_TARGETS | clients | memstores)
                    yield ctx.diag(
                        UnknownTarget,
                        element,
                        evidence=f"target '{name}' is not built-in or declared",
                        fix_context=f'For memory output add <memstore id="{name}"/> above the writer; '
                        f"known targets: {', '.join(valid)}.",
                    )


class DuplicateGenerateName(Rule):
    definition = authoring_rule_definition("DM403")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for parent in ctx.iter():
            seen: dict[str, etree._Element] = {}
            for child in parent:
                if not isinstance(child.tag, str) or child.tag not in _GENERATES:
                    continue
                name = child.get("name")
                if name is None:
                    continue
                if name in seen:
                    yield ctx.diag(
                        DuplicateGenerateName,
                        child,
                        evidence=f'sibling generate name="{name}" occurs more than once',
                    )
                seen.setdefault(name, child)


class UnknownSource(Rule):
    definition = authoring_rule_definition("DM402")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        clients, memstores = _declared_ids(ctx)
        for element in ctx.iter(*_SOURCE_READERS):
            source = element.get("source")
            if not source:
                continue
            element_tag = str(element.tag)
            source_type = element.get("type")
            if _source_is_declared(source, element_tag, source_type, clients, memstores):
                continue
            diagnostic = _unknown_source_diagnostic(source, element_tag, source_type, clients, memstores)
            if diagnostic is None:
                continue
            yield ctx.diag(
                UnknownSource,
                element,
                evidence=diagnostic.evidence,
                fix_context=diagnostic.fix_context,
            )


class MissingInclude(Rule):
    definition = authoring_rule_definition("DM405")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        if ctx.base_dir is None:
            return  # inline XML: relative includes are not resolvable, don't false-positive
        for element in ctx.iter(EL_INCLUDE):
            uri = element.get("uri")
            if not uri or "{" in uri:  # dynamic {var} uris resolve at runtime
                continue
            if not (ctx.base_dir / uri).is_file():
                yield ctx.diag(
                    MissingInclude,
                    element,
                    evidence=f'uri="{uri}" does not resolve beside the descriptor',
                )


RULES: tuple[type[Rule], ...] = (
    UnknownTarget,
    UnknownSource,
    MissingInclude,
    DuplicateGenerateName,
)
