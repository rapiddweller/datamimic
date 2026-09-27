import logging

from datamimic_ce.engine.dsl.api import (
    ConditionStatement,
    GenerateStatement,
    IfStatement,
    retrieve_sub_statement_by_fullname,
)
from datamimic_ce.engine.dsl.model.flow.branches.if_model import IfModel
from datamimic_ce.engine.dsl.model.generation.generate_model import GenerateModel


def _generate(name: str) -> GenerateStatement:
    return GenerateStatement(GenerateModel(name=name, count="1"), None)


def test_conditional_generate_lookup_keeps_executed_branch_semantics() -> None:
    outer = _generate("outer")
    condition = ConditionStatement(outer)
    branch = IfStatement(IfModel(condition="True"), condition)
    inner = GenerateStatement(GenerateModel(name="inner", count="1"), branch)
    outer.sub_statements = [condition]
    branch.sub_statements = [inner]

    assert retrieve_sub_statement_by_fullname(outer, "outer|inner") is None
    condition.add_executed_statement(branch)
    assert retrieve_sub_statement_by_fullname(outer, "outer|inner") is inner


def test_conditional_lookup_uses_the_executed_set_iteration_without_copying() -> None:
    outer = _generate("outer")
    condition = ConditionStatement(outer)
    first = IfStatement(IfModel(condition="True"), condition)
    second = IfStatement(IfModel(condition="True"), condition)
    first_inner = _generate("inner")
    second_inner = _generate("inner")
    outer.sub_statements = [condition]
    first.sub_statements = [first_inner]
    second.sub_statements = [second_inner]

    executed = condition.executed_statements
    condition.add_executed_statement(first)
    condition.add_executed_statement(second)
    condition.add_executed_statement(first)

    assert condition.executed_statements is executed
    assert isinstance(executed, set)
    assert len(executed) == 2
    assert retrieve_sub_statement_by_fullname(outer, "outer|inner") is next(iter(executed)).sub_statements[0]


def test_matching_composite_returns_its_miss_without_searching_later_siblings() -> None:
    outer = _generate("outer")
    decoy = _generate("chosen")
    condition = ConditionStatement(outer)
    branch = IfStatement(IfModel(condition="True"), condition)
    chosen = _generate("chosen")
    target = _generate("target")
    outer.sub_statements = [decoy, condition]
    decoy.sub_statements = []
    branch.sub_statements = [chosen]
    chosen.sub_statements = [target]
    condition.add_executed_statement(branch)

    assert retrieve_sub_statement_by_fullname(outer, "outer|chosen|target") is None

    outer.sub_statements = [condition]
    assert retrieve_sub_statement_by_fullname(outer, "outer|chosen|target") is target


def test_conditional_lookup_recurses_only_through_executed_nested_conditions() -> None:
    outer = _generate("outer")
    condition = ConditionStatement(outer)
    branch = IfStatement(IfModel(condition="True"), condition)
    nested_condition = ConditionStatement(branch)
    nested_branch = IfStatement(IfModel(condition="True"), nested_condition)
    target = _generate("target")
    outer.sub_statements = [condition]
    branch.sub_statements = [nested_condition]
    nested_branch.sub_statements = [target]
    condition.add_executed_statement(branch)

    assert retrieve_sub_statement_by_fullname(outer, "outer|target") is None
    nested_condition.add_executed_statement(nested_branch)
    assert retrieve_sub_statement_by_fullname(outer, "outer|target") is target


def test_conditional_lookup_preserves_missing_execution_and_malformed_path_diagnostics(caplog, monkeypatch) -> None:
    outer = _generate("outer")
    condition = ConditionStatement(outer)
    outer.sub_statements = [condition]
    # A prior engine run installs the operational stderr handler and disables
    # propagation; caplog needs the record to reach its root handler.
    monkeypatch.setattr(logging.getLogger("DATAMIMIC"), "propagate", True)

    with caplog.at_level(logging.ERROR, logger="DATAMIMIC"):
        assert retrieve_sub_statement_by_fullname(outer, "outer|inner") is None

    assert caplog.messages == [
        "Error when retrieve sub statement: Can't retrieve 'None' of `<condition>` "
        "because it didn't execute any element"
    ]
    caplog.clear()

    with caplog.at_level(logging.ERROR, logger="DATAMIMIC"):
        assert retrieve_sub_statement_by_fullname(outer, "unknown") is None

    assert caplog.messages == [
        "Error when retrieve sub statement by fullname 'unknown': list index out of range"
    ]
