from unittest.mock import MagicMock

from datamimic_ce.engine.dsl.model.setup.database_model import DatabaseModel
from datamimic_ce.engine.dsl.model.setup.mongodb_model import MongoDBModel
from datamimic_ce.engine.dsl.statements.setup.database_statement import DatabaseStatement
from datamimic_ce.engine.dsl.statements.setup.mongodb_statement import MongoDBStatement
from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.api import MongoDBConnectionConfig, RdbmsConnectionConfig
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.tasks.setup.database_task import DatabaseTask
from datamimic_ce.engine.runtime.tasks.setup.mongodb_task import MongoDBTask


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
    DatabaseTask(statement).execute(context)

    config = context.register_client_config.call_args.args[1]
    assert isinstance(config, RdbmsConnectionConfig)
    assert config.host == "localhost"
    assert config.port == 5432
    context.register_client_config.assert_called_once_with("db", config)


def test_mongodb_task_builds_io_config_without_statement_side_effects() -> None:
    model = MongoDBModel(id="mongo", host="localhost", port="27017", database="sample")
    statement = MongoDBStatement(model)
    assert statement.model is model
    assert not hasattr(statement, "_mongodb_client")

    context = MagicMock(spec=SetupContext)
    MongoDBTask(statement).execute(context)

    config = context.register_client_config.call_args.args[1]
    assert isinstance(config, MongoDBConnectionConfig)
    assert config.port == 27017
    context.register_client_config.assert_called_once_with("mongo", config)
