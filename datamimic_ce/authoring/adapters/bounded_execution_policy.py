# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Use the CE registry's eligibility facts; the executor owns count/target isolation."""

from decimal import Decimal, InvalidOperation, Overflow

from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic
from datamimic_ce.authoring.domain.common import MAX_AUTHORING_DECIMAL_SCALE
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId, Diagnostic, DiagnosticPhase
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1, DmJsonNodeV1, iter_dm_json_nodes
from datamimic_ce.authoring.domain.rule_catalog import authoring_rule_definition
from datamimic_ce.authoring.domain.script_semantics import admits_python_library
from datamimic_ce.engine.dsl.api import ExecuteStatement, get_element_definition, parse_consumer
from datamimic_ce.engine.dsl.parsers.input.target import parse_function_string
from datamimic_ce.engine.dsl.vocabulary.contracts.dsl_element import BoundedExecutionStrategy, ElementContentModeKind
from datamimic_ce.engine.io.api import buffered_exporter_names


def _is_bounded_python_library(node: DmJsonNodeV1, path: tuple[str | int, ...]) -> bool:
    """A setup-level Python library; the bounded child checks its source before it runs (#332)."""
    content = node.content
    uri = content.value if content is not None and content.kind is ElementContentModeKind.URI else None
    script = content.value if content is not None and content.kind is ElementContentModeKind.SCRIPT else None
    type_ = node.properties.get("type")
    target = node.properties.get("target")
    return path == ("document", "root", "children", path[-1]) and admits_python_library(
        ExecuteStatement.language(type_ if isinstance(type_, str) else None, uri),
        target=None if target is None else str(target),
        script=script,
    )


def _exports_to_file(document: DmJsonDocumentV1) -> bool:
    """Whether a product of this document delivers to a buffered file exporter; invalid targets count as none."""
    for node, _ in iter_dm_json_nodes(document):
        targets = node.properties.get("target")
        if node.kind == "generate" and isinstance(targets, str):
            try:
                entries = parse_function_string(targets)
            except ValueError:
                continue
            if any(entry["function_name"] in buffered_exporter_names() for entry in entries):
                return True
    return False


class CeBoundedExecutionPolicy:
    def diagnostics(
        self, document: DmJsonDocumentV1, project: tuple[DmJsonDocumentV1, ...] = ()
    ) -> tuple[Diagnostic, ...]:
        """Findings for one document; ``project`` holds the other documents of its include graph, because the
        delivery rule spans every file."""
        diagnostics = []
        for node, path in iter_dm_json_nodes(document):
            if node.properties.get("type") == "decimal" and node.properties.get("granularity") is not None:
                try:
                    quantum = Decimal(str(node.properties["granularity"]))
                    exponent = quantum.normalize().as_tuple().exponent if quantum.is_finite() else None
                except (InvalidOperation, Overflow):
                    quantum = Decimal("NaN")
                    exponent = None
                if not quantum.is_finite() or (isinstance(exponent, int) and exponent < -MAX_AUTHORING_DECIMAL_SCALE):
                    diagnostics.append(
                        Diagnostic(
                            code=AuthoringRuleId.LIMIT,
                            phase=DiagnosticPhase.POLICY,
                            message=(
                                "CE decimal ranges require representable granularity and at most 15 decimal places."
                            ),
                            path=path + ("properties", "granularity"),
                            expected={"maximum_decimal_places": MAX_AUTHORING_DECIMAL_SCALE},
                            remediation="Use representable granularity with at most 15 decimal places.",
                        )
                    )
            definition = get_element_definition(node.kind)
            strategy = None if definition is None else definition.bounded_execution_profile.strategy
            if strategy in (None, BoundedExecutionStrategy.UNSUPPORTED) or (
                strategy is BoundedExecutionStrategy.PYTHON_LIBRARY and not _is_bounded_python_library(node, path)
            ):
                diagnostics.append(
                    catalog_diagnostic(
                        AuthoringRuleId.UNSUPPORTED_BOUNDED_OPERATION,
                        f"The <{node.kind}> element has no proven bounded CE execution policy.",
                        phase=DiagnosticPhase.POLICY,
                        path=path,
                    )
                )
        products = tuple((node, path) for node, path in iter_dm_json_nodes(document) if node.kind == "generate")
        for node, path in products:
            targets = node.properties.get("target")
            if isinstance(targets, str):
                try:
                    parse_function_string(targets)
                except ValueError:
                    diagnostics.append(
                        catalog_diagnostic(
                            AuthoringRuleId.INPUT,
                            "Target declaration is invalid.",
                            phase=DiagnosticPhase.POLICY,
                            path=path + ("properties", "target"),
                        )
                    )
        if any(_exports_to_file(each) for each in (document, *project)):
            delivery_rule = authoring_rule_definition("DM407")
            for node, path in products:
                targets = node.properties.get("target")
                if not isinstance(targets, str) or not parse_consumer(targets):
                    diagnostics.append(
                        Diagnostic(
                            code=delivery_rule.id,
                            phase=DiagnosticPhase.POLICY,
                            message=delivery_rule.explanation,
                            path=path + ("properties", "target"),
                            remediation=delivery_rule.fix_hint,
                        )
                    )
        return tuple(diagnostics)
