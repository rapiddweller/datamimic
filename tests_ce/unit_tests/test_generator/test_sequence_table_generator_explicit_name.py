# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""SequenceTableGenerator explicit sequence= name (migration parity: DBSequenceGenerator binds to
an arbitrarily DBA-named native sequence, e.g. 'zsv.t_angebote_id_seq' - not derivable from the
{type}_{name}_seq convention). Unit-tested with a recording fake client (same precedent as
test_generator_cache_behavior.py) because the assertion target is the literal string that reaches
the client, which a live-DB DSL test can't observe directly."""

import uuid
from pathlib import Path

import pytest

from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.domains.common.literal_generators.generator_util import GeneratorUtil
from datamimic_ce.exporters.test_result_exporter import TestResultExporter
from datamimic_ce.product_storage.memstore_manager import MemstoreManager


class DummyRootGenStmt:
    def __init__(self, type_: str = "orders", count: int = 10):
        self.type = type_
        self.count = count


class DummyStmt:
    def __init__(self, name: str, database: str, root_gen):
        self.name = name
        self.parent = None
        self.database = database
        self._root_gen = root_gen

    def get_root_generate_statement(self):
        return self._root_gen


class RecordingRdbmsClient:
    """Records every sequence_name it is asked for, so tests can assert the literal string."""

    def __init__(self):
        self._seq = {}
        self.requested_names: list[str] = []

    def get_current_sequence_number(
        self, sequence_name: str, table_name: str | None = None, column_name: str | None = None
    ) -> int:
        self.requested_names.append(sequence_name)
        return self._seq.get(sequence_name, 1000)

    def increase_sequence_number(
        self, sequence_name: str, increment: int, table_name: str | None = None, column_name: str | None = None
    ) -> None:
        self.requested_names.append(sequence_name)
        self._seq[sequence_name] = self._seq.get(sequence_name, 1000) + increment


@pytest.fixture()
def setup_context() -> SetupContext:
    return SetupContext(
        memstore_manager=MemstoreManager(),
        task_id=str(uuid.uuid4()),
        test_mode=True,
        test_result_exporter=TestResultExporter(),
        default_separator=",",
        default_locale="en_US",
        default_dataset="default",
        use_mp=False,
        descriptor_dir=Path("."),
        num_process=1,
        default_variable_prefix="${",
        default_variable_suffix="}",
        default_line_separator="\n",
        current_seed=123,
        clients={},
        data_source_len={},
        properties={},
        namespace={},
        global_variables={},
        generators={},
        default_source_scripted=False,
        report_logging=False,
    )


def _make(setup_context: SetupContext, generator_str: str, key: str):
    client = RecordingRdbmsClient()
    setup_context.clients["db1"] = client
    root_gen = DummyRootGenStmt(type_="orders", count=5)
    stmt = DummyStmt(name="id", database="db1", root_gen=root_gen)
    gen = GeneratorUtil(context=setup_context).create_generator(generator_str, stmt=stmt, key=key)
    return gen, client


def test_default_name_is_the_existing_convention(setup_context: SetupContext):
    _, client = _make(setup_context, "SequenceTableGenerator", key="k1")
    assert client.requested_names == ["orders_id_seq"]


def test_empty_parens_behave_like_no_parens(setup_context: SetupContext):
    _, client = _make(setup_context, "SequenceTableGenerator()", key="k2")
    assert client.requested_names == ["orders_id_seq"]


def test_explicit_sequence_name_reaches_client_verbatim(setup_context: SetupContext):
    gen, client = _make(setup_context, "SequenceTableGenerator(sequence='zsv.t_angebote_id_seq')", key="k3")
    assert client.requested_names == ["zsv.t_angebote_id_seq"]
    # pre_execute (the increment side) must resolve to the same explicit name
    gen.pre_execute(setup_context)
    assert client.requested_names[-1] == "zsv.t_angebote_id_seq"


def test_pre_execute_uses_convention_name_when_no_override(setup_context: SetupContext):
    gen, client = _make(setup_context, "SequenceTableGenerator", key="k4")
    gen.pre_execute(setup_context)
    assert client.requested_names == ["orders_id_seq", "orders_id_seq"]


def test_positional_arg_is_rejected(setup_context: SetupContext):
    with pytest.raises(ValueError, match="positional"):
        _make(setup_context, "SequenceTableGenerator('positional_value')", key="k5")


def test_unsupported_kwarg_is_rejected(setup_context: SetupContext):
    with pytest.raises(ValueError, match="bogus"):
        _make(setup_context, "SequenceTableGenerator(bogus='x')", key="k6")


def test_malformed_args_are_rejected(setup_context: SetupContext):
    with pytest.raises(ValueError):
        _make(setup_context, "SequenceTableGenerator(sequence=)", key="k7")


def test_non_string_sequence_is_rejected(setup_context: SetupContext):
    with pytest.raises(ValueError, match="string"):
        _make(setup_context, "SequenceTableGenerator(sequence=42)", key="k8")
