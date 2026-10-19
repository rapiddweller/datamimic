import pytest

from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1
from datamimic_ce.authoring.domain.environments import DatabaseEnvironmentBinding, MongoDbEnvironmentBinding


def document(children):
    return DmJsonDocumentV1.model_validate({"root": {"kind": "setup", "children": children}})


def test_policy_keeps_ce_count_semantics_for_sources_and_nested_counts():
    from datamimic_ce.authoring.adapters.bounded_execution_policy import CeBoundedExecutionPolicy
    task = document([{"kind": "generate", "properties": {"name": "rows", "source": "input.csv"}, "children": [
        {"kind": "generate", "properties": {"name": "children", "count": "parent.n"}}]}])
    assert CeBoundedExecutionPolicy().diagnostics(task) == ()


@pytest.mark.parametrize("node", [{"kind": "include", "properties": {"uri": "child.xml"}},
    {"kind": "execute", "content": {"kind": "script", "value": "print(1)"}}])
def test_policy_rejects_unproven_nested_execution(node):
    from datamimic_ce.authoring.adapters.bounded_execution_policy import CeBoundedExecutionPolicy
    diagnostics = CeBoundedExecutionPolicy().diagnostics(document([node]))
    assert diagnostics and diagnostics[0].phase.value == "policy"
    assert diagnostics[0].path == ("document", "root", "children", 0)


def test_environment_bindings_validate_identity_family_and_duplicates():
    from datamimic_ce.authoring.domain.environment_bindings import validate_environment_bindings
    task = document([{"kind": "database", "properties": {"id": "primary"}}])
    assert validate_environment_bindings(task, (DatabaseEnvironmentBinding(environment="primary", family="database"),)) == ()
    assert validate_environment_bindings(task, ())[0].code.value == "unknown_environment"
    wrong = MongoDbEnvironmentBinding(environment="primary", family="mongodb")
    assert validate_environment_bindings(task, (wrong,))[0].code.value == "environment_family_mismatch"
    assert validate_environment_bindings(task, (wrong, wrong))[0].code.value == "duplicate_environment_binding"


def test_file_delivery_requires_a_target_on_each_product():
    from datamimic_ce.authoring.adapters.bounded_execution_policy import CeBoundedExecutionPolicy
    task = document([{"kind": "generate", "properties": {"name": "parents", "count": 1, "target": "JSON"}, "children": [
        {"kind": "generate", "properties": {"name": "children", "count": 1}}]}])
    findings = CeBoundedExecutionPolicy().diagnostics(task)
    assert any(item.code == "DM407" for item in findings)
