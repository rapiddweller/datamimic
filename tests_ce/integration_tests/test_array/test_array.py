# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest


class TestArray:
    @pytest.fixture
    def test_dir(self) -> Path:
        return Path(__file__).resolve().parent

    def test_array_simple_types(self, test_dir: Path) -> None:
        test_engine = DataMimicTest(test_dir=test_dir, filename="test_array_simple_types.xml")
        test_engine.test_with_timer()

    def test_array_invalid_type(self, test_dir: Path) -> None:
        test_engine = DataMimicTest(test_dir=test_dir, filename="test_array_invalid_type.xml")
        # Use pytest.raises to capture the expected error
        with pytest.raises(ValueError):
            test_engine.test_with_timer()

    def test_array_script(self, test_dir: Path) -> None:
        test_engine = DataMimicTest(test_dir=test_dir, filename="test_array_script.xml")
        test_engine.test_with_timer()
