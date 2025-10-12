# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
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
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="functional_test_datetime.xml", capture_test_result=True
        )
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
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="functional_test_date_epoch.xml", capture_test_result=True
        )
        test_engine.test_with_timer()
        result = test_engine.capture_result()
        date_time_test = result["EpochConversionExample"]
        assert len(date_time_test) == 10
        assert date_time_test[0]["epoch_output1"] == "1612174084"
        assert date_time_test[0]["epoch_milli_output1"] == "1612174084000"
        assert date_time_test[0]["epoch_output2"] == "1612174084"
        assert date_time_test[0]["epoch_milli_output2"] == "1612174084000"

    def test_datetime_precision(self) -> None:
        # Initialize the test engine
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="functional_test_date_milliseconds.xml", capture_test_result=True
        )
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
            assert datetime_with_millis.endswith(".123"), (
                f"Expected milliseconds to be '.123', but got '{datetime_with_millis}'"
            )

            # Validate microseconds precision
            datetime_with_microseconds = entry["datetime_to_microseconds"]
            assert datetime_with_microseconds.endswith(".123456"), (
                f"Expected microseconds to be '.123456', but got '{datetime_with_microseconds}'"
            )

            # Validate nanoseconds precision
            datetime_with_nanoseconds = entry["datetime_to_nanoseconds"]
            assert datetime_with_nanoseconds.endswith(".123456000"), (
                f"Expected nanoseconds to be '.123456000', but got '{datetime_with_nanoseconds}'"
            )

            # Check epoch outputs (seconds, millis, micros, and nanos)
            ref = entry["epoch_reference"]
            expected_epoch_seconds = entry["to_epoch"]
            assert ref == expected_epoch_seconds, f"Expected epoch in seconds: {ref}, but got: {expected_epoch_seconds}"

            ref = f"{entry['epoch_reference']}000"
            expected_epoch_millis = entry["to_epoch_millis"]
            assert ref == expected_epoch_millis, (
                f"Expected epoch in milliseconds: {ref}, but got: {expected_epoch_millis}"
            )

            ref = f"{entry['epoch_reference']}000000"
            expected_epoch_micros = entry["to_epoch_micros"]
            assert ref == expected_epoch_micros, (
                f"Expected epoch in microseconds: {ref}, but got: {expected_epoch_micros}"
            )

            ref = f"{entry['epoch_reference']}000000000"
            expected_epoch_nanos = entry["to_epoch_nanos"]
        assert ref == expected_epoch_nanos, f"Expected epoch in nanoseconds: {ref}, but got: {expected_epoch_nanos}"

    def test_datetime_weighted_functional(self) -> None:
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="functional_test_datetime_weighted.xml",
            capture_test_result=True,
        )
        engine.test_with_timer()

        result = engine.capture_result()
        weighted = result["weighted_datetime_test"]
        assert len(weighted) == 200

        # Verify March-only
        for row in weighted:
            dt = row["march_only"]
            assert 1 <= dt.day <= 31
            assert dt.year == 2024
            assert dt.month == 3

        # Verify Mondays-only (weekday: Monday==0)
        for row in weighted:
            dt = row["mondays_only"]
            assert dt.year == 2024 and dt.month == 1
            assert dt.weekday() == 0

        # Verify 15th only across Jan–Feb 2024
        for row in weighted:
            dt = row["dom_15_only"]
            assert dt.year == 2024
            assert dt.month in (1, 2)
            assert dt.day == 15

        # Combined filters: March + Monday + 4th
        for row in weighted:
            dt = row["combined_filters"]
            assert dt.year == 2024 and dt.month == 3 and dt.day == 4 and dt.weekday() == 0

        # Tight boundary: ensure within exact 6-second window
        from datetime import datetime as _dt

        lo = _dt(2025, 7, 20, 12, 0, 0)
        hi = _dt(2025, 7, 20, 12, 0, 5)
        for row in weighted:
            dt = row["tight_window_weighted"]
            assert lo <= dt <= hi

        # Determinism: equal sequences for det_a and det_b
        for row in weighted:
            assert row["det_a"] == row["det_b"]

    def test_datetime_weighted_invalid(self) -> None:
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="functional_test_datetime_weighted_invalid.xml",
            capture_test_result=False,
        )
        with pytest.raises(ValueError):
            engine.test_with_timer()

    def test_datetime_weighted_sugar(self) -> None:
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="functional_test_datetime_sugar.xml",
            capture_test_result=True,
        )
        engine.test_with_timer()
        result = engine.capture_result()
        rows = result["weighted_datetime_sugar"]
        assert len(rows) == 250

        # uniform: just ensure within range
        from datetime import datetime as _dt
        lo2024 = _dt(2024, 1, 1, 0, 0, 0)
        hi2024 = _dt(2024, 12, 31, 23, 59, 59)
        for r in rows:
            d = r["uniform"]
            assert lo2024 <= d <= hi2024

        # biz_days: Mon-Fri only
        for r in rows:
            d = r["biz_days"]
            assert 0 <= d.weekday() <= 4

        # weekends: Sat/Sun only
        for r in rows:
            d = r["weekends"]
            assert d.weekday() in (5, 6)

        # months_include: only Mar, Jul, Aug, Sep
        allowed = {3, 7, 8, 9}
        for r in rows:
            d = r["months_include"]
            assert d.month in allowed

        # months_exclude: never Feb or Apr
        forbidden = {2, 4}
        for r in rows:
            d = r["months_exclude"]
            assert d.month not in forbidden

        # months_q1: only Jan, Feb, Mar
        for r in rows:
            d = r["months_q1"]
            assert d.month in {1, 2, 3}

        # months_q2_q4: only Apr-Jun or Oct-Dec
        for r in rows:
            d = r["months_q2_q4"]
            assert d.month in {4, 5, 6, 10, 11, 12}

        # dom_last: last day of month
        import calendar as _cal
        for r in rows:
            d = r["dom_last"]
            last = _cal.monthrange(d.year, d.month)[1]
            assert d.day == last

        # dom_multi: days 1-5, 15, 31 only (but 31 may not exist in some months)
        allowed_dom = set(range(1, 6)) | {15, 31}
        for r in rows:
            d = r["dom_multi"]
            assert d.day in allowed_dom and d.day <= _cal.monthrange(d.year, d.month)[1]

        # hours_office_gran15_10: hours 9..17 should dominate, minutes multiples of 15, seconds multiples of 10
        office_hours_count = 0
        for r in rows:
            d = r["hours_office_gran15_10"]
            if 9 <= d.hour <= 17:
                office_hours_count += 1
            assert d.minute in (0, 15, 30, 45)
            assert d.second in (0, 10, 20, 30, 40, 50)
        # not strict, but majority in office hours
        assert office_hours_count > len(rows) * 0.5

        # plain determinism: equal sequences for plain_det_a and plain_det_b
        for r in rows:
            assert r["plain_det_a"] == r["plain_det_b"]
