# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Typed reference navigation and schemas generated from public DTOs."""

from __future__ import annotations

from typing import Annotated, Literal, assert_never

from pydantic import Field, JsonValue

from .common import AuthoringModel, NonEmptyStrictStr
from .diagnostics import RuleCatalogEntry
from .requests import AuthoringSchemaId, BuildRequestV5, ReferenceTopic


class ProjectStarter(AuthoringModel):
    """A minimal project: the text of ``datamimic.xml`` and the content of ``acceptance/build.json``."""

    entry_xml: NonEmptyStrictStr
    acceptance: BuildRequestV5


class AuthoringAssemblyReference(AuthoringModel):
    entry_kind: Literal["assembly"] = "assembly"
    name: NonEmptyStrictStr
    instruction: NonEmptyStrictStr
    starter: ProjectStarter | None = None


class AuthoringVariantReference(AuthoringModel):
    entry_kind: Literal["expectation"] = "expectation"
    name: NonEmptyStrictStr
    json_schema: dict[str, JsonValue]


class AuthoringExampleReference(AuthoringModel):
    entry_kind: Literal["example"] = "example"
    name: NonEmptyStrictStr
    title: NonEmptyStrictStr
    project: ProjectStarter | None = None
    verification: Literal["not_executed"] = "not_executed"


class AuthoringLearningReference(AuthoringModel):
    entry_kind: Literal["learning"] = "learning"
    name: NonEmptyStrictStr
    path: NonEmptyStrictStr
    description: NonEmptyStrictStr


ReferenceEntry = Annotated[
    AuthoringAssemblyReference | AuthoringVariantReference | AuthoringExampleReference | AuthoringLearningReference,
    Field(discriminator="entry_kind"),
]


class ReferenceResult(AuthoringModel):
    ok: Literal[True] = True
    topic: ReferenceTopic
    name: NonEmptyStrictStr | None = None
    content: NonEmptyStrictStr
    next_topics: tuple[ReferenceTopic, ...] = ()
    rules: tuple[RuleCatalogEntry, ...] | None = None
    entries: tuple[ReferenceEntry, ...] | None = None


class AuthoringContractSchemas(AuthoringModel):
    dm_json_document_v1: dict[str, JsonValue]
    dm_json_node_v1: dict[str, JsonValue]
    compile_document_request: dict[str, JsonValue]
    compile_document_result: dict[str, JsonValue]
    decompile_document_request: dict[str, JsonValue]
    decompile_document_result: dict[str, JsonValue]
    build_request_v5: dict[str, JsonValue]
    ready_build: dict[str, JsonValue]
    rejected_build: dict[str, JsonValue]
    build_result: dict[str, JsonValue]
    expectation_intent: dict[str, JsonValue]
    environment_binding: dict[str, JsonValue]
    diagnostic: dict[str, JsonValue]

    def select(self, schema_id: AuthoringSchemaId) -> dict[str, JsonValue]:
        match schema_id:
            case AuthoringSchemaId.DM_JSON_DOCUMENT_V1:
                return self.dm_json_document_v1
            case AuthoringSchemaId.DM_JSON_NODE_V1:
                return self.dm_json_node_v1
            case AuthoringSchemaId.COMPILE_DOCUMENT_REQUEST:
                return self.compile_document_request
            case AuthoringSchemaId.COMPILE_DOCUMENT_RESULT:
                return self.compile_document_result
            case AuthoringSchemaId.DECOMPILE_DOCUMENT_REQUEST:
                return self.decompile_document_request
            case AuthoringSchemaId.DECOMPILE_DOCUMENT_RESULT:
                return self.decompile_document_result
            case AuthoringSchemaId.READY_BUILD:
                return self.ready_build
            case AuthoringSchemaId.REJECTED_BUILD:
                return self.rejected_build
            case AuthoringSchemaId.BUILD_REQUEST_V5:
                return self.build_request_v5
            case AuthoringSchemaId.EXPECTATION_INTENT:
                return self.expectation_intent
            case AuthoringSchemaId.ENVIRONMENT_BINDING:
                return self.environment_binding
            case AuthoringSchemaId.DIAGNOSTIC:
                return self.diagnostic
            case AuthoringSchemaId.BUILD_RESULT:
                return self.build_result
        assert_never(schema_id)
