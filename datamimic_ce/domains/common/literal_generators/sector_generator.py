# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
import random

from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil
from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator

class SectorGenerator(BaseLiteralGenerator):
    def __init__(self, dataset: str | None = "US", locale: str | None = None) -> None:
        """Initialize the SectorGenerator.

        Args:
            dataset: The dataset (country code) to use for generating sectors.
                    Defaults to "US".
            locale: The locale to use for generating sectors.
                    If provided, this will be used instead of dataset.
        """
        # Use locale parameter if provided, otherwise use dataset
        # Ensure country_code is never None by defaulting to "US"
        country_code = locale if locale is not None else (dataset if dataset is not None else "US")

        file_path = Path(__file__).parent.joinpath(f"data/organization/sector_{country_code}.csv")

        # Use the file content storage to cache the data
        self._sector_data_load = FileContentStorage.load_file_with_custom_func(
            cache_key=str(file_path),
            read_func=lambda: FileUtil.read_mutil_column_wgt_file(file_path)
        )

    def generate(self) -> str:
        """Generate a random sector.

        Returns:
            A randomly chosen sector.
        """
        return random.choice(self._sector_data_load)
