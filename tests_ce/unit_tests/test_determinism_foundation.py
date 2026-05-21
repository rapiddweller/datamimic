"""Tests for the CE determinism foundation.

Pins the contract of:

* :func:`resolve_rng` — policy/transport channels, error on
  ``seeded_mode=True`` without a seed source.
* :func:`now_utc_naive` — naive UTC, recent.
* :func:`resolve_clock` — deterministic branch returns the anchor.
* Cross-process byte-stability via subprocess invocation.
"""

from __future__ import annotations

import random
import subprocess
import sys
from datetime import datetime, timezone

import pytest

from datamimic_ce.domains.domain_core.runtime import (
    now_utc_naive,
    resolve_clock,
    resolve_rng,
)
from datamimic_ce.domains.domain_core.runtime.clock import DETERMINISTIC_ANCHOR


# ---------- resolve_rng ----------------------------------------------------


def test_resolve_rng_seeded_rng_is_reproducible() -> None:
    a_rng, a_mode = resolve_rng(rng=random.Random(42), seeded_mode=True)
    b_rng, b_mode = resolve_rng(rng=random.Random(42), seeded_mode=True)
    assert a_mode is True and b_mode is True
    assert [a_rng.random() for _ in range(5)] == [b_rng.random() for _ in range(5)]


def test_resolve_rng_seeded_mode_true_without_source_raises() -> None:
    with pytest.raises(ValueError, match="requires rng="):
        resolve_rng(seeded_mode=True)


def test_resolve_rng_seeded_mode_true_with_rng_returns_that_rng() -> None:
    src = random.Random(123)
    rng, mode = resolve_rng(rng=src, seeded_mode=True)
    assert rng is src and mode is True


def test_resolve_rng_seeded_mode_false_is_non_deterministic() -> None:
    a_rng, a_mode = resolve_rng(seeded_mode=False)
    b_rng, b_mode = resolve_rng(seeded_mode=False)
    assert a_mode is False and b_mode is False
    assert a_rng.random() != b_rng.random()


def test_resolve_rng_lone_rng_is_transport_only() -> None:
    """An injected rng without an explicit seeded_mode is transport, mode=False."""
    src = random.Random(7)
    rng, mode = resolve_rng(rng=src)
    assert rng is src and mode is False


def test_resolve_rng_nothing_supplied_is_unseeded() -> None:
    a_rng, a_mode = resolve_rng()
    b_rng, b_mode = resolve_rng()
    assert a_mode is False and b_mode is False
    assert a_rng.random() != b_rng.random()


# ---------- now_utc_naive / resolve_clock ----------------------------------


def test_now_utc_naive_returns_naive_utc() -> None:
    ts = now_utc_naive()
    assert ts.tzinfo is None
    delta = abs((ts - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds())
    assert delta < 5.0


def test_deterministic_anchor_is_stable_and_naive() -> None:
    assert DETERMINISTIC_ANCHOR == datetime(2025, 1, 1, 12, 0, 0)
    assert DETERMINISTIC_ANCHOR.tzinfo is None


def test_resolve_clock_deterministic_returns_anchor() -> None:
    assert resolve_clock(deterministic=True) == DETERMINISTIC_ANCHOR


def test_resolve_clock_live_returns_recent_naive_utc() -> None:
    ts = resolve_clock(deterministic=False)
    assert ts.tzinfo is None
    delta = abs((ts - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds())
    assert delta < 5.0


# ---------- Cross-process determinism --------------------------------------


def test_resolve_rng_byte_identical_across_python_invocations() -> None:
    """Deterministic mode must survive process restarts."""
    script = (
        "import random;"
        "from datamimic_ce.domains.domain_core.runtime import resolve_rng;"
        "r, _ = resolve_rng(rng=random.Random(42), seeded_mode=True);"
        "print(','.join(f'{r.random():.18f}' for _ in range(5)))"
    )
    out_a = subprocess.check_output([sys.executable, "-c", script], text=True).strip()
    out_b = subprocess.check_output([sys.executable, "-c", script], text=True).strip()
    assert out_a == out_b, "resolve_rng output drifted across Python processes."
