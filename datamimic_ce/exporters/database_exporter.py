# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
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

        if len(rest) > 0 and isinstance(rest[0], dict):
            name = rest[0].get("type", name)

        self._client.insert(name, data)
