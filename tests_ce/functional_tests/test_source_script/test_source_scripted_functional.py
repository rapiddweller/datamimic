# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestSourceScripted:
    _test_dir = Path(__file__).resolve().parent

    def test_csv_source_scripted(self):
        """
        Test if the output of generation match the expect result.
        For example check if the age column is a number , which mean the source script is evaluate correctly
        Args:
            test_dir (): current test dir
        """
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_csv_source_scripted.xml", capture_test_result=True
        )
        engine.test_with_timer()

        result = engine.capture_result()
        people_from_source = result["people_from_source"]

        assert result
        assert len(people_from_source) == 10
        for people in people_from_source:
            if people["people_name"] == "Steve":
                assert people["people_age"] == 59
            elif people["people_name"] == "Daniel":
                assert people["people_age"] == 70
            elif people["people_name"] == "Tom":
                assert people["people_age"] == 81
            elif people["people_name"] == "David":
                assert people["people_age"] == 92
            elif people["people_name"] == "Ocean":
                assert people["people_age"] == 103

    def test_json_source_script_cyclic(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_json_source_scripted.xml", capture_test_result=True
        )
        engine.test_with_timer()

        result = engine.capture_result()
        json_product = result["json-product"]

        assert len(json_product) == 100
        for product in json_product:
            if product.get("name") == "May":
                assert product.get("age") == 23
            elif product.get("name") == "Alice":
                assert product.get("age") == 26
            elif product.get("name") in ["Bob", "Other"]:
                assert 10 <= product.get("age") <= 40

            if product.get("name") == "Other":
                assert (
                    product.get("variable") == "This is a string, so that it won't evaluate script {random_age(20,40)}"
                )
            else:
                assert product.get("variable") == "addition_1"

    def test_iterate_source_script(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_iterate_source_scripted.xml", capture_test_result=True
        )
        engine.test_with_timer()

        result = engine.capture_result()
        iterate_json = result["iterate_json"]

        assert len(iterate_json) == 4
        for product in iterate_json:
            if product.get("name") == "May":
                assert product.get("age") == 23
            elif product.get("name") == "Alice":
                assert product.get("age") == 26
            elif product.get("name") == ["Bob", "Other"]:
                assert 10 <= product.get("age") <= 40

            if product.get("name") == "Other":
                assert (
                    product.get("variable") == "This is a string, so that it won't evaluate script {random_age(20,40)}"
                )
            else:
                assert product.get("variable") == "addition_1"

        iterate_csv = result["iterate_csv"]
        assert result
        assert len(iterate_csv) == 5
        for people in iterate_csv:
            if people["name"] == "Steve":
                assert people["age"] == 59
            elif people["name"] == "Daniel":
                assert people["age"] == 70
            elif people["name"] == "Tom":
                assert people["age"] == 81
            elif people["name"] == "David":
                assert people["age"] == 92
            elif people["name"] == "Ocean":
                assert people["age"] == 103

    def test_part_source_script(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_part_source_scripted.xml", capture_test_result=True
        )
        engine.test_with_timer()

        result = engine.capture_result()
        iterate_json = result["test_json"]

        assert len(iterate_json) == 10
        for product in iterate_json[0]["people"]:
            if product.get("name") == "May":
                assert product.get("age") == 23
            elif product.get("name") == "Alice":
                assert product.get("age") == 26
            elif product.get("name") == ["Bob", "Other"]:
                assert 10 <= product.get("age") <= 40

            if product.get("name") == "Other":
                assert (
                    product.get("variable") == "This is a string, so that it won't evaluate script {random_age(20,40)}"
                )
            else:
                assert product.get("variable") == "addition_1"

        iterate_csv = result["test_csv"]
        assert len(iterate_csv) == 10
        for people in iterate_csv[0]["people"]:
            if people["name"] == "Steve":
                assert people["age"] == 59
            elif people["name"] == "Daniel":
                assert people["age"] == 70
            elif people["name"] == "Tom":
                assert people["age"] == 81
            elif people["name"] == "David":
                assert people["age"] == 92
            elif people["name"] == "Ocean":
                assert people["age"] == 103
