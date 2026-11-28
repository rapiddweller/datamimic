# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from datamimic_ce.engine.dsl.vocabulary.constants.attribute_constants import META_TARGET_ENTITY
from datamimic_ce.engine.io.api import has_mongodb_upsert_target
from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient, MongoDBConnectionConfig

CLIENTS = {"mongo": MagicMock(spec=MongoDBClient)}


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("mongo.upsert", True),
        ("mongo.upsert()", True),
        (" mongo . upsert ", True),
        ("mongo.delete", False),
        ("mongo", False),
        ("mongo.upsert.extra", False),
        ("other.upsert", False),
    ],
)
def test_upsert_target_is_read_as_the_exporter_registry_reads_it(target: str, expected: bool) -> None:
    assert has_mongodb_upsert_target({target}, CLIENTS) is expected


def _client(monkeypatch: pytest.MonkeyPatch) -> tuple[MongoDBClient, MagicMock]:
    collection = MagicMock()
    collection.insert_many.side_effect = lambda docs: MagicMock(inserted_ids=[f"new{i}" for i, _ in enumerate(docs)])
    collection.find.return_value = []
    connection = MagicMock()
    connection.__getitem__.return_value.__getitem__.return_value = collection

    @contextmanager
    def connect():
        yield connection

    client = MongoDBClient(MongoDBConnectionConfig(host="localhost", port=27017, database="test"))
    monkeypatch.setattr(client, "_create_connection", connect)
    return client, collection


@pytest.mark.parametrize(
    ("docs", "inserted", "updated"),
    [
        ([{"a": 1}, {"a": 2}], 2, []),
        ([{"_id": 1, "a": 1}, {"_id": 2, "a": 2}], 0, [1, 2]),
        ([{"_id": 1, "a": 1}, {"a": 2}], 1, [1]),
        ([{"a": 1}, {"_id": 2, "a": 2}], 1, [2]),
    ],
    ids=["all-new", "all-keyed", "keyed-first-mixed", "new-first-mixed"],
)
def test_upsert_decides_insert_or_update_per_document(monkeypatch, docs, inserted, updated) -> None:
    client, collection = _client(monkeypatch)
    client.upsert({META_TARGET_ENTITY: "rows"}, docs)

    assert (len(collection.insert_many.call_args.args[0]) if inserted else 0) == inserted
    assert [call.args[0]["_id"] for call in collection.update_one.call_args_list] == updated
    assert all(call.kwargs == {"upsert": True} for call in collection.update_one.call_args_list)
    looked_up = collection.find.call_args.args[0]["_id"]["$in"]
    assert looked_up == [f"new{i}" for i in range(inserted)] + updated
