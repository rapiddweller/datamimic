# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



import time
from pathlib import Path

import psutil
from memory_profiler import memory_usage
from prettytable import PrettyTable

from datamimic_ce.datamimic import DataMimic
from datamimic_ce.logger import logger


class PerformanceTestUtil:

    @staticmethod
    def measure_cpu_usage(xml_file: Path):
        """
        this function get xml file direction and measure cpu usage when generate that xml file
        :return: process CPU usage
        """
        time.sleep(5)  # Warm-up period
        cpu_before = psutil.cpu_percent(interval=None)
        logger.disabled = True
        kwargs = {"descriptor_path": xml_file, "task_id": "test"}
        DataMimic(**kwargs).parse_and_execute()
        logger.disabled = False
        cpu_after = psutil.cpu_percent(interval=None)

        # calculate usage
        cpu_usage = cpu_after - cpu_before
        return cpu_usage

    @staticmethod
    def format_mem_usage(mem_bytes_value):
        if isinstance(mem_bytes_value, str):
            return mem_bytes_value

        if abs(mem_bytes_value) < 1000:
            return str(mem_bytes_value) + " B"
        elif abs(mem_bytes_value) < 1e6:
            return str(round(mem_bytes_value / 1024, 2)) + " KB"
        elif abs(mem_bytes_value) < 1e9:
            return str(round(mem_bytes_value / 1024**2, 2)) + " MB"
        else:
            return str(round(mem_bytes_value / 1024**3, 2)) + " GB"

    @staticmethod
    def modify_value_in_properties(properties_path: str | Path, property_key: str, new_value: str):
        """
        change value in properties file
        :param properties_path: direction of properties file
        :param property_key: name of value want to change e.g. "count", "multiprocessing"
        :param new_value: value want to change
        """
        properties_dict = {}
        # Read the content of the file
        with open(properties_path) as file:
            for line in file:
                # removes trailing whitespace and '\n' chars
                line = line.strip()
                # skips blanks and comments w/o =
                if "=" not in line:
                    continue
                # Skip comments
                if not line.startswith("#"):
                    key, value = line.split("=", 1)
                    properties_dict[key] = value

        # Find and update the line containing property_key
        properties_dict[property_key] = new_value

        # Write the updated content back to the file
        with open(properties_path, "w") as file:
            for key, value in properties_dict.items():
                file.write(f"{key}={value}\n")

    @staticmethod
    def modify_display_measure_result(header_cell: str, results: dict):
        """
        Convenience function for modify measured values.
        Take the result values, add them into prettytable
        :param header_cell: top left cell in a table, define data labels or the units of measurement for data
        :param results: result data after measured;
        format of the results is {"test_group_1":{"test_case_1":value,"test_case_2":value,...},"test_group_2":...}
        """
        # Create a PrettyTable
        table = PrettyTable()

        # Set columns
        columns = [f"{header_cell}"] + list(results.keys())
        table.field_names = columns

        # Add the rows
        tests = set(test for group in results.values() for test in group)
        sorted_tests = list(sorted(tests))
        for test in sorted_tests:
            row = [test]
            for group_key in columns[1:]:
                row.append(results.get(group_key, {}).get(test, "-"))
            table.add_row(row)
        return table

    @staticmethod
    def cpu_measuring_handle(xml_path: Path, rounds: int | None = 1):
        """
        Generate data for xml_path xml and calculate cpu usage of that process
        :param xml_path: direction of test case xml
        :param rounds: number of times you want to run generate function
        :return: average process cpu usage
        """
        test_results = []
        for _i in range(rounds):
            while True:
                process_usage = PerformanceTestUtil.measure_cpu_usage(xml_file=xml_path)
                if process_usage <= 0:
                    continue
                else:
                    test_results.append(process_usage)
                    break
        # calculate average values
        sum_count = 0
        sum_usage = 0
        for result in test_results:
            sum_count += 1
            sum_usage += result
        avg_process_usage = sum_usage / sum_count
        return avg_process_usage

    @staticmethod
    def measure_ram_usage(xml_file: Path):
        """
        this function get xml file direction and measure RAM usage when generate that xml file
        :return: RAM usage of process (in bytes)
        """
        time.sleep(5)  # Warm-up period
        logger.disabled = True
        measure_result = memory_usage(DataMimic(xml_file, "test").parse_and_execute, max_usage=True)
        logger.disabled = False
        mem_usage = measure_result * (1024**2)
        return mem_usage

    @staticmethod
    def ram_measuring_handle(xml_path: Path, rounds: int | None = 1):
        """
        Generate data for xml_path xml and calculate RAM usage of that process
        :param xml_path: direction of test case xml
        :param rounds: number of times you want to run generate function
        :return: average RAM usage (in bytes)
        """
        test_results = []
        for _i in range(rounds):
            iterations = 0  # iterations use to prevent infinite loop
            while True:
                process_usage = PerformanceTestUtil.measure_ram_usage(xml_file=xml_path)
                if process_usage > 0:
                    test_results.append(process_usage)
                    break
                elif process_usage <= 0 and iterations <= 3:
                    iterations += 1
                    continue
                else:
                    test_results.append(0)
                    break

        # calculate average values
        sum_count = 0
        sum_usage = 0
        for result in test_results:
            if result > 0:
                sum_count += 1
                sum_usage += result
        avg_process_usage = sum_usage / sum_count if sum_usage > 0 else 0
        return avg_process_usage
