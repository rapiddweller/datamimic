# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from abc import abstractmethod

from datamimic_ce.clients.client import Client
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination


class DatabaseClient(Client):
    def __init__(self, credential):
        self._credential = credential

    @property
    def credential(self):
        return self._credential

    @abstractmethod
    def get_by_page_with_query(self, original_query: str, pagination: DataSourcePagination | None = None):
        """
        Get data from database when there is a query by pagination
        """

    @abstractmethod
    def get_by_page_with_type(self, table_name: str, pagination: DataSourcePagination | None = None) -> list:
        """
        Get data from database when there is a type (table name) by pagination
        """

    @abstractmethod
    def get_cyclic_data(self, query: str, cyclic: bool, data_len: int, pagination: DataSourcePagination) -> list:
        """
        Get cyclic data from database
        """

    @abstractmethod
    def count_table_length(self, table_name: str) -> int:
        """
        Count number of database length when there is type
        :param table_name:
        :return:
        """

    @abstractmethod
    def count_query_length(self, query: str) -> int:
        """
        Count number of database length when there is selector
        :param query:
        :return:
        """
