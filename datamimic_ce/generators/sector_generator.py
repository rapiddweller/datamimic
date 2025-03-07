# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domains.common.data_loaders.company_loader import CompanyLoader
from datamimic_ce.generators.generator import Generator
from datamimic_ce.utils.file_content_storage import FileContentStorage


class SectorGenerator(Generator):
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
        
        # Use the file content storage to cache the data
        self._sector_data_load = FileContentStorage.load_file_with_custom_func(
            cache_key=f"sector_{country_code}",
            read_func=lambda: self._load_sector_data(country_code)
        )

    def _load_sector_data(self, country_code: str) -> list[str]:
        """Load sector data using the CompanyDataLoader.
        
        Args:
            country_code: The country code to use.
            
        Returns:
            List of sector values.
        """
        # Get sector data from CompanyDataLoader
        sector_data = CompanyLoader.get_country_specific_data(
            data_type="sector",
            country_code=country_code,
            domain_path="organization"
        )
        
        # Extract just the values, not the weights
        return [item[0] for item in sector_data]

    def generate(self) -> str:
        """Generate a random sector.
        
        Returns:
            A randomly chosen sector.
        """
        return random.choice(self._sector_data_load)
