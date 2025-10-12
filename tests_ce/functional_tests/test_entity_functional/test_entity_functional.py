# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import datetime
from pathlib import Path

import pandas as pd

from datamimic_ce.data_mimic_test import DataMimicTest


class TestEntityFunctional:
    _test_dir = Path(__file__).resolve().parent

    def test_functional_entity_person(self) -> None:
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="functional_test_entity_person.xml", capture_test_result=True
        )
        engine.test_with_timer()

        result = engine.capture_result()
        assert result

        females = result["female"]
        for female in females:
            assert 1 <= female["age"] <= 10
            assert female["gender"] == "female"

        males = result["male"]
        for male in males:
            assert 20 <= male["age"] <= 45
            # TODO: Modify other_gender_quota
            assert male["gender"] == "male" or male["gender"] == "other"

    def test_functional_entity_product(self) -> None:
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="functional_test_entity_product.xml", capture_test_result=True
        )
        engine.test_with_timer()

        result = engine.capture_result()
        assert result

        default_product = result["default_product"]
        assert len(default_product) == 50
        self._check_product(default_product)

        us_product = result["us_product"]
        assert len(us_product) == 50
        self._check_product(us_product)

    def test_functional_entity_order(self) -> None:
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="functional_test_entity_order.xml", capture_test_result=True
        )
        engine.test_with_timer()

        result = engine.capture_result()
        assert result

        default_order = result["default_order"]
        assert len(default_order) == 50
        self._check_order(default_order)

        us_order = result["us_order"]
        assert len(us_order) == 50
        self._check_order(us_order)

    def _check_product(self, products):
        """
        helper of test case test_functional_entity_product
        """
        ecommerce_data_dir = Path(__file__).resolve().parents[3] / "datamimic_ce/domains/domain_data/ecommerce"
        category_list = pd.read_csv(ecommerce_data_dir.joinpath("product_categories_US.csv"))["category"].tolist()
        brands_list = pd.read_csv(ecommerce_data_dir.joinpath("product_brands_US.csv"))["brand"].tolist()
        benefits_list = pd.read_csv(ecommerce_data_dir.joinpath("product_benefits_US.csv"))["benefit"].tolist()
        conditions_list = pd.read_csv(ecommerce_data_dir.joinpath("product_conditions_US.csv"))["condition"].tolist()
        availabilities_list = pd.read_csv(ecommerce_data_dir.joinpath("product_availability_US.csv"))[
            "availability"
        ].tolist()
        currencies_list = pd.read_csv(ecommerce_data_dir.joinpath("currencies_US.csv"))["code"].tolist()
        colors_list = pd.read_csv(ecommerce_data_dir.joinpath("product_colors_US.csv"))["color"].tolist()
        for product in products:
            product_id = product["product_id"]
            assert isinstance(product_id, str)
            assert product_id.startswith("PROD")
            assert len(product_id) == len("PROD") + 8

            name = product["name"]
            category = product["category"]
            brand = product["brand"]

            assert category in category_list
            assert brand in brands_list
            assert isinstance(name, str)
            assert brand in name
            assert len(name) > len(brand)

            description = product["description"]
            assert isinstance(description, str)
            assert name in description
            assert category.lower().replace("_", " ") in description
            assert any(benefit in description for benefit in benefits_list)

            assert 1.99 <= product["price"] <= 19.99

            sku = product["sku"]
            assert isinstance(sku, str)
            assert len(sku) == 14

            condition = product["condition"]
            assert condition in conditions_list

            assert product["availability"] in availabilities_list
            assert product["currency"] in currencies_list

            weight = product["weight"]
            assert isinstance(weight, float)

            dimensions = product["dimensions"]
            assert isinstance(dimensions, str)
            assert dimensions.endswith("cm")

            assert product["color"] in colors_list

            rating = product["rating"]
            assert isinstance(rating, float)
            assert 1.0 <= rating <= 5.0

            tags = product["tags"]
            assert isinstance(tags, list)
            assert len(tags) >= 4
            assert category.lower().replace("_", " ") in tags
            assert brand.lower() in tags
            assert condition.lower() in tags if condition != "NEW" else condition.lower() not in tags

    def _check_order(self, orders):
        """
        helper of test case test_functional_entity_order
        """
        ecommerce_data_dir = Path(__file__).resolve().parents[3] / "datamimic_ce/domains/domain_data/ecommerce"
        status_list = pd.read_csv(ecommerce_data_dir.joinpath("order_statuses_US.csv"))["status"].tolist()
        payment_methods_list = pd.read_csv(ecommerce_data_dir.joinpath("payment_methods_US.csv"))["method"].tolist()
        shipping_methods_list = pd.read_csv(ecommerce_data_dir.joinpath("shipping_methods_US.csv"))["method"].tolist()
        currencies_list = pd.read_csv(ecommerce_data_dir.joinpath("currencies_US.csv"))["code"].tolist()

        for order in orders:
            assert "order_id" in order
            order_id = order["order_id"]
            assert isinstance(order_id, str)
            assert order_id.startswith("ORD")
            assert len(order_id) == len("ORD") + 8

            assert "user_id" in order
            user_id = order["user_id"]
            assert isinstance(user_id, str)
            assert user_id.startswith("USER")
            assert len(user_id) == len("USER") + 8

            assert "date" in order
            assert isinstance(order["date"], datetime.datetime)

            assert "status" in order
            assert isinstance(order["status"], str)
            assert order["status"] in status_list

            assert "payment_method" in order
            assert isinstance(order["payment_method"], str)
            assert order["payment_method"] in payment_methods_list

            assert "shipping_method" in order
            assert isinstance(order["shipping_method"], str)
            assert order["shipping_method"] in shipping_methods_list

            assert "shipping_address" in order
            assert isinstance(order["shipping_address"], str)

            assert "billing_address" in order
            assert isinstance(order["billing_address"], str)

            assert "currency" in order
            assert isinstance(order["currency"], str)
            assert order["currency"] in currencies_list

            assert "tax_amount" in order
            assert isinstance(order["tax_amount"], float)
            assert order["tax_amount"] > 0.0

            assert "shipping_amount" in order
            assert isinstance(order["shipping_amount"], float)
            assert order["shipping_amount"] >= 0.0

            assert "discount_amount" in order
            assert isinstance(order["discount_amount"], float)
            assert order["discount_amount"] >= 0.0

            assert "total_amount" in order
            assert isinstance(order["total_amount"], float)
            assert order["total_amount"] > (order["tax_amount"] + order["shipping_amount"] - order["discount_amount"])
