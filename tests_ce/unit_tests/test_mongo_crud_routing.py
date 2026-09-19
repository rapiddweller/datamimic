# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.constants.attribute_constants import META_SELECTOR, META_TARGET_ENTITY, META_TYPE
from datamimic_ce.exporters.mongodb_exporter import MongoDBExporter


class TestMongoCrudRouting:
    """A mongo CRUD write resolves its collection targetEntity -> type -> name, like the RDBMS
    exporter — so a plain target='db.update' iterate (statement name only, no metadata) works."""

    def test_name_only_falls_back_to_name(self):
        data, routing = MongoDBExporter._routing(("db_order", [{"_id": 1}]))
        assert routing[META_TARGET_ENTITY] == "db_order"
        assert data == [{"_id": 1}]

    def test_type_metadata_wins_over_name(self):
        _, routing = MongoDBExporter._routing(("stmt_name", [], {META_TYPE: "orders"}))
        assert routing[META_TARGET_ENTITY] == "orders"

    def test_explicit_target_entity_preserved(self):
        _, routing = MongoDBExporter._routing(("n", [], {META_TARGET_ENTITY: "explicit"}))
        assert routing[META_TARGET_ENTITY] == "explicit"

    def test_selector_collection_is_not_overridden_by_statement_name(self):
        # statement name ("cleanup") deliberately differs from the selector's own collection
        # ("db_order") - the common real-world idiom (a cleanup/delete step is named for what it
        # does, not for the collection it targets). A name-based fallback must never shadow this:
        # MongoDBClient.update/upsert/delete each resolve the collection from the selector
        # themselves, and only fall through to targetEntity when no selector is present.
        _, routing = MongoDBExporter._routing(("cleanup", [], {META_SELECTOR: "find: 'db_order', filter: {}"}))
        assert routing[META_SELECTOR] == "find: 'db_order', filter: {}"
        assert META_TARGET_ENTITY not in routing
