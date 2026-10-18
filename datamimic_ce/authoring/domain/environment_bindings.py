# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Validate credential-free host bindings for CE client declarations."""

from .diagnostics import AuthoringBuildDiagnosticCode, Diagnostic, DiagnosticPhase
from .dm_json import DmJsonDocumentV1
from .environments import ConfiguredEnvironmentBinding


def validate_environment_bindings(
    document: DmJsonDocumentV1,
    bindings: tuple[ConfiguredEnvironmentBinding, ...],
) -> tuple[Diagnostic, ...]:
    by_environment: dict[str, ConfiguredEnvironmentBinding] = {}
    diagnostics = []
    for index, binding in enumerate(bindings):
        if binding.environment in by_environment:
            diagnostics.append(
                _diagnostic(
                    AuthoringBuildDiagnosticCode.DUPLICATE_ENVIRONMENT_BINDING,
                    "Environment binding is declared more than once.",
                    ("environment_bindings", index, "environment"),
                )
            )
        else:
            by_environment[binding.environment] = binding
    declarations: dict[str, str] = {}
    for index, node in enumerate(document.root.children):
        if node.kind not in {"database", "mongodb"}:
            continue
        name = node.properties.get("id")
        path: tuple[str | int, ...] = ("document", "root", "children", index, "properties", "id")
        if not isinstance(name, str) or not name:
            diagnostics.append(
                _diagnostic(
                    AuthoringBuildDiagnosticCode.UNKNOWN_ENVIRONMENT,
                    "Client declaration requires an environment identity.",
                    path,
                )
            )
            continue
        if name in declarations:
            diagnostics.append(
                _diagnostic(
                    AuthoringBuildDiagnosticCode.CONFLICTING_ENVIRONMENT_REFERENCE,
                    "Environment identity has multiple client declarations.",
                    path,
                )
            )
            continue
        declarations[name] = node.kind
        selected_binding = by_environment.get(name)
        if selected_binding is None:
            diagnostics.append(
                _diagnostic(
                    AuthoringBuildDiagnosticCode.UNKNOWN_ENVIRONMENT,
                    "Client declaration has no supplied host binding.",
                    path,
                )
            )
        elif selected_binding.family != node.kind:
            diagnostics.append(
                _diagnostic(
                    AuthoringBuildDiagnosticCode.ENVIRONMENT_FAMILY_MISMATCH,
                    "Client declaration and supplied binding have different families.",
                    path,
                )
            )
    return tuple(diagnostics)


def _diagnostic(code: AuthoringBuildDiagnosticCode, message: str, path: tuple[str | int, ...]) -> Diagnostic:
    return Diagnostic(
        code=code,
        phase=DiagnosticPhase.ENVIRONMENT_BINDING,
        message=message,
        path=path,
        remediation="Supply exactly one matching typed ID-only binding per CE client declaration.",
    )
