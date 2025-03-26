# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.logger import logger
from datamimic_ce.utils.file_util import FileUtil


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

        file_path = Path(__file__).parent.parent.parent.parent.joinpath(
            f"domain_data/common/organization/sector_{country_code}.csv"
        )

        try:
            # Use the file content storage to cache the data
            self._sector_data_load = FileUtil.read_csv_to_list_of_tuples_without_header(file_path)
        except FileNotFoundError as e:
            logger.warning(f"Sector data does not exist for country code '{country_code}', using 'US' as fallback: {e}")
            file_path = Path(__file__).parent.parent.parent.parent.joinpath(
                "domain_data/common/organization/sector_US.csv"
            )
            self._sector_data_load = FileUtil.read_csv_to_list_of_tuples_without_header(file_path)

    def generate(self) -> str:
        """Generate a random sector.

        Returns:
            A randomly chosen sector.
        """
        return random.choice(self._sector_data_load)[0]
