# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

import pandas as pd

class TestEntityFunctional:
    _test_dir = Path(__file__).resolve().parent

    def test_functional_entity_person(self) -> None:
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="functional_test_entity_person.xml",
            capture_test_result=True)
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
            test_dir=self._test_dir,
            filename="functional_test_entity_product.xml",
            capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        assert result

        default_product = result["default_product"]
        assert len(default_product) == 50
        self._check_product(default_product)

        us_product = result["us_product"]
        assert len(us_product) == 50
        self._check_product(us_product)

    def _check_product(self, products):
        """
        helper of test case test_functional_entity_product
        """
        ecommerce_data_dir = Path(__file__).resolve().parents[3]/"datamimic_ce/domain_data/ecommerce"
        category_list = pd.read_csv(ecommerce_data_dir.joinpath("product_categories_US.csv"))["category"].tolist()
        brands_list = pd.read_csv(ecommerce_data_dir.joinpath("product_brands_US.csv"))["brand"].tolist()
        benefits_list = pd.read_csv(ecommerce_data_dir.joinpath("product_benefits.csv"))["benefit"].tolist()
        conditions_list = pd.read_csv(ecommerce_data_dir.joinpath("product_conditions_US.csv"))["condition"].tolist()
        availabilities_list = pd.read_csv(ecommerce_data_dir.joinpath("product_availability_US.csv"))["availability"].tolist()
        currencies_list = pd.read_csv(ecommerce_data_dir.joinpath("currencies_US.csv"))["code"].tolist()
        colors_list = pd.read_csv(ecommerce_data_dir.joinpath("product_colors_US.csv"))["color"].tolist()
        for product in products:
            product_id = product["product_id"]
            assert isinstance(product_id, str)
            assert product_id.startswith("PROD")
            assert len(product_id) == len("PROD")+8

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
            assert category.lower().replace('_', ' ') in description
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
            assert category.lower().replace('_', ' ') in tags
            assert brand.lower() in tags
            assert condition.lower() in tags if condition != "NEW" else condition.lower() not in tags
