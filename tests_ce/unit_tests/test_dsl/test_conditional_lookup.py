from datamimic_ce.engine.dsl.model.generate_model import GenerateModel
from datamimic_ce.engine.dsl.model.if_model import IfModel
from datamimic_ce.engine.dsl.statements.condition_statement import ConditionStatement
from datamimic_ce.engine.dsl.statements.generate_statement import GenerateStatement
from datamimic_ce.engine.dsl.statements.if_statement import IfStatement


def test_conditional_generate_lookup_keeps_executed_branch_semantics() -> None:
    outer = GenerateStatement(GenerateModel(name="outer", count="1"), None)
    condition = ConditionStatement(outer)
    branch = IfStatement(IfModel(condition="True"), condition)
    inner = GenerateStatement(GenerateModel(name="inner", count="1"), branch)
    outer.sub_statements = [condition]
    branch.sub_statements = [inner]

    assert outer.retrieve_sub_statement_by_fullname("outer|inner") is None
    condition.add_executed_statement(branch)
    assert outer.retrieve_sub_statement_by_fullname("outer|inner") is inner
