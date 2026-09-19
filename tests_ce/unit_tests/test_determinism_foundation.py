"""Tests for the CE determinism foundation (wall-clock SPOT).

RNG-ownership behaviour is pinned by ``test_base_generator_hierarchy.py``.
This file covers the clock primitives and cross-process byte-stability.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone

from datamimic_ce.domains.domain_core.runtime import now_utc_naive, resolve_clock
from datamimic_ce.domains.domain_core.runtime.clock import DETERMINISTIC_ANCHOR

# ---------- now_utc_naive / resolve_clock ----------------------------------


def test_now_utc_naive_returns_naive_utc() -> None:
    ts = now_utc_naive()
    assert ts.tzinfo is None
    delta = abs((ts - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds())
    assert delta < 5.0


def test_deterministic_anchor_is_stable_and_naive() -> None:
    assert datetime(2025, 1, 1, 12, 0, 0) == DETERMINISTIC_ANCHOR
    assert DETERMINISTIC_ANCHOR.tzinfo is None


def test_resolve_clock_deterministic_returns_anchor() -> None:
    assert resolve_clock(deterministic=True) == DETERMINISTIC_ANCHOR


def test_resolve_clock_live_returns_recent_naive_utc() -> None:
    ts = resolve_clock(deterministic=False)
    assert ts.tzinfo is None
    delta = abs((ts - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds())
    assert delta < 5.0


# ---------- Cross-process determinism --------------------------------------


def test_seeded_generator_byte_identical_across_python_invocations() -> None:
    """A seeded generator must produce the same RNG stream across process
    restarts — proves the determinism contract is process-independent."""
    script = (
        "import random;"
        "from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator;"
        "g = BaseDomainGenerator(rng=random.Random(42));"
        "print(','.join(f'{g.rng.random():.18f}' for _ in range(5)))"
    )
    out_a = subprocess.check_output([sys.executable, "-c", script], text=True).strip()
    out_b = subprocess.check_output([sys.executable, "-c", script], text=True).strip()
    assert out_a == out_b, "seeded generator output drifted across Python processes."
