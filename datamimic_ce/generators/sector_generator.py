# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.generators.generator import Generator
from datamimic_ce.logger import logger
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class SectorGenerator(Generator):
    def __init__(self, locale: str | None = "en") -> None:
        # Prepare file path
        prefix_path = Path(__file__).parent.parent
        file_name = f"entities/data/organization/sector_{locale}.csv"
        file_path = prefix_path.joinpath(file_name)

        # Load file data
        file_content_storage = FileContentStorage()
        try:
            self._sector_data_load = file_content_storage.load_file_with_custom_func(
                str(file_path),
                lambda: FileUtil.read_csv_having_single_column(file_path),
            )
        except FileNotFoundError:
            logger.warning(f"No such file or directory: 'sector_{locale}.csv'. Change to sector_en datas")
            file_path = prefix_path.joinpath("entities/data/organization/sector_en.csv")
            self._sector_data_load = file_content_storage.load_file_with_custom_func(
                str(file_path),
                lambda: FileUtil.read_csv_having_single_column(file_path),
            )

    def generate(self) -> str:
        return random.choice(self._sector_data_load)
