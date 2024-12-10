# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from collections.abc import Callable


class FileContentStorage:
    """
    Load file and store content in cache for later use
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._file_data = {}

    # def load_file_with_path(self, file_path: Path):
    #     """
    #     Load file and store content in cache for later use
    #
    #     :param file_path:
    #     :param read_func:
    #     :return:
    #     """
    #     file_path_str = str(file_path)
    #     # Load CSV file
    #     if file_path_str.endswith("csv"):
    #         res = FileUtil.read_weight_csv(file_path)
    #     # Load .properties file
    #     elif file_path_str.endswith(".properties"):
    #         res = FileUtil.parse_properties(file_path)
    #     else:
    #         raise ValueError(f"Cannot read file '{file_path_str}' from storage.")
    #     # Store file in storage
    #     self._file_data[file_path_str] = res
    #     return res

    def load_file_with_custom_func(self, file_path_str: str, read_func: Callable):
        """
        Load file from storage or using custom function to read file
        :param file_path_str:
        :param read_func:
        :return:
        """
        # Try to load from storage
        if file_path_str in self._file_data:
            return self._file_data[file_path_str]

        # Read file using custom function
        res = read_func()

        # Store file into storage
        self._file_data[file_path_str] = res

        return res
