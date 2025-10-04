# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator
from datamimic_ce.domains.ecommerce.models.product import Product


class ProductService(BaseDomainService[Product]):
    """Service for managing product data.

    This class provides methods for generating and operating on product data,
    including creating products, filtering products, and formatting outputs.
    """

    def __init__(self, dataset: str | None = None, min_price: float = 0.99, max_price: float = 999.99):
        #  Prefer generator to own normalization. Pass through when provided,
        # fallback to "US" for backward compatibility with generator signature.
        super().__init__(
            ProductGenerator(dataset=dataset or "US", min_price=min_price, max_price=max_price),
            Product,
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        #  SPOT - list all required inputs used by generator helpers
        patterns = [
            "ecommerce/product_adjectives_{CC}.csv",
            "ecommerce/product_categories_{CC}.csv",
            "ecommerce/product_brands_{CC}.csv",
            "ecommerce/product_benefits_{CC}.csv",
            "ecommerce/product_colors_{CC}.csv",
            "ecommerce/product_conditions_{CC}.csv",
            "ecommerce/product_availability_{CC}.csv",
            "ecommerce/currencies_{CC}.csv",
            "ecommerce/product/rating_weights_{CC}.csv",
            "ecommerce/product/trending_tags_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
