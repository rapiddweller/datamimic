# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.exporters.exporter import Exporter


class DatabaseExporter(Exporter):
    def __init__(self, client: RdbmsClient):
        self._client = client

    def consume(self, product: tuple[str, list[dict[str, Any]], dict[str, Any] | None]) -> None:
        """
        Write data into SQL database

        Args:
            product: Tuple containing (name, data, metadata)
                    where metadata is optional and may contain type information
        """
        name, data, *rest = product
        if not data:
            return

        self._client.insert(self._table_name(name, rest), data)

    def update(self, product: tuple) -> int:
        """UPDATE rows by primary key (target="db.update"). Returns the matched-row count."""
        name, data, *rest = product
        return self._client.update(self._table_name(name, rest), data) if data else 0

    def upsert(self, product: tuple) -> None:
        """UPDATE by primary key, INSERT what matched nothing (target="db.upsert")."""
        name, data, *rest = product
        if data:
            self._client.upsert(self._table_name(name, rest), data)

    def delete(self, product: tuple) -> int:
        """DELETE rows by primary key (target="db.delete"). Returns the deleted-row count."""
        name, data, *rest = product
        return self._client.delete(self._table_name(name, rest), data) if data else 0

    @staticmethod
    def _table_name(name: str, rest: list) -> str:
        # targetEntity -> type -> name (see StatementUtil.resolve_target_entity).
        from datamimic_ce.statements.statement_util import StatementUtil

        return StatementUtil.resolve_target_entity_from_metadata(
            name, rest[0] if rest and isinstance(rest[0], dict) else None
        )
