# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Thin facade over independently testable authoring use cases."""

from __future__ import annotations

import contextlib
import platform
from importlib import metadata

from pydantic import BaseModel, JsonValue, TypeAdapter, ValidationError

from datamimic_ce.authoring.application.build import BuildDocumentWorkflow
from datamimic_ce.authoring.application.project_run import ProjectRunWorkflow
from datamimic_ce.authoring.application.raw_xml import RawXmlUseCase
from datamimic_ce.authoring.application.schema import contract_schemas
from datamimic_ce.authoring.application.use_cases import (
    CompileDocumentUseCase,
    DecompileDocumentUseCase,
)
from datamimic_ce.authoring.domain.capabilities import (
    CapabilityDomain,
    CapabilityLookupResult,
    DslCatalogSnapshot,
    GitRuntimeVersion,
    RuntimeVersion,
)
from datamimic_ce.authoring.domain.project_run import ProjectRunRequest, ProjectRunResult, UnverifiedProjectRunResult
from datamimic_ce.authoring.domain.project_scaffold import ProjectPattern, ProjectScaffold
from datamimic_ce.authoring.domain.reference import (
    AuthoringAssemblyReference,
    ReferenceLookupResult,
    ReferenceResult,
)
from datamimic_ce.authoring.domain.requests import (
    BUILD_PROTOCOL,
    AuthoringSchemaId,
    BuildResult,
    CompileDocumentRequest,
    CompileDocumentResult,
    DecompileDocumentRequest,
    DecompileDocumentResult,
    LintRequest,
    LintResult,
    ReferenceRequest,
    ReferenceTopic,
    RunPhase,
    RunRequest,
    RunResult,
)
from datamimic_ce.authoring.ports import (
    BoundedExecutionPolicy,
    BoundedExecutor,
    DescriptorValidator,
    DmJsonDescriptorContract,
    DslCatalog,
    ExternalEffectsDetector,
    ProjectFiles,
    ProjectRunner,
)


class _VcsInfo(BaseModel):
    vcs: str
    commit_id: str | None = None


class _DirectUrl(BaseModel):
    """The part of the PEP 610 `direct_url.json` that names a VCS install."""

    vcs_info: _VcsInfo | None = None


def _git_commit(direct_url_json: bytes | None) -> str | None:
    """The commit of a git install; None for every other install, so a commit is never guessed.

    The bytes are parsed as JSON, so bytes that are not UTF-8 are a ValidationError, the same as bad JSON (#704).
    """
    if direct_url_json is None:
        return None
    try:
        vcs_info = _DirectUrl.model_validate_json(direct_url_json).vcs_info
    except ValidationError:
        return None
    return vcs_info.commit_id or None if vcs_info is not None and vcs_info.vcs == "git" else None


class AuthoringApplication:
    """Expose the canonical public use-case methods without owning their rules."""

    def __init__(
        self,
        catalog: DslCatalog,
        validator: DescriptorValidator,
        executor: BoundedExecutor,
        descriptor_contract: DmJsonDescriptorContract,
        bounded_execution_policy: BoundedExecutionPolicy,
        files: ProjectFiles,
        project_validator: DescriptorValidator,
        project_executor: BoundedExecutor,
        external_effects: ExternalEffectsDetector,
        project_runner: ProjectRunner,
    ) -> None:
        self._validator = validator
        self._raw_xml = RawXmlUseCase(validator, executor)
        self._catalog = catalog
        self._descriptor_contract = descriptor_contract
        self._compile_document = CompileDocumentUseCase(descriptor_contract, validator)
        self._decompile_document = DecompileDocumentUseCase(descriptor_contract, validator)
        # Build proves the project entry, so its validator and executor are bound to it, not to the descriptor.
        self._build = BuildDocumentWorkflow(
            descriptor_contract, project_validator, project_executor, bounded_execution_policy, files
        )
        self._project_run = ProjectRunWorkflow(self._build.execute, external_effects, project_runner)

    def run_project(self, request: ProjectRunRequest) -> ProjectRunResult:
        """Build the bound project, then run it for its real output within the allowed effects."""
        return self._project_run.execute(request)

    def run_project_unverified(
        self, request: ProjectRunRequest, confirm_unverified: bool
    ) -> UnverifiedProjectRunResult:
        return self._project_run.execute_unverified(request, confirm_unverified)

    def build_protocol(self) -> str:
        """The Build contract version this package speaks; clients check it instead of the package version."""
        return BUILD_PROTOCOL

    def version(self) -> RuntimeVersion:
        """The package and Python versions and the Build protocol; a git install also names its commit."""
        ce_version, direct_url = "unknown", None
        try:
            distribution = metadata.distribution("datamimic-ce")
            ce_version = distribution.version
            # Read the bytes and let the JSON parser judge them: a text read could raise UnicodeDecodeError (#704).
            for file in distribution.files or ():
                if file.name == "direct_url.json":
                    with contextlib.suppress(OSError):
                        direct_url = file.read_binary()
        except metadata.PackageNotFoundError:
            pass
        facts = {
            "ce_version": ce_version,
            "python_version": platform.python_version(),
            "build_protocol": BUILD_PROTOCOL,
        }
        commit = _git_commit(direct_url)
        return RuntimeVersion(**facts) if commit is None else GitRuntimeVersion(**facts, commit=commit)

    def reference(self, request: ReferenceRequest) -> ReferenceLookupResult:
        return self._catalog.reference(request)

    def reference_names(self, topic: ReferenceTopic) -> tuple[str, ...]:
        """Every name addressable via ``reference(topic, name)`` for the topic."""
        result = self.reference(ReferenceRequest(topic=topic))
        if not isinstance(result, ReferenceResult):
            raise LookupError(f"the catalog has no {topic} topic listing")
        if result.rules is not None:
            return tuple(str(rule.rule_id) for rule in result.rules)
        return tuple(entry.name for entry in result.entries or ())

    def scaffold(self, pattern: ProjectPattern) -> ProjectScaffold:
        """The starter project of one pattern: the files that Build proves as written."""
        match pattern:
            case ProjectPattern.FLAT:
                name = "starter"
        result = self._catalog.reference(ReferenceRequest(topic=ReferenceTopic.ASSEMBLY, name=name))
        for entry in (result.entries or ()) if isinstance(result, ReferenceResult) else ():
            if isinstance(entry, AuthoringAssemblyReference) and entry.starter is not None:
                return ProjectScaffold.from_starter(pattern, entry.starter.entry_xml, entry.starter.acceptance)
        raise LookupError(f"the catalog has no {name} starter project")

    def capabilities(self) -> DslCatalogSnapshot:
        """Return the typed, model-derived catalog for the CLI presentation boundary."""
        return self._catalog.snapshot()

    def capability_names(self, domain: CapabilityDomain) -> tuple[str, ...]:
        """Return the names owned by one typed capability domain."""
        return self._catalog.snapshot().capability_names(domain)

    def capability(self, domain: CapabilityDomain, name: str) -> CapabilityLookupResult:
        """Return one closed lookup result from the single live catalog snapshot."""
        return self._catalog.snapshot().capability(domain, name)

    def document_schema(self) -> dict[str, JsonValue]:
        """Return the closed registry-derived DM JSON schema through the injected contract."""
        return TypeAdapter(dict[str, JsonValue]).validate_python(self._descriptor_contract.document_schema())

    def schema(self, schema_id: AuthoringSchemaId) -> dict[str, JsonValue]:
        """Return one enum-addressed schema from the shared generated schema owner."""
        return contract_schemas(self._descriptor_contract).select(schema_id)

    def compile_document(self, request: CompileDocumentRequest) -> CompileDocumentResult:
        return self._compile_document.execute(request)

    def decompile_document(self, request: DecompileDocumentRequest) -> DecompileDocumentResult:
        return self._decompile_document.execute(request)

    def build(self) -> BuildResult:
        """Prove the bound project: its datamimic.xml entry against its acceptance/build.json."""
        return self._build.execute()

    def lint(self, request: LintRequest) -> LintResult:
        return self._validator.validate(request.xml)

    def dry_run(self, request: RunRequest) -> RunResult:
        return self._raw_xml.execute(request, phase=RunPhase.DRY_RUN)

    def run(self, request: RunRequest) -> RunResult:
        return self._raw_xml.execute(request, phase=RunPhase.RUN)
