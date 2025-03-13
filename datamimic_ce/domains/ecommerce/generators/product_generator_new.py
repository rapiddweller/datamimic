# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Product generator module.

This module provides a generator for e-commerce product data.
"""

from typing import Optional, List, Tuple, ClassVar

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator


class ProductGeneratorNew(BaseDomainGenerator):
    """Generator for e-commerce product data.

    This class provides methods to generate individual products or batches
    of products with realistic data.
    """

    _product_data_dataset_not_found_set: ClassVar[set[str]] = set()

    def __init__(self, dataset: Optional[str] = None):
        # Use 'global' as the default dataset key
        self._dataset = dataset or "global"
        self._processed_product_data_dataset = None

    def _get_processed_dataset_list(self, dataset_not_found_list: set[str]) -> list[str]:
        """Get the processed dataset list.

        Args:
            dataset_not_found_list: The list of dataset not found.
        """
        processed_dataset_list = []
        if self._dataset not in dataset_not_found_list:
            processed_dataset_list.append(self._dataset)
        #TODO:

    def _load_data(self, data_type: str, dataset: Optional[str] = None) -> List[Tuple[str, float]]:
        """Load data for the specified type and dataset.

        Args:
            data_type: The type of data to load
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing values and weights
        """

        if self._processed_city_data_dataset is None:
            processed_dataset_list = self._get_processed_dataset_list(self._product_data_dataset_not_found_set)

    def get_random_product(self):
        pass
