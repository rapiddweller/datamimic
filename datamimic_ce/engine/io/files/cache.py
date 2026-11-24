# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import os
from collections.abc import Callable
from typing import ClassVar

from datamimic_ce.engine.dsl.parsers.input.resource import resource_reader_active


class FileContentStorage:
    """
    Load file and store content in cache for later use
    """

    _file_data_cache: ClassVar[dict[str, object]] = {}
    _file_signatures: ClassVar[dict[str, tuple[int, int] | None]] = {}
    # How the cached content was read (reader kind, separator, encoding): the same path read another way is stale.
    _file_variants: ClassVar[dict[str, tuple[object, ...]]] = {}

    @staticmethod
    def file_signature(cache_key: str) -> tuple[int, int] | None:
        """Size and mtime of the file behind the key; None when it is not a file on disk.

        A cached entry whose file is gone stays served (preloaded or virtual content).
        """
        try:
            stat = os.stat(cache_key)
        except (OSError, ValueError):
            return None
        return stat.st_size, stat.st_mtime_ns

    @classmethod
    def is_fresh(cls, cache_key: str, variant: tuple[object, ...] = ()) -> bool:
        if cache_key not in cls._file_data_cache:
            return False
        stored = cls._file_variants.get(cache_key, ())
        if stored and variant and stored != variant:
            return False  # an entry or a request without a variant (preloaded content) matches every reader
        current = cls.file_signature(cache_key)
        return current is None or current == cls._file_signatures.get(cache_key)

    @classmethod
    def load_file_with_cache(cls, cache_key: str):
        """
        Load file from storage, if cache key is not found, raise ValueError
        :param cache_key:
        :return:
        """
        if cls.is_fresh(cache_key):
            return cls._file_data_cache[cache_key]
        else:
            raise ValueError(f"Cannot find cache key '{cache_key}' in file content storage")

    @classmethod
    def load_file_with_custom_func(
        cls, cache_key: str, read_func: Callable[[], object], variant: tuple[object, ...] = ()
    ) -> object:
        """
        Load file from storage or using custom function to read file
        :param cache_key:
        :param read_func:
        :param variant: how read_func parses the file; content cached for another variant is read again
        :return:
        """
        if resource_reader_active():
            return read_func()
        # Try to load from storage
        if cls.is_fresh(cache_key, variant):
            return cls._file_data_cache[cache_key]

        # Read file using custom function
        signature = cls.file_signature(cache_key)
        res = read_func()

        # Store file into storage
        cls._file_data_cache[cache_key] = res
        cls._file_signatures[cache_key] = signature
        cls._file_variants[cache_key] = variant

        return res
