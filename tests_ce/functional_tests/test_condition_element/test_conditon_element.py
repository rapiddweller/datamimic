# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestConditionElement:
    _test_dir = Path(__file__).resolve().parent

    def test_condition_element(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_condition_element.xml",
                                    capture_test_result=True)
        test_engine.test_with_timer()
        result = test_engine.capture_result()
        assert len(result) == 1
        data = result["CONDITIONTEST"]
        for e in data:
            if e["condition"] == "user_logged_in":
                assert e.get("IfCondition") == "Show logged content"
            elif e["condition"] == "user_is_premium":
                assert e.get("ElseIfCondition") == "Show gold message"
            else:
                assert e.get("ElseCondition") == "Redirect to login page"
