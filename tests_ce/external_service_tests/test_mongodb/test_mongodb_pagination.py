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
from datamimic_ce.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.data_mimic_test import DataMimicTest


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
        client = MongoDBClient(
            credential=MongoDBConnectionConfig(host="unreachable.invalid", port=27017, database="x")
        )
        with pytest.raises(ValueError, match="Syntax error"):
            client.get_documents_by_collection("   ")
