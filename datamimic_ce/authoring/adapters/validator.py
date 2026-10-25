# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Use the normal CE parser for in-memory descriptor hard validation."""

import re
from contextlib import suppress
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Literal

from lxml import etree

from datamimic_ce.authoring.adapters.dryrun import (
    _BoundedPolicyRefusal,
    _IncludeBudgetExceeded,
    _literal_include_graph,
)
from datamimic_ce.authoring.adapters.linter import _run_rules
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic
from datamimic_ce.authoring.domain.diagnostics import (
    AuthoringRuleId,
    AuthoringSystemDiagnosticCode,
    CeErrorIdentity,
    Diagnostic,
    DiagnosticPhase,
)
from datamimic_ce.authoring.domain.requests import IncludedDescriptor, IncludeGraphResult, LintResult
from datamimic_ce.authoring.domain.rule_catalog import RuleSeverity, authoring_rule_definition
from datamimic_ce.engine.dsl.api import (
    EL_DATABASE,
    EL_MONGODB,
    DescriptorParser,
    parse_properties,
    parse_xml_source,
    resource_reader_scope,
)
from datamimic_ce.engine.dsl.parsers.base.client_config import ConnectionProfileLoader
from datamimic_ce.errors.base import ParserValidationError, UserErrorBase


class CeDescriptorValidator:
    def __init__(
        self,
        workspace_context: AuthoringWorkspaceContext,
        *,
        profile_loader: ConnectionProfileLoader,
        properties: dict[str, str] | dict[str, object] | None = None,
        runtime_environment: Literal["development", "production"] = "production",
    ) -> None:
        self._workspace_context = workspace_context
        self._profile_loader = profile_loader
        self._properties = properties
        self._runtime_environment = runtime_environment

    def validate(self, xml: str, *, descriptor_path: PurePosixPath | None = None) -> LintResult:
        logical_path = descriptor_path or self._workspace_context.descriptor_path
        if logical_path != self._workspace_context.descriptor_path:
            return _rejected(logical_path, "Descriptor path does not match the bound workspace path.")
        try:
            physical_path = self._workspace_context.resolve_descriptor_path(logical_path)
            with resource_reader_scope(self._workspace_context.read_resource_bytes):
                self._refuse_oversized_includes(xml, physical_path)
                DescriptorParser.parse_xml(
                    xml,
                    physical_path,
                    self._properties,
                    self._runtime_environment,
                    profile_loader=self._profile_loader,
                    logical_descriptor_path=logical_path.as_posix(),
                )
        except UserErrorBase as error:
            identity = CeErrorIdentity(error_code=error.code, issue_code=error.issue_code) if error.code else None
            prefix: tuple[str | int, ...] = ("descriptor", logical_path.as_posix())
            if error.location is not None:
                prefix += (error.location.element_tag,)
                if error.location.line is not None:
                    prefix += ("line", error.location.line)
                if error.location.attribute is not None:
                    prefix += ("attribute", error.location.attribute)
            if isinstance(error, ParserValidationError) and error.validation_errors:
                diagnostics = []
                for detail in error.validation_errors:
                    location = detail.get("loc", ())
                    if not isinstance(location, tuple | list) or not all(
                        isinstance(part, str | int) for part in location
                    ):
                        raise TypeError("parser validation location must contain only strings or integers") from error
                    diagnostics.append(
                        _diagnostic(
                            "Descriptor field failed parser validation.",
                            path=prefix + tuple(location),
                            identity=identity,
                        )
                    )
                # The parser message may echo resolved (possibly secret) values; the static rule
                # projection names the violated rule and the exact element instead.
                diagnostics.extend(_rule_diagnostics(parse_xml_source(xml), physical_path, logical_path))
                return LintResult(ok=False, diagnostics=tuple(diagnostics))
            return LintResult(
                ok=False,
                diagnostics=(
                    _diagnostic(
                        "Descriptor failed parser validation.",
                        path=prefix,
                        identity=identity,
                    ),
                ),
            )
        except etree.XMLSyntaxError as error:
            return LintResult(
                ok=False,
                diagnostics=(
                    _diagnostic(
                        "Descriptor is not well-formed XML.",
                        path=("descriptor", logical_path.as_posix(), "line", error.position[0]),
                    ),
                ),
            )
        except _IncludeBudgetExceeded as refusal:
            return LintResult(ok=False, diagnostics=_graph_refused(logical_path, str(refusal)).diagnostics)
        except (ValueError, OSError):
            # Parser/resource errors may contain credentials and physical host paths.
            return _rejected(logical_path, "Descriptor or its workspace resources failed validation.")
        root = parse_xml_source(xml)
        steps, complete = self._entry_project(root, physical_path)
        with resource_reader_scope(self._workspace_context.read_resource_bytes):
            _resolve_project_targets(root, steps, physical_path.parent)
        project = (root, *steps.values()) if steps else ()
        findings = _rule_diagnostics(root, physical_path, logical_path, project=project, declarations_complete=complete)
        return LintResult(ok=not any(item.severity == "error" for item in findings), diagnostics=findings)

    def _refuse_oversized_includes(self, xml: str, physical_path: Path) -> None:
        """The parser decodes literal ``.properties`` includes eagerly, so the byte budget has to hold before it
        runs. Every other graph problem (missing file, non-literal uri, cycle) is left to the parser and Build."""
        try:
            _literal_include_graph(parse_xml_source(xml), physical_path)
        except _IncludeBudgetExceeded:
            raise
        except (etree.XMLSyntaxError, ValueError, OSError):
            return

    def _entry_project(self, root: etree._Element, physical_path: Path) -> tuple[dict[str, etree._Element], bool]:
        """The entry's literal steps by uri, so the entry sees what a step declares; empty for a single file. An
        unreadable graph leaves its declarations unknown, so the entry's lint does not pre-empt the graph refusal
        that Build and dry-run report."""
        try:
            with resource_reader_scope(self._workspace_context.read_resource_bytes):
                graph = _literal_include_graph(root, physical_path)
            steps = {
                uri: parse_xml_source(str(data, "utf-8")) for uri, data in graph if PurePosixPath(uri).suffix == ".xml"
            }
        except (etree.XMLSyntaxError, ValueError, OSError):
            return {}, False
        return steps, True

    def include_graph(self, xml: str) -> IncludeGraphResult:
        """The ``.xml`` steps of the entry's literal include graph, read through the contained workspace reader
        with the same rules the bounded run applies."""
        logical_path = self._workspace_context.descriptor_path
        try:
            physical_path = self._workspace_context.resolve_descriptor_path(logical_path)
            with resource_reader_scope(self._workspace_context.read_resource_bytes):
                graph = _literal_include_graph(parse_xml_source(xml), physical_path)
        except _BoundedPolicyRefusal as refusal:
            return _graph_refused(logical_path, str(refusal))  # static rule texts, no paths or values
        except etree.XMLSyntaxError:
            return _graph_refused(logical_path, "An included step is not well-formed XML.")
        except (ValueError, OSError):
            return _graph_refused(logical_path, "An included file is missing or lies outside the workspace.")
        steps: list[tuple[str, str, str]] = []
        for uri, data in graph:
            if PurePosixPath(uri).suffix == ".xml":
                try:
                    steps.append((uri, str(data, "utf-8"), sha256(data).hexdigest()))
                except UnicodeDecodeError:
                    return _graph_refused(logical_path, "An included step is not UTF-8 encoded.")
        entry_root = parse_xml_source(xml)
        roots = [parse_xml_source(text) for _, text, _ in steps]
        with resource_reader_scope(self._workspace_context.read_resource_bytes):
            changed = _resolve_project_targets(
                entry_root, {uri: root for (uri, _, _), root in zip(steps, roots, strict=True)}, physical_path.parent
            )
        descriptors = [
            IncludedDescriptor(uri=uri, xml=_analysis_xml(root, text, changed), sha256=digest)
            for (uri, text, digest), root in zip(steps, roots, strict=True)
        ]
        # Bindings and sinks resolve against the entry, and a step's clients end with that step; refusing them
        # here keeps a step-declared client from surfacing first as an undeclared id in another step.
        refusals = []
        for step, root in zip(descriptors, roots, strict=True):
            for element in root:
                if isinstance(element.tag, str) and element.tag in (EL_DATABASE, EL_MONGODB):
                    refusals.append(
                        catalog_diagnostic(
                            AuthoringRuleId.INCLUDE,
                            "Clients belong to the entry descriptor, not to an included step.",
                            phase=DiagnosticPhase.POLICY,
                            path=(
                                "include",
                                step.uri,
                                element.tag,
                                *(("line", element.sourceline) if element.sourceline is not None else ()),
                            ),
                        )
                    )
        if refusals:
            return IncludeGraphResult(ok=False, diagnostics=tuple(refusals))
        project = (entry_root, *roots)
        findings: list[Diagnostic] = []
        for step, root in zip(descriptors, roots, strict=True):
            findings.extend(
                _rule_diagnostics(root, physical_path, logical_path, project=project, prefix=("include", step.uri))
            )
        return IncludeGraphResult(
            ok=not any(item.severity == "error" for item in findings),
            descriptors=tuple(descriptors),
            diagnostics=tuple(findings),
            entry_xml=_analysis_xml(entry_root, xml, changed),
        )


def _rule_diagnostics(
    root: etree._Element,
    physical_path: Path,
    logical_path: PurePosixPath,
    *,
    project: tuple[etree._Element, ...] = (),
    declarations_complete: bool = True,
    prefix: tuple[str, ...] | None = None,
) -> tuple[Diagnostic, ...]:
    """Lint findings of one descriptor; an included step is linted with its project and reported at its uri."""
    location = prefix or ("descriptor", logical_path.as_posix())
    diagnostics = []
    for finding in _run_rules(
        root, base_dir=physical_path.parent, project=project, declarations_complete=declarations_complete
    ):
        definition = authoring_rule_definition(finding.rule)
        diagnostics.append(
            Diagnostic(
                code=finding.rule,
                phase=DiagnosticPhase.XML,
                message=definition.explanation,
                path=(
                    *location,
                    finding.path,
                    *(("line", finding.line) if finding.line is not None else ()),
                ),
                severity="error"
                if finding.severity is RuleSeverity.ERROR
                else ("warning" if finding.severity is RuleSeverity.WARNING else "info"),
                remediation=definition.fix_hint,
            )
        )
    return tuple(diagnostics)


def _diagnostic(message: str, *, path: tuple[str | int, ...], identity: CeErrorIdentity | None = None) -> Diagnostic:
    return Diagnostic(
        code=AuthoringSystemDiagnosticCode.DESCRIPTOR,
        phase=DiagnosticPhase.XML,
        message=message,
        path=path,
        ce_error=identity,
        remediation="Repair the indicated descriptor field or its workspace-local resource configuration.",
    )


# The undotted form of the runtime's whole-value rule (dispatch.retrieve_element_attributes, which is not DSL
# API); a .properties file is flat. Keep the two in step.
_PLACEHOLDER = r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"


def _resolve_project_targets(
    entry: etree._Element, steps: dict[str, etree._Element], base_dir: Path
) -> set[etree._Element]:
    """Substitute whole-value ``{name}`` placeholders in ``target`` attributes in place, in the order the runtime
    parses them: a literal ``.properties`` include applies to the siblings after it and their subtrees, and a step
    starts from the properties its include saw. An undefined name stays as written. A step's own ``.properties``
    includes are ignored: the runtime resolves them against the step's directory, where they fail. Returns the
    documents that changed."""
    changed: set[etree._Element] = set()

    def walk(element: etree._Element, inherited: dict[str, str], document: etree._Element, in_step: bool) -> None:
        properties = dict(inherited)
        for child in element:
            if not isinstance(child.tag, str):
                continue
            uri = child.get("uri", "")
            if child.tag == "include":
                if PurePosixPath(uri).suffix == ".properties" and not in_step and not any(m in uri for m in "{\\:"):
                    with suppress(OSError, ValueError):  # an unreadable file adds nothing: the parser reports it
                        properties.update(parse_properties(base_dir / uri))
                elif uri in steps:
                    walk(steps[uri], properties, steps[uri], True)
                continue
            target = child.get("target")
            placeholder = re.fullmatch(_PLACEHOLDER, target) if target else None
            if placeholder is not None and placeholder[1] in properties:
                child.attrib["target"] = properties[placeholder[1]]
                changed.add(document)
            walk(child, properties, document, in_step)

    walk(entry, {}, entry, False)
    return changed


def _analysis_xml(root: etree._Element, xml: str, changed: set[etree._Element]) -> str:
    """The document as analysis reads it: re-serialised only when a placeholder resolved, so line numbers move
    only for a descriptor that uses one."""
    return etree.tostring(root, encoding="unicode") if root in changed else xml


def _graph_refused(path: PurePosixPath, message: str) -> IncludeGraphResult:
    return IncludeGraphResult(
        ok=False,
        diagnostics=(
            catalog_diagnostic(
                AuthoringRuleId.INCLUDE,
                message,
                phase=DiagnosticPhase.POLICY,
                path=("descriptor", str(path), "include"),
            ),
        ),
    )


def _rejected(path: PurePosixPath, message: str) -> LintResult:
    return LintResult(ok=False, diagnostics=(_diagnostic(message, path=("descriptor", path.as_posix())),))
