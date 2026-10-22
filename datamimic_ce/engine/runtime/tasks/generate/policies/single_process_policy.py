# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Central registry of features CE runs single-process.

One place to maintain WHICH features force single-process, the user-facing reason, and
the Enterprise (EE) scaling recommendation. Add a feature here (not scattered in the
worker logic) to make CE serialise it; ``resolve_single_process`` is the single entry
point used by the generate task.
"""

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from datamimic_ce.engine.dsl.api import (
    CompositeStatement,
    ElementStatement,
    GenerateStatement,
    IncludeStatement,
    KeyStatement,
    ReferenceStatement,
    Statement,
    VariableStatement,
)
from datamimic_ce.engine.io.api import RegisteredClient, uses_mysql_sequence_storage
from datamimic_ce.engine.runtime.logging import logger
from datamimic_ce.engine.runtime.tasks.values.construction.entity_constructor import parse_constructor_string
from datamimic_ce.engine.runtime.tasks.values.construction.factory import RUNTIME_GENERATOR_TYPES

ClientMap = Mapping[str, RegisteredClient]
_GLOBAL_INCREMENT_TYPE = next(
    generator_type
    for generator_type in RUNTIME_GENERATOR_TYPES
    if generator_type.__name__ == "GlobalIncrementGenerator"
)


def _is_global_constraint(stmt: Statement) -> bool:
    """A cross-row constraint (no value/tuple repeats across the whole run): a unique
    <generate>/<key>/<variable>, or a unique or composite <reference>."""
    if isinstance(stmt, GenerateStatement):
        return bool(stmt.unique)
    if isinstance(stmt, KeyStatement | VariableStatement):
        return bool(stmt.unique)
    if isinstance(stmt, ReferenceStatement):
        return bool(stmt.unique) or stmt.is_composite
    return False


def _uses_global_constraint(stmt: GenerateStatement, seeded: bool, clients: ClientMap) -> bool:
    stack: list[Statement] = [stmt]
    while stack:
        current = stack.pop()
        if _is_global_constraint(current):
            return True
        if isinstance(current, CompositeStatement):
            stack.extend(current.sub_statements)
    return False


def _uses_domain_identifiers(stmt: GenerateStatement, seeded: bool, clients: ClientMap) -> bool:
    from datamimic_ce.domains.api import get_entity_spec

    stack: list[Statement] = [stmt]
    while stack:
        current = stack.pop()
        # Included descriptors are resolved at execution time and may allocate identifiers.
        # Keep their enclosing generate serial without evaluating dynamic includes early.
        if isinstance(current, IncludeStatement):
            return True
        if isinstance(current, VariableStatement) and current.entity is not None:
            entity_name, _kwargs = parse_constructor_string(current.entity)
            spec = get_entity_spec(entity_name)
            if spec is not None and any(field.unique_identifier_format is not None for field in spec.attributes):
                return True
        if isinstance(current, CompositeStatement):
            stack.extend(current.sub_statements)
    return False


def _uses_global_increment(
    stmt: GenerateStatement,
    seeded: bool,
    clients: ClientMap,
    *,
    generators: Mapping[str, object] | None = None,
) -> bool:
    """A qualified counter must stay in its owning process, including nested fields
    and explicitly named instances already resolved by setup declarations/includes."""
    stack: list[Statement] = list(stmt.sub_statements)
    while stack:
        child = stack.pop()
        if isinstance(child, KeyStatement | VariableStatement | ElementStatement) and child.generator is not None:
            expression = child.generator.strip()
            if expression.split("(", 1)[0].strip() == "GlobalIncrementGenerator" or (
                generators is not None and isinstance(generators.get(expression), _GLOBAL_INCREMENT_TYPE)
            ):
                return True
        if isinstance(child, CompositeStatement):
            stack.extend(child.sub_statements)
    return False


def _has_delete_target(stmt: GenerateStatement, seeded: bool, clients: ClientMap) -> bool:
    return any(".delete" in target for target in stmt.targets)


def _seeded(stmt: GenerateStatement, seeded: bool, clients: ClientMap) -> bool:
    """Under <setup rngSeed> nearly all generation draws on a per-worker rng that restarts per worker,
    so the output depends on the core count. CE runs any seeded generate single-process to keep it
    reproducible regardless of machine; EE distributes seeded generation deterministically."""
    return seeded


def _uses_mysql_sequence(stmt: GenerateStatement, seeded: bool, clients: ClientMap) -> bool:
    mysql_sources = {source_id for source_id, client in clients.items() if uses_mysql_sequence_storage(client)}
    if not mysql_sources:
        return False

    stack: list[Statement] = list(stmt.sub_statements)
    while stack:
        child = stack.pop()
        if isinstance(child, KeyStatement):
            generator = child.generator
            if (
                generator is not None
                and generator.startswith("SequenceTableGenerator")
                and child.database in mysql_sources
            ):
                return True
        if isinstance(child, CompositeStatement):
            stack.extend(child.sub_statements)
    return False


@dataclass(frozen=True)
class SingleProcessPolicy:
    """One feature CE serialises. ``ee_scalable`` adds the Enterprise upgrade hint to the log."""

    feature: str
    applies: Callable[[GenerateStatement, bool, ClientMap], bool]
    reason: str
    ee_scalable: bool


# THE registry — the single place to maintain CE's single-process policies.
POLICIES: tuple[SingleProcessPolicy, ...] = (
    SingleProcessPolicy(
        feature="mysql-sequence",
        applies=_uses_mysql_sequence,
        reason="MySQL SequenceTableGenerator has no atomic native sequence reservation",
        ee_scalable=False,
    ),
    SingleProcessPolicy(
        feature="unique/composite",
        applies=_uses_global_constraint,
        reason="'unique'/'composite' is a global cross-row constraint",
        ee_scalable=True,
    ),
    SingleProcessPolicy(
        feature="domain-identifier",
        applies=_uses_domain_identifiers,
        reason="domain identifiers require one run-wide allocation scope, including pages and deferred includes",
        ee_scalable=True,
    ),
    SingleProcessPolicy(
        feature="global-increment",
        applies=_uses_global_increment,
        reason="GlobalIncrementGenerator counters are local to one root setup context, including pages",
        ee_scalable=False,
    ),
    SingleProcessPolicy(
        feature="delete",
        applies=_has_delete_target,
        reason="delete operations run sequentially",
        ee_scalable=False,
    ),
    SingleProcessPolicy(
        feature="seeded",
        applies=_seeded,
        reason="rngSeed is set — seeded generation runs single-process to stay reproducible across machines",
        ee_scalable=True,
    ),
)

_EE_HINT = " Multiprocess scaling of this is an Enterprise (EE) feature."


def _control_value(text: str) -> str:
    """Make descriptor text safe for a ' | '-delimited CONTROL record: no line breaks, no spaced pipes."""
    return re.sub(r"\s*\|\s*", "|", " ".join(text.split()))


def resolve_single_process(
    stmt: GenerateStatement,
    requested_workers: int,
    seeded: bool = False,
    clients: ClientMap | None = None,
    *,
    generators: Mapping[str, object] | None = None,
) -> int | None:
    """Return 1 if any single-process policy applies to ``stmt`` (logging once when it overrides
    a multiprocess request, with the EE recommendation where the feature is EE-scalable), else
    None so the caller keeps ``requested_workers``. ``seeded`` = a <setup rngSeed> is in effect."""
    resolved_clients: ClientMap = clients or {}
    for policy in POLICIES:
        applies = (
            _uses_global_increment(stmt, seeded, resolved_clients, generators=generators)
            if policy.applies is _uses_global_increment
            else policy.applies(stmt, seeded, resolved_clients)
        )
        if not applies:
            continue
        if requested_workers > 1:
            hint = _EE_HINT if policy.ee_scalable else ""
            logger.info(
                "CONTROL | kind=policy | policy=%s | stmt=%s | override_workers=%s -> %s | reason=%s",
                policy.feature,
                _control_value(stmt.full_name),
                requested_workers,
                1,
                policy.reason + hint,
            )
        return 1
    return None
