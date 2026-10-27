# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Output evidence for RS2: the rest before one roster entry, from the shift windows of the person (see README.md,
Python)."""

import datetime  # the module, as scripts see it: a library name shadows the script global of the same name
from collections.abc import Mapping, Sequence

Row = Mapping[str, object]


def _window(entry: Row, shift_types: Mapping[object, Row]) -> tuple[datetime.datetime, datetime.datetime]:
    shift = shift_types[entry["shift_code"]]
    day = entry["shift_date"]
    start_hour = shift["start_hour"]
    length_hours = shift["length_hours"]
    if not isinstance(day, datetime.date) or not isinstance(start_hour, int) or not isinstance(length_hours, int):
        raise TypeError("a roster entry needs a date and a shift type with integer hours")
    starts_at = datetime.datetime(day.year, day.month, day.day, start_hour)
    return starts_at, starts_at + datetime.timedelta(hours=length_hours)


def rest_hours_before(roster: Sequence[Row], shift_types: Sequence[Row], entry_id: object) -> float | None:
    """RS2: hours between the end of the person's previous shift and the start of this one; negative when they
    overlap; None for the person's first shift."""
    types = {row["shift_code"]: row for row in shift_types}
    entry = next(row for row in roster if row["entry_id"] == entry_id)
    starts_at, _ = _window(entry, types)
    earlier_ends = [
        _window(row, types)[1]
        for row in roster
        if row["staff_id"] == entry["staff_id"] and row["entry_id"] != entry_id and _window(row, types)[0] <= starts_at
    ]
    return (starts_at - max(earlier_ends)).total_seconds() / 3600 if earlier_ends else None
