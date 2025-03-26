# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


class ExporterStateManager:
    """
    Manages the state of exporters for each worker.
    """

    def __init__(self, worker_id):
        self._worker_id = worker_id
        self._storage_dict = {}

    @property
    def worker_id(self):
        return self._worker_id

    def get_storage(self, key: str):
        if key not in self._storage_dict:
            self._storage_dict[key] = ExporterStateStorage(None)
        return self._storage_dict[key]

    def load_exporter_state(self, key: str):
        storage = self.get_storage(key)

        return storage.global_counter, storage.current_counter, storage.chunk_index, storage.chunk_size

    def rotate_chunk(self, key: str):
        storage = self.get_storage(key)

        storage.chunk_index = storage.chunk_index + 1
        storage.current_counter = 0

    def save_state(self, key: str, global_counter: int, current_counter: int):
        storage = self.get_storage(key)

        storage.global_counter = global_counter
        storage.current_counter = current_counter


class ExporterStateStorage:
    """
    Stores the state of an exporter for a worker.
    """

    def __init__(self, chunk_size: int | None):
        self._global_counter = 0
        self._current_counter = 0
        self._chunk_index = 0
        self._chunk_size = chunk_size

    @property
    def global_counter(self):
        return self._global_counter

    @global_counter.setter
    def global_counter(self, value):
        self._global_counter = value

    @property
    def current_counter(self):
        return self._current_counter

    @current_counter.setter
    def current_counter(self, value):
        self._current_counter = value

    @property
    def chunk_size(self):
        return self._chunk_size

    @property
    def chunk_index(self):
        return self._chunk_index

    @chunk_index.setter
    def chunk_index(self, value):
        self._chunk_index = value
