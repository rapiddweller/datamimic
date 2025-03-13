# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestEntityFunctional:
    _test_dir = Path(__file__).resolve().parent

    def test_entity_person(self) -> None:
        engine = DataMimicTest(test_dir=self._test_dir, filename="person_entity_test.xml", capture_test_result=True)
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
