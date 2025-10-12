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

from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.utils.dataset_loader import (
    load_weighted_values_try_dataset,
    pick_one_weighted,
)


class ProductGenerator(BaseDomainGenerator):
    """Generator for e-commerce product data.

    This class provides methods to generate individual products or batches
    of products with realistic data.
    """

    def __init__(
        self, dataset: str = "US", min_price: float = 0.99, max_price: float = 999.99, rng: random.Random | None = None
    ):
        self._dataset = dataset.upper()  #  make dataset suffix case-consistent for CSV resolution
        self._min_price = min(min_price, max_price)
        self._max_price = max(min_price, max_price)
        self._rng: random.Random = rng or random.Random()

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def rng(self) -> random.Random:
        return self._rng

    # Helper: pick rating bucket and apply half-star tweak
    def pick_rating(self, *, start: Path) -> float:
        values, weights = load_weighted_values_try_dataset(
            "ecommerce", "product", "rating_weights.csv", dataset=self._dataset, start=start
        )
        base_s = pick_one_weighted(self._rng, list(values), list(weights))
        try:
            base = float(base_s)
        except (TypeError, ValueError):
            base = 3.0
        if self._rng.random() < 0.5:
            base -= 0.5
        return max(1.0, base)

    # Helper: maybe pick a trending tag
    def maybe_pick_trending_tag(self, *, start: Path) -> str | None:
        if self._rng.random() >= 0.2:
            return None
        values, weights = load_weighted_values_try_dataset(
            "ecommerce", "product", "trending_tags.csv", dataset=self._dataset, start=start
        )
        return pick_one_weighted(self._rng, values, weights)

    def get_product_data_by_data_type(self, data_type: str) -> str:
        """Load data for the specified type and dataset.
        Args:
            data_type: The type of data to load
        Returns:
            Data of product base on dat type
        """
        # Special-case: nouns live in per-category CSVs already present in domain_data
        if data_type.startswith("product_nouns_"):
            category = data_type.removeprefix("product_nouns_")
            category_norm = category.lower()
            values, weights = load_weighted_values_try_dataset(
                "ecommerce",
                f"product_nouns_{category_norm}.csv",
                dataset=self._dataset,
                start=Path(__file__),
            )
            return pick_one_weighted(self._rng, values, weights)

        # Headered weighted CSVs: select by 'weight', return first column (value)
        if data_type in {
            "product_adjectives",
            "product_categories",
            "product_brands",
            "product_colors",
            "product_conditions",
            "product_availability",
            "currencies",
            "product_benefits",
        }:
            from datamimic_ce.domains.utils.dataset_path import dataset_path
            from datamimic_ce.utils.file_util import FileUtil

            file_name = f"{data_type.lower()}_{self._dataset}.csv"
            file_path = dataset_path("ecommerce", file_name, start=Path(__file__))
            header_dict, loaded_data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, delimiter=",")
            w_idx = header_dict.get("weight")
            if w_idx is not None:
                chosen = self._rng.choices(loaded_data, weights=[float(row[w_idx]) for row in loaded_data], k=1)[0]
            else:
                chosen = self._rng.choice(loaded_data)
            return chosen[0]

        # Fallback: headerless 2-column weighted CSVs
        values, weights = load_weighted_values_try_dataset(
            "ecommerce", f"{data_type.lower()}.csv", dataset=self._dataset, start=Path(__file__)
        )
        return pick_one_weighted(self._rng, values, weights)

    def price_with_strategy(self) -> float:
        """Generate a price using common pricing strategies.
        Returns:
            A price following common pricing strategies like .99 endings
        """
        min_price = self._min_price
        max_price = self._max_price
        # Use different price points based on common retail pricing strategies
        price_points = [
            round(self._rng.uniform(min_price, max_price), 2),  # Regular price
            round(self._rng.uniform(max(min_price, 1.0), min(max_price, 100)), 99) / 100,  # $X.99 price
            round(self._rng.uniform(max(min_price, 100), min(max_price, 1000)), 95) / 100,  # $X.95 price
            round(self._rng.uniform(max(min_price, 1000), max_price), 0),  # Whole dollar price for expensive items
        ]

        price = self._rng.choice(price_points)
        return max(min_price, min(price, max_price))  # Ensure price is between min_price and max_price

    def get_random_features(self, category: str, min_feature: int = 1, max_feature: int = 1) -> list[str]:
        features = self._load_product_json("features_by_category").get(
            category, ["High quality", "Versatile", "Durable"]
        )
        return self._rng.sample(features, min(len(features), self._rng.randint(min_feature, max_feature)))

    def get_random_weight(self, category: str) -> float:
        weights = self._load_product_json("weight_ranges_by_category").get(category, {"min": 0.1, "max": 50.0})
        return round(self._rng.uniform(weights["min"], weights["max"]), 2)

    def get_random_dimensions(self, category) -> str:
        default_dimensions = {
            "length": {"min": 1, "max": 200},
            "width": {"min": 1, "max": 200},
            "height": {"min": 1, "max": 200},
        }
        dimensions = self._load_product_json("dimension_ranges_by_category").get(category, default_dimensions)
        length = round(self._rng.uniform(dimensions["length"]["min"], dimensions["length"]["max"]), 1)
        width = round(self._rng.uniform(dimensions["width"]["min"], dimensions["width"]["max"]), 1)
        height = round(self._rng.uniform(dimensions["height"]["min"], dimensions["height"]["max"]), 1)

        return f"{length} x {width} x {height} cm"

    def get_random_tags(self, category: str) -> list[str]:
        tags = self._load_product_json("tags_by_category").get(category, ["product", "item", "goods"])
        return self._rng.sample(tags, min(len(tags), self._rng.randint(2, 4)))

    @staticmethod
    def _load_product_json(file_name):
        #  Keep JSON helper for non-weighted structured data; paths resolved via dataset_path in FileUtil
        from datamimic_ce.domains.utils.dataset_path import dataset_path
        from datamimic_ce.utils.file_util import FileUtil

        file_path = dataset_path("ecommerce", "product", f"{file_name}.json", start=Path(__file__))
        return FileUtil.read_json(file_path)
