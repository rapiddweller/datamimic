# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import random
import string

import pytest

from datamimic_ce.domains.ecommerce.models.product import Product
from datamimic_ce.domains.ecommerce.services import ProductService


class TestEntityProduct:
    _supported_datasets = ["US",]

    def _check_product_data(self, product: Product):
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
        self._check_product_data(product)

    def test_generate_multiple_product(self):
        product_service = ProductService()
        products = product_service.generate_batch(100)
        assert len(products) == 100
        for product in products:
            self._check_product_data(product)

    def test_product_property_cache(self):
        product_service = ProductService()
        product = product_service.generate()
        assert product.product_id == product.product_id
        assert product.name == product.name
        assert product.description == product.description
        assert product.price == product.price
        assert product.category == product.category
        assert product.brand == product.brand
        assert product.sku == product.sku
        assert product.condition == product.condition
        assert product.availability == product.availability
        assert product.currency == product.currency
        assert product.weight == product.weight
        assert product.dimensions == product.dimensions
        assert product.color == product.color
        assert product.rating == product.rating
        assert product.tags == product.tags

    def test_two_different_entities(self):
        product_service = ProductService()
        product1 = product_service.generate()
        product2 = product_service.generate()
        assert product1.to_dict() != product2.to_dict()
        assert product1.name != product2.name

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        product_service = ProductService(dataset=dataset)
        product = product_service.generate()
        self._check_product_data(product)

    def test_not_supported_dataset(self):
        random_dataset = "".join(random.choices(string.ascii_uppercase, k=2))
        while random_dataset in self._supported_datasets:
            random_dataset = "".join(random.choices(string.ascii_uppercase, k=2))
        # Raise FileNotFoundError because not found csv file of unsupported dataset
        with pytest.raises(FileNotFoundError):
            product_service = ProductService(dataset=random_dataset)
            product_service.generate()
