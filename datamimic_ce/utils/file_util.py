# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import csv
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from pandas import DataFrame

from datamimic_ce.utils.file_content_storage import FileContentStorage


class FileUtil:
    @staticmethod
    def parse_properties(path: Path, encoding="utf-8") -> dict[str, str]:
        """
        Parse properties from file then save into a dict
        :param path:
        :param encoding:
        :return:
        """

        try:
            properties_dict = {}
            # Load file content from cache or file
            data = FileContentStorage.load_file_with_custom_func(
                str(path), lambda: [line.strip() for line in path.open("r", encoding=encoding)]
            )
            # Parse properties from file content
            for line in data:
                # Skip comments and empty lines
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    properties_dict[key.strip()] = value.strip()
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Property file not found {str(path)}, please check the file path again. Error message: {e}"
            ) from e

        return properties_dict

    @staticmethod
    def _read_raw_csv(file_path: Path, separator: str, encoding="utf-8") -> list[tuple]:
        """
        Read raw csv data
        """
        try:
            return FileContentStorage.load_file_with_custom_func(
                str(file_path),
                lambda: [
                    tuple(row)
                    for row in csv.reader(file_path.open("r", newline="", encoding=encoding), delimiter=separator)
                ],
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(f"CSV file not found '{file_path}', error: {e}") from e

    @staticmethod
    def read_csv_to_dict_list(file_path: Path, separator: str, encoding="utf-8") -> list[dict]:
        """
        Read data from csv and parse into list of dict
        """
        raw_data = FileUtil._read_raw_csv(file_path, separator, encoding)
        header = raw_data[0]
        processed_data = [dict(zip(header, row, strict=False)) for row in raw_data[1:]]
        return processed_data

    @staticmethod
    def read_weight_csv(file_path: Path, separator: str = ",", encoding="utf-8") -> DataFrame:
        """
        Read none_header, 2_columns, weight csv
        then return as DataFrame
        """
        # Load file content from cache or file
        raw_data = FileUtil._read_raw_csv(file_path, separator, encoding)

        # Convert data to DataFrame, select only 2 columns (data and weight)
        df = pd.DataFrame(raw_data, columns=[0, 1])
        # Convert column 1 to float and replace NaN with 1
        df[1] = df[1].astype(float).fillna(1)
        # Replace NaN df in the first column with None to avoid nan
        df[0] = df[0].replace(to_replace=np.nan, value=None)
        # Calculate probability using count stat
        df[1] = df[1] / df[1].sum()

        return df

    @staticmethod
    def read_json(file_path: Path, encoding="utf-8") -> list[dict] | dict:
        """
        Read data from JSON
        """
        try:
            return FileContentStorage.load_file_with_custom_func(
                str(file_path), lambda: json.load(file_path.open(mode="r", encoding=encoding))
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(f"JSON file not found '{file_path}', error: {e}") from e

    @staticmethod
    def read_json_to_list(file_path: Path, encoding="utf-8") -> list[dict]:
        """
        Read data from JSON and parse into list of dict
        """
        json_data = FileUtil.read_json(file_path, encoding)
        if isinstance(json_data, list):
            return json_data
        else:
            raise ValueError(f"JSON file '{file_path}' must contain a list of objects")

    @staticmethod
    def read_json_to_dict(file_path: Path, encoding="utf-8") -> dict:
        """
        Read data from JSON and parse into dict
        """
        json_data = FileUtil.read_json(file_path, encoding)
        if isinstance(json_data, dict):
            return json_data
        else:
            raise ValueError(f"JSON file '{file_path}' must contain a dictionary")

    @staticmethod
    def read_csv_to_dict_of_tuples_with_header(
        file_path: Path, delimiter: str = ",", encoding="utf-8"
    ) -> tuple[dict, list[tuple]]:
        """
        Read CSV to header dict and data list
        :param delimiter: delimiter used in the CSV file
        :param file_path: path to the CSV file
        :param encoding: encoding of the CSV file
        :return: a tuple containing a dictionary of headers and a list of tuples with string datas
        """
        # Load raw data
        raw_data = FileUtil._read_raw_csv(file_path, delimiter, encoding)
        header = raw_data[0]
        data_rows = raw_data[1:]

        # Create header dict
        header_dict = {}
        for idx, column in enumerate(header):
            modified_column = column.replace("\ufeff", "")
            header_dict[modified_column] = idx

        # Return header dict and data rows
        return header_dict, data_rows

    @staticmethod
    def read_csv_to_list_of_tuples_without_header(
        file_path: Path, delimiter: str = ",", encoding="utf-8"
    ) -> list[tuple]:
        """
        Read CSV without header to data list
        :param file_path: path to the CSV file
        :param delimiter: delimiter used in the CSV file
        :param encoding: encoding of the CSV file
        :return: a list of tuples containing the string data
        """
        return FileUtil._read_raw_csv(file_path, delimiter, encoding)

    @staticmethod
    def read_wgt_file(file_path: Path, delimiter: str = ",", encoding="utf-8") -> tuple[list, list]:
        """
        Read wgt file having no header and 2 columns (wgt is 2nd column)
        :param file_path:
        :param delimiter:
        :param encoding: encoding of the CSV file
        :return: Tuple contain list of values and list of weights
        """
        values = []
        weights = []

        # Load raw data
        raw_data = FileUtil._read_raw_csv(file_path, delimiter, encoding)

        # Process data
        for row in raw_data:
            values.append(row[0])
            if len(row) == 2:
                weights.append(float(row[1]))
            elif len(row) == 1:
                # Assume weight as 1 if missing
                weights.append(1.0)
            else:
                raise ValueError(f"Not a valid wgt file {str(file_path)}")

        # Normalize weights
        weights_sum = sum(weights)
        weights = [weight / weights_sum for weight in weights]

        return values, weights

    @staticmethod
    def read_csv_having_weight_column(filepath: Path, weight_column_name: str, delimiter: str = ",", encoding="utf-8"):
        """
        Read CSV file having one weight column
        :param filepath:
        :param weight_column_name:
        :param delimiter:
        :param encoding:
        :return:
        """
        weights = []  # List to store weights
        data_without_weights = []  # List to store dictionaries of data without the specified weight column

        # Load raw data
        list_of_dict_data = FileUtil.read_csv_to_dict_list(filepath, delimiter, encoding)

        # Process data
        for row in list_of_dict_data:
            # Extract and remove the specified weight column from the row
            weight = row.pop(weight_column_name, None)
            if weight is not None:
                # Convert weight to the appropriate type (float, int) if necessary
                weights.append(float(weight))
                # Add the modified row (now without the weight) to the data_without_weights list
                data_without_weights.append(row)

        # Return the tuple of weights list and data_without_weights list
        return (weights, data_without_weights)

    @staticmethod
    def read_mutil_column_wgt_file(
        file_path: Path,
        weight_col_index: int = 1,
        delimiter: str = ",",
        encoding="utf-8",
    ) -> tuple[list, list]:
        """
        Read wgt file having no header and mutil columns,
        if weight column missing or wrong index then weight value will be 1.0
        :param file_path:
        :param weight_col_index: index of weight column (default = 1)
        :param delimiter:
        :param encoding:
        :return: Tuple contain list of values and list of weights
        """
        weights = []  # List to store weights
        values = []  # List to store data

        # Load raw data
        raw_data = FileUtil._read_raw_csv(file_path, delimiter, encoding)

        for row in raw_data:
            # Skip the empty row
            if not row:
                continue
            # default weight 1.0 when weight column is missing or wrong index
            if weight_col_index < 0 or weight_col_index >= len(row):
                weights.append(1.0)
            else:
                weight = row[weight_col_index]
                weights.append(float(weight) if weight else 1.0)

            values.append(row)
        # Return the tuple of values list and weights list
        return values, weights

    @staticmethod
    def copy_file(source: Path, destination: Path) -> None:
        """
        Copy a file from source to destination.

        Args:
            source (Path): Source file path
            destination (Path): Destination file path
        """
        shutil.copy2(source, destination)

    @staticmethod
    def create_project_structure(project_dir: Path) -> None:
        """
        Create the initial project structure with necessary files and directories.

        Args:
            project_dir (Path): Target project directory
        """

        initial_descriptor_content = """
<setup>
    <generate name="datamimic_user_list" count="1000" target="CSV,JSON">
        <variable name="person" entity="Person(min_age=18, max_age=90, female_quota=0.5)"/>
        <key name="id" generator="IncrementGenerator"/>
        <key name="given_name" script="person.given_name"/>
        <key name="family_name" script="person.family_name"/>
        <key name="gender" script="person.gender"/>
        <key name="birthDate" script="person.birthdate" converter="DateFormat('%d.%m.%Y')"/>
        <key name="email" script="person.family_name + '@' + person.given_name + '.de'"/>
        <key name="ce_user" values="True, False"/>
        <key name="ee_user" values="True, False"/>
        <key name="datamimic_lover" constant="DEFINITELY"/>
    </generate>
</setup>
        """

        # Create basic directory structure
        (project_dir / "data").mkdir(exist_ok=True)
        (project_dir / "output").mkdir(exist_ok=True)
        (project_dir / "script").mkdir(exist_ok=True)
        (project_dir / "config").mkdir(exist_ok=True)

        # Create the descriptor file with the specified content
        descriptor_path = project_dir / "datamimic.xml"
        descriptor_path.write_text(initial_descriptor_content)

        # Create a default README.md
        readme_content = f"""
# DATAMIMIC Project: {project_dir.name}
This project was created using DATAMIMIC.

## Project Structure
- `data/`: Directory for input data files, like .ent.csv or .wgt.csv
- `script/`: Directory for input scripts or custom functions
- `output/`: Directory for generated output
- `config/`: Configuration files
- `datamimic.xml`: Main project descriptor file

## Initial Setup
The project is initialized with a sample descriptor that generates user data with the following fields:
- User ID (auto-incrementing)
- First Name
- Last Name
- Gender
- Birth Date
- Email
- CE User status
- EE User status
- DATAMIMIC Lover status

## Getting Started
1. Review and modify the `datamimic.xml` file to customize your data generation
2. Place any required input files in the `data/` directory
3. Run the project using: `datamimic run datamimic.xml`
        """
        (project_dir / "README.md").write_text(readme_content)
