# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import copy

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.constants.attribute_constants import META_SELECTOR, META_TARGET_ENTITY
from datamimic_ce.exporters.exporter import Exporter


class MongoDBExporter(Exporter):
    def __init__(self, client: MongoDBClient):
        self._client = client

    @staticmethod
    def _routing(product: tuple) -> tuple[list, dict]:
        """The write data and a collection-routing dict for it. The collection follows the same
        precedence as the RDBMS exporter — targetEntity -> type -> name — so a CRUD write that only
        carries the statement name (e.g. a plain ``target="db.update"`` iterate) still resolves its
        collection instead of demanding an explicit type/selector. A selector already resolves its
        OWN collection (MongoDBClient.update/upsert/delete parse it), so the name-based fallback is
        only injected when there is no selector - never override the filter's own target."""
        from datamimic_ce.statements.statement_util import StatementUtil

        temp_product = copy.deepcopy(product)
        name, data = temp_product[0], temp_product[1]
        metadata = temp_product[2] if len(temp_product) > 2 and isinstance(temp_product[2], dict) else {}
        routing = dict(metadata)
        if META_TARGET_ENTITY not in routing and META_SELECTOR not in routing:
            routing[META_TARGET_ENTITY] = StatementUtil.resolve_target_entity_from_metadata(name, metadata)
        return data, routing

    def consume(self, product) -> None:
        """Write data into MongoDB database"""
        from datamimic_ce.statements.statement_util import StatementUtil

        temp_product = copy.deepcopy(product)
        # targetEntity -> type -> name routes the write to its collection (same as the RDBMS exporter).
        metadata = temp_product[2] if len(temp_product) > 2 else None
        collection = StatementUtil.resolve_target_entity_from_metadata(temp_product[0], metadata)
        data = temp_product[1]
        self._client.insert(collection, data, False)

    def update(self, product: tuple) -> int:
        """
        Update data into MongoDB database
        :return: The number of documents matched for an update.
        """
        data, routing = self._routing(product)
        return self._client.update(routing, data) if data else 0

    def upsert(self, product: tuple) -> tuple:
        """
        Update MongoDB data with upsert {true}
        """
        data, routing = self._routing(product)
        return product[0], self._client.upsert(selector_dict=routing, updated_data=data)

    def delete(self, product: tuple):
        """
        Delete data from MongoDB database
        """
        data, routing = self._routing(product)
        if data:
            self._client.delete(routing, data)
