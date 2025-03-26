# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Product generator module.

This module provides a generator for e-commerce product data.
"""

import random
from pathlib import Path

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.utils.file_util import FileUtil


class ProductGenerator(BaseDomainGenerator):
    """Generator for e-commerce product data.

    This class provides methods to generate individual products or batches
    of products with realistic data.
    """

    def __init__(self, dataset: str = "US", min_price: float = 0.99, max_price: float = 999.99):
        self._dataset = dataset
        self._min_price = min(min_price, max_price)
        self._max_price = max(min_price, max_price)

    def get_product_data_by_data_type(self, data_type: str) -> str:
        """Load data for the specified type and dataset.
        Args:
            data_type: The type of data to load
        Returns:
            Data of product base on dat type
        """
        file_name = f"{data_type.lower()}_{self._dataset.upper()}.csv"
        file_path = Path(__file__).parent.parent.parent.parent / "domain_data/ecommerce" / file_name
        header_dict, loaded_data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, delimiter=",")

        wgt_idx = header_dict["weight"]
        return random.choices(loaded_data, weights=[float(row[wgt_idx]) for row in loaded_data])[0][0]

    def price_with_strategy(self) -> float:
        """Generate a price using common pricing strategies.
        Returns:
            A price following common pricing strategies like .99 endings
        """
        min_price = self._min_price
        max_price = self._max_price
        # Use different price points based on common retail pricing strategies
        price_points = [
            round(random.uniform(min_price, max_price), 2),  # Regular price
            round(random.uniform(max(min_price, 1.0), min(max_price, 100)), 99) / 100,  # $X.99 price
            round(random.uniform(max(min_price, 100), min(max_price, 1000)), 95) / 100,  # $X.95 price
            round(random.uniform(max(min_price, 1000), max_price), 0),  # Whole dollar price for expensive items
        ]

        price = random.choice(price_points)
        return max(min_price, min(price, max_price))  # Ensure price is between min_price and max_price

    def get_random_features(self, category: str, min_feature: int = 1, max_feature: int = 1) -> list[str]:
        features = self._load_product_json("features_by_category").get(
            category, ["High quality", "Versatile", "Durable"]
        )
        return random.sample(features, min(len(features), random.randint(min_feature, max_feature)))

    def get_random_weight(self, category: str) -> float:
        weights = self._load_product_json("weight_ranges_by_category").get(category, {"min": 0.1, "max": 50.0})
        return round(random.uniform(weights["min"], weights["max"]), 2)

    def get_random_dimensions(self, category) -> str:
        default_dimensions = {
            "length": {"min": 1, "max": 200},
            "width": {"min": 1, "max": 200},
            "height": {"min": 1, "max": 200},
        }
        dimensions = self._load_product_json("dimension_ranges_by_category").get(category, default_dimensions)
        length = round(random.uniform(dimensions["length"]["min"], dimensions["length"]["max"]), 1)
        width = round(random.uniform(dimensions["width"]["min"], dimensions["width"]["max"]), 1)
        height = round(random.uniform(dimensions["height"]["min"], dimensions["height"]["max"]), 1)

        return f"{length} x {width} x {height} cm"

    def get_random_tags(self, category: str) -> list[str]:
        tags = self._load_product_json("tags_by_category").get(category, ["product", "item", "goods"])
        return random.sample(tags, min(len(tags), random.randint(2, 4)))

    @staticmethod
    def _load_product_json(file_name):
        file_path = Path(__file__).parent.parent.parent.parent / "domain_data/ecommerce/product" / f"{file_name}.json"
        return FileUtil.read_json(file_path)
