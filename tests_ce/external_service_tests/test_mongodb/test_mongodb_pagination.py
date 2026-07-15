# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# For questions and support, contact: info@rapiddweller.com

"""Mongo sources must push skip/limit to the server instead of loading the full collection
and slicing in Python (memory), and <variable type=... source=mongodb distribution="ordered">
(the loads_all=False path, get_by_page_with_type) must actually advance page to page instead of
silently reloading the same rows every time (correctness - variable_task.py previously called
get_by_page_with_type(product_type) with no pagination argument at all)."""

from pathlib import Path

import pytest

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.config import settings
from datamimic_ce.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination


def _local_client() -> MongoDBClient:
    """Same host/port split as conf/local.env.properties vs. conf/environment.env.properties
    (used by the DSL-fixture tests below via <mongodb id="mongodb"/>) - a direct client
    construction can't read those files, so it must branch the same way by hand."""
    if settings.RUNTIME_ENVIRONMENT == "development":
        host, port = "localhost", 47017
    else:
        host, port = "mongo", 27017
    return MongoDBClient(
        credential=MongoDBConnectionConfig(
            host=host,
            port=port,
            database="datamimic",
            user="datamimic",
            password="datamimic",
            authSource="admin",
        )
    )


class TestMongoDbPagination:
    _test_dir = Path(__file__).resolve().parent

    def test_ordered_variable_read_advances_across_pages(self):
        """Happy path: 20 seeded docs, read back in 4 pages of 5 - the union of all pages must
        be exactly 1..20 with no duplicates, proving each page actually skips past the last."""
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_mongodb_pagination_happy.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()
        ids = [row["row_id"] for row in result["page"]]

        assert len(ids) == 20
        assert sorted(ids) == list(range(1, 21)), f"expected 1..20 with no duplicates, got {sorted(ids)}"

    def test_ordered_variable_read_handles_uneven_last_page(self):
        """Edge case: 17 seeded docs with pageSize=5 (pages of 5, 5, 5, 2) - the short last page
        must not be padded with repeats from earlier pages."""
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_mongodb_pagination_edge.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()
        ids = [row["row_id"] for row in result["page"]]

        assert len(ids) == 17
        assert sorted(ids) == list(range(1, 18)), f"expected 1..17 with no duplicates, got {sorted(ids)}"

    def test_empty_collection_name_still_raises(self):
        """Error/regression case: MongoDBClient.get_documents_by_collection's guard for an
        empty/whitespace collection name must survive the pagination-threading change. Not
        expressible as a DM DSL fixture: <variable type=""> is rejected by pydantic model
        validation before it ever reaches this runtime branch, so there is no authorable
        descriptor that exercises it - only a direct client call can, hence a client-level test
        rather than an engine-level one. No network call happens before the guard, so a dummy,
        unreachable connection config is enough - this never dials out."""
        client = MongoDBClient(credential=MongoDBConnectionConfig(host="unreachable.invalid", port=27017, database="x"))
        with pytest.raises(ValueError, match="Syntax error"):
            client.get_documents_by_collection("   ")

    def test_limit_zero_returns_empty_not_pymongo_no_limit(self):
        """pymongo's own cursor.limit(0) means "no limit" (return everything), not "return
        nothing" - both get() (the "find" query-type branch) and get_documents_by_collection
        must guard pagination.limit == 0 explicitly rather than pass it straight to pymongo, or
        a caller asking for zero rows would silently get the whole collection back instead.
        Seeds/cleans up via raw pymongo (MongoDBClient.insert/delete take the DSL task-layer
        query-dict shape, not a plain collection name - overkill for a self-contained fixture)."""
        client = _local_client()
        collection = "mongo_pagination_limit_zero"
        with client._create_connection() as conn:
            coll = conn[client._credential.database][collection]
            coll.delete_many({})
            coll.insert_many([{"row_id": i} for i in range(1, 6)])
        try:
            zero = DataSourcePagination(skip=0, limit=0)
            assert client.get(f"find: '{collection}', filter: {{}}", zero) == []
            assert client.get_documents_by_collection(collection, zero) == []

            # sanity: a real limit on the same collection still returns rows (proves the guard
            # isn't just swallowing every pagination argument)
            some = DataSourcePagination(skip=0, limit=2)
            assert len(client.get(f"find: '{collection}', filter: {{}}", some)) == 2
        finally:
            with client._create_connection() as conn:
                conn[client._credential.database][collection].delete_many({})

    def test_get_by_page_with_query_find_vs_aggregate(self):
        """get_by_page_with_query dispatches differently by query type: "find" queries are
        already skip/limit-ed server-side by get() (must not be re-sliced); "aggregate" queries
        get a Python-side skip/limit fallback since get() fully materializes them. Also covers
        the pagination=None short-circuit (return self.get(query) with no slicing at all)."""
        client = _local_client()
        collection = "mongo_pagination_query_dispatch"
        with client._create_connection() as conn:
            coll = conn[client._credential.database][collection]
            coll.delete_many({})
            coll.insert_many([{"row_id": i} for i in range(1, 6)])
        try:
            # pagination=None: full unpaginated read
            all_docs = client.get_by_page_with_query(f"find: '{collection}', filter: {{}}")
            assert len(all_docs) == 5

            # "find": server-side skip/limit, not re-sliced
            page = DataSourcePagination(skip=1, limit=2)
            find_page = client.get_by_page_with_query(f"find: '{collection}', filter: {{}}", page)
            assert [d["row_id"] for d in find_page] == [2, 3]

            # "aggregate": Python-side skip/limit fallback
            agg_query = f"aggregate: '{collection}', pipeline: [{{'$sort': {{'row_id': 1}}}}]"
            agg_page = client.get_by_page_with_query(agg_query, page)
            assert [d["row_id"] for d in agg_page] == [2, 3]
        finally:
            with client._create_connection() as conn:
                conn[client._credential.database][collection].delete_many({})
