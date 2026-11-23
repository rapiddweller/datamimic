# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Find the statements of a project that reach outside its directory."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Literal

from datamimic_ce.authoring.adapters.dryrun import (
    UNREADABLE_TARGET,
    classify_targets,
    literal_include_graph,
    memstore_ids,
)
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.project_run import ExternalEffect, ExternalEffectKind
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH
from datamimic_ce.engine.dsl.api import (
    CompositeStatement,
    DatabaseStatement,
    DescriptorParser,
    ExecuteStatement,
    GenerateStatement,
    MongoDBStatement,
    SetupStatement,
    Statement,
    parse_properties,
    parse_xml_file,
)
from datamimic_ce.engine.io.api import resolve_target_entity

UNREADABLE_PROJECT = "The project entry or an included step could not be read."
_RUNTIME_ENVIRONMENT: Literal["development", "production"] = "development"


def external_effects(
    statement: SetupStatement, descriptor: str, memstores: frozenset[str], rdbms_clients: frozenset[str] = frozenset()
) -> tuple[ExternalEffect, ...]:
    """The effects of one statement tree. Files in the project, memstores, console and log are not external.
    The classification of targets is the bounded run's; this policy refuses what that policy neutralizes."""
    found: list[ExternalEffect] = []

    def effect(kind: ExternalEffectKind, name: str) -> None:
        found.append(ExternalEffect(kind=kind, name=name or "(unnamed)", descriptor=descriptor))

    def walk(node: Statement) -> None:
        if isinstance(node, DatabaseStatement):
            effect(ExternalEffectKind.DATABASE, node.model.id)
        elif isinstance(node, MongoDBStatement):
            effect(ExternalEffectKind.MONGODB, node.model.id)
        elif isinstance(node, ExecuteStatement):
            effect(ExternalEffectKind.EXECUTE, node.uri or "inline")
        elif isinstance(node, GenerateStatement):
            classified = classify_targets(node.targets, memstores)
            for name in classified.external:
                effect(ExternalEffectKind.TARGET, name)
            if classified.unreadable:
                effect(ExternalEffectKind.UNRESOLVED, UNREADABLE_TARGET)
            if node.create_table is not None:
                entity = resolve_target_entity(node.target_entity, node.type, node.name)
                for client in sorted(node.target_client_ids & rdbms_clients):
                    effect(ExternalEffectKind.SCHEMA, f"{client}.{entity}")
        if isinstance(node, CompositeStatement):
            for child in node.sub_statements:
                walk(child)

    walk(statement)
    return tuple(found)


class CeExternalEffectsDetector:
    """Reads the entry and every literal included step, as the run would, and classifies their statements."""

    def __init__(self, workspace: AuthoringWorkspaceContext) -> None:
        self._workspace = workspace

    def effects(self) -> tuple[ExternalEffect, ...]:
        entry = self._workspace.resolve_descriptor_path(PROJECT_ENTRY_PATH)
        entry_name = PROJECT_ENTRY_PATH.as_posix()
        try:
            root = parse_xml_file(entry)
            graph = literal_include_graph(root, entry)
            properties: dict[str, str] = {}
            for node in root.iter("include"):
                uri = node.get("uri", "")
                if PurePosixPath(uri).suffix == ".properties":
                    properties.update(parse_properties(entry.parent / uri))
            steps = {
                uri: self._parse(entry.parent / uri, properties)
                for uri, _ in graph
                if PurePosixPath(uri).suffix == ".xml"
            }
            statements = {entry_name: self._parse(entry, properties), **steps}
        except (OSError, ValueError):
            # A project that cannot be read as a whole cannot be shown safe.
            return (ExternalEffect(kind=ExternalEffectKind.UNRESOLVED, name=UNREADABLE_PROJECT, descriptor=entry_name),)
        memstores = frozenset(id_ for statement in statements.values() for id_ in memstore_ids(statement))
        rdbms_clients = frozenset(
            child.model.id
            for statement in statements.values()
            for child in statement.sub_statements
            if isinstance(child, DatabaseStatement)
        )
        return tuple(
            found
            for descriptor, statement in statements.items()
            for found in external_effects(statement, descriptor, memstores, rdbms_clients)
        )

    def _parse(self, path: Path, properties: dict[str, str]) -> SetupStatement:
        return DescriptorParser.parse(
            path, properties, _RUNTIME_ENVIRONMENT, profile_loader=self._workspace.load_connection_profile
        )
