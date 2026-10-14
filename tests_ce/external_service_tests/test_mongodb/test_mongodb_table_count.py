"""Exercise both public count routes against a real MongoDB collection."""

from uuid import uuid4

from datamimic_ce.engine.io.api import database_count_table_length
from tests_ce.external_service_tests.test_mongodb.test_mongodb_pagination import _local_client


def test_table_count_and_facade_read_native_collection_counts():
    client = _local_client()
    name = f"table_count_{uuid4().hex}"
    with client._create_connection() as conn:
        collection = conn[client._credential.database][name]
        try:
            for expected in (0, 3):
                if expected:
                    collection.insert_many([{"value": i} for i in range(expected)])
                assert client.count_table_length(name) == expected
                assert database_count_table_length(client, name) == expected
        finally:
            collection.drop()
        assert name not in conn[client._credential.database].list_collection_names()
