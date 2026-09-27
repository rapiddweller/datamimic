"""Unit tests for the entity resolvers and the MongoDB collection dispatch.

These cover the new sourceEntity/targetEntity logic WITHOUT a live MongoDB: the resolvers are pure,
and the Mongo client derives the collection before it connects (empty data returns early), so the
targetEntity/selector/type/missing branches are exercised with no server.
"""

import pytest

from datamimic_ce.engine.dsl.api import parse_consumer
from datamimic_ce.engine.io.api import (
    resolve_source_collection,
    resolve_source_entity,
    resolve_target_entity,
    resolve_target_entity_from_metadata,
)
from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig


def test_parse_consumer_preserves_nested_arguments_and_deduplicates() -> None:
    consumers = parse_consumer(
        " CSV(chunk_size=2, encoding='utf-8'), MongoDB.upsert, CSV(chunk_size=2, encoding='utf-8') "
    )
    assert consumers == {
        "CSV(chunk_size=2, encoding='utf-8')",
        "MongoDB.upsert",
    }
    assert parse_consumer(None) == set()
    assert parse_consumer(" , ") == set()


# ---- resolve_source_entity: name-fallback families (RDBMS/memstore/nestedKey) ----


def test_resolve_source_entity_precedence():
    assert resolve_source_entity("ent", "typ", "nm") == "ent"  # sourceEntity wins
    assert resolve_source_entity(None, "typ", "nm") == "typ"  # -> type
    assert resolve_source_entity(None, None, "nm") == "nm"  # -> name
    assert resolve_source_entity(None, None, None) is None


# ---- resolve_source_collection: explicit-only family (MongoDB), no name fallback ----


def test_resolve_source_collection_precedence_and_no_name_fallback():
    assert resolve_source_collection("ent", "typ") == "ent"
    assert resolve_source_collection(None, "typ") == "typ"
    assert resolve_source_collection(None, None) is None  # name is NOT a fallback


# ---- resolve_target_entity ----


def test_resolve_target_entity_precedence_and_metadata():
    assert resolve_target_entity("ent", "typ", "nm") == "ent"
    assert resolve_target_entity(None, "typ", "nm") == "typ"
    assert resolve_target_entity(None, None, "nm") == "nm"
    assert resolve_target_entity_from_metadata("nm", {"target_entity": "ent"}) == "ent"
    assert resolve_target_entity_from_metadata("nm", {"type": "typ"}) == "typ"
    assert resolve_target_entity_from_metadata("nm", None) == "nm"


# ---- MongoDB collection dispatch (no live server: empty data returns before connecting) ----


def _client():
    cfg = MongoDBConnectionConfig(host="localhost", port=1, database="d", user=None, password=None)
    return MongoDBClient(cfg)


def test_mongo_update_accepts_target_entity_as_collection():
    # empty data -> update derives the collection from targetEntity then returns 0 without connecting
    assert _client().update({"target_entity": "orders"}, []) == 0


@pytest.mark.parametrize("op", ["update", "delete", "upsert"])
def test_mongo_crud_raises_when_no_collection_hint(op):
    # the collection dispatch raises before any connection when no targetEntity/type/selector is given
    client = _client()
    with pytest.raises(ValueError, match=r"(targetEntity|type|selector)"):
        getattr(client, op)({}, [{"_id": 1}])
