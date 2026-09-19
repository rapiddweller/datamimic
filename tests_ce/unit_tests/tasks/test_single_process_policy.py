# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""Central single-process policy: every feature CE serialises hits the one registry path
(decision + log). Covers the merged unique features (<generate/variable/key ... unique>),
composite <reference>, and delete — so the policy/log is asserted in one place."""

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.reference_statement import ReferenceStatement
from datamimic_ce.statements.variable_statement import VariableStatement
from datamimic_ce.tasks.single_process_policy import resolve_single_process
from datamimic_ce.clients.rdbms_client import RdbmsClient


def _gen(children=(), unique=False, targets=()) -> MagicMock:
    g = MagicMock(spec=GenerateStatement)
    g.name, g.unique, g.sub_statements, g.targets = "g", unique, list(children), list(targets)
    return g


def _child(spec, unique=False, is_composite=False) -> MagicMock:
    c = MagicMock(spec=spec)
    c.unique = unique
    if spec is ReferenceStatement:
        c.is_composite = is_composite
    return c


def _mysql_client() -> RdbmsClient:
    client = object.__new__(RdbmsClient)
    client._credential = SimpleNamespace(dbms="mysql")
    return client


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


def test_seeded_generate_forces_single_process():
    # nearly all seeded generation is worker-count-dependent, so any seeded <generate> runs single-process
    assert resolve_single_process(_gen(), requested_workers=4, seeded=True) == 1


def test_unseeded_generate_keeps_requested_workers():
    # no rngSeed -> determinism is not requested -> keep multiprocess
    assert resolve_single_process(_gen(), requested_workers=4, seeded=False) is None


def test_mysql_sequence_generator_forces_single_process() -> None:
    key = _child(KeyStatement)
    key.generator = "SequenceTableGenerator"
    key.database = "mysql-db"
    key.sub_statements = []

    assert resolve_single_process(
        _gen(children=[key]),
        requested_workers=4,
        clients={"mysql-db": _mysql_client()},
    ) == 1


def test_postgresql_sequence_generator_keeps_multiprocessing() -> None:
    key = _child(KeyStatement)
    key.generator = "SequenceTableGenerator(sequence='orders_id_seq')"
    key.database = "pg-db"
    key.sub_statements = []
    client = object.__new__(RdbmsClient)
    client._credential = SimpleNamespace(dbms="postgresql")

    assert resolve_single_process(
        _gen(children=[key]),
        requested_workers=4,
        clients={"pg-db": client},
    ) is None


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
