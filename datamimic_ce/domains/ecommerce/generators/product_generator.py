# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Product generator module.

This module provides a generator for e-commerce product data.
"""
import random
from pathlib import Path
from typing import Optional

from datamimic_ce.utils.file_util import FileUtil

from datamimic_ce.utils.file_content_storage import FileContentStorage

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator


class ProductGenerator(BaseDomainGenerator):
    """Generator for e-commerce product data.

    This class provides methods to generate individual products or batches
    of products with realistic data.
    """

    def __init__(self, dataset: Optional[str] = None):
        self._dataset = dataset

    def load_product_data(self, data_type: str) -> str:
        """Load data for the specified type and dataset.
        Args:
            data_type: The type of data to load
        Returns:
            A list of tuples containing values and weights
        """
        if self._dataset:
            cache_key = f"{data_type}_{self._dataset}"
        else:
            cache_key = f"{data_type}"

        if cache_key not in self._LOADED_DATA_CACHE:
            file_path = (Path(__file__).parent.parent.parent
                         .parent / "domain_data" / "ecommerce" / f"{cache_key}.csv")
            self._LOADED_DATA_CACHE[cache_key] = FileContentStorage.load_file_with_custom_func(
                cache_key=str(file_path),
                read_func=lambda: FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, delimiter=",")
            )
        header_dict, loaded_data = self._LOADED_DATA_CACHE[cache_key]

        wgt_idx = header_dict["weight"]
        return random.choices(loaded_data, weights=[float(row[wgt_idx]) for row in loaded_data])[0][0]

    def price_with_strategy(self, min_price, max_price):
        """Generate a price using common pricing strategies.

        Args:
            min_price: Minimum price
            max_price: Maximum price

        Returns:
            A price following common pricing strategies like .99 endings
        """
        # Use different price points based on common retail pricing strategies
        price_points = [
            round(random.uniform(min_price, max_price), 2),  # Regular price
            round(random.uniform(max(min_price, 1.0), min(max_price, 100)), 99) / 100,  # $X.99 price
            round(random.uniform(max(min_price, 100), min(max_price, 1000)), 95) / 100,  # $X.95 price
            round(random.uniform(max(min_price, 1000), max_price), 0),  # Whole dollar price for expensive items
        ]

        price = random.choice(price_points)
        return max(min_price, min(price, max_price))  # Ensure price is between min_price and max_price

    def get_random_features(self, category: str, min_feature: int = 1, max_feature: int = 1):
        cache_key = "features_by_category"
        if cache_key not in self._LOADED_DATA_CACHE:
            self._load_product_json(cache_key)
        features = self._LOADED_DATA_CACHE[cache_key].get(category, ["High quality", "Versatile", "Durable"])
        return random.sample(features, min(len(features), random.randint(min_feature, max_feature)))

    def get_random_weight(self, category: str):
        cache_key = "weight_ranges_by_category"
        if cache_key not in self._LOADED_DATA_CACHE:
            self._load_product_json(cache_key)
        weights = self._LOADED_DATA_CACHE[cache_key].get(category, {"min": 0.1, "max": 50.0})
        return round(random.uniform(weights["min"], weights["max"]), 2)

    def get_random_dimensions(self, category):
        cache_key = "dimension_ranges_by_category"
        default_dimensions = {
            "length": {"min": 1, "max": 200},
            "width": {"min": 1, "max": 200},
            "height": {"min": 1, "max": 200}
        }
        if cache_key not in self._LOADED_DATA_CACHE:
            self._load_product_json(cache_key)

        dimensions = self._LOADED_DATA_CACHE[cache_key].get(category, default_dimensions)
        length = round(random.uniform(dimensions["length"]["min"], dimensions["length"]["max"]), 1)
        width = round(random.uniform(dimensions["width"]["min"], dimensions["width"]["max"]), 1)
        height = round(random.uniform(dimensions["height"]["min"], dimensions["height"]["max"]), 1)

        return f"{length} x {width} x {height} cm"

    def get_random_tags(self, category: str):
        cache_key = "tags_by_category"
        if cache_key not in self._LOADED_DATA_CACHE:
            self._load_product_json(cache_key)
        tags = self._LOADED_DATA_CACHE[cache_key].get(category, ["product", "item", "goods"])
        return random.sample(tags, min(len(tags), random.randint(2, 4)))

    def _load_product_json(self, cache_key):
        file_path = (Path(__file__).parent.parent.parent
                     .parent / "domain_data" / "ecommerce" / f"{cache_key}.json")
        self._LOADED_DATA_CACHE[cache_key] = FileContentStorage.load_file_with_custom_func(
            cache_key=str(file_path),
            read_func=lambda: FileUtil.read_json_to_dict(file_path)
        )

