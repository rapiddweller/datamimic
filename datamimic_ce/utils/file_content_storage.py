# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from collections.abc import Callable
from typing import Any, ClassVar

from datamimic_ce.logger import logger


class FileContentStorage:
    """
    Load file and store content in cache for later use
    """

    _file_data_cache: ClassVar[dict[str, Any]] = {}

    @classmethod
    def load_file_with_cache(cls, cache_key: str):
        """
        Load file from storage, if cache key is not found, raise ValueError
        :param cache_key:
        :return:
        """
        if cache_key in cls._file_data_cache:
            return cls._file_data_cache[cache_key]
        else:
            raise ValueError(f"Cannot find cache key '{cache_key}' in file content storage")

    @classmethod
    def load_file_with_custom_func(cls, cache_key: str, read_func: Callable):
        """
        Load file from storage or using custom function to read file
        :param cache_key:
        :param read_func:
        :return:
        """
        # Try to load from storage
        if cache_key in cls._file_data_cache:
            return cls._file_data_cache[cache_key]

        logger.debug(f"CACHE MISS: File content storage cache miss, load file for {cache_key}")

        # Read file using custom function
        res = read_func()

        # Store file into storage
        cls._file_data_cache[cache_key] = res

        return res
