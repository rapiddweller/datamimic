# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.
"""The MongoDB upsert descriptor of the external shard, run here against an in-memory collection.

Same XML and same per-class assertions as ``test_upsert_decision`` in the external-service shard."""

import importlib.util
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parents[1] / "external_service_tests" / "test_mongodb_routing_matrix"


def _shared_checks():
    spec = importlib.util.spec_from_file_location("upsert_decision_checks", _DIR / "test_upsert_decision.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.check_classes


class _Cursor(list):
    def skip(self, count: int) -> "_Cursor":
        return _Cursor(self[count:])

    def limit(self, count: int) -> "_Cursor":
        return _Cursor(self[:count])


class _Collection:
    def __init__(self) -> None:
        self.docs: list[dict] = []
        self._next = 0

    def _matches(self, doc: dict, query: dict | None) -> bool:
        for key, wanted in (query or {}).items():
            if isinstance(wanted, dict) and "$in" in wanted:
                if doc.get(key) not in wanted["$in"]:
                    return False
            elif doc.get(key) != wanted:
                return False
        return True

    def find(self, query: dict | None = None, projection: dict | None = None) -> _Cursor:
        return _Cursor(dict(doc) for doc in self.docs if self._matches(doc, query))

    def count_documents(self, query: dict) -> int:
        return len(self.find(query))

    def insert_many(self, docs: list[dict]):
        ids = []
        for doc in docs:
            self._next += 1
            doc.setdefault("_id", f"oid{self._next}")
            self.docs.append(dict(doc))
            ids.append(doc["_id"])
        return type("Result", (), {"inserted_ids": ids})

    def update_one(self, query: dict, update: dict, upsert: bool = False) -> None:
        for doc in self.docs:
            if self._matches(doc, query):
                doc.update(update["$set"])
                return
        if upsert:
            self.docs.append({**query, **update["$set"]})

    def delete_many(self, query: dict) -> None:
        self.docs = [doc for doc in self.docs if not self._matches(doc, query)]


@pytest.fixture
def fake_mongo(monkeypatch: pytest.MonkeyPatch) -> dict[str, _Collection]:
    collections: dict[str, _Collection] = {}

    class _Database:
        def __getitem__(self, name: str) -> _Collection:
            return collections.setdefault(name, _Collection())

    class _Connection:
        def __getitem__(self, name: str) -> _Database:
            return _Database()

    @contextmanager
    def connect(self) -> Iterator[_Connection]:
        yield _Connection()

    monkeypatch.setattr(MongoDBClient, "_create_connection", connect)
    return collections


def test_upsert_descriptor_outcome_per_class(fake_mongo: dict[str, _Collection]) -> None:
    engine = DataMimicTest(test_dir=_DIR, filename="upsert_decision.xml", capture_test_result=True)
    engine.test_with_timer()
    _shared_checks()(engine.capture_result())
