# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Request and result envelopes for the Authoring use-case boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import (
    Field,
    JsonValue,
    StrictBool,
    StrictInt,
    StrictStr,
    ValidationError,
    model_validator,
)

from .capture import CapturedProducts, ProductCaptureEvidence, SmokeExportCapture
from .common import (
    MAX_AUTHORING_MAX_COUNT,
    MAX_AUTHORING_XML_LENGTH,
    AuthoringModel,
    NonEmptyStrictStr,
    NonNegativeStrictInt,
    WorkspaceDescriptorPath,
)
from .diagnostics import AuthoringRuleId, Diagnostic, DiagnosticPhase
from .dm_json import DmJsonDocumentV1
from .environments import ConfiguredEnvironmentBinding
from .expectations import ExpectationIntent, expectation_identity
from .proof import (
    AcceptanceRequirement,
    BuildVerificationEvidence,
    BuildVerificationOptions,
    ProductRoleDeclaration,
    VerificationGateStatus,
)


class LintRequest(AuthoringModel):
    xml: NonEmptyStrictStr


class IncludedDescriptor(AuthoringModel):
    """One file of an entry's literal include graph, read from the bound workspace. ``xml`` is the step as
    analysis reads it, with target placeholders resolved; ``sha256`` binds the bytes that were read."""

    uri: NonEmptyStrictStr
    xml: NonEmptyStrictStr
    sha256: NonEmptyStrictStr


class IncludeGraphResult(AuthoringModel):
    """The ``.xml`` steps an entry includes, in execution order, or why the graph is not provable."""

    ok: StrictBool
    descriptors: tuple[IncludedDescriptor, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    # The entry as analysis reads it: target placeholders resolved from the project's .properties includes.
    entry_xml: str | None = None


class LintResult(AuthoringModel):
    ok: StrictBool
    diagnostics: tuple[Diagnostic, ...] = ()

    @classmethod
    def from_input_error(cls, message: str) -> LintResult:
        from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic

        return cls(
            ok=False,
            diagnostics=(catalog_diagnostic(AuthoringRuleId.INPUT, message, phase=DiagnosticPhase.MODEL),),
        )


class ReferenceTopic(StrEnum):
    OVERVIEW = "overview"
    ASSEMBLY = "assembly"
    RULES = "rules"
    EXPECTATIONS = "expectations"
    EXAMPLES = "examples"
    LEARNING = "learning"


class AuthoringSchemaId(StrEnum):
    """Stable names for focused public Authoring schema discovery."""

    DM_JSON_DOCUMENT_V1 = "dm_json_document_v1"
    DM_JSON_NODE_V1 = "dm_json_node_v1"
    COMPILE_DOCUMENT_REQUEST = "compile_document_request"
    COMPILE_DOCUMENT_RESULT = "compile_document_result"
    DECOMPILE_DOCUMENT_REQUEST = "decompile_document_request"
    DECOMPILE_DOCUMENT_RESULT = "decompile_document_result"
    READY_BUILD = "ready_build"
    REJECTED_BUILD = "rejected_build"
    BUILD_REQUEST_V5 = "build_request_v5"
    EXPECTATION_INTENT = "expectation_intent"
    ENVIRONMENT_BINDING = "environment_binding"
    DIAGNOSTIC = "diagnostic"
    BUILD_RESULT = "build_result"


class ReferenceRequest(AuthoringModel):
    """Typed navigation over the model-derived authoring catalog."""

    topic: ReferenceTopic = ReferenceTopic.OVERVIEW
    name: NonEmptyStrictStr | None = None


DEFAULT_AUTHORING_MAX_COUNT = 10
DEFAULT_AUTHORING_SAMPLE_ROWS = 5
DEFAULT_AUTHORING_DESCRIPTOR_PATH = PurePosixPath("model.xml")
# A project is a directory: its entry descriptor and the acceptance Build proves it against sit at fixed paths.
PROJECT_ENTRY_PATH = PurePosixPath("datamimic.xml")
PROJECT_ACCEPTANCE_PATH = PurePosixPath("acceptance/build.json")


class BuildRequestV5(AuthoringModel):
    """The project's acceptance, read from ``acceptance/build.json``; the project files are the model."""

    version: Literal["5.0"] = "5.0"
    expectations: tuple[ExpectationIntent, ...] = ()
    environment_bindings: tuple[ConfiguredEnvironmentBinding, ...] = ()
    product_roles: tuple[ProductRoleDeclaration, ...] = ()
    acceptance_requirements: tuple[AcceptanceRequirement, ...] = ()
    verification: BuildVerificationOptions = Field(default_factory=BuildVerificationOptions)
    max_count: StrictInt | None = Field(
        default=None,
        ge=1,
        le=MAX_AUTHORING_MAX_COUNT,
        description=(
            "Limit for the captured rows of all products together. Omit it: when every product has a literal "
            "count or reads a memstore back, Build uses the declared total (at least "
            f"{DEFAULT_AUTHORING_MAX_COUNT}, at most {MAX_AUTHORING_MAX_COUNT}); otherwise "
            f"{DEFAULT_AUTHORING_MAX_COUNT}."
        ),
    )
    sample_rows: StrictInt = Field(default=DEFAULT_AUTHORING_SAMPLE_ROWS, ge=1, le=50)

    @model_validator(mode="after")
    def expectations_are_unique(self) -> BuildRequestV5:
        if len(self.expectations) != len({expectation_identity(item) for item in self.expectations}):
            raise ValueError("build expectations must be unique")
        return self

    def capture_limit(self, declared_rows: int | None) -> int:
        """The explicit max_count; else the declared total of rows, kept between the default and the ceiling."""
        if self.max_count is not None:
            return self.max_count
        if declared_rows is None:
            return DEFAULT_AUTHORING_MAX_COUNT
        return min(max(DEFAULT_AUTHORING_MAX_COUNT, declared_rows), MAX_AUTHORING_MAX_COUNT)


class RunRequest(AuthoringModel):
    xml: NonEmptyStrictStr
    descriptor_path: WorkspaceDescriptorPath = DEFAULT_AUTHORING_DESCRIPTOR_PATH
    max_count: StrictInt = Field(default=DEFAULT_AUTHORING_MAX_COUNT, ge=1, le=MAX_AUTHORING_MAX_COUNT)
    sample_rows: StrictInt = Field(default=DEFAULT_AUTHORING_SAMPLE_ROWS, ge=1, le=50)
    allow_side_effects: StrictBool = False
    timeout_seconds: StrictInt = Field(default=30, ge=1, le=120)


class RunPhase(StrEnum):
    LINT = "lint"
    DRY_RUN = "dry_run"
    RUN = "run"


class ProductEvidence(AuthoringModel):
    """Bounded, deterministic sample evidence for one authored product."""

    name: NonEmptyStrictStr
    count: NonNegativeStrictInt
    rows: tuple[dict[str, JsonValue], ...] = ()
    capture: ProductCaptureEvidence | None = None


class RunResult(AuthoringModel):
    ok: StrictBool
    phase: RunPhase
    products: tuple[ProductEvidence, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()

    @classmethod
    def from_input_error(cls, message: str) -> RunResult:
        from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic

        return cls(
            ok=False,
            phase=RunPhase.RUN,
            diagnostics=(catalog_diagnostic(AuthoringRuleId.INPUT, message, phase=DiagnosticPhase.MODEL),),
        )


HexSha256 = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]


class CompileDocumentRequest(AuthoringModel):
    """Compile one agent-only DM JSON descriptor at its canonical project path."""

    document: DmJsonDocumentV1
    descriptor_path: WorkspaceDescriptorPath = DEFAULT_AUTHORING_DESCRIPTOR_PATH


class DecompileDocumentRequest(AuthoringModel):
    """Decompile one persisted XML descriptor without inventing Build Expectations."""

    xml: NonEmptyStrictStr
    descriptor_path: WorkspaceDescriptorPath = DEFAULT_AUTHORING_DESCRIPTOR_PATH


class CompiledDocumentArtifact(AuthoringModel):
    """Canonical descriptor artifact; Expectations deliberately do not appear here."""

    document: DmJsonDocumentV1
    compiled_xml: NonEmptyStrictStr
    xml_sha256: HexSha256
    semantic_sha256: HexSha256
    ce_version: NonEmptyStrictStr


class ReadyCompileDocument(AuthoringModel):
    outcome: Literal["ready"] = "ready"
    document_schema: Literal[AuthoringSchemaId.DM_JSON_DOCUMENT_V1] = AuthoringSchemaId.DM_JSON_DOCUMENT_V1
    artifact: CompiledDocumentArtifact
    diagnostics: tuple[Diagnostic, ...] = ()


class RejectedCompileDocument(AuthoringModel):
    outcome: Literal["rejected"] = "rejected"
    phase: Literal[DiagnosticPhase.COMPILE, DiagnosticPhase.XML]
    diagnostics: tuple[Diagnostic, ...] = Field(min_length=1)

    @classmethod
    def from_input_error(cls, message: str) -> RejectedCompileDocument:
        from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic

        diagnostic = catalog_diagnostic(AuthoringRuleId.INPUT, message, phase=DiagnosticPhase.COMPILE)
        return cls(phase=DiagnosticPhase.COMPILE, diagnostics=(diagnostic,))


CompileDocumentResult = Annotated[
    ReadyCompileDocument | RejectedCompileDocument,
    Field(discriminator="outcome"),
]


class ReadyDecompileDocument(AuthoringModel):
    outcome: Literal["ready"] = "ready"
    document_schema: Literal[AuthoringSchemaId.DM_JSON_DOCUMENT_V1] = AuthoringSchemaId.DM_JSON_DOCUMENT_V1
    document: DmJsonDocumentV1
    source_xml_sha256: HexSha256
    canonical_xml_sha256: HexSha256
    semantic_sha256: HexSha256
    ce_version: NonEmptyStrictStr
    diagnostics: tuple[Diagnostic, ...] = ()


class RejectedDecompileDocument(AuthoringModel):
    outcome: Literal["rejected"] = "rejected"
    phase: Literal[DiagnosticPhase.XML, DiagnosticPhase.DECOMPILE]
    diagnostics: tuple[Diagnostic, ...] = Field(min_length=1)

    @classmethod
    def from_input_error(cls, message: str) -> RejectedDecompileDocument:
        from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic

        diagnostic = catalog_diagnostic(AuthoringRuleId.INPUT, message, phase=DiagnosticPhase.DECOMPILE)
        return cls(phase=DiagnosticPhase.DECOMPILE, diagnostics=(diagnostic,))


DecompileDocumentResult = Annotated[
    ReadyDecompileDocument | RejectedDecompileDocument,
    Field(discriminator="outcome"),
]


class ProjectFileDigest(AuthoringModel):
    """One project file the proof depends on, by workspace path and content hash."""

    path: WorkspaceDescriptorPath
    sha256: HexSha256


class BuildArtifact(AuthoringModel):
    """The project files a build proved, each bound by its digest: changing any of them voids the proof."""

    files: tuple[ProjectFileDigest, ...] = Field(min_length=2)
    ce_version: NonEmptyStrictStr

    @model_validator(mode="after")
    def files_are_sorted_and_unique(self) -> BuildArtifact:
        paths = [item.path for item in self.files]
        if paths != sorted(set(paths)):
            raise ValueError("project file digests must be sorted by path and unique")
        return self


class ValidatedReviewArtifact(BuildArtifact):
    """Reviewable compiler output that failed bounded Evidence and cannot be committed."""

    assurance: Literal["validated_not_ready"] = "validated_not_ready"


class SourceAccessEvidence(AuthoringModel):
    """Observed source-router requests, without locators or connection facts."""

    source_type: NonEmptyStrictStr
    requests: StrictInt = Field(ge=1)


class BuildAssurance(AuthoringModel):
    """Closed proof scope carried only by an honest ReadyBuild."""

    scope: Literal["declared_model_bounded"] = "declared_model_bounded"
    mode: Literal["local_bounded", "target_isolated"]
    source_accesses: tuple[SourceAccessEvidence, ...] = ()


class RejectedBuild(AuthoringModel):
    outcome: Literal["rejected"] = "rejected"
    phase: DiagnosticPhase
    diagnostics: tuple[Diagnostic, ...] = Field(min_length=1)
    review_artifact: ValidatedReviewArtifact | None = None
    evidence: tuple[ProductEvidence, ...] = ()
    verification: BuildVerificationEvidence = Field(default_factory=BuildVerificationEvidence)

    @model_validator(mode="after")
    def review_artifact_matches_phase(self) -> RejectedBuild:
        if self.phase is DiagnosticPhase.EVIDENCE and self.review_artifact is None:
            raise ValueError("evidence rejections require a validated review artifact")
        if self.phase is not DiagnosticPhase.EVIDENCE and self.review_artifact is not None:
            raise ValueError("only evidence rejections may carry a validated review artifact")
        return self

    @classmethod
    def from_input_error(cls, message: str) -> RejectedBuild:
        from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic

        phase = DiagnosticPhase.MODEL
        diagnostic = catalog_diagnostic(AuthoringRuleId.INPUT, message, phase=phase)
        return cls(phase=phase, diagnostics=(diagnostic,))

    @classmethod
    def from_model_validation(cls, error: ValidationError) -> RejectedBuild:
        from datamimic_ce.authoring.domain.validation import validation_diagnostics

        locations = tuple(item.get("loc", ()) for item in error.errors())
        binding_only = bool(locations) and all(
            location and location[0] == "environment_bindings" for location in locations
        )
        phase = DiagnosticPhase.ENVIRONMENT_BINDING if binding_only else DiagnosticPhase.MODEL
        remediation = (
            "Repair the host-owned environment binding at the reported path."
            if binding_only
            else "Repair the canonical authoring model at the reported path."
        )
        return cls(
            phase=phase,
            diagnostics=validation_diagnostics(error, phase=phase, remediation=remediation),
        )


class ReadyBuild(AuthoringModel):
    outcome: Literal["ready"] = "ready"
    artifact: BuildArtifact
    assurance: BuildAssurance
    evidence: tuple[ProductEvidence, ...] = Field(min_length=1)
    verification: BuildVerificationEvidence = Field(default_factory=BuildVerificationEvidence)
    diagnostics: tuple[Diagnostic, ...] = ()

    @model_validator(mode="after")
    def reject_error_diagnostics(self) -> ReadyBuild:
        if any(diagnostic.severity == "error" for diagnostic in self.diagnostics):
            raise ValueError("ready builds cannot contain error diagnostics")
        if any(
            gate.status in {VerificationGateStatus.FAILED, VerificationGateStatus.BLOCKED}
            for gate in (self.verification.smoke_export, self.verification.deterministic_replay)
        ):
            raise ValueError("ready builds cannot contain failed or blocked verification")
        if any(
            item.capture is None or not item.capture.complete or item.capture.observed != item.count
            for item in self.evidence
        ):
            raise ValueError("ready builds require complete capture provenance for every product")
        return self


BuildResult = Annotated[ReadyBuild | RejectedBuild, Field(discriminator="outcome")]


class BoundedExecutionRequest(AuthoringModel):
    xml: NonEmptyStrictStr = Field(max_length=MAX_AUTHORING_XML_LENGTH)
    descriptor_path: WorkspaceDescriptorPath = DEFAULT_AUTHORING_DESCRIPTOR_PATH
    max_count: StrictInt = Field(default=DEFAULT_AUTHORING_MAX_COUNT, ge=1, le=MAX_AUTHORING_MAX_COUNT)
    allow_side_effects: StrictBool = False
    timeout_seconds: StrictInt = Field(default=30, ge=1, le=120)
    environment_properties: tuple[tuple[NonEmptyStrictStr, StrictStr], ...] = ()
    smoke_export: StrictBool = False
    # PYTHONHASHSEED of the child process; None inherits the caller's environment.
    hash_seed: StrictInt | None = Field(default=None, ge=0, le=4294967295)


@dataclass(frozen=True)
class BoundedExecutionEvidence:
    """Validated full execution evidence, kept inside the application boundary."""

    ok: bool
    captured: CapturedProducts
    diagnostics: tuple[Diagnostic, ...] = ()
    smoke_export: SmokeExportCapture = SmokeExportCapture.not_requested()
    base_run_ok: bool = True
    source_accesses: tuple[SourceAccessEvidence, ...] = ()
    # Workspace files the run opened for reading, hashed from the private copy it read them from.
    files: tuple[ProjectFileDigest, ...] = ()
