# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.generators.generator import Generator
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class WeightedEntityDataSource(Generator):
    """
    Purpose: generate a dict of entity (header_name: row_value)
    from "entity.wgt.ent.csv" file with corresponding weight.

    Extends: Generator (Abstract Class).

    Example format for this file type:

    - file_name must have ".wgt.ent.csv" extension: people.wgt.ent.csv

    - file_content always contains weight column with number as weight

        id, name, age, weight

        1, Steve, 20, 15

        2, Daniel, 30, 20

        3, Tom, 10, 10

        4, David, 50, 30

        5, Ocean, 37, 23

    With this file format, this generate will generate random Dict for example {id=1, name=Steve, age=20} with
    corresponding weight in weight column.
    Attributes:
        file_path (str): file path of "entity.wgt.ent.csv", check Example for format detail of this file type
    """

    def __init__(self, file_path: Path, separator: str, weight_column_name: str | None = None):
        file_store = FileContentStorage()
        weight_column = weight_column_name or "weight"
        self._weights, self._data_dict_list = file_store.load_file_with_custom_func(
            str(file_path),
            lambda: FileUtil.read_csv_having_weight_column(file_path, weight_column, separator),
        )

    def generate(self) -> dict:
        """
        Generate a dict represent an entity with weight from file ".wgt.ent.csv"

        Returns:
            entity (Dict): generated entity as dict
        """
        return random.choices(self._data_dict_list, weights=self._weights, k=1)[0]
