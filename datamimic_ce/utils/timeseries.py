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

_ISO_DURATION_RE = re.compile(
    r"^P"
    r"(?:(?P<w>\d+)W)?"
    r"(?:(?P<d>\d+)D)?"
    r"(?:T"
    r"(?:(?P<h>\d+)H)?"
    r"(?:(?P<m>\d+)M)?"
    r"(?:(?P<s>\d+)S)?"
    r")?$"
)


def parse_iso_datetime(value: str) -> datetime:
    """Parse an ISO 8601 datetime, accepting the ``Z`` UTC suffix on Python 3.10."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_iso_duration(value: str) -> timedelta:
    """Parse a (subset of) ISO 8601 duration into a ``timedelta``.

    Supports weeks/days/hours/minutes/seconds. Months and years are intentionally
    not supported -- they are not constant-length durations.
    """
    match = _ISO_DURATION_RE.match(value)
    if not match:
        raise ValueError(f"Invalid ISO 8601 duration: {value!r}")
    parts = {k: int(v) if v else 0 for k, v in match.groupdict().items()}
    if not any(parts.values()):
        raise ValueError(f"Empty ISO 8601 duration: {value!r}")
    delta = timedelta(
        weeks=parts["w"],
        days=parts["d"],
        hours=parts["h"],
        minutes=parts["m"],
        seconds=parts["s"],
    )
    if delta.total_seconds() <= 0:
        raise ValueError(f"ISO 8601 duration must be positive: {value!r}")
    return delta


def ticks_per_series(from_value: str, to_value: str, interval_value: str) -> int:
    """Number of ticks in the half-open window ``[from, to)`` at ``interval``."""
    start = parse_iso_datetime(from_value)
    end = parse_iso_datetime(to_value)
    step = parse_iso_duration(interval_value)
    if end <= start:
        raise ValueError(f"'to' ({to_value}) must be after 'from' ({from_value})")
    span_seconds = (end - start).total_seconds()
    return int(span_seconds // step.total_seconds())


@dataclass(frozen=True)
class TimeSeriesNamespace:
    """Per-iteration view exposed as ``ts`` in the script context."""

    now: datetime
    step: int
    series: int


def ts_at(global_idx: int, ticks_per_series_: int, from_value: str, interval_value: str) -> TimeSeriesNamespace:
    """Compute the ``ts`` namespace for a given global iteration index.

    Loop order is contiguous-per-series: series 0 steps 0..N-1, then series 1, etc.
    This guarantees the "first-N-stable" property: the first ticks of series 0
    are byte-identical regardless of total window length.
    """
    series = global_idx // ticks_per_series_
    step = global_idx % ticks_per_series_
    now = parse_iso_datetime(from_value) + parse_iso_duration(interval_value) * step
    return TimeSeriesNamespace(now=now, step=step, series=series)
