# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
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
        try:
            from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry

            return DataSourceRegistry.get_cyclic_data_list(
                data=self._storage[product_type], cyclic=cyclic, pagination=pagination
            )
        except KeyError as e:
            logger.error(f"Data naming '{product_type}' is empty in memstore: {e}")
            raise KeyError(f"Data naming '{product_type}' is empty in memstore") from e

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

    def sumEntityColumn(self, product_type: str, column: str):
        """Sum a numeric column across all rows of one type (migration parity). Values are coerced via
        float() - memstore rows sourced from CSV carry strings, not numbers. Non-numeric cells (a CSV
        may carry stray values, e.g. a placeholder) are skipped, not fatal, matching the legacy
        lenient aggregation."""
        total = 0.0
        for row in self._storage.get(product_type, []):
            try:
                total += float(row[column])
            except (TypeError, ValueError):
                continue  # skip a non-numeric cell instead of aborting the whole sum
        return int(total) if total.is_integer() else total

    def entityCount(self, product_type: str) -> int:
        """Alias of get_data_len_by_type (legacy camelCase naming)."""
        return self.get_data_len_by_type(product_type)

    def removeNotExistingIds(self, product_type: str, id_col: str, ref_type: str, client) -> None:
        """Keep only the rows of `product_type` whose `id_col` value exists in `ref_type` as read
        from an RDBMS `client` (migration parity: an inner-join filter). Mutates the stored rows in
        place - no return value, matching the legacy imperative "remove" semantics. Both sides of
        the id comparison are string-coerced: `client`'s column is DB-typed (e.g. int), memstore
        rows sourced from CSV carry strings for the same logical id."""
        existing = {str(row[0]) for row in client.get_random_rows_by_columns(ref_type, [id_col])}
        self._storage[product_type] = [
            r for r in self._storage.get(product_type, []) if str(r.get(id_col)) in existing
        ]
