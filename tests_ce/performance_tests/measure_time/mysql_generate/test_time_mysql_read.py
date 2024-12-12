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


class TestTimeMysqlRead:
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

    def _insert_data(self, filename: str, count: str, multiprocessing: str):
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        xml_path = self._test_dir.joinpath(filename)
        kwargs = {"descriptor_path": xml_path, "task_id": "test"}
        DataMimic(**kwargs).parse_and_execute()

    @pytest.mark.run(order=1)
    def test_single_thread_mysql_read_200(self, benchmark):
        count = "200"
        multiprocessing = "False"
        benchmark.group = "single_thread_mysql_read"
        benchmark.name = f"test_{count}"
        # insert data
        self._insert_data("measure_mysql_write.xml", count=count, multiprocessing=multiprocessing)
        # execute benchmark test
        time.sleep(1)  # Warm-up period
        xml_path = self._test_dir.joinpath("measure_mysql_read.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test", "test_mode": True}
        engine = DataMimic(**kwargs)
        benchmark(engine.parse_and_execute)
        # re-check result
        result = engine.capture_test_result()
        products = result["time_measure"]
        assert len(products) == int(count)

    @pytest.mark.run(order=2)
    def test_single_thread_mysql_read_2000(self, benchmark):
        count = "2000"
        multiprocessing = "False"
        benchmark.group = "single_thread_mysql_read"
        benchmark.name = f"test_{count}"
        # insert data
        self._insert_data("measure_mysql_write.xml", count=count, multiprocessing=multiprocessing)
        # execute benchmark test
        time.sleep(1)  # Warm-up period
        xml_path = self._test_dir.joinpath("measure_mysql_read.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test", "test_mode": True}
        engine = DataMimic(**kwargs)
        benchmark(engine.parse_and_execute)
        # re-check result
        result = engine.capture_test_result()
        products = result["time_measure"]
        assert len(products) == int(count)

    @pytest.mark.run(order=3)
    def test_single_thread_mysql_read_20000(self, benchmark):
        count = "20000"
        multiprocessing = "False"
        benchmark.group = "single_thread_mysql_read"
        benchmark.name = f"test_{count}"
        # insert data
        self._insert_data("measure_mysql_write.xml", count=count, multiprocessing=multiprocessing)
        # execute benchmark test
        time.sleep(1)  # Warm-up period
        xml_path = self._test_dir.joinpath("measure_mysql_read.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test", "test_mode": True}
        engine = DataMimic(**kwargs)
        benchmark(engine.parse_and_execute)
        # re-check result
        result = engine.capture_test_result()
        products = result["time_measure"]
        assert len(products) == int(count)

    @pytest.mark.run(order=4)
    def test_multiprocessing_mysql_read_200(self, benchmark):
        count = "200"
        multiprocessing = "True"
        benchmark.group = "multiprocessing_mysql_read"
        benchmark.name = f"test_{count}"
        # insert data
        self._insert_data("measure_mysql_write.xml", count=count, multiprocessing=multiprocessing)
        # execute benchmark test
        time.sleep(1)  # Warm-up period
        xml_path = self._test_dir.joinpath("measure_mysql_read.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test", "test_mode": True}
        engine = DataMimic(**kwargs)
        benchmark(engine.parse_and_execute)
        # re-check result
        result = engine.capture_test_result()
        products = result["time_measure"]
        assert len(products) == int(count)

    @pytest.mark.run(order=5)
    def test_multiprocessing_mysql_read_2000(self, benchmark):
        count = "2000"
        multiprocessing = "True"
        benchmark.group = "multiprocessing_mysql_read"
        benchmark.name = f"test_{count}"
        # insert data
        self._insert_data("measure_mysql_write.xml", count=count, multiprocessing=multiprocessing)
        # execute benchmark test
        time.sleep(1)  # Warm-up period
        xml_path = self._test_dir.joinpath("measure_mysql_read.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test", "test_mode": True}
        engine = DataMimic(**kwargs)
        benchmark(engine.parse_and_execute)
        # re-check result
        result = engine.capture_test_result()
        products = result["time_measure"]
        assert len(products) == int(count)

    @pytest.mark.run(order=6)
    def test_multiprocessing_mysql_read_20000(self, benchmark):
        count = "20000"
        multiprocessing = "True"
        benchmark.group = "multiprocessing_mysql_read"
        benchmark.name = f"test_{count}"
        # insert data
        self._insert_data("measure_mysql_write.xml", count=count, multiprocessing=multiprocessing)
        # execute benchmark test
        time.sleep(1)  # Warm-up period
        xml_path = self._test_dir.joinpath("measure_mysql_read.xml")
        kwargs = {"descriptor_path": xml_path, "task_id": "test", "test_mode": True}
        engine = DataMimic(**kwargs)
        benchmark(engine.parse_and_execute)
        # re-check result
        result = engine.capture_test_result()
        products = result["time_measure"]
        assert len(products) == int(count)
