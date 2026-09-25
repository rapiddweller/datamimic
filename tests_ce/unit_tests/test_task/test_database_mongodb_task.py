from unittest.mock import MagicMock, patch

from datamimic_ce.engine.dsl.enums.dbms_enums import Dbms
from datamimic_ce.engine.dsl.model.database_model import DatabaseModel
from datamimic_ce.engine.dsl.model.mongodb_model import MongoDBModel
from datamimic_ce.engine.dsl.statements.database_statement import DatabaseStatement
from datamimic_ce.engine.dsl.statements.mongodb_statement import MongoDBStatement
from datamimic_ce.engine.io.api import MongoDBConnectionConfig, RdbmsConnectionConfig
from datamimic_ce.engine.runtime.contexts.setup_context import SetupContext
from datamimic_ce.engine.runtime.tasks.database_task import DatabaseTask
from datamimic_ce.engine.runtime.tasks.mongodb_task import MongoDBTask


def test_database_task_builds_io_config_from_dsl_model() -> None:
    statement = DatabaseStatement(
        DatabaseModel(
            id="db",
            dbms=Dbms.POSTGRESQL,
            host="localhost",
            port="5432",
            database="sample",
            user="user",
            password="secret",
            db_schema="public",
        )
    )
    context = MagicMock(spec=SetupContext)
    context.task_id = "task"
    client = object()

    with patch(
        "datamimic_ce.engine.runtime.tasks.database_task.create_rdbms_client", return_value=client
    ) as create_client:
        DatabaseTask(statement).execute(context)

    config = create_client.call_args.args[0]
    assert isinstance(config, RdbmsConnectionConfig)
    assert config.host == "localhost"
    assert config.port == 5432
    create_client.assert_called_once_with(config, "task")
    context.add_client.assert_called_once_with("db", client)


def test_mongodb_task_builds_io_config_without_statement_side_effects() -> None:
    model = MongoDBModel(id="mongo", host="localhost", port="27017", database="sample")
    statement = MongoDBStatement(model)
    assert statement.model is model
    assert not hasattr(statement, "_mongodb_client")

    context = MagicMock(spec=SetupContext)
    client = object()
    with patch(
        "datamimic_ce.engine.runtime.tasks.mongodb_task.create_mongodb_client", return_value=client
    ) as create_client:
        MongoDBTask(statement).execute(context)

    config = create_client.call_args.args[0]
    assert isinstance(config, MongoDBConnectionConfig)
    assert config.port == 27017
    context.add_client.assert_called_once_with("mongo", client)
