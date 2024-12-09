# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

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
