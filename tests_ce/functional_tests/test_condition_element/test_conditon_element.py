# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



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
