# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



import json
import subprocess
from pathlib import Path

from prettytable import PrettyTable


class TestMeasureTimeSummary:
    _test_dir = Path(__file__).resolve().parent

    def exec_time_measure(self, test_uri: list[str], save_uri: str):
        """
        execute command to measure process time with benchmark,
        save result in save_uri then display it
        """
        # Define the command, create folder to store result
        create_folder_command = ["mkdir", "-p", Path(save_uri).parent]
        subprocess.run(create_folder_command)
        # Define the command, save benchmark result to save_uri
        command = ["poetry", "run", "pytest",
                   "--benchmark-sort=name",
                   "--benchmark-columns=min,max,mean,rounds",
                   f"--benchmark-json={save_uri}"]
        command.extend(test_uri)
        # Run the command
        subprocess.run(command)
        return self._modify_display_measure_result(save_uri)

    @staticmethod
    def _modify_display_measure_result(save_uri: str):
        """
        use prettytable to modify display of benchmark result
        """
        # Load JSON data from file
        with open(save_uri) as file:
            data = json.load(file)

        # Extract group names dynamically from the benchmarks
        group_names = set()
        for benchmark in data["benchmarks"]:
            group_names.add(benchmark["group"])

        # Determine the time unit based on the first benchmark's mean value
        time_unit = "s"
        for benchmark in data["benchmarks"]:
            if "stats" in benchmark and "mean" in benchmark["stats"]:
                first_mean_value = benchmark["stats"]["mean"]
                if abs(first_mean_value) < 1:
                    time_unit = "ms"
                break  # Exit the loop once a valid mean value is found

        # Create a dictionary to store values for each benchmark name
        consolidated_data = {}
        for benchmark in data["benchmarks"]:
            name = benchmark["name"]

            # Check if the group does not have a corresponding test or the value is negative
            if name not in consolidated_data:
                consolidated_data[name] = {group: "" for group in group_names}

            # get mean value
            mean_value = benchmark["stats"]["mean"] if "stats" in benchmark and "mean" in benchmark[
                "stats"] else None

            if mean_value is not None and mean_value >= 0:
                # Convert mean value to milliseconds if time_unit is "ms"
                mean_value = round(mean_value * 1000, 4) if time_unit == "ms" else round(mean_value, 4)
                consolidated_data[name][benchmark["group"]] = f"{mean_value:,.4f}"
            else:
                consolidated_data[name][benchmark["group"]] = "undefined"

        # Create a PrettyTable
        table = PrettyTable()

        # check empty
        if not group_names or not consolidated_data:
            return table

        # Define columns with time unit
        table.field_names = [f"Avg time ({time_unit})", *list(sorted(group_names))]

        #  sort consolidated_data
        sorted_consolidated_data = dict(sorted(consolidated_data.items(), key=lambda item: item[0]))

        # Populate the table with consolidated data
        for name, values in sorted_consolidated_data.items():
            row_values = [name] + [values[group] if values[group] != "undefined" else "undefined" for group in
                                   sorted(group_names)]
            table.add_row(row_values)

        return table

    def test_measure_simple_case_without_source(self):
        test_uri = [f"{self._test_dir}/simple_generate_without_source/"]
        save_uri = "test-artifacts/performance-reports/report_time_simple_case_without_source.json"
        table = self.exec_time_measure(test_uri, save_uri)
        print("Measure Time Simple Generate Without Source Summary:")
        print(table)
        print("\n")

    def test_measure_simple_case_with_source(self):
        test_uri = [f"{self._test_dir}/simple_generate_with_source/"]
        save_uri = "test-artifacts/performance-reports/report_time_simple_case_with_source.json"
        table = self.exec_time_measure(test_uri, save_uri)
        print("Measure Time Simple Generate With Source Summary:")
        print(table)
        print("\n")

    def test_measure_mongodb_write(self):
        test_uri = [f"{self._test_dir}/mongodb_generate/test_time_mongodb_write.py"]
        save_uri = "test-artifacts/performance-reports/report_time_mongodb_database.json"
        table = self.exec_time_measure(test_uri, save_uri)
        print("Measure Time MongoDB Summary:")
        print(table)
        print("\n")

    def test_measure_mongodb_read(self):
        test_uri = [f"{self._test_dir}/mongodb_generate/test_time_mongodb_read.py"]
        save_uri = "test-artifacts/performance-reports/report_time_mongodb_database.json"
        table = self.exec_time_measure(test_uri, save_uri)
        print("Measure Time MongoDB Summary:")
        print(table)
        print("\n")

    def test_measure_mysql_write(self):
        test_uri = [f"{self._test_dir}/mysql_generate/test_time_mysql_write.py"]
        save_uri = "test-artifacts/performance-reports/report_time_mysql_database.json"
        table = self.exec_time_measure(test_uri, save_uri)
        print("Measure Time MySQL Summary:")
        print(table)
        print("\n")

    def test_measure_mysql_read(self):
        test_uri = [f"{self._test_dir}/mysql_generate/test_time_mysql_read.py"]
        save_uri = "test-artifacts/performance-reports/report_time_mysql_database.json"
        table = self.exec_time_measure(test_uri, save_uri)
        print("Measure Time MySQL Summary:")
        print(table)
        print("\n")

    def test_measure_mssql_write(self):
        test_uri = [f"{self._test_dir}/mssql_generate/test_time_mssql_write.py"]
        save_uri = "test-artifacts/performance-reports/report_time_mssql_database.json"
        table = self.exec_time_measure(test_uri, save_uri)
        print("Measure Time MsSQL Summary:")
        print(table)
        print("\n")

    def test_measure_mssql_read(self):
        test_uri = [f"{self._test_dir}/mssql_generate/test_time_mssql_read.py"]
        save_uri = "test-artifacts/performance-reports/report_time_mssql_database.json"
        table = self.exec_time_measure(test_uri, save_uri)
        print("Measure Time MsSQL Summary:")
        print(table)
        print("\n")

    def test_measure_postgresql_write(self):
        test_uri = [f"{self._test_dir}/postgresql_generate/test_time_postgresql_write.py"]
        save_uri = "test-artifacts/performance-reports/report_time_postgresql_database.json"
        table = self.exec_time_measure(test_uri, save_uri)
        print("Measure Time Postgresql Summary:")
        print(table)
        print("\n")

    def test_measure_postgresql_read(self):
        test_uri = [f"{self._test_dir}/postgresql_generate/test_time_postgresql_read.py"]
        save_uri = "test-artifacts/performance-reports/report_time_postgresql_database.json"
        table = self.exec_time_measure(test_uri, save_uri)
        print("Measure Time Postgresql Summary:")
        print(table)
        print("\n")
