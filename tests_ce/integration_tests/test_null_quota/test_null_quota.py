# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest


class TestNullQuota:
    @pytest.fixture
    def test_dir(self) -> Path:
        return Path(__file__).resolve().parent

    def test_null_quota(self, test_dir: Path) -> None:
        test_engine = DataMimicTest(test_dir=test_dir, filename="test_null_quota.xml")
        test_engine.test_with_timer()
