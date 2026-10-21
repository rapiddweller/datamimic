# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Named boundaries from Authoring application to CE-owned adapters."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Protocol

from .domain.capabilities import DslCatalogSnapshot
from .domain.diagnostics import Diagnostic
from .domain.dm_json import DmJsonCompilation, DmJsonDocumentV1
from .domain.reference import ReferenceResult
from .domain.requests import (
    BoundedExecutionEvidence,
    BoundedExecutionRequest,
    IncludeGraphResult,
    LintResult,
    ReferenceRequest,
)


class DmJsonDescriptorContract(Protocol):
    def compile(self, document: DmJsonDocumentV1) -> DmJsonCompilation: ...
    def decompile(self, xml: str) -> DmJsonDocumentV1: ...
    def document_schema(self) -> dict[str, object]: ...
    def project_document_schema(self, schema: Mapping[str, object]) -> dict[str, object]: ...


class DslCatalog(Protocol):
    def snapshot(self) -> DslCatalogSnapshot: ...
    def reference(self, request: ReferenceRequest) -> ReferenceResult: ...


class DescriptorValidator(Protocol):
    def validate(self, xml: str, *, descriptor_path: PurePosixPath | None = None) -> LintResult: ...
    def include_graph(self, xml: str) -> IncludeGraphResult: ...


class BoundedExecutor(Protocol):
    def execute(self, request: BoundedExecutionRequest) -> BoundedExecutionEvidence: ...


class BoundedExecutionPolicy(Protocol):
    def diagnostics(self, document: DmJsonDocumentV1) -> tuple[Diagnostic, ...]: ...
