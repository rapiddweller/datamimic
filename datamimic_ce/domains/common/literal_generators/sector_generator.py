# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.domains.domain_core.base_domain_generator import normalize_dataset
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.logger import logger
from datamimic_ce.utils.file_util import FileUtil


class SectorGenerator(BaseLiteralGenerator):
    def __init__(self, dataset: str | None = None, locale: str | None = None, rng: random.Random | None = None) -> None:
        """Initialize the SectorGenerator.

        Args:
            dataset: The dataset (country code) to use for generating sectors.
            locale: The locale to use for generating sectors.
                    If provided, this will be used instead of dataset.
        """
        country_code = locale if locale is not None else normalize_dataset(dataset)

        file_path = dataset_path("common", "organization", f"sector_{country_code}.csv", start=Path(__file__))

        try:
            # Use the file content storage to cache the data
            self._sector_data_load = FileUtil.read_csv_to_list_of_tuples_without_header(file_path)
        except FileNotFoundError as e:
            logger.warning(f"Sector data does not exist for country code '{country_code}', using 'US' as fallback: {e}")
            file_path = dataset_path("common", "organization", "sector_US.csv", start=Path(__file__))
            self._sector_data_load = FileUtil.read_csv_to_list_of_tuples_without_header(file_path)
        super().__init__(rng=rng)

    def generate(self) -> str:
        """Generate a random sector.

        Returns:
            A randomly chosen sector.
        """
        return self._rng.choice(self._sector_data_load)[0]
