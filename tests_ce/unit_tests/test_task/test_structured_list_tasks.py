from pathlib import Path

from datamimic_ce.engine.dsl.model.values.scalar.key_model import KeyModel
from datamimic_ce.engine.dsl.model.values.structured.array_model import ArrayModel
from datamimic_ce.engine.dsl.model.values.structured.item_model import ItemModel
from datamimic_ce.engine.dsl.model.values.structured.list_model import ListModel
from datamimic_ce.engine.dsl.statements.values.scalar.key_statement import KeyStatement
from datamimic_ce.engine.dsl.statements.values.structured.array_statement import ArrayStatement
from datamimic_ce.engine.dsl.statements.values.structured.item_statement import ItemStatement
from datamimic_ce.engine.dsl.statements.values.structured.list_statement import ListStatement
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager
from datamimic_ce.engine.runtime.tasks.values.structured.list_task import ListTask


def _setup_context() -> SetupContext:
    return SetupContext(
        memstore_manager=MemstoreManager(),
        task_id="structured-list-task-test",
        test_mode=True,
        test_result_exporter=TestResultExporter(),
        default_separator="|",
        default_locale="en",
        default_dataset="US",
        use_mp=False,
        descriptor_dir=Path("."),
        num_process=1,
        default_variable_prefix="__",
        default_variable_suffix="__",
        default_line_separator="\n",
    )


def _item(*children: KeyStatement | ArrayStatement, condition: str | None = None) -> ItemStatement:
    statement = ItemStatement(ItemModel(condition=condition))
    statement.sub_statements = list(children)
    return statement


def _key(parent: ItemStatement, name: str, value: str, data_type: str = "string") -> KeyStatement:
    statement = KeyStatement(KeyModel(name=name, type=data_type, constant=value), parent)
    statement.sub_statements = []
    return statement


def _run_list(statement: ListStatement) -> dict:
    setup = _setup_context()
    parent = GenIterContext(setup, "profile")
    ListTask(ctx=setup, statement=statement).execute(parent)
    return parent.current_product


def test_list_keeps_item_order_and_isolates_heterogeneous_fields() -> None:
    first = ItemStatement(ItemModel())
    first.sub_statements = [_key(first, "name", "first"), _key(first, "number", "64", "int")]
    second = _item(ArrayStatement(ArrayModel(name="numbers", script="[3, 5]")))
    statement = ListStatement(ListModel(name="entries"))
    statement.sub_statements = [first, second]

    assert _run_list(statement) == {"entries": [{"name": "first", "number": 64}, {"numbers": [3, 5]}]}


def test_list_keeps_false_condition_as_none_until_list_converter_runs() -> None:
    present = ItemStatement(ItemModel())
    present.sub_statements = [_key(present, "value", "kept")]
    absent = ItemStatement(ItemModel(condition="False"))
    absent.sub_statements = [_key(absent, "unused", "ignored")]
    statement = ListStatement(ListModel(name="entries"))
    statement.sub_statements = [present, absent]

    assert _run_list(statement) == {"entries": [{"value": "kept"}, None]}

    statement = ListStatement(ListModel(name="entries", converter="RemoveNoneOrEmptyElement"))
    statement.sub_statements = [present, absent]
    assert _run_list(statement) == {"entries": [{"value": "kept"}]}


def test_empty_list_and_empty_array_values_are_preserved() -> None:
    empty_statement = ListStatement(ListModel(name="entries"))
    empty_statement.sub_statements = []
    assert _run_list(empty_statement) == {"entries": []}

    empty_array_item = _item(ArrayStatement(ArrayModel(name="values", script="[]")))
    statement = ListStatement(ListModel(name="entries"))
    statement.sub_statements = [empty_array_item]
    assert _run_list(statement) == {"entries": [{"values": []}]}
