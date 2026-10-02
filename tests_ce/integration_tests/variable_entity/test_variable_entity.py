# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


class TestVariableEntity:
    _test_dir = Path(__file__).resolve().parent

    def test_person_entity(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_person_entity.xml", capture_test_result=True
        )
        engine.test_with_timer()
        rows = engine.capture_result()["user"]

        assert len(rows) == 5
        assert [row["id"] for row in rows] == [1, 2, 3, 4, 5]
        assert all(row["name"] and row["email"] and row["birthday"] for row in rows)
        assert all(isinstance(row["age"], int) and row["age"] >= 0 for row in rows)

    def test_company_entity(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_company_entity.xml")
        engine.test_with_timer()

    def test_city_entity(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_city_entity.xml")
        engine.test_with_timer()

    def test_address_entity(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_address_entity.xml")
        engine.test_with_timer()

    def test_credit_card_entity(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_credit_card_entity.xml")
        engine.test_with_timer()
