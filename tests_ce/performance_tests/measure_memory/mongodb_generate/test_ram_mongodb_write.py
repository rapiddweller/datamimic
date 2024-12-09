# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from pathlib import Path

import pytest

from tests_ce.performance_tests.performance_test_util import PerformanceTestUtil


class TestRAMMongoDBWrite:
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
        table = PerformanceTestUtil.modify_display_measure_result(header_cell="Avg RAM usage",
                                                                  results=results)
        print("\nRAM Usage Summary for MongoDB Write Data:")
        print(table)

        # Teardown code, change back properties file to default value
        default_count = "100"
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

    @pytest.mark.run(order=1)
    def test_single_thread_mongodb_write_100(self, class_fixture):
        count = "100"
        multiprocessing = "False"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        test_group = "single_thread_mongodb_write"
        test_case = f"test_{count}"
        rounds = 3

        xml_path = self._test_dir.joinpath("ram_measure_mongodb_write.xml")
        avg_process_usage = PerformanceTestUtil.ram_measuring_handle(xml_path=xml_path, rounds=rounds)
        # add result to class_fixture results variable for late use in summary table
        results = class_fixture
        test_result = PerformanceTestUtil.format_mem_usage(avg_process_usage)

        self._add_test_values_to_class_fixture(class_fixture_results=results,
                                               test_group=test_group,
                                               test_case=test_case,
                                               value=test_result)

    @pytest.mark.run(order=2)
    def test_single_thread_mongodb_write_1000(self, class_fixture) -> None:
        count = "1000"
        multiprocessing = "False"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        test_group = "single_thread_mongodb_write"
        test_case = f"test_{count}"
        rounds = 3

        xml_path = self._test_dir.joinpath("ram_measure_mongodb_write.xml")
        avg_process_usage = PerformanceTestUtil.ram_measuring_handle(xml_path=xml_path, rounds=rounds)
        # add result to class_fixture results variable for late use in summary table
        results = class_fixture
        test_result = PerformanceTestUtil.format_mem_usage(avg_process_usage)

        self._add_test_values_to_class_fixture(class_fixture_results=results,
                                               test_group=test_group,
                                               test_case=test_case,
                                               value=test_result)

    @pytest.mark.run(order=3)
    def test_single_thread_mongodb_write_10000(self, class_fixture) -> None:
        count = "10000"
        multiprocessing = "False"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        test_group = "single_thread_mongodb_write"
        test_case = f"test_{count}"
        rounds = 3

        xml_path = self._test_dir.joinpath("ram_measure_mongodb_write.xml")
        avg_process_usage = PerformanceTestUtil.ram_measuring_handle(xml_path=xml_path, rounds=rounds)
        # add result to class_fixture results variable for late use in summary table
        results = class_fixture
        test_result = PerformanceTestUtil.format_mem_usage(avg_process_usage)

        self._add_test_values_to_class_fixture(class_fixture_results=results,
                                               test_group=test_group,
                                               test_case=test_case,
                                               value=test_result)

    @pytest.mark.run(order=4)
    def test_multiprocessing_mongodb_write_100(self, class_fixture) -> None:
        count = "100"
        multiprocessing = "True"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        test_group = "multiprocessing_mongodb_write"
        test_case = f"test_{count}"
        rounds = 3

        xml_path = self._test_dir.joinpath("ram_measure_mongodb_write.xml")
        avg_process_usage = PerformanceTestUtil.ram_measuring_handle(xml_path=xml_path, rounds=rounds)
        # add result to class_fixture results variable for late use in summary table
        results = class_fixture
        test_result = PerformanceTestUtil.format_mem_usage(avg_process_usage)

        self._add_test_values_to_class_fixture(class_fixture_results=results,
                                               test_group=test_group,
                                               test_case=test_case,
                                               value=test_result)

    @pytest.mark.run(order=5)
    def test_multiprocessing_mongodb_write_1000(self, class_fixture) -> None:
        count = "1000"
        multiprocessing = "True"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        test_group = "multiprocessing_mongodb_write"
        test_case = f"test_{count}"
        rounds = 3

        xml_path = self._test_dir.joinpath("ram_measure_mongodb_write.xml")
        avg_process_usage = PerformanceTestUtil.ram_measuring_handle(xml_path=xml_path, rounds=rounds)
        # add result to class_fixture results variable for late use in summary table
        results = class_fixture
        test_result = PerformanceTestUtil.format_mem_usage(avg_process_usage)

        self._add_test_values_to_class_fixture(class_fixture_results=results,
                                               test_group=test_group,
                                               test_case=test_case,
                                               value=test_result)

    @pytest.mark.run(order=6)
    def test_multiprocessing_mongodb_write_10000(self, class_fixture) -> None:
        count = "10000"
        multiprocessing = "True"
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "count", count)
        PerformanceTestUtil.modify_value_in_properties(self._base_path, "multiprocessing", multiprocessing)

        test_group = "multiprocessing_mongodb_write"
        test_case = f"test_{count}"
        rounds = 3

        xml_path = self._test_dir.joinpath("ram_measure_mongodb_write.xml")
        avg_process_usage = PerformanceTestUtil.ram_measuring_handle(xml_path=xml_path, rounds=rounds)
        # add result to class_fixture results variable for late use in summary table
        results = class_fixture
        test_result = PerformanceTestUtil.format_mem_usage(avg_process_usage)

        self._add_test_values_to_class_fixture(class_fixture_results=results,
                                               test_group=test_group,
                                               test_case=test_case,
                                               value=test_result)
