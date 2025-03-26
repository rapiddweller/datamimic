# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


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
