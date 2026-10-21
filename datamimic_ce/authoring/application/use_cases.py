# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Compile and decompile through the same descriptor contract and parser."""

from hashlib import sha256
from importlib import metadata

from datamimic_ce.authoring.domain.diagnostics import AuthoringCodecDiagnosticCode, Diagnostic, DiagnosticPhase
from datamimic_ce.authoring.domain.dm_json import DmJsonCodecError, DmJsonDocumentV1
from datamimic_ce.authoring.domain.document_identity import semantic_fingerprint
from datamimic_ce.authoring.domain.requests import (
    CompiledDocumentArtifact,
    CompileDocumentRequest,
    CompileDocumentResult,
    DecompileDocumentRequest,
    DecompileDocumentResult,
    ReadyCompileDocument,
    ReadyDecompileDocument,
    RejectedCompileDocument,
    RejectedDecompileDocument,
)
from datamimic_ce.authoring.ports import DescriptorValidator, DmJsonDescriptorContract


class CompileDocumentUseCase:
    """Compile and hard-validate one canonical agent-only descriptor document."""

    def __init__(self, contract: DmJsonDescriptorContract, validator: DescriptorValidator) -> None:
        self._contract = contract
        self._validator = validator

    def execute(self, request: CompileDocumentRequest) -> CompileDocumentResult:
        try:
            compilation = self._contract.compile(request.document)
        except DmJsonCodecError as error:
            return RejectedCompileDocument(
                phase=DiagnosticPhase.COMPILE,
                diagnostics=(
                    _codec_diagnostic(
                        error,
                        code=AuthoringCodecDiagnosticCode.COMPILE_INVALID,
                        phase=DiagnosticPhase.COMPILE,
                        remediation="Repair the DM JSON node at the reported path.",
                    ),
                ),
            )
        lint = self._validator.validate(
            compilation.xml,
            descriptor_path=request.descriptor_path,
        )
        if not lint.ok:
            return RejectedCompileDocument(
                phase=DiagnosticPhase.XML,
                diagnostics=lint.diagnostics,
            )
        return ReadyCompileDocument(
            artifact=_compiled_document_artifact(compilation.document, compilation.xml), diagnostics=lint.diagnostics
        )


class DecompileDocumentUseCase:
    """Validate and completely decompile XML; unsupported semantics fail closed."""

    def __init__(self, contract: DmJsonDescriptorContract, validator: DescriptorValidator) -> None:
        self._contract = contract
        self._validator = validator

    def execute(self, request: DecompileDocumentRequest) -> DecompileDocumentResult:
        lint = self._validator.validate(
            request.xml,
            descriptor_path=request.descriptor_path,
        )
        if not lint.ok:
            return RejectedDecompileDocument(
                phase=DiagnosticPhase.XML,
                diagnostics=lint.diagnostics,
            )
        try:
            document = self._contract.decompile(request.xml)
            canonical_xml = self._contract.compile(document).xml
        except DmJsonCodecError as error:
            return RejectedDecompileDocument(
                phase=DiagnosticPhase.DECOMPILE,
                diagnostics=(
                    _codec_diagnostic(
                        error,
                        code=AuthoringCodecDiagnosticCode.DECOMPILE_UNSUPPORTED,
                        phase=DiagnosticPhase.DECOMPILE,
                        remediation="Keep this XML human-managed or rewrite it using supported typed DM JSON nodes.",
                    ),
                ),
            )
        return ReadyDecompileDocument(
            document=document,
            source_xml_sha256=sha256(request.xml.encode("utf-8")).hexdigest(),
            canonical_xml_sha256=sha256(canonical_xml.encode("utf-8")).hexdigest(),
            semantic_sha256=semantic_fingerprint(document),
            ce_version=metadata.version("datamimic_ce"),
            diagnostics=lint.diagnostics,
        )


def _codec_diagnostic(
    error: DmJsonCodecError,
    *,
    code: AuthoringCodecDiagnosticCode,
    phase: DiagnosticPhase,
    remediation: str,
) -> Diagnostic:
    """Preserve structured codec repair facts at the application boundary."""
    return Diagnostic(
        code=code,
        phase=phase,
        message=str(error),
        path=error.path,
        expected=error.expected,
        actual=error.actual,
        remediation=error.remediation or remediation,
    )


def _compiled_document_artifact(document: DmJsonDocumentV1, xml: str) -> CompiledDocumentArtifact:
    return CompiledDocumentArtifact(
        document=document,
        compiled_xml=xml,
        xml_sha256=sha256(xml.encode("utf-8")).hexdigest(),
        semantic_sha256=semantic_fingerprint(document),
        ce_version=metadata.version("datamimic_ce"),
    )
