# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Proofs for the generic time-series primitive on ``<generate>``.

Time-series mode is activated by ISO 8601 ``from``/``to``/``interval`` attributes
on ``<generate>``. Per iteration the script context gets a ``ts`` namespace with
``ts.now`` (datetime), ``ts.step`` (int 0..N-1) and ``ts.series`` (int 0..count-1).

The primitive is intentionally domain-agnostic: the same DSL serves IoT,
financial ticks, log streams, etc. -- the user decides what the rows look like
via ``<key>`` elements.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str) -> list[dict]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    result = engine.capture_result()
    # Each fixture has exactly one top-level generate; return its rows.
    assert len(result) == 1, f"expected one product key, got {list(result)}"
    return next(iter(result.values()))


# ---------------------------------------------------------------------------
# Core: tick math, replay, loop order
# ---------------------------------------------------------------------------


def test_basic_single_series_progresses_through_24_hours() -> None:
    """Default ``count`` (no attribute) yields a single series of N ticks."""
    rows = _run("basic_one_series.xml")
    assert len(rows) == 24, "24h window at PT1H interval = 24 rows"
    assert [r["step"] for r in rows] == list(range(24))
    assert [r["series"] for r in rows] == [0] * 24
    assert [r["hour"] for r in rows] == list(range(24))
    assert rows[0]["timestamp"].startswith("2026-01-01T00:00:00")
    assert rows[-1]["timestamp"].startswith("2026-01-01T23:00:00")


def test_basic_single_series_replays_identically() -> None:
    assert _run("basic_one_series.xml") == _run("basic_one_series.xml")


def test_multi_series_loop_order_is_contiguous_per_series() -> None:
    """count=3 with 6 ticks each: series 0 first, then 1, then 2."""
    rows = _run("multi_series.xml")
    assert len(rows) == 18
    expected_series = [s for s in range(3) for _ in range(6)]
    expected_step = list(range(6)) * 3
    assert [r["series"] for r in rows] == expected_series
    assert [r["step"] for r in rows] == expected_step
    assert [r["series_id"] for r in rows[:6]] == ["series_000"] * 6
    assert [r["series_id"] for r in rows[6:12]] == ["series_001"] * 6


def test_multi_series_replays_identically() -> None:
    assert _run("multi_series.xml") == _run("multi_series.xml")


# ---------------------------------------------------------------------------
# Prefix stability: enlarging the window must not perturb earlier ticks
# ---------------------------------------------------------------------------


def test_window_prefix_is_stable_across_window_sizes() -> None:
    """First 24 rows of a 7d window must equal all 24 rows of a 1d window."""
    short = _run("window_short.xml")
    long = _run("window_long.xml")
    assert len(short) == 24
    assert len(long) == 24 * 7
    assert long[:24] == short, "prefix-stability guarantee violated"


# ---------------------------------------------------------------------------
# Seasonality: math.sin pattern is computable purely from ts.now
# ---------------------------------------------------------------------------


def test_seasonal_pattern_has_diurnal_shape() -> None:
    rows = _run("seasonal.xml")
    by_hour = {r["hour"]: r["value"] for r in rows}
    # 20 - 10*cos(h*pi/12) peaks at h=12 (cos(pi) = -1 -> 30) and bottoms at h=0/24 (cos(0) = 1 -> 10).
    assert by_hour[12] > by_hour[0], "noon should peak above midnight"
    assert by_hour[6] > by_hour[0] and by_hour[6] < by_hour[12], "6am between midnight and noon"


# ---------------------------------------------------------------------------
# Non-IoT use-cases: same primitive, no domain vocabulary
# ---------------------------------------------------------------------------


def test_stock_tickers_use_case() -> None:
    rows = _run("use_case_stock_ticks.xml")
    assert len(rows) == 3 * 6  # 3 symbols x (30min / 5min)
    assert sorted({r["symbol"] for r in rows}) == ["AAPL", "GOOG", "MSFT"]
    # Each symbol must walk through the same step sequence with the same prices.
    aapl = [r for r in rows if r["symbol"] == "AAPL"]
    msft = [r for r in rows if r["symbol"] == "MSFT"]
    assert [r["price"] for r in aapl] == [r["price"] for r in msft], (
        "price formula is a pure function of ts.step -- same across series"
    )


def test_log_stream_without_id_column() -> None:
    """The user can simply not emit a series-id column when they don't want one."""
    rows = _run("use_case_log_stream.xml")
    assert len(rows) == 10
    assert all("series" not in r for r in rows), "no series column should appear"
    assert [r["level"] for r in rows] == ["INFO", "WARN", "ERROR"] * 3 + ["INFO"]
    assert rows[0]["message"] == "request 0"
    assert rows[-1]["message"] == "request 9"


# ---------------------------------------------------------------------------
# Validation: time-series attributes must be set together
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Interval resolution: seconds, milliseconds, microseconds (datetime.timedelta limit)
# ---------------------------------------------------------------------------


def test_interval_seconds() -> None:
    rows = _run("interval_seconds.xml")
    assert len(rows) == 30
    assert [r["second"] for r in rows] == list(range(30))


def test_interval_milliseconds() -> None:
    """PT0.001S = 1 ms via ISO 8601 fractional seconds (no separate ms symbol)."""
    rows = _run("interval_milliseconds.xml")
    assert len(rows) == 50
    # 1 ms in microseconds = 1000; step n -> microsecond = n * 1000.
    assert [r["micro"] for r in rows] == [n * 1000 for n in range(50)]


def test_interval_microseconds_is_finest_supported_resolution() -> None:
    """PT0.000001S = 1 us. Below this, datetime.timedelta cannot represent the delta."""
    rows = _run("interval_microseconds.xml")
    assert len(rows) == 20
    assert [r["micro"] for r in rows] == list(range(20))


def test_sub_microsecond_interval_rejected() -> None:
    """Nanosecond-scale intervals round to timedelta(0); error must mention the microsecond floor."""
    with pytest.raises(ValueError) as exc:
        _run("invalid_subus_interval.xml")
    assert "1us" in str(exc.value), f"expected error to mention the microsecond floor, got: {exc.value}"


def test_partial_window_raises() -> None:
    """`interval` alone (without start/end) must be rejected at parse time."""
    with pytest.raises(ValueError) as exc:
        _run("invalid_partial_window.xml")
    msg = str(exc.value)
    assert "start" in msg or "end" in msg, f"expected helpful error mentioning missing attrs, got: {msg}"


# Each error message must mention BOTH the offending DSL attribute name AND the offending value,
# so a user looking at the error can find the line in their XML and see what they typed.


def test_bad_start_datetime_error_mentions_attr_and_value() -> None:
    with pytest.raises(ValueError) as exc:
        _run("invalid_bad_start.xml")
    msg = str(exc.value)
    assert "start" in msg, f"error must mention the offending attribute (start): {msg}"
    assert "not-a-datetime" in msg, f"error must echo the offending value: {msg}"
    assert "ISO 8601" in msg, f"error must hint at the expected format: {msg}"


def test_bad_end_datetime_error_mentions_attr_and_value() -> None:
    with pytest.raises(ValueError) as exc:
        _run("invalid_bad_end.xml")
    msg = str(exc.value)
    assert "end" in msg, f"error must mention the offending attribute (end): {msg}"
    assert "January 8th, 2026" in msg, f"error must echo the offending value: {msg}"


def test_bad_interval_error_mentions_attr_and_value_and_example() -> None:
    """A user writing '1h' instead of 'PT1H' is a very common mistake; the error
    must point them at the correct ISO 8601 syntax."""
    with pytest.raises(ValueError) as exc:
        _run("invalid_bad_interval.xml")
    msg = str(exc.value)
    assert "interval" in msg, f"error must mention the offending attribute (interval): {msg}"
    assert "1h" in msg, f"error must echo the offending value: {msg}"
    assert "PT1H" in msg, f"error must show a canonical example so the user can fix it: {msg}"


def test_end_before_start_error_mentions_both_attrs() -> None:
    with pytest.raises(ValueError) as exc:
        _run("invalid_end_before_start.xml")
    msg = str(exc.value)
    assert "start" in msg and "end" in msg, f"ordering error must reference both attrs: {msg}"


def test_ts_variable_name_is_reserved_in_timeseries_mode() -> None:
    """`<variable name="ts">` shadows the time-iterator namespace at script-eval
    time. The parser must reject it up front with a message naming the rule."""
    with pytest.raises(ValueError) as exc:
        _run("invalid_ts_variable_collision.xml")
    msg = str(exc.value)
    assert "ts" in msg, f"error must name the reserved variable: {msg}"
    assert "reserved" in msg or "time-iterator" in msg or "time-series" in msg, (
        f"error must explain why 'ts' is rejected: {msg}"
    )


# ---------------------------------------------------------------------------
# Pagination invariance: page boundaries must not perturb output
# ---------------------------------------------------------------------------


def test_pagination_does_not_affect_output() -> None:
    """Same DSL run with a small pageSize produces byte-identical output to the
    default pageSize. Without this, splitting a long series across pages could
    desynchronise series/step (worker computes them from the global index)."""
    default_paging = _run("basic_one_series.xml")
    small_paging = _run("basic_one_series_paginated.xml")
    assert default_paging == small_paging, (
        "page boundaries must not perturb time-series output -- this would break "
        "the prefix-stability and contiguous-per-series guarantees"
    )


# ---------------------------------------------------------------------------
# Composition with other DSL constructs: the ts namespace must reach them
# ---------------------------------------------------------------------------


def test_composes_with_key_condition() -> None:
    """ts.* available inside a <key condition="..."> expression."""
    rows = _run("composition_condition.xml")
    assert len(rows) == 6
    assert [r["step"] for r in rows] == list(range(6))
    # Even-step rows include `even_only`, odd rows omit it.
    for r in rows:
        if r["step"] % 2 == 0:
            assert "even_only" in r and r["even_only"] == r["step"]
        else:
            assert "even_only" not in r or r["even_only"] is None


def test_composes_with_nested_key() -> None:
    """ts.* reaches inside a <nestedKey> sub-scope."""
    rows = _run("composition_nested_key.xml")
    assert len(rows) == 3
    for i, r in enumerate(rows):
        assert r["step"] == i
        assert r["meta"]["second"] == i
        assert r["meta"]["iso_now"].endswith(f"00:00:0{i}+00:00")
