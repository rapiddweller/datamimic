import pytest

from datamimic_ce.engine.dsl.api import GenerateStatement, SetupStatement, find_generate_statement_by_name
from datamimic_ce.engine.dsl.model.flow.branches.if_model import IfModel
from datamimic_ce.engine.dsl.model.generation.generate_model import GenerateModel
from datamimic_ce.engine.dsl.model.setup.setup_model import SetupModel
from datamimic_ce.engine.dsl.statements.flow.branches.condition_statement import ConditionStatement
from datamimic_ce.engine.dsl.statements.flow.branches.if_statement import IfStatement
from datamimic_ce.engine.runtime.contracts import FactoryConfig
from datamimic_ce.engine.runtime.lifecycle.runner import RuntimeRunSession


def _generate(name: str, *, count: str | None = None, target: str | None = None) -> GenerateStatement:
    return GenerateStatement(GenerateModel(name=name, count=count or "1", target=target), None)


def _session_without_initialization() -> RuntimeRunSession:
    return RuntimeRunSession.__new__(RuntimeRunSession)


def test_entity_lookup_returns_matching_statement_and_first_depth_first_duplicate() -> None:
    root = _generate("root")
    first_parent = _generate("first-parent")
    first_match = _generate("selected")
    second_match = _generate("selected")
    root.sub_statements = [first_parent, second_match]
    first_parent.sub_statements = [first_match]

    assert find_generate_statement_by_name(root, "root") is root
    assert find_generate_statement_by_name(root, "selected") is first_match


def test_entity_lookup_does_not_descend_into_non_generate_branches() -> None:
    root = _generate("root")
    condition = ConditionStatement(root)
    branch = IfStatement(IfModel(condition="True"), condition)
    hidden_match = _generate("selected")
    root.sub_statements = [condition]
    condition.sub_statements = [branch]
    branch.sub_statements = [hidden_match]

    assert find_generate_statement_by_name(root, "selected") is None


def test_missing_entity_keeps_factory_error_message() -> None:
    root = SetupStatement(SetupModel())
    root.sub_statements = []

    with pytest.raises(ValueError) as error:
        _session_without_initialization()._validate_xml_model(root, FactoryConfig("missing", 7))

    assert error.value.args == ("Entity name 'missing' not found in the XML model",)


def test_factory_validation_keeps_count_and_multi_target_mutations() -> None:
    root = SetupStatement(SetupModel())
    selected = _generate("selected", count="3", target="CSV,JSON")
    root.sub_statements = [selected]

    _session_without_initialization()._validate_xml_model(root, FactoryConfig("selected", 7))

    assert selected.count == "7"
    assert selected.targets == set()
