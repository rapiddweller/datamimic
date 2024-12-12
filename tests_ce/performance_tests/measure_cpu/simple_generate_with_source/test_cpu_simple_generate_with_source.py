# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import os
from pathlib import Path

import pytest

from tests_ce.performance_tests.performance_test_util import PerformanceTestUtil


class TestCPUSimpleGenerateWithSource:
    _test_dir = Path(__file__).resolve().parent
    _base_path = _test_dir.joinpath("conf/base.properties")

    @pytest.fixture(scope="class", autouse=True)
    def class_fixture(self):
        """
        set setup variable and breakdown for test class
        """
        results = {}

        yield results

        # modify result summary and print it
        table = PerformanceTestUtil.modify_display_measure_result(header_cell="Avg CPU usage(%)", results=results)
        print("\nCPU Usage Summary for Simple Generation with Source:")
        print(f"Number of CPU cores: {os.cpu_count()}")
        print(table)

        # Teardown code
        default_count = "1000"
        default_multiprocessing = "False"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", default_count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", default_multiprocessing)

    @staticmethod
    def _add_test_values_to_class_fixture(class_fixture_results: dict, test_group: str, test_case: str, value):
        """
        convenience function help add value to summary result, avoid duplicate code
        :param class_fixture_results: results variable of class_fixture is put into test case
        :param test_group: name of group test, will be used as name of column at summary table
        :param test_case: name of test case, will be used as name row at summary table
        :param value: measuring result value
        """
        if class_fixture_results.get(f"{test_group}"):
            class_fixture_results[f"{test_group}"][f"{test_case}"] = value
        else:
            class_fixture_results[f"{test_group}"] = {}
            class_fixture_results[f"{test_group}"][f"{test_case}"] = value

    def test_cpu_single_thread_with_source_1000(self, class_fixture):
        count = "1000"
        multiprocessing = "False"
        test_group = "single_thread_with_source"
        test_case = f"test_{count}"
        rounds = 5

        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)
        xml_path = self._test_dir.joinpath("cpu_measure_simple_generate_with_source.xml")

        avg_process_usage = PerformanceTestUtil.cpu_measuring_handle(xml_path=xml_path, rounds=rounds)
        # add result to class_fixture results variable for late use in summary table
        results = class_fixture
        test_result = f"{avg_process_usage:.2f}%"

        self._add_test_values_to_class_fixture(
            class_fixture_results=results, test_group=test_group, test_case=test_case, value=test_result
        )

    def test_cpu_single_thread_with_source_10000(self, class_fixture):
        count = "10000"
        multiprocessing = "False"
        test_group = "single_thread_with_source"
        test_case = f"test_{count}"
        rounds = 5
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)
        xml_path = self._test_dir.joinpath("cpu_measure_simple_generate_with_source.xml")

        avg_process_usage = PerformanceTestUtil.cpu_measuring_handle(xml_path=xml_path, rounds=rounds)
        # add result to class_fixture results variable for late use in summary table
        results = class_fixture
        test_result = f"{avg_process_usage:.2f}%"

        self._add_test_values_to_class_fixture(
            class_fixture_results=results, test_group=test_group, test_case=test_case, value=test_result
        )

    def test_cpu_single_thread_with_source_100000(self, class_fixture):
        count = "100000"
        multiprocessing = "False"
        test_group = "single_thread_with_source"
        test_case = f"test_{count}"
        rounds = 5

        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)
        xml_path = self._test_dir.joinpath("cpu_measure_simple_generate_with_source.xml")

        avg_process_usage = PerformanceTestUtil.cpu_measuring_handle(xml_path=xml_path, rounds=rounds)
        # add result to class_fixture results variable for late use in summary table
        results = class_fixture
        test_result = f"{avg_process_usage:.2f}%"

        self._add_test_values_to_class_fixture(
            class_fixture_results=results, test_group=test_group, test_case=test_case, value=test_result
        )

    def test_cpu_multiprocessing_with_source_1000(self, class_fixture):
        count = "1000"
        multiprocessing = "True"
        test_group = "multiprocessing_with_source"
        test_case = f"test_{count}"
        rounds = 5

        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)
        xml_path = self._test_dir.joinpath("cpu_measure_simple_generate_with_source.xml")

        avg_process_usage = PerformanceTestUtil.cpu_measuring_handle(xml_path=xml_path, rounds=rounds)
        # add result to class_fixture results variable for late use in summary table
        results = class_fixture
        test_result = f"{avg_process_usage:.2f}%"

        self._add_test_values_to_class_fixture(
            class_fixture_results=results, test_group=test_group, test_case=test_case, value=test_result
        )

    def test_cpu_multiprocessing_with_source_10000(self, class_fixture):
        count = "10000"
        multiprocessing = "True"
        test_group = "multiprocessing_with_source"
        test_case = f"test_{count}"
        rounds = 5

        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)
        xml_path = self._test_dir.joinpath("cpu_measure_simple_generate_with_source.xml")

        avg_process_usage = PerformanceTestUtil.cpu_measuring_handle(xml_path=xml_path, rounds=rounds)
        # add result to class_fixture results variable for late use in summary table
        results = class_fixture
        test_result = f"{avg_process_usage:.2f}%"

        self._add_test_values_to_class_fixture(
            class_fixture_results=results, test_group=test_group, test_case=test_case, value=test_result
        )

    def test_cpu_multiprocessing_with_source_100000(self, class_fixture):
        count = "100000"
        multiprocessing = "True"
        test_group = "multiprocessing_with_source"
        test_case = f"test_{count}"
        rounds = 5

        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)
        xml_path = self._test_dir.joinpath("cpu_measure_simple_generate_with_source.xml")

        avg_process_usage = PerformanceTestUtil.cpu_measuring_handle(xml_path=xml_path, rounds=rounds)
        # add result to class_fixture results variable for late use in summary table
        results = class_fixture
        test_result = f"{avg_process_usage:.2f}%"

        self._add_test_values_to_class_fixture(
            class_fixture_results=results, test_group=test_group, test_case=test_case, value=test_result
        )
