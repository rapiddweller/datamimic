# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.exporters.exporter import Exporter
from datamimic_ce.logger import logger


class Memstore(Exporter):
    # TODO: consider to use redis for caching memstore data instead using python dict
    """
    Store temporary generated data in memory
    """

    def __init__(self, memstore_id: str):
        self._memstore_id = memstore_id
        self._storage: dict = {}

    def get_all_data_by_type(self, product_type: str):
        """
        Get all data in memstore by data type
        :param product_type:
        :return:
        """
        return self._storage.get(product_type, [])

    def get_data_by_type(self, product_type: str, pagination: DataSourcePagination | None, cyclic: bool):
        """
        Get data in memstore by data type and pagination
        :param product_type:
        :param pagination:
        :param cyclic:
        :return:
        """
        from datamimic_ce.data_sources.data_source_util import DataSourceUtil

        return DataSourceUtil.get_cyclic_data_list(
            data=self._storage[product_type], cyclic=cyclic, pagination=pagination
        )

    def get_data_len_by_type(self, entity_name: str) -> int:
        """
        Get length of data from memstore
        """
        try:
            return len(self._storage[entity_name])
        except KeyError:
            logger.error(f"Data having entity '{entity_name}' is empty in memstore")
        return 0

    def consume(self, product: tuple):
        """
        Write data into memstore
        :param product:
        :return:
        """
        name = product[0]
        data = product[1]
        self._storage[name] = self._storage.get(name, []) + data
