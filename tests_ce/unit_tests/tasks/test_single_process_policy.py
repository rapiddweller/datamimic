# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""Central single-process policy: every feature CE serialises hits the one registry path
(decision + log). Covers the merged unique features (<generate/variable/key ... unique>),
composite <reference>, and delete — so the policy/log is asserted in one place."""

import logging
from unittest.mock import MagicMock

import pytest

from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.reference_statement import ReferenceStatement
from datamimic_ce.statements.variable_statement import VariableStatement
from datamimic_ce.tasks.single_process_policy import resolve_single_process


def _gen(children=(), unique=False, targets=(), source=None, loads_all=False, generator=None) -> MagicMock:
    g = MagicMock(spec=GenerateStatement)
    g.name, g.unique, g.sub_statements, g.targets = "g", unique, list(children), list(targets)
    g.source, g.generator = source, generator
    g.distribution = MagicMock(loads_all=loads_all)
    return g


def _child(spec, unique=False, is_composite=False, generator=None) -> MagicMock:
    c = MagicMock(spec=spec)
    c.unique, c.generator = unique, generator
    if spec is ReferenceStatement:
        c.is_composite = is_composite
    return c


@pytest.mark.parametrize(
    "stmt",
    [
        _gen(unique=True),  # <generate source unique>
        _gen(children=[_child(KeyStatement, unique=True)]),  # <key values|source unique>
        _gen(children=[_child(VariableStatement, unique=True)]),  # <variable values|source unique>
        _gen(children=[_child(ReferenceStatement, unique=True)]),  # <reference unique>
        _gen(children=[_child(ReferenceStatement, is_composite=True)]),  # composite <reference>
        _gen(targets=["mytable.delete"]),  # delete operation
    ],
)
def test_policy_forces_single_process(stmt):
    assert resolve_single_process(stmt, requested_workers=4) == 1


def test_no_constraint_keeps_requested_workers():
    plain = _gen(children=[_child(KeyStatement, unique=False)])
    assert resolve_single_process(plain, requested_workers=4) is None


@pytest.mark.parametrize(
    "stmt",
    [
        _gen(source="x.csv", loads_all=True),  # shuffled/cumulated <generate source>
        _gen(children=[_child(KeyStatement, generator="IntegerGenerator(min=1, max=9)")]),  # seeded random generator
    ],
)
def test_seeded_ordering_forces_single_process(stmt):
    # worker-count-dependent under a seed -> single-process for machine-independent reproducibility
    assert resolve_single_process(stmt, requested_workers=4, seeded=True) == 1
    # without a seed, determinism is not requested -> keep multiprocess
    assert resolve_single_process(stmt, requested_workers=4, seeded=False) is None


def test_mp_safe_generator_not_forced_even_when_seeded():
    # increment/sequence generators do not draw on the seeded rng -> stay multiprocess
    g = _gen(children=[_child(KeyStatement, generator="GlobalIncrementGenerator()")])
    assert resolve_single_process(g, requested_workers=4, seeded=True) is None


def test_logs_once_on_override_with_ee_hint():
    messages: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            messages.append(record.getMessage())

    handler = _Capture()
    log = logging.getLogger("DATAMIMIC")
    prev_level = log.level
    log.setLevel(logging.INFO)  # bare unit test: engine isn't here to set the visible level
    log.addHandler(handler)
    try:
        resolve_single_process(_gen(unique=True), requested_workers=4)  # override -> logs
        resolve_single_process(_gen(unique=True), requested_workers=1)  # no MP asked -> silent
    finally:
        log.removeHandler(handler)
        log.setLevel(prev_level)

    assert sum("single-process" in m for m in messages) == 1
    assert any("Enterprise" in m for m in messages)  # EE recommendation on the scalable feature
