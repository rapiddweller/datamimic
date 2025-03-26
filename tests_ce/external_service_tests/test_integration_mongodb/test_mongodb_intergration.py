# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.config import settings
from datamimic_ce.data_mimic_test import DataMimicTest


class TestMongoDB:
    _test_dir = Path(__file__).resolve().parent

    def test_mongodb_update(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_update.xml")
        test_engine.test_with_timer()

    def test_mongodb_selector(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_selector.xml")
        test_engine.test_with_timer()

    def test_mongodb_selector_mp(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_selector_mp.xml")
        test_engine.test_with_timer()

    def test_mongodb_upsert(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_upsert.xml")
        test_engine.test_with_timer()

    def test_mongodb_delete(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_delete.xml")
        test_engine.test_with_timer()

    def test_mongodb_query(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_query.xml")
        test_engine.test_with_timer()

    def test_mongodb_aggregate(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_aggregate.xml")
        test_engine.test_with_timer()

    @pytest.mark.skipif(settings.RUNTIME_ENVIRONMENT != "development", reason="Run only on local")
    def test_mongodb_local_env(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_local_env.xml")
        test_engine.test_with_timer()

    @pytest.mark.skipif(settings.RUNTIME_ENVIRONMENT == "development", reason="Not run on local")
    def test_mongodb_global_env(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_global_env.xml")
        test_engine.test_with_timer()

    def test_mongodb_dynamic_selector(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_dynamic_selector.xml")
        test_engine.test_with_timer()
