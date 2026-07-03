"""Unit tests for the entity resolvers and the MongoDB collection dispatch.

These cover the new sourceEntity/targetEntity logic WITHOUT a live MongoDB: the resolvers are pure,
and the Mongo client derives the collection before it connects (empty data returns early), so the
targetEntity/selector/type/missing branches are exercised with no server.
"""

from types import SimpleNamespace

import pytest

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.statements.statement_util import StatementUtil


def _stmt(source_entity=None, type_=None, name="stmt"):
    return SimpleNamespace(source_entity=source_entity, type=type_, name=name)


# ---- resolve_source_entity: name-fallback families (RDBMS/memstore/nestedKey) ----

def test_resolve_source_entity_precedence():
    assert StatementUtil.resolve_source_entity(_stmt("ent", "typ", "nm")) == "ent"   # sourceEntity wins
    assert StatementUtil.resolve_source_entity(_stmt(None, "typ", "nm")) == "typ"    # -> type
    assert StatementUtil.resolve_source_entity(_stmt(None, None, "nm")) == "nm"      # -> name


# ---- resolve_source_collection: explicit-only family (MongoDB), no name fallback ----

def test_resolve_source_collection_precedence_and_no_name_fallback():
    assert StatementUtil.resolve_source_collection(_stmt("ent", "typ", "nm")) == "ent"
    assert StatementUtil.resolve_source_collection(_stmt(None, "typ", "nm")) == "typ"
    assert StatementUtil.resolve_source_collection(_stmt(None, None, "nm")) is None  # name is NOT a fallback


# ---- resolve_target_entity ----

def test_resolve_target_entity_precedence_and_metadata():
    assert StatementUtil.resolve_target_entity("ent", "typ", "nm") == "ent"
    assert StatementUtil.resolve_target_entity(None, "typ", "nm") == "typ"
    assert StatementUtil.resolve_target_entity(None, None, "nm") == "nm"
    assert StatementUtil.resolve_target_entity_from_metadata("nm", {"target_entity": "ent"}) == "ent"
    assert StatementUtil.resolve_target_entity_from_metadata("nm", {"type": "typ"}) == "typ"
    assert StatementUtil.resolve_target_entity_from_metadata("nm", None) == "nm"


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
