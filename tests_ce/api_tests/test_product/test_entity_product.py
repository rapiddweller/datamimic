# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import pytest

from datamimic_ce.domains.ecommerce.models.product import Product
from datamimic_ce.domains.ecommerce.services import ProductService


class TestEntityProduct:
    _supported_datasets = ["US",]

    def _check_entity_data(self, product: Product):
        assert isinstance(product, Product)
        assert isinstance(product.product_id, str)
        assert isinstance(product.category, str)
        assert isinstance(product.brand, str)
        assert isinstance(product.name, str)
        assert isinstance(product.description, str)
        assert isinstance(product.price, float)
        assert isinstance(product.sku, str)
        assert isinstance(product.condition, str)
        assert isinstance(product.availability, str)
        assert isinstance(product.currency, str)
        assert isinstance(product.weight, float)
        assert isinstance(product.dimensions, str)
        assert isinstance(product.color, str)
        assert isinstance(product.rating, float)
        assert isinstance(product.tags, list)
        assert isinstance(product.to_dict(), dict)

        assert product.product_id is not None
        assert product.name is not None
        assert product.description is not None
        assert product.price is not None
        assert product.category is not None
        assert product.brand is not None
        assert product.sku is not None
        assert product.condition is not None
        assert product.availability is not None
        assert product.currency is not None
        assert product.weight is not None
        assert product.dimensions is not None
        assert product.color is not None
        assert product.rating is not None
        assert product.tags is not None

    def test_generate_single_product(self):
        product_service = ProductService()
        product = product_service.generate()
        self._check_entity_data(product)
