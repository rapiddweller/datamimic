# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestEntityFunctional:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_entity_person(self) -> None:
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="person_entity_test.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        assert result

        females = result["female"]
        for female in females:
            assert 1 <= female["age"] <= 10
            assert female["gender"] == "female"

        males = result["male"]
        for male in males:
            assert 20 <= male["age"] <= 45
            assert male["gender"] == "male"
