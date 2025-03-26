# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestStringInKeyVariableNode:
    _test_dir = Path(__file__).resolve().parent

    def test_string_with_key(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_string_with_key.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()
        query = result["test_string_key"]
        assert len(query) == 3
        for e in query:
            assert e["query"] == "find: 'orders', filter: 'status': 'active', 'priority': 'high'"

    def test_string_variable(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_string_in_variable.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()
        query = result["test_string_variable"]
        assert len(query) == 3
        for e in query:
            assert e["query"] == "find: 'ordered'"

    def test_string_multiple_variable(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_string_multiple_variable.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()
        query = result["test_string_multiple_variable"]
        assert len(query) == 3
        for e in query:
            assert e["query"] == "find: 'classA'"

    def test_string_multiple_key(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_string_multiple_key.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()
        query = result["test_string_multiple_key"]
        assert len(query) == 3
        for e in query:
            assert e["shipping_card_2"] == "'package' is being prepared."
            assert e["shipping_card_3"] == "'package' has already been shipped."
            assert e["shipping_card_4"] == "Now 'package' has arrived to your address."
            assert (
                e["shipping_card_5"]
                == "Details of shipping card: 'package' is being prepared. 'package' has already been shipped. 'package' has already been shipped."
            )
