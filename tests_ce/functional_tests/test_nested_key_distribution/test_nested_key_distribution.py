# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestVariableDistribution:
    _test_dir = Path(__file__).resolve().parent

    def test_random_distribution_nested_key(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_random_distribution_nested_key.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        nested_key = result.get("check", [])[0].get("nested_key")
        assert len(nested_key) == 100
        assert len(set(list(map(lambda ele: ele.get("counter"), nested_key)))) == 100

        cyclic_nested_key = result.get("check", [])[0].get("cyclic_nested_key")
        assert len(cyclic_nested_key) == 120
        assert len(set(list(map(lambda ele: ele.get("counter"), cyclic_nested_key)))) == 100

        ordered_nested_key = result.get("ordered_check", [])[0].get("nested_key")
        assert len(ordered_nested_key) == 100
        assert ordered_nested_key[0].get("counter") == 1
        assert ordered_nested_key[-1].get("counter") == 100
        assert ordered_nested_key != nested_key
        assert ordered_nested_key == sorted(nested_key, key=lambda ele: ele.get("counter"))
