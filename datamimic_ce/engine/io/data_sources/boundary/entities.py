# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.


from typing import overload


@overload
def resolve_source_entity(source_entity: str | None, type_: str | None, name: str) -> str: ...


@overload
def resolve_source_entity(source_entity: str | None, type_: str | None, name: None) -> str | None: ...


def resolve_source_entity(source_entity: str | None, type_: str | None, name: str | None) -> str | None:
    """Resolve read entity for SQL and memstore sources: sourceEntity, type, then name."""
    return source_entity or type_ or name


def resolve_source_collection(source_entity: str | None, type_: str | None) -> str | None:
    """Resolve Mongo collection; a statement name is not a collection fallback."""
    return source_entity or type_
