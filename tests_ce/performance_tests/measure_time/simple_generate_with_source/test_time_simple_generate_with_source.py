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


class TestTimeSimpleGenerateWithSource:
    _test_dir = Path(__file__).resolve().parent
    _base_path = _test_dir.joinpath("conf/base.properties")

    @pytest.fixture(scope="class", autouse=True)
    def setup_and_teardown(self):
        # Provide the setup value to the test class
        yield

        # Teardown code (runs after each test method)
        default_count = "1000"
        default_multiprocessing = "False"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", default_count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", default_multiprocessing)

    def test_single_thread_with_source_1000(self, benchmark):
        count = "1000"
        multiprocessing = "False"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        benchmark.group = "single_thread_with_source"
        benchmark.name = f"test_{count}"
        xml_path = self._test_dir.joinpath("measure_simple_generate_with_source.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test"}

        time.sleep(1)  # Warm-up period
        benchmark(DataMimic(**kwargs).parse_and_execute)

    def test_single_thread_with_source_10000(self, benchmark):
        count = "10000"
        multiprocessing = "False"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        benchmark.group = "single_thread_with_source"
        benchmark.name = f"test_{count}"
        xml_path = self._test_dir.joinpath("measure_simple_generate_with_source.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test"}

        time.sleep(1)  # Warm-up period
        benchmark(DataMimic(**kwargs).parse_and_execute)

    def test_single_thread_with_source_with_source_100000(self, benchmark):
        count = "100000"
        multiprocessing = "False"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        benchmark.group = "single_thread_with_source"
        benchmark.name = f"test_{count}"
        xml_path = self._test_dir.joinpath("measure_simple_generate_with_source.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test"}

        time.sleep(1)  # Warm-up period
        benchmark(DataMimic(**kwargs).parse_and_execute)

    def test_multiprocessing_with_source_1000(self, benchmark):
        count = "1000"
        multiprocessing = "True"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        benchmark.group = "multiprocessing_with_source"
        benchmark.name = f"test_{count}"
        xml_path = self._test_dir.joinpath("measure_simple_generate_with_source.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test"}

        time.sleep(1)  # Warm-up period
        benchmark(DataMimic(**kwargs).parse_and_execute)

    def test_multiprocessing_with_source_10000(self, benchmark):
        count = "10000"
        multiprocessing = "True"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        benchmark.group = "multiprocessing_with_source"
        benchmark.name = f"test_{count}"
        xml_path = self._test_dir.joinpath("measure_simple_generate_with_source.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test"}

        time.sleep(1)  # Warm-up period
        benchmark(DataMimic(**kwargs).parse_and_execute)

    def test_multiprocessing_with_source_100000(self, benchmark):
        count = "100000"
        multiprocessing = "True"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        benchmark.group = "multiprocessing_with_source"
        benchmark.name = f"test_{count}"
        xml_path = self._test_dir.joinpath("measure_simple_generate_with_source.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test"}

        time.sleep(1)  # Warm-up period
        benchmark(DataMimic(**kwargs).parse_and_execute)
