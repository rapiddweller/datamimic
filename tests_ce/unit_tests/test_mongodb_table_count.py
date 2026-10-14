"""The database table-count contract also applies to MongoDB collections."""

from unittest.mock import MagicMock

import pytest
from pymongo.errors import OperationFailure

from datamimic_ce.engine.io.api import database_count_table_length
from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig


@pytest.mark.parametrize("use_facade", [False, True])
@pytest.mark.parametrize("count", [0, 5])
def test_mongodb_table_count_returns_native_integer(monkeypatch, use_facade, count):
    client = MongoDBClient(MongoDBConnectionConfig(host="localhost", port=1, database="counts"))
    connection = MagicMock()
    connection.__enter__.return_value["counts"]["widgets"].count_documents.return_value = count
    monkeypatch.setattr(client, "_create_connection", lambda: connection)

    actual = database_count_table_length(client, "widgets") if use_facade else client.count_table_length("widgets")

    assert type(actual) is int
    assert actual == count


@pytest.mark.parametrize("use_facade", [False, True])
def test_mongodb_table_count_preserves_backend_error(monkeypatch, use_facade):
    client = MongoDBClient(MongoDBConnectionConfig(host="localhost", port=1, database="counts"))
    connection = MagicMock()
    connection.__enter__.return_value["counts"]["widgets"].count_documents.side_effect = OperationFailure("denied")
    monkeypatch.setattr(client, "_create_connection", lambda: connection)

    with pytest.raises(OperationFailure, match="denied"):
        if use_facade:
            database_count_table_length(client, "widgets")
        else:
            client.count_table_length("widgets")


@pytest.mark.parametrize("use_facade", [False, True])
def test_mongodb_table_count_preserves_invalid_name_error(use_facade):
    client = MongoDBClient(MongoDBConnectionConfig(host="localhost", port=1, database="counts"))

    with pytest.raises(ValueError, match="collection name"):
        if use_facade:
            database_count_table_length(client, "   ")
        else:
            client.count_table_length("   ")
