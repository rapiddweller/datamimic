# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A naive date or datetime compares with an ISO text literal in a row condition (#690)."""

from datetime import UTC, date, datetime

import pytest

from datamimic_ce.authoring.domain.row_conditions import (
    RowConditionError,
    RowConditionFailure,
    evaluate_row_condition,
    parse_temporal_literal,
)

WINDOW = "{f} > '1936-11-22' and {f} < '2008-11-23'"


@pytest.mark.parametrize(
    ("value", "holds"),
    [
        (date(1936, 11, 22), False),  # min - 1 day
        (date(1936, 11, 23), True),  # min
        (date(2000, 6, 15), True),  # inside
        (date(2008, 11, 22), True),  # max
        (date(2008, 11, 23), False),  # max + 1 day
        (datetime(1936, 11, 22, 0, 0, 0), False),  # a date literal is midnight: the strict bound excludes it
        (datetime(1936, 11, 22, 0, 0, 1), True),
        (datetime(2000, 6, 15, 13, 45, 10), True),
        (datetime(2008, 11, 22, 23, 59, 59, 999999), True),
        (datetime(2008, 11, 23, 0, 0, 0), False),
    ],
)
def test_window_over_a_date_or_datetime(value, holds):
    assert evaluate_row_condition(WINDOW.format(f="born"), {"born": value}) is holds


@pytest.mark.parametrize(
    ("condition", "holds"),
    [
        ("at == '2000-06-15 13:45:10'", True),
        ("at == '2000-06-15T13:45:10.000000'", True),
        ("at != '2000-06-15T13:45:10'", False),
        ("at >= '2000-06-15T13:45:10' and at <= '2000-06-15T13:45:10'", True),
        ("at == '2000-06-15'", False),
        ("'2000-06-15' < at < '2000-06-16'", True),
    ],
)
def test_datetime_literals_and_literal_on_the_left(condition, holds):
    assert evaluate_row_condition(condition, {"at": datetime(2000, 6, 15, 13, 45, 10)}) is holds


def test_two_date_fields_compare_and_a_text_field_stays_text():
    assert evaluate_row_condition("start < end", {"start": date(2000, 1, 1), "end": date(2000, 1, 2)})
    assert evaluate_row_condition("note > '2000-01-01'", {"note": "2000-06-15"})


@pytest.mark.parametrize(
    ("condition", "row", "failure"),
    [
        ("d > '15.06.2000'", {"d": date(2000, 6, 15)}, RowConditionFailure.TEMPORAL_LITERAL),
        ("d > '2000-6-15'", {"d": date(2000, 6, 15)}, RowConditionFailure.TEMPORAL_LITERAL),
        ("d > '2000-13-45'", {"d": date(2000, 6, 15)}, RowConditionFailure.TEMPORAL_LITERAL),
        ("d > '2000-06-15T00:00:00Z'", {"d": datetime(2000, 6, 15)}, RowConditionFailure.TEMPORAL_LITERAL),
        ("d > '2000-06-15T00:00:00+02:00'", {"d": datetime(2000, 6, 15)}, RowConditionFailure.TEMPORAL_LITERAL),
        ("d > '2000-06-15 00:00:00'", {"d": date(2000, 6, 15)}, RowConditionFailure.TEMPORAL_LITERAL),
        ("d > '2000-06-15'", {"d": datetime(2000, 6, 15, tzinfo=UTC)}, RowConditionFailure.UNSUPPORTED_VALUE),
        ("d < at", {"d": date(2000, 6, 15), "at": datetime(2000, 6, 15)}, RowConditionFailure.TYPE_MISMATCH),
        ("d == at", {"d": date(2000, 6, 15), "at": datetime(2000, 6, 15)}, RowConditionFailure.TYPE_MISMATCH),
        ("d in ('2000-06-15',)", {"d": date(2000, 6, 15)}, RowConditionFailure.TYPE_MISMATCH),
        ("'2000-06-15' in days", {"days": [date(2000, 6, 15)]}, RowConditionFailure.TYPE_MISMATCH),
        ("d > 5", {"d": date(2000, 6, 15)}, RowConditionFailure.TYPE_MISMATCH),
        ("d > '2000-06-15'", {}, RowConditionFailure.MISSING_VALUE),
    ],
)
def test_everything_else_is_refused_with_a_reason(condition, row, failure):
    with pytest.raises(RowConditionError) as error:
        evaluate_row_condition(condition, row)
    assert error.value.failure is failure


def test_a_date_in_a_nested_mapping_compares():
    assert evaluate_row_condition("person.born < '2000-01-01'", {"person": {"id": 1, "born": date(1999, 12, 31)}})


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2000-06-15", date(2000, 6, 15)),
        ("2000-06-15 13:45:10", datetime(2000, 6, 15, 13, 45, 10)),
        ("2000-06-15T13:45:10.5", datetime(2000, 6, 15, 13, 45, 10, 500000)),
        ("2000-06-15T13:45:10Z", None),
        ("2000-06-15T13:45", None),
        ("20000615", None),
        ("2000-02-30", None),
    ],
)
def test_the_iso_literal_rule(text, expected):
    assert parse_temporal_literal(text) == expected
