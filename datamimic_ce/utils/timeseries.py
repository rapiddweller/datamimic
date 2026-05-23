# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Time-series iteration helper for the ``<generate>`` element.

Activated by ``start``/``end``/``interval`` attributes on ``<generate>``. Strict
ISO 8601 inputs:

* ``start``, ``end`` -- ISO 8601 datetime (``2026-01-01T00:00:00Z`` etc.)
* ``interval``      -- ISO 8601 duration (``PT1H``, ``PT15M``, ``P1D``, ``PT0.001S``)

Exposes a ``ts`` namespace in the script context per iteration:

* ``ts.now``    -- ``datetime`` of the current tick
* ``ts.step``   -- ``int`` 0..N-1 (position within one series)
* ``ts.series`` -- ``int`` 0..count-1 (which series this row belongs to)

Note on naming: a ``<key name="ts">`` output column would shadow the namespace,
because ``current_product`` overrides ``current_variables`` in the script scope
(so a key can reference its own previously-assigned value). Pick a different
column name for the timestamp, e.g. ``<key name="timestamp" script="ts.now.isoformat()">``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import isodate


@dataclass(frozen=True)
class TimeSeriesNamespace:
    """Per-iteration view exposed as ``ts`` in the script context."""

    now: datetime
    step: int
    series: int


@dataclass(frozen=True)
class TimeSeriesConfig:
    """Parsed ``<generate start/end/interval>`` attributes.

    Built once per ``<generate>`` and reused for every iteration so the ISO
    strings are not re-parsed in the hot loop.
    """

    start: datetime
    interval: timedelta
    ticks_per_series: int

    @classmethod
    def parse(cls, start: str, end: str, interval: str) -> TimeSeriesConfig:
        start_dt = cls._parse_datetime(start, "start")
        end_dt = cls._parse_datetime(end, "end")
        interval_td = cls._parse_duration(interval)
        if end_dt <= start_dt:
            raise ValueError(
                f"<generate end=...> must be after <generate start=...>; "
                f"got start={start!r}, end={end!r}"
            )
        ticks = int((end_dt - start_dt).total_seconds() // interval_td.total_seconds())
        return cls(start=start_dt, interval=interval_td, ticks_per_series=ticks)

    def at(self, global_idx: int) -> TimeSeriesNamespace:
        """``ts`` namespace for one iteration.

        Loop order is contiguous-per-series: series 0 steps 0..N-1, then series 1, etc.
        This guarantees first-N-stability: the first ticks of series 0 are byte-
        identical regardless of total window length.
        """
        series = global_idx // self.ticks_per_series
        step = global_idx % self.ticks_per_series
        return TimeSeriesNamespace(now=self.start + self.interval * step, step=step, series=series)

    @staticmethod
    def _parse_datetime(value: str, attr: str) -> datetime:
        # `Z` is valid ISO 8601 UTC but fromisoformat only accepts it from Python 3.11;
        # normalise so this works on 3.10 too.
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(
                f"<generate {attr}=...> must be an ISO 8601 datetime "
                f"(e.g. '2026-01-01T00:00:00Z' or '2026-01-01'), got {value!r}"
            ) from exc

    @staticmethod
    def _parse_duration(value: str) -> timedelta:
        try:
            delta = isodate.parse_duration(value)
        except isodate.ISO8601Error as exc:
            raise ValueError(
                f"<generate interval=...> must be an ISO 8601 duration "
                f"(e.g. 'PT1H', 'PT15M', 'P1D', 'PT0.001S' for ms), got {value!r}"
            ) from exc
        # isodate.parse_duration may return Duration (months/years); we don't accept those
        # because they don't map to a constant-length timedelta. Equally, sub-microsecond
        # inputs (PT0.0000001S etc.) round down to timedelta(0) -- treat both the same way.
        if not isinstance(delta, timedelta) or delta <= timedelta(0):
            raise ValueError(
                f"<generate interval=...> must be a positive duration of at least 1us "
                f"(datetime.timedelta microsecond floor; months/years are not constant-length "
                f"and not supported); got {value!r}"
            )
        return delta
