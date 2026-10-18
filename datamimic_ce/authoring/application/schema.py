# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Project schemas from actual DTOs and the injected CE descriptor contract."""

from pydantic import JsonValue, TypeAdapter

from datamimic_ce.authoring.domain.diagnostics import Diagnostic
from datamimic_ce.authoring.domain.dm_json import DmJsonNodeV1
from datamimic_ce.authoring.domain.environments import ConfiguredEnvironmentBinding
from datamimic_ce.authoring.domain.expectations import ExpectationIntent
from datamimic_ce.authoring.domain.reference import AuthoringContractSchemas
from datamimic_ce.authoring.domain.requests import (
    BuildRequestV4,
    BuildResult,
    CompileDocumentRequest,
    CompileDocumentResult,
    DecompileDocumentRequest,
    DecompileDocumentResult,
    ReadyBuild,
    RejectedBuild,
)
from datamimic_ce.authoring.ports import DmJsonDescriptorContract


def contract_schemas(contract: DmJsonDescriptorContract) -> AuthoringContractSchemas:
    return AuthoringContractSchemas(
        dm_json_document_v1=TypeAdapter(dict[str, JsonValue]).validate_python(contract.document_schema()),
        dm_json_node_v1=TypeAdapter(dict[str, JsonValue]).validate_python(
            contract.project_document_schema(DmJsonNodeV1.model_json_schema())
        ),
        compile_document_request=TypeAdapter(dict[str, JsonValue]).validate_python(
            contract.project_document_schema(CompileDocumentRequest.model_json_schema())
        ),
        compile_document_result=TypeAdapter(dict[str, JsonValue]).validate_python(
            contract.project_document_schema(TypeAdapter(CompileDocumentResult).json_schema())
        ),
        decompile_document_request=DecompileDocumentRequest.model_json_schema(),
        decompile_document_result=TypeAdapter(dict[str, JsonValue]).validate_python(
            contract.project_document_schema(TypeAdapter(DecompileDocumentResult).json_schema())
        ),
        build_request_v4=TypeAdapter(dict[str, JsonValue]).validate_python(
            contract.project_document_schema(BuildRequestV4.model_json_schema())
        ),
        ready_build=TypeAdapter(dict[str, JsonValue]).validate_python(
            contract.project_document_schema(ReadyBuild.model_json_schema())
        ),
        rejected_build=TypeAdapter(dict[str, JsonValue]).validate_python(
            contract.project_document_schema(RejectedBuild.model_json_schema())
        ),
        build_result=TypeAdapter(dict[str, JsonValue]).validate_python(
            contract.project_document_schema(TypeAdapter(BuildResult).json_schema())
        ),
        expectation_intent=TypeAdapter(ExpectationIntent).json_schema(),
        environment_binding=TypeAdapter(ConfiguredEnvironmentBinding).json_schema(),
        diagnostic=Diagnostic.model_json_schema(),
    )
