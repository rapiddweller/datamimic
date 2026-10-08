from pathlib import Path
from typing import cast

import pytest

from datamimic_ce.engine.dsl.model.flow.commands.execute_model import ExecuteModel
from datamimic_ce.engine.dsl.statements.flow.commands.execute_statement import ExecuteStatement
from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.clients.client import Client, RegisteredClient
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.io.contracts import SqlScriptClient
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager
from datamimic_ce.engine.runtime.tasks.flow.commands.execute_task import ExecuteTask


def _context(descriptor_dir: Path) -> SetupContext:
    return SetupContext(
        memstore_manager=MemstoreManager(),
        task_id="execute-test",
        test_mode=True,
        test_result_exporter=TestResultExporter(),
        default_separator="|",
        default_locale="en",
        default_dataset="US",
        use_mp=False,
        descriptor_dir=descriptor_dir,
        num_process=1,
        default_variable_prefix="__",
        default_variable_suffix="__",
        default_line_separator="\n",
    )


def _sqlite_client(task_id: str = "execute-test") -> RdbmsClient:
    credential = RdbmsConnectionConfig(
        dbms=Dbms.SQLITE,
        host=None,
        port=None,
        user=None,
        password=None,
        database="execute-test",
        db_schema=None,
    )
    return RdbmsClient(credential, task_id=task_id)


def _sql_task(target: str, code: str) -> ExecuteTask:
    # The parser attaches inline XML text after validating the attributes model.
    model = ExecuteModel.model_construct(uri=None, target=target, type="sql", script=None)
    statement = ExecuteStatement(model, "sql", code)
    return ExecuteTask(statement)


def test_sql_execute_interpolates_and_commits_against_sqlite(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    context = _context(tmp_path)
    client = _sqlite_client()
    context.add_client("db", client)
    context.namespace["table"] = "events"

    _sql_task("db", "CREATE TABLE {table} (id INTEGER); INSERT INTO {table} VALUES (7);").execute(context)

    assert [tuple(row) for row in client.get("SELECT id FROM events")] == [(7,)]
    client.engine.dispose()


def test_sql_execute_missing_target_keeps_key_error(tmp_path) -> None:
    with pytest.raises(KeyError, match="missing"):
        _sql_task("missing", "SELECT 1;").execute(_context(tmp_path))


def test_sql_execute_non_rdbms_target_fails_without_sql_method(tmp_path) -> None:
    context = _context(tmp_path)
    context.add_client("other", Client())

    with pytest.raises(AttributeError, match="execute_sql_script"):
        _sql_task("other", "SELECT 1;").execute(context)


def test_sql_execute_preserves_custom_client_with_sql_script_capability(tmp_path) -> None:
    class CustomSqlClient:
        def __init__(self) -> None:
            self.executed: list[str] = []

        def execute_sql_script(self, query: str) -> None:
            self.executed.append(query)

    context = _context(tmp_path)
    client = CustomSqlClient()
    context.add_client("custom", client)

    _sql_task("custom", "SELECT 1;").execute(context)

    assert client.executed == ["SELECT 1;"]


def test_sql_execute_accepts_dynamically_exposed_sql_script_client(tmp_path) -> None:
    class DynamicSqlClient:
        def __init__(self) -> None:
            self.executed: list[str] = []

        def __getattr__(self, name: str):
            if name == "execute_sql_script":
                return self.executed.append
            raise AttributeError(name)

    context = _context(tmp_path)
    dynamic_client = DynamicSqlClient()
    client = cast(SqlScriptClient, dynamic_client)
    context.add_client("custom", client)

    _sql_task("custom", "SELECT 1;").execute(context)

    assert dynamic_client.executed == ["SELECT 1;"]


def test_sql_execute_does_not_probe_dynamic_capability_before_invocation(tmp_path) -> None:
    class SingleLookupSqlClient:
        def __init__(self) -> None:
            self.executed: list[str] = []
            self.lookups = 0

        def __getattr__(self, name: str):
            if name != "execute_sql_script":
                raise AttributeError(name)
            self.lookups += 1
            if self.lookups > 1:
                raise AttributeError(name)

            def execute(query: str) -> None:
                self.executed.append(query)

            return execute

    context = _context(tmp_path)
    dynamic_client = SingleLookupSqlClient()
    client = cast(SqlScriptClient, dynamic_client)
    context.add_client("custom", client)

    _sql_task("custom", "SELECT 1;").execute(context)

    assert dynamic_client.lookups == 1
    assert dynamic_client.executed == ["SELECT 1;"]


def test_sql_execute_accepts_positional_only_sql_script_client(tmp_path) -> None:
    class PositionalOnlySqlClient:
        def __init__(self) -> None:
            self.executed: list[str] = []

        def execute_sql_script(self, sql: str, /) -> None:
            self.executed.append(sql)

    context = _context(tmp_path)
    client = PositionalOnlySqlClient()
    sql_client: SqlScriptClient = client
    registered_client: RegisteredClient = sql_client
    context.add_client("custom", registered_client)

    _sql_task("custom", "SELECT 1;").execute(context)

    assert client.executed == ["SELECT 1;"]


def test_sql_execute_rolls_back_all_statements_on_failure(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    context = _context(tmp_path)
    client = _sqlite_client()
    context.add_client("db", client)
    client.execute_sql_script("CREATE TABLE anchor (id INTEGER);")

    with pytest.raises(RuntimeError, match="Error when execute SQL"):
        _sql_task(
            "db",
            "INSERT INTO anchor VALUES (1); "
            "CREATE TABLE rollback_probe (id INTEGER); "
            "INSERT INTO missing_table VALUES (2);",
        ).execute(context)

    assert client.get("SELECT id FROM anchor") == []
    assert client.get("SELECT name FROM sqlite_master WHERE name = 'rollback_probe'") == []
    client.engine.dispose()
