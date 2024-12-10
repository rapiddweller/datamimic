# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



import time
from pathlib import Path

import pytest

from datamimic_ce.datamimic import DataMimic
from tests_ce.performance_tests.performance_test_util import PerformanceTestUtil


class TestTimeMongoDBWrite:
    _test_dir = Path(__file__).resolve().parent
    _base_path = _test_dir.joinpath("conf/base.properties")

    @pytest.fixture(scope="class", autouse=True)
    def setup_and_teardown(self):
        # Provide the setup value to the test class
        yield

        # Teardown code, change back properties file to default value
        default_count = "200"
        default_multiprocessing = "False"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", default_count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", default_multiprocessing)

    @pytest.mark.run(order=1)
    def test_single_thread_mongodb_write_200(self, benchmark) -> None:
        count = "200"
        multiprocessing = "False"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        benchmark.group = "single_thread_mongodb_write"
        benchmark.name = f"test_{count}"
        xml_path = self._test_dir.joinpath("measure_mongodb_write.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test"}

        time.sleep(1)  # Warm-up period
        benchmark(DataMimic(**kwargs).parse_and_execute)

    @pytest.mark.run(order=2)
    def test_single_thread_mongodb_write_2000(self, benchmark) -> None:
        count = "2000"
        multiprocessing = "False"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        benchmark.group = "single_thread_mongodb_write"
        benchmark.name = f"test_{count}"
        xml_path = self._test_dir.joinpath("measure_mongodb_write.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test"}

        time.sleep(1)  # Warm-up period
        benchmark(DataMimic(**kwargs).parse_and_execute)

    @pytest.mark.run(order=3)
    def test_single_thread_mongodb_write_20000(self, benchmark) -> None:
        count = "20000"
        multiprocessing = "False"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        benchmark.group = "single_thread_mongodb_write"
        benchmark.name = f"test_{count}"
        xml_path = self._test_dir.joinpath("measure_mongodb_write.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test"}

        time.sleep(1)  # Warm-up period
        benchmark(DataMimic(**kwargs).parse_and_execute)

    @pytest.mark.run(order=4)
    def test_multiprocessing_mongodb_write_200(self, benchmark) -> None:
        count = "200"
        multiprocessing = "True"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        benchmark.group = "multiprocessing_mongodb_write"
        benchmark.name = f"test_{count}"
        xml_path = self._test_dir.joinpath("measure_mongodb_write.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test"}

        time.sleep(1)  # Warm-up period
        benchmark(DataMimic(**kwargs).parse_and_execute)

    @pytest.mark.run(order=5)
    def test_multiprocessing_mongodb_write_2000(self, benchmark) -> None:
        count = "2000"
        multiprocessing = "True"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        benchmark.group = "multiprocessing_mongodb_write"
        benchmark.name = f"test_{count}"
        xml_path = self._test_dir.joinpath("measure_mongodb_write.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test"}

        time.sleep(1)  # Warm-up period
        benchmark(DataMimic(**kwargs).parse_and_execute)

    @pytest.mark.run(order=6)
    def test_multiprocessing_mongodb_write_20000(self, benchmark) -> None:
        count = "20000"
        multiprocessing = "True"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        benchmark.group = "multiprocessing_mongodb_write"
        benchmark.name = f"test_{count}"
        xml_path = self._test_dir.joinpath("measure_mongodb_write.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test"}

        time.sleep(1)  # Warm-up period
        benchmark(DataMimic(**kwargs).parse_and_execute)
