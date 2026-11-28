# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The mode a <key>/<variable> chooses from its attributes, and which generator init errors wait for a row."""

import uuid
from pathlib import Path

import pytest

from datamimic_ce.engine.dsl.api import GenerateStatement, KeyStatement, VariableStatement
from datamimic_ce.engine.dsl.model.generation.generate_model import GenerateModel
from datamimic_ce.engine.dsl.model.values.scalar.key_model import KeyModel
from datamimic_ce.engine.dsl.model.values.variables.variable_model import VariableModel
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager
from datamimic_ce.engine.runtime.tasks.values.key_variable_task import KeyVariableTask
from datamimic_ce.engine.runtime.tasks.values.scalar.key_task import KeyTask
from datamimic_ce.engine.runtime.tasks.values.variable.task import VariableTask
from datamimic_ce.errors import GeneratorConfigError, IssueCode, TaskConfigError

Mode = KeyVariableTask.Mode


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
        clients={},
        data_source_len={},
        properties={},
        namespace={},
        global_variables={},
        generators={},
        default_source_scripted=False,
        report_logging=False,
    )


def _key(setup_context: SetupContext, **attributes: str) -> KeyTask:
    generate = GenerateStatement(GenerateModel(name="rows", count="2", type="rows"), None)
    key = KeyStatement(KeyModel(name="field", **attributes), generate)
    generate.sub_statements = [key]
    key.sub_statements = []
    return KeyTask(setup_context, key)


@pytest.mark.parametrize(
    ("attributes", "mode"),
    [
        ({"script": "1"}, Mode.SCRIPT),
        ({"constant": "x"}, Mode.CONSTANT),
        ({"string": "x"}, Mode.STRING),
        ({"values": "('a', 'b')"}, Mode.VALUES),
        ({"generator": "IntegerGenerator(min=1, max=3)"}, Mode.GENERATOR),
        ({"generator": "IntegerGenerator(min=1, max=this.n)"}, Mode.LAZY_GENERATOR),
        ({"generator": "IntegerGenerator(min=1, max=this['n'])"}, Mode.LAZY_GENERATOR),
        ({"pattern": "[a-z]{3}"}, Mode.PATTERN),
        ({"type": "int", "min": "1", "max": "3"}, Mode.GENERATOR),
        ({"type": "string"}, Mode.RANDOM),
    ],
    ids=[
        "script",
        "constant",
        "string",
        "values",
        "generator",
        "lazy_generator",
        "lazy_generator_mapping",
        "pattern",
        "range",
        "random",
    ],
)
def test_key_attributes_choose_the_mode(setup_context: SetupContext, attributes: dict[str, str], mode: Mode) -> None:
    assert _key(setup_context, **attributes)._mode is mode


def test_variable_attributes_choose_a_mode(setup_context: SetupContext) -> None:
    generate = GenerateStatement(GenerateModel(name="rows", count="2", type="rows"), None)
    variable = VariableStatement(VariableModel(name="v", constant="x"), generate)
    variable.sub_statements = []
    assert VariableTask(setup_context, variable, None)._mode is Mode.CONSTANT


@pytest.mark.parametrize("generator", ["IntegerGenerator(min=1, bogus=3)", "IntegerGenerator(min=1,"])
def test_a_generator_that_cannot_be_built_stops_at_construction(setup_context: SetupContext, generator: str) -> None:
    with pytest.raises(TaskConfigError) as raised:
        _key(setup_context, generator=generator)
    assert raised.value.issue_code == IssueCode.TASK_EXPRESSION_EVAL_FAILED


def test_an_unknown_generator_class_stops_at_construction_with_its_typed_error(setup_context: SetupContext) -> None:
    with pytest.raises(GeneratorConfigError) as raised:
        _key(setup_context, generator="NoSuchGenerator")
    assert raised.value.issue_code == IssueCode.GENERATOR_CREATE_FAILED


def test_a_name_that_exists_only_per_row_is_built_on_the_first_row(setup_context: SetupContext) -> None:
    task = _key(setup_context, generator="IntegerGenerator(min=1, max=nosuchvariable)")
    assert task._mode is Mode.LAZY_GENERATOR


class _RaisesInConstructor:
    def __init__(self, kind: str = "attribute"):
        if kind == "attribute":
            self.missing_attribute  # noqa: B018
        elif kind == "name":
            missing_name  # type: ignore[name-defined]  # noqa: F821, B018
        else:
            {}["missing_key"]


@pytest.mark.parametrize("kind", ["attribute", "name", "key"])
def test_a_lookup_that_fails_inside_the_constructor_stops_at_construction(
    setup_context: SetupContext, kind: str
) -> None:
    """Only a lookup the expression itself cannot resolve waits for a row; the same error type raised by the
    constructor's own code is a real init error, also for a generate with no rows."""
    setup_context.namespace["RaisesInConstructor"] = _RaisesInConstructor
    with pytest.raises(TaskConfigError) as raised:
        _key(setup_context, generator=f"RaisesInConstructor(kind='{kind}')")
    assert raised.value.issue_code == IssueCode.TASK_EXPRESSION_EVAL_FAILED
