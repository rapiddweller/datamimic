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

from collections.abc import Callable
from dataclasses import dataclass

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.domain_core.generator_registry import generator_namespace
from datamimic_ce.logger import logger
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.reference_statement import ReferenceStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.statements.variable_statement import VariableStatement


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


def _uses_global_constraint(stmt: GenerateStatement, seeded: bool) -> bool:
    return _is_global_constraint(stmt) or any(_is_global_constraint(child) for child in stmt.sub_statements)


def _has_delete_target(stmt: GenerateStatement, seeded: bool) -> bool:
    return any(".delete" in target for target in stmt.targets)


def _has_seeded_random_generator(stmt: Statement) -> bool:
    """True for a literal generator=... that draws on the rng. The generator CLASS is the source of
    truth: a BaseLiteralGenerator declares multiprocess_safe (guaranteed by the base class). An unknown
    or non-literal generator is treated as rng-driven (conservative -> single-process)."""
    if not isinstance(stmt, KeyStatement | VariableStatement) or not isinstance(stmt.generator, str):
        return False
    cls = generator_namespace().get(stmt.generator.split("(", 1)[0].strip())
    if cls is not None and issubclass(cls, BaseLiteralGenerator):
        return not cls.multiprocess_safe
    return True


def _seeded_order_dependent(stmt: GenerateStatement, seeded: bool) -> bool:
    """Under <setup rngSeed>, a feature whose per-row result depends on the worker count — a shuffled or
    cumulated <generate source>, or a seeded random literal generator — must run single-process so the
    output replays identically regardless of core count (EE distributes these deterministically)."""
    if not seeded:
        return False
    if stmt.source is not None and stmt.distribution.loads_all:
        return True
    return any(_has_seeded_random_generator(child) for child in stmt.sub_statements)


@dataclass(frozen=True)
class SingleProcessPolicy:
    """One feature CE serialises. ``ee_scalable`` adds the Enterprise upgrade hint to the log."""

    feature: str
    applies: Callable[[GenerateStatement, bool], bool]
    reason: str
    ee_scalable: bool


# THE registry — the single place to maintain CE's single-process policies.
POLICIES: tuple[SingleProcessPolicy, ...] = (
    SingleProcessPolicy(
        feature="unique/composite",
        applies=_uses_global_constraint,
        reason="'unique'/'composite' is a global cross-row constraint",
        ee_scalable=True,
    ),
    SingleProcessPolicy(
        feature="delete",
        applies=_has_delete_target,
        reason="delete operations run sequentially",
        ee_scalable=False,
    ),
    SingleProcessPolicy(
        feature="seeded-ordering",
        applies=_seeded_order_dependent,
        reason="rngSeed is set with a worker-count-dependent selection (shuffled/cumulated source or seeded generator)",
        ee_scalable=True,
    ),
)

_EE_HINT = " Multiprocess scaling of this is an Enterprise (EE) feature."


def resolve_single_process(stmt: GenerateStatement, requested_workers: int, seeded: bool = False) -> int | None:
    """Return 1 if any single-process policy applies to ``stmt`` (logging once when it overrides
    a multiprocess request, with the EE recommendation where the feature is EE-scalable), else
    None so the caller keeps ``requested_workers``. ``seeded`` = a <setup rngSeed> is in effect."""
    for policy in POLICIES:
        if not policy.applies(stmt, seeded):
            continue
        if requested_workers > 1:
            hint = _EE_HINT if policy.ee_scalable else ""
            logger.info(
                f"<generate> '{stmt.name}': {policy.reason} — CE runs it single-process "
                f"({requested_workers} requested workers ignored).{hint}"
            )
        return 1
    return None
