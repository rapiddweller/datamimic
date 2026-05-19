"""Tests for the CE determinism foundation.

Locks the contract of:
- ``resolve_rng`` — policy/transport separation, error on seeded_mode without seed
- ``derive_child_seed`` — deterministic, namespace-keyed, process-independent
- ``spawn_rng`` — different parent state ⇒ different child
- ``now_utc_naive`` — returns naive UTC
- ``DETERMINISTIC_ANCHOR`` — stable, in-the-past, naive
- ``resolve_clock`` — deterministic branch returns the anchor
"""

from __future__ import annotations

import random
import subprocess
import sys
from datetime import datetime, timezone

import pytest

from datamimic_ce.domains.domain_core.runtime import (
    DETERMINISTIC_ANCHOR,
    derive_child_seed,
    now_utc_naive,
    resolve_clock,
    resolve_rng,
    spawn_rng,
)


# ---------- resolve_rng ----------------------------------------------------


def test_resolve_rng_seeded_mode_true_with_seed_is_deterministic() -> None:
    a = resolve_rng(seed=42, seeded_mode=True)
    b = resolve_rng(seed=42, seeded_mode=True)
    assert [a.random() for _ in range(5)] == [b.random() for _ in range(5)]


def test_resolve_rng_seeded_mode_true_with_string_seed_is_deterministic() -> None:
    a = resolve_rng(seed="regression-suite-42", seeded_mode=True)
    b = resolve_rng(seed="regression-suite-42", seeded_mode=True)
    assert [a.random() for _ in range(5)] == [b.random() for _ in range(5)]


def test_resolve_rng_seeded_mode_true_int_and_str_seeds_diverge() -> None:
    """seed=42 (int) and seed='42' (str) must NOT collide.

    The canonicalisation pipeline keeps the two representations distinct
    so that callers don't get accidental hash collisions across types.
    """
    a = resolve_rng(seed=42, seeded_mode=True)
    b = resolve_rng(seed="42", seeded_mode=True)
    # First draw should already differ.
    assert a.random() != b.random()


def test_resolve_rng_seeded_mode_true_without_source_raises() -> None:
    """Seeded mode without seed or rng is a contract violation."""
    with pytest.raises(ValueError, match="requires a seed or an rng"):
        resolve_rng(seeded_mode=True)


def test_resolve_rng_seeded_mode_false_is_non_deterministic() -> None:
    a = resolve_rng(seed=42, seeded_mode=False)
    b = resolve_rng(seed=42, seeded_mode=False)
    # CSPRNG seeding => two independent Randoms with overwhelming probability.
    assert a.random() != b.random()


def test_resolve_rng_seeded_mode_none_with_seed_is_deterministic() -> None:
    """Legacy bridge: passing only a seed gives deterministic output."""
    a = resolve_rng(seed=42)
    b = resolve_rng(seed=42)
    assert [a.random() for _ in range(5)] == [b.random() for _ in range(5)]


def test_resolve_rng_seeded_mode_none_with_rng_only_returns_rng() -> None:
    """Transport channel: caller-supplied rng is returned as-is."""
    src = random.Random(123)
    out = resolve_rng(rng=src)
    assert out is src


def test_resolve_rng_seeded_mode_none_with_nothing_is_unseeded() -> None:
    """Nothing supplied → live wall-clock-seeded Random (matches old behaviour)."""
    a = resolve_rng()
    b = resolve_rng()
    # Two independent Randoms; the first draw will diverge with overwhelming probability.
    assert a.random() != b.random()


# ---------- derive_child_seed / spawn_rng ----------------------------------


def test_derive_child_seed_is_deterministic_for_same_parent_state() -> None:
    parent_a = random.Random(42)
    parent_b = random.Random(42)
    assert derive_child_seed(parent_a, "ns", "field") == derive_child_seed(parent_b, "ns", "field")


def test_derive_child_seed_differs_per_label() -> None:
    parent = random.Random(42)
    s1 = derive_child_seed(parent, "ns", "field-a")
    parent = random.Random(42)
    s2 = derive_child_seed(parent, "ns", "field-b")
    assert s1 != s2


def test_derive_child_seed_differs_per_namespace() -> None:
    parent = random.Random(42)
    s1 = derive_child_seed(parent, "ns-a", "field")
    parent = random.Random(42)
    s2 = derive_child_seed(parent, "ns-b", "field")
    assert s1 != s2


def test_spawn_rng_is_deterministic_and_isolated() -> None:
    parent_a = random.Random(42)
    parent_b = random.Random(42)
    child_a = spawn_rng(parent_a, name="x")
    child_b = spawn_rng(parent_b, name="x")
    assert [child_a.random() for _ in range(3)] == [child_b.random() for _ in range(3)]
    # The parents should have advanced equivalently, too.
    assert parent_a.random() == parent_b.random()


# ---------- now_utc_naive / resolve_clock ----------------------------------


def test_now_utc_naive_returns_naive_utc() -> None:
    ts = now_utc_naive()
    assert ts.tzinfo is None
    # And it should be roughly current.
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
    """The deterministic mode must survive process restarts."""
    script = (
        "from datamimic_ce.domains.domain_core.runtime import resolve_rng;"
        "r = resolve_rng(seed='cross-process-test', seeded_mode=True);"
        "print(','.join(f'{r.random():.18f}' for _ in range(5)))"
    )
    out_a = subprocess.check_output([sys.executable, "-c", script], text=True).strip()
    out_b = subprocess.check_output([sys.executable, "-c", script], text=True).strip()
    assert out_a == out_b, "resolve_rng output drifted across Python processes."
