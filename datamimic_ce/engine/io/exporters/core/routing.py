# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from collections.abc import Mapping

from datamimic_ce.engine.dsl.vocabulary.constants.attribute_constants import META_TARGET_ENTITY, META_TYPE
from datamimic_ce.engine.dsl.vocabulary.enums.operation_enums import ExportOperation
from datamimic_ce.engine.io.clients.client import Client
from datamimic_ce.engine.io.clients.operations import is_mongodb_client
from datamimic_ce.engine.io.contracts import ExportMetadata


def resolve_target_entity(target_entity: str | None, type_: str | None, name: str) -> str:
    """Resolve output entity: targetEntity, type, then name."""
    return target_entity or type_ or name


def resolve_target_entity_from_metadata(name: str, metadata: ExportMetadata | Mapping[str, str] | None) -> str:
    """Resolve an output entity from exporter metadata."""
    md = metadata or {}
    return resolve_target_entity(md.get(META_TARGET_ENTITY), md.get(META_TYPE), name)


def has_mongodb_upsert_target(targets: set[str], clients: Mapping[str, Client]) -> bool:
    for target in targets:
        if "." in target:
            consumer, operation = target.split(".", 1)
            if operation == ExportOperation.UPSERT.value and is_mongodb_client(clients.get(consumer)):
                return True
    return False
