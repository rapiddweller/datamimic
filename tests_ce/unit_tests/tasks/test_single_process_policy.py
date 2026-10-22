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

from datamimic_ce.engine.dsl.api import GenerateStatement
from datamimic_ce.engine.dsl.model.setup.include_model import IncludeModel
from datamimic_ce.engine.dsl.statements.setup.include_statement import IncludeStatement
from datamimic_ce.engine.dsl.statements.values.references.reference_statement import ReferenceStatement
from datamimic_ce.engine.dsl.statements.values.scalar.key_statement import KeyStatement
from datamimic_ce.engine.dsl.statements.values.variables.variable_statement import VariableStatement
from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.runtime.tasks.generate.policies.single_process_policy import resolve_single_process


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
    client._credential = SimpleNamespace(dbms=Dbms.MYSQL)
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


@pytest.mark.parametrize("uri", ["unopened.xml", "{path_determined_per_parent}"])
@pytest.mark.parametrize("nested", [False, True])
def test_deferred_include_keeps_identifier_allocation_in_one_process(uri: str, nested: bool) -> None:
    include = IncludeStatement(IncludeModel(uri=uri))
    children = [_gen(children=[include])] if nested else [include]

    assert resolve_single_process(_gen(children=children), requested_workers=2) == 1


@pytest.mark.parametrize("identifier_format, expected", [(None, None), ("PAN", 1)])
def test_domain_identifier_policy_parses_entity_constructor(
    monkeypatch: pytest.MonkeyPatch, identifier_format: str | None, expected: int | None
) -> None:
    child = _child(VariableStatement)
    child.entity = "Person(code='0012', mode=fast)"
    spec = SimpleNamespace(attributes=[SimpleNamespace(unique_identifier_format=identifier_format)])
    names: list[str] = []

    def get_entity_spec(name: str) -> SimpleNamespace:
        names.append(name)
        return spec

    monkeypatch.setattr("datamimic_ce.domains.api.get_entity_spec", get_entity_spec)

    assert resolve_single_process(_gen(children=[child]), requested_workers=4) == expected
    assert names == ["Person"]


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
    client._credential = SimpleNamespace(dbms=Dbms.POSTGRESQL)

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

    control = [dict(part.split("=", 1) for part in m.split(" | ")[1:]) for m in messages if m.startswith("CONTROL |")]
    policy_lines = [line for line in control if line["kind"] == "policy"]
    assert len(policy_lines) == 1
    assert policy_lines[0]["policy"] == "unique/composite"
    assert policy_lines[0]["override_workers"] == "4 -> 1"
    assert "Enterprise (EE) feature" in policy_lines[0]["reason"]  # EE recommendation on the scalable feature


def test_descriptor_name_cannot_inject_control_fields() -> None:
    messages: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            messages.append(record.getMessage())

    stmt = _gen(unique=True)
    stmt.full_name = "a | kind=end | status=ok\nCONTROL | kind=end"
    handler = _Capture()
    log = logging.getLogger("DATAMIMIC")
    prev_level = log.level
    log.setLevel(logging.INFO)
    log.addHandler(handler)
    try:
        assert resolve_single_process(stmt, requested_workers=4) == 1
    finally:
        log.removeHandler(handler)
        log.setLevel(prev_level)

    control = [m for m in messages if m.startswith("CONTROL |")]
    assert len(control) == 1
    assert "\n" not in control[0]
    parsed = dict(part.split("=", 1) for part in control[0].split(" | ")[1:])
    assert parsed["kind"] == "policy"
    assert "stmt" in parsed


@pytest.mark.parametrize(
    "field",
    [
        '<key name="id" generator="GlobalIncrementGenerator"/>',
        '<variable name="id" generator="GlobalIncrementGenerator()"/>',
        '<key name="value" constant="text"><element name="id" generator="GlobalIncrementGenerator"/></key>',
        '<nestedKey name="items" count="2"><key name="id" generator=" GlobalIncrementGenerator ( ) "/></nestedKey>',
        '<condition><if condition="True"><generate name="children" count="2" target="">'
        '<key name="id" generator="GlobalIncrementGenerator"/></generate></if></condition>',
    ],
)
def test_global_increment_policy_walks_native_statements(tmp_path, field):
    from datamimic_ce.engine.dsl.api import DescriptorParser
    from datamimic_ce.engine.io.api import load_connection_profile

    descriptor = tmp_path / "policy.xml"
    descriptor.write_text(f'<setup><generate name="rows" count="3" target="">{field}</generate></setup>')
    statement = DescriptorParser.parse(descriptor, None, "production", profile_loader=load_connection_profile)
    assert resolve_single_process(statement.sub_statements[0], requested_workers=2) == 1


@pytest.mark.parametrize("expression", ["IncrementGenerator", "GlobalIncrementGeneratorOther", "other"])
def test_other_generators_keep_requested_workers(expression):
    key = _child(KeyStatement)
    key.generator = expression
    assert resolve_single_process(_gen(children=[key]), requested_workers=2) is None


@pytest.mark.parametrize("relabel_policy", [False, True])
def test_only_referenced_global_increment_alias_forces_serial(monkeypatch, relabel_policy):
    from dataclasses import replace

    from datamimic_ce.engine.runtime.tasks.generate.policies import single_process_policy
    from datamimic_ce.engine.runtime.tasks.values.construction.global_increment import GlobalIncrementGenerator

    if relabel_policy:
        monkeypatch.setattr(
            single_process_policy,
            "POLICIES",
            tuple(replace(policy, feature="descriptive label") for policy in single_process_policy.POLICIES),
        )

    # Named instances are already resolved in setup, including inherited includes.
    root = SimpleNamespace(global_increment_registry=None)
    root.root = root
    counter = GlobalIncrementGenerator("counter", root)
    key = _child(KeyStatement)
    key.generator = "counter"
    statement = _gen(children=[key])
    assert resolve_single_process(statement, 2, generators={"counter": counter}) == 1
    key.generator = "IncrementGenerator"
    assert resolve_single_process(statement, 2, generators={"counter": counter}) is None
    key.generator = "counter"
    assert resolve_single_process(statement, 2, generators={"counter": object()}) is None
