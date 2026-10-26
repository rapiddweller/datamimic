# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Per-row rule evidence for the shift roster, used by suitability and by output validation.

These are lookups over a whole table for the current record. A script comprehension cannot do them: it does not
see the fields of the current record (see README.md, Python).
"""

import datetime  # the module, as scripts see it: a library name shadows the script global of the same name
from collections.abc import Mapping, Sequence

Row = Mapping[str, object]


def _holding_status(holding: Row, day: datetime.date) -> str:
    issued_on = holding["issued_on"]
    expires_on = holding["expires_on"]
    if not isinstance(issued_on, datetime.date):
        return "not_yet_issued"
    if not isinstance(expires_on, datetime.date):
        return "no_expiry_date"  # a missing expiry date is not unlimited validity
    return "valid" if day <= expires_on else "expired"  # the expiry date itself is still valid


def certificate_status(holdings: Sequence[Row], staff_id: str, cert_code: str, day: datetime.date) -> str:
    """RS1: the status of the person's certification on ``day``; one valid holding is enough."""
    statuses = [
        _holding_status(holding, day)
        for holding in holdings
        if holding["staff_id"] == staff_id and holding["cert_code"] == cert_code
    ]
    if "valid" in statuses:
        return "valid"
    return statuses[0] if statuses else "missing"


def valid_certificates(holdings: Sequence[Row], staff_id: str, day: datetime.date) -> list[str]:
    """RS1 and RS4: the certification codes the person holds validly on ``day``."""
    codes = sorted({str(holding["cert_code"]) for holding in holdings if holding["staff_id"] == staff_id})
    return [code for code in codes if certificate_status(holdings, staff_id, code, day) == "valid"]


def on_approved_leave(leave: Sequence[Row], staff_id: str, day: datetime.date) -> bool:
    """RS6: an approved leave covers ``day``; a requested leave does not."""
    return any(
        row["staff_id"] == staff_id and row["status"] == "approved" and row["first_day"] <= day <= row["last_day"]
        for row in leave
    )


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


def busiest_week_hours(roster: Sequence[Row], shift_types: Sequence[Row], staff_id: str) -> int:
    """RS3: the person's hours in the ISO week with the most hours."""
    lengths = {row["shift_code"]: row["length_hours"] for row in shift_types}
    weeks: dict[int, int] = {}
    for row in roster:
        day = row["shift_date"]
        length = lengths[row["shift_code"]]
        if row["staff_id"] == staff_id and isinstance(day, datetime.date) and isinstance(length, int):
            week = day.isocalendar().week
            weeks[week] = weeks.get(week, 0) + length
    return max(weeks.values(), default=0)


def wards_on_day(roster: Sequence[Row], staff_id: str, day: datetime.date) -> int:
    """RS5: the number of wards the person works in on ``day``."""
    return len({row["ward_id"] for row in roster if row["staff_id"] == staff_id and row["shift_date"] == day})


def lead_holders(
    roster: Sequence[Row], holdings: Sequence[Row], slot_id: str, lead_cert: str, day: datetime.date
) -> int:
    """RS4: the number of staff in the slot who hold the lead certification validly on ``day``."""
    return sum(
        certificate_status(holdings, str(row["staff_id"]), lead_cert, day) == "valid"
        for row in roster
        if row["slot_id"] == slot_id
    )
