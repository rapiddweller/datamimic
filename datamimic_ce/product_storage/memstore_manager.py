# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.exporters.memstore import Memstore


class MemstoreManager:
    """
    Manage all current mem-stores
    """

    def __init__(self):
        self._memstores = {}

    def add_memstore(self, memstore_id: str) -> None:
        """
        Add new memstore to pool
        :param memstore_id:
        :return:
        """
        if memstore_id in self._memstores:
            raise ValueError(f"Memstore {memstore_id} has already existed")
        else:
            self._memstores[memstore_id] = Memstore(memstore_id)

    def get_memstore(self, memstore_id: str) -> Memstore:
        """
        Get memstore from pool using memstore_id
        :param memstore_id:
        :return:
        """
        if memstore_id not in self._memstores:
            raise ValueError(f"Cannot find memstore {memstore_id}")
        else:
            return self._memstores[memstore_id]

    def contain(self, memstore_id: str) -> bool:
        """
        Check if specific memstore is existed in pool
        :param memstore_id:
        :return:
        """
        return memstore_id in self._memstores

    def get_memstores_list(self) -> list:
        """
        Get all memstores in pool
        :return:
        """
        return list(self._memstores.keys())
