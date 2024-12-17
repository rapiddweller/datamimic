# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import copy

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.exporters.exporter import Exporter


class MongoDBExporter(Exporter):
    def __init__(self, client: MongoDBClient):
        self._client = client

    def consume(self, product) -> None:
        """Write data into MongoDB database"""
        temp_product = copy.deepcopy(product)
        name = temp_product[0]
        data = temp_product[1]
        self._client.insert(name, data, False)

    def update(self, product: tuple) -> int:
        """
        Update data into MongoDB database
        :return: The number of documents matched for an update.
        """
        temp_product = copy.deepcopy(product)
        if len(temp_product) > 2:
            data = temp_product[1]
            # product[2] contain "type" or "selector" attribute info
            target_query = product[2]
            return self._client.update(target_query, data)
        else:
            raise ValueError("'type' or 'selector' statement's attribute is missing")

    def upsert(self, product: tuple) -> tuple:
        """
        Update MongoDB data with upsert {true}
        """
        temp_product = copy.deepcopy(product)
        name, product_list, selector_dict = temp_product
        return name, self._client.upsert(selector_dict=selector_dict, updated_data=product_list)

    def delete(self, product: tuple):
        """
        Delete data from MongoDB database
        """
        temp_product = copy.deepcopy(product)
        if len(temp_product) > 2:
            data = temp_product[1]
            # product[2] contain "type" or "selector" attribute info
            target_query = temp_product[2]
            self._client.delete(target_query, data)
