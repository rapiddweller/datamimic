# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.exporters.exporter import Exporter


class DatabaseExporter(Exporter):
    def __init__(self, client: RdbmsClient):
        self._client = client

    def consume(self, product) -> None:
        """Write data into SQL database"""
        name, data, *_ = product
        if len(data) == 0:
            return
        if len(product) > 2:
            name = product[2].get("type", None) or name
        self._client.insert(name, data)
