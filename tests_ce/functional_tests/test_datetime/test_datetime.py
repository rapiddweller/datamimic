# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



from datetime import datetime
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest


class TestDateTime:
    _test_dir = Path(__file__).resolve().parent

    def test_datetime_functional(self) -> None:
        engine = DataMimicTest(test_dir=self._test_dir, filename="functional_test_datetime.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        date_time_test = result["date_time_test"]

        assert len(date_time_test) == 50
        for data in date_time_test:
            assert isinstance(data["date_time_constant"], str)
            assert data["date_time_constant"] == "2020-02-01"
            assert isinstance(data["date_time_with_in"], datetime)
            assert data["date_time_with_in"] == datetime(year=2021, month=2, day=1)
            assert isinstance(data["date_time_with_in_out"], str)
            assert data["date_time_with_in_out"] == "01.02.2022"
            assert isinstance(data["date_time_with_out"], str)
            assert data["date_time_with_out"] == datetime.now().strftime("%d.%m.%Y")

    def test_datetime_invalid_in_date_format(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="functional_test_date_invalid_in_format.xml")
        # Use pytest.raises to capture the expected error
        with pytest.raises(ValueError):
            test_engine.test_with_timer()

    def test_datetime_empty_in_date_format(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="functional_test_date_empty_in_format.xml")
        # Use pytest.raises to capture the expected error
        with pytest.raises(ValueError):
            test_engine.test_with_timer()

    def test_datetime_empty_out_date_format(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="functional_test_date_empty_out_format.xml")
        # Use pytest.raises to capture the expected error
        with pytest.raises(ValueError):
            test_engine.test_with_timer()

    def test_datetime_invalid_input1(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="functional_test_date_invalid_input_1.xml")
        # Use pytest.raises to capture the expected error
        with pytest.raises(ValueError):
            test_engine.test_with_timer()

    def test_datetime_invalid_input2(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="functional_test_date_invalid_input_2.xml")
        # Use pytest.raises to capture the expected error
        with pytest.raises(ValueError):
            test_engine.test_with_timer()

    def test_datetime_epoch(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="functional_test_date_epoch.xml", capture_test_result=True)
        test_engine.test_with_timer()
        result = test_engine.capture_result()
        date_time_test = result["EpochConversionExample"]
        assert len(date_time_test) == 10
        assert date_time_test[0]["epoch_output1"] == '1612174084'
        assert date_time_test[0]["epoch_milli_output1"] == '1612174084000'
        assert date_time_test[0]["epoch_output2"] == '1612174084'
        assert date_time_test[0]["epoch_milli_output2"] == '1612174084000'

    def test_datetime_precision(self) -> None:
        # Initialize the test engine
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="functional_test_date_milliseconds.xml",
                                    capture_test_result=True)
        test_engine.test_with_timer()

        # Capture the test result
        result = test_engine.capture_result()

        # Extract the test results for the "PrecisionExample"
        date_time_test = result["PrecisionExample"]

        # Assert that the result contains 10 generated entries
        assert len(date_time_test) == 10, f"Expected 10 results, but got {len(date_time_test)}"

        # Iterate through the results and validate the entries
        for entry in date_time_test:
            # Validate milliseconds precision
            datetime_with_millis = entry["datetime_to_millis"]
            assert isinstance(datetime_with_millis, str), "The datetime with milliseconds should be a string."
            assert datetime_with_millis.endswith(
                '.123'), f"Expected milliseconds to be '.123', but got '{datetime_with_millis}'"

            # Validate microseconds precision
            datetime_with_microseconds = entry["datetime_to_microseconds"]
            assert datetime_with_microseconds.endswith(
                '.123456'), f"Expected microseconds to be '.123456', but got '{datetime_with_microseconds}'"

            # Validate nanoseconds precision
            datetime_with_nanoseconds = entry["datetime_to_nanoseconds"]
            assert datetime_with_nanoseconds.endswith(
                '.123456000'), f"Expected nanoseconds to be '.123456000', but got '{datetime_with_nanoseconds}'"

            # Check epoch outputs (seconds, millis, micros, and nanos)
            ref = entry["epoch_reference"]
            expected_epoch_seconds = entry["to_epoch"]
            assert ref == expected_epoch_seconds, f"Expected epoch in seconds: {ref}, but got: {expected_epoch_seconds}"

            ref = f'{entry["epoch_reference"]}000'
            expected_epoch_millis = entry["to_epoch_millis"]
            assert ref == expected_epoch_millis, f"Expected epoch in milliseconds: {ref}, but got: {expected_epoch_millis}"

            ref = f'{entry["epoch_reference"]}000000'
            expected_epoch_micros = entry["to_epoch_micros"]
            assert ref == expected_epoch_micros, f"Expected epoch in microseconds: {ref}, but got: {expected_epoch_micros}"

            ref = f'{entry["epoch_reference"]}000000000'
            expected_epoch_nanos = entry["to_epoch_nanos"]
            assert ref == expected_epoch_nanos, f"Expected epoch in nanoseconds: {ref}, but got: {expected_epoch_nanos}"