# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Time-series iteration helper for the ``<generate>`` element.

Activated by ``from``/``to``/``interval`` attributes on ``<generate>``. Strict
ISO 8601 inputs:

* ``from``, ``to`` -- ISO 8601 datetime (``2026-01-01T00:00:00Z`` etc.)
* ``interval``    -- ISO 8601 duration (``PT1H``, ``PT15M``, ``P1D``, ``P1DT12H``)

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

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

# ISO 8601 duration subset: weeks/days/hours/minutes/seconds.
# Seconds accept fractional values (e.g. PT0.001S = 1 ms, PT0.000001S = 1 us),
# limited by Python's microsecond-precision timedelta.
_ISO_DURATION_RE = re.compile(
    r"^P"
    r"(?:(?P<w>\d+)W)?"
    r"(?:(?P<d>\d+)D)?"
    r"(?:T"
    r"(?:(?P<h>\d+)H)?"
    r"(?:(?P<m>\d+)M)?"
    r"(?:(?P<s>\d+(?:\.\d+)?)S)?"
    r")?$"
)


def _parse_iso_datetime(value: str) -> datetime:
    """Parse an ISO 8601 datetime, accepting the ``Z`` UTC suffix on Python 3.10."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_iso_duration(value: str) -> timedelta:
    """Parse a subset of ISO 8601 durations (weeks/days/hours/minutes/seconds).

    Seconds accept fractional values down to Python's microsecond limit;
    sub-microsecond intervals (e.g. nanoseconds) are not representable in
    ``datetime.timedelta`` and are rejected with a clear error.
    """
    match = _ISO_DURATION_RE.match(value)
    if not match:
        raise ValueError(f"Invalid ISO 8601 duration: {value!r}")
    groups = match.groupdict()
    # Compute the input duration in seconds (float) before constructing the
    # timedelta -- otherwise sub-microsecond inputs round to zero and we can't
    # distinguish "user wrote 0" from "user wrote a value below our resolution".
    total = (
        int(groups["w"] or 0) * 604_800
        + int(groups["d"] or 0) * 86_400
        + int(groups["h"] or 0) * 3_600
        + int(groups["m"] or 0) * 60
        + float(groups["s"] or 0)
    )
    if total <= 0:
        raise ValueError(f"ISO 8601 duration must be positive: {value!r}")
    if total < 1e-6:
        raise ValueError(
            f"ISO 8601 duration below 1us is not representable in datetime.timedelta: {value!r}"
        )
    return timedelta(seconds=total)


@dataclass(frozen=True)
class TimeSeriesNamespace:
    """Per-iteration view exposed as ``ts`` in the script context."""

    now: datetime
    step: int
    series: int


@dataclass(frozen=True)
class TimeSeriesConfig:
    """Parsed ``<generate from/to/interval>`` attributes.

    Built once per ``<generate>`` and reused for every iteration so the ISO
    strings are not re-parsed in the hot loop.
    """

    start: datetime
    interval: timedelta
    ticks_per_series: int

    @classmethod
    def parse(cls, from_value: str, to_value: str, interval_value: str) -> TimeSeriesConfig:
        start = _parse_iso_datetime(from_value)
        end = _parse_iso_datetime(to_value)
        interval = _parse_iso_duration(interval_value)
        if end <= start:
            raise ValueError(f"'to' ({to_value!r}) must be after 'from' ({from_value!r})")
        ticks = int((end - start).total_seconds() // interval.total_seconds())
        return cls(start=start, interval=interval, ticks_per_series=ticks)

    def at(self, global_idx: int) -> TimeSeriesNamespace:
        """Compute the ``ts`` namespace for a given global iteration index.

        Loop order is contiguous-per-series: series 0 steps 0..N-1, then series 1, etc.
        This guarantees the "first-N-stable" property: the first ticks of series 0
        are byte-identical regardless of total window length.
        """
        series = global_idx // self.ticks_per_series
        step = global_idx % self.ticks_per_series
        return TimeSeriesNamespace(now=self.start + self.interval * step, step=step, series=series)
