# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Thin facade over independently testable authoring use cases."""

from __future__ import annotations

from pydantic import JsonValue, TypeAdapter

from datamimic_ce.authoring.application.build import BuildDocumentWorkflow
from datamimic_ce.authoring.application.raw_xml import RawXmlUseCase
from datamimic_ce.authoring.application.schema import contract_schemas
from datamimic_ce.authoring.application.use_cases import (
    CompileDocumentUseCase,
    DecompileDocumentUseCase,
)
from datamimic_ce.authoring.domain.capabilities import CapabilityDomain, CapabilityLookupResult, DslCatalogSnapshot
from datamimic_ce.authoring.domain.reference import ReferenceResult
from datamimic_ce.authoring.domain.requests import (
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
    ProjectFiles,
)


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

    def reference(self, request: ReferenceRequest) -> ReferenceResult:
        return self._catalog.reference(request)

    def reference_names(self, topic: ReferenceTopic) -> tuple[str, ...]:
        """Every name addressable via ``reference(topic, name)`` for the topic."""
        result = self.reference(ReferenceRequest(topic=topic))
        if result.rules is not None:
            return tuple(str(rule.rule_id) for rule in result.rules)
        return tuple(entry.name for entry in result.entries or ())

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
