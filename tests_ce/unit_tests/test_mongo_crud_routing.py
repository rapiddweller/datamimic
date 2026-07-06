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

    def test_selector_filter_preserved_alongside_resolved_collection(self):
        _, routing = MongoDBExporter._routing(("db_order", [], {META_SELECTOR: "find: 'db_order', filter: {}"}))
        # the selector survives (a filter) AND the collection is resolved from the name
        assert routing[META_SELECTOR] == "find: 'db_order', filter: {}"
        assert routing[META_TARGET_ENTITY] == "db_order"
