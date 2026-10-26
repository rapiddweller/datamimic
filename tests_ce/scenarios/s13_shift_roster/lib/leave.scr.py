# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""RS6: approved leave on one day, used by suitability and by output validation."""

import datetime  # the module, as scripts see it: a library name shadows the script global of the same name
from collections.abc import Mapping, Sequence


def on_approved_leave(leave: Sequence[Mapping[str, object]], staff_id: str, day: datetime.date) -> bool:
    """An approved leave covers ``day``, its first and last day included; a requested leave does not."""
    return any(
        row["staff_id"] == staff_id and row["status"] == "approved" and row["first_day"] <= day <= row["last_day"]
        for row in leave
    )
