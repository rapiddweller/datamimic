# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Use the normal CE parser for in-memory descriptor hard validation."""

from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Literal

from lxml import etree

from datamimic_ce.authoring.adapters.dryrun import _BoundedPolicyRefusal, _literal_include_graph
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
from datamimic_ce.engine.dsl.api import DescriptorParser, parse_xml_source, resource_reader_scope
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
        except (ValueError, OSError):
            # Parser/resource errors may contain credentials and physical host paths.
            return _rejected(logical_path, "Descriptor or its workspace resources failed validation.")
        root = parse_xml_source(xml)
        project, complete = self._entry_project(root, physical_path)
        findings = _rule_diagnostics(root, physical_path, logical_path, project=project, declarations_complete=complete)
        return LintResult(ok=not any(item.severity == "error" for item in findings), diagnostics=findings)

    def _entry_project(self, root: etree._Element, physical_path: Path) -> tuple[tuple[etree._Element, ...], bool]:
        """The entry and its literal steps, so the entry sees what a step declares; empty for a single file. An
        unreadable graph leaves its declarations unknown, so the entry's lint does not pre-empt the graph refusal
        that Build and dry-run report."""
        try:
            with resource_reader_scope(self._workspace_context.read_resource_bytes):
                graph = _literal_include_graph(root, physical_path)
            steps = [parse_xml_source(str(data, "utf-8")) for uri, data in graph if PurePosixPath(uri).suffix == ".xml"]
        except (etree.XMLSyntaxError, ValueError, OSError):
            return (), False
        return ((root, *steps) if steps else ()), True

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
        descriptors = []
        for uri, data in graph:
            if PurePosixPath(uri).suffix == ".xml":
                try:
                    text = str(data, "utf-8")
                except UnicodeDecodeError:
                    return _graph_refused(logical_path, "An included step is not UTF-8 encoded.")
                descriptors.append(IncludedDescriptor(uri=uri, xml=text, sha256=sha256(data).hexdigest()))
        roots = [parse_xml_source(step.xml) for step in descriptors]
        project = (parse_xml_source(xml), *roots)
        findings: list[Diagnostic] = []
        for step, root in zip(descriptors, roots, strict=True):
            findings.extend(
                _rule_diagnostics(root, physical_path, logical_path, project=project, prefix=("include", step.uri))
            )
        return IncludeGraphResult(
            ok=not any(item.severity == "error" for item in findings),
            descriptors=tuple(descriptors),
            diagnostics=tuple(findings),
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
