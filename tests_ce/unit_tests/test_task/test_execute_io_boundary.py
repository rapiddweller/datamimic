from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from datamimic_ce.engine.dsl.model.flow.commands.execute_model import ExecuteModel
from datamimic_ce.engine.dsl.statements.flow.commands.execute_statement import ExecuteStatement
from datamimic_ce.engine.runtime.tasks.flow.commands.execute_task import ExecuteTask


@pytest.mark.parametrize("target, missing_key", [("missing", "missing"), (None, None)])
def test_sql_execute_interpolates_before_missing_client_lookup(target, missing_key) -> None:
    root = SimpleNamespace(clients={})
    context = SimpleNamespace(
        root=root,
        evaluate_python_expression=Mock(return_value="SELECT 9"),
    )
    statement = ExecuteStatement(
        ExecuteModel.model_construct(target=target),
        exec_type="sql",
        code="SELECT {value}",
    )

    with pytest.raises(KeyError) as raised:
        ExecuteTask(statement).execute(context)

    assert raised.value.args == (missing_key,)
    context.evaluate_python_expression.assert_called_once_with("f'''SELECT {value}'''")
