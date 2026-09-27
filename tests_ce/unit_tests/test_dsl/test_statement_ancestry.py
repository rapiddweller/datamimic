from datamimic_ce.engine.dsl.api import (
    ConditionStatement,
    GenerateStatement,
    IfStatement,
    Statement,
    get_nearest_generate_statement,
)
from datamimic_ce.engine.dsl.model.flow.branches.if_model import IfModel


def test_root_generate_lookup_stops_at_setup_and_finds_enclosing_generate() -> None:
    setup = Statement(None, None)
    generate = object.__new__(GenerateStatement)
    Statement.__init__(generate, "outer", setup)
    child = Statement("leaf", generate)

    assert get_nearest_generate_statement(setup) is None
    assert get_nearest_generate_statement(generate) is None
    assert get_nearest_generate_statement(child) is generate


def test_root_generate_lookup_uses_nearest_generate_and_condition_branches_are_transparent() -> None:
    setup = Statement(None, None)
    outer = object.__new__(GenerateStatement)
    Statement.__init__(outer, "outer", setup)
    inner = object.__new__(GenerateStatement)
    Statement.__init__(inner, "inner", outer)
    condition = ConditionStatement(inner)
    branch = IfStatement(IfModel(condition="True"), condition)
    leaf = Statement("leaf", branch)

    assert get_nearest_generate_statement(inner) is None
    assert leaf.parent_stmt is inner
    assert get_nearest_generate_statement(leaf) is inner
