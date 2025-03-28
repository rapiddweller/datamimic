# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestGenerateDistribution:
    _test_dir = Path(__file__).resolve().parent

    def test_random_distribution_generate(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_random_distribution_generate.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        random_check = result.get("random_check", [])
        assert len(random_check) == 100
        assert len(set(list(map(lambda ele: ele.get("counter"), random_check)))) == 100

        ordered_check = result.get("ordered_check", [])
        assert len(ordered_check) == 100
        assert ordered_check[0].get("counter") == 1
        assert ordered_check[-1].get("counter") == 100
        assert ordered_check == sorted(ordered_check, key=lambda ele: ele.get("counter"))
        assert ordered_check != random_check

        cyclic_check_1 = result.get("cyclic_check_1", [])
        assert len(cyclic_check_1) == 150
        assert len(set(list(map(lambda ele: ele.get("counter"), cyclic_check_1)))) == 100
        assert cyclic_check_1[:100] != ordered_check
