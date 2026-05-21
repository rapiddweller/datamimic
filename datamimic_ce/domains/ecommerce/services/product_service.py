# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from random import Random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field
from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator
from datamimic_ce.domains.ecommerce.models.product import Product

PRODUCT_SCHEMA = EntitySchema(
    "Product",
    (
        field("product_id", str, "Unique product identifier."),
        field("name", str, "Product name."),
        field("description", str, "Product description."),
        field("price", float, "Product price."),
        field("category", str, "Product category."),
        field("brand", str, "Product brand."),
        field("sku", str, "Stock keeping unit."),
        field("condition", str, "Product condition."),
        field("availability", str, "Availability status."),
        field("currency", str, "Price currency code."),
        field("weight", float, "Product weight."),
        field("dimensions", str, "Product dimensions."),
        field("color", str, "Product color."),
        field("rating", float, "Average customer rating."),
        field("tags", list, "Product tags."),
    ),
)


class ProductService(BaseDomainService[Product]):
    """Service for managing product data.

    This class provides methods for generating and operating on product data,
    including creating products, filtering products, and formatting outputs.
    """

    DATASET_PATTERNS = (
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
    )

    def __init__(
        self,
        dataset: str | None = None,
        min_price: float = 0.99,
        max_price: float = 999.99,
        rng: Random | None = None,
    ):
        super().__init__(
            ProductGenerator(
                dataset=dataset, min_price=min_price, max_price=max_price, rng=rng
            ),
            Product,
        )

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return PRODUCT_SCHEMA.fields
