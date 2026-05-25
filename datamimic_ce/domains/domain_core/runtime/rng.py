"""RNG derivation SPOT for CE determinism.

A single place for the "fork a reproducible child RNG from a parent" operation,
so seeded runs derive child RNGs the same way everywhere (generators, the setup
root seed, demographic sampling).
"""

from __future__ import annotations

import random
from random import Random
from typing import Any


def derive_child_seed(parent: Random) -> int:
    """Draw a reproducible child seed (int) from ``parent``."""
    return parent.randrange(2**63)


def spawn_rng(parent: Random) -> Random:
    """Fork a reproducible child ``Random`` from ``parent``."""
    return Random(derive_child_seed(parent))


def ensure_rng(rng: Random | None) -> Random:
    """Return ``rng`` if not None, else a fresh wall-clock ``Random()``.

    Use at the boundary where a class needs to own a ``Random`` instance
    (not the module): caller-supplied rng marks the run seeded, ``None``
    means "give me my own wall-clock instance".
    """
    return rng if rng is not None else Random()


def or_module(rng: Random | None) -> Any:
    """Return ``rng`` if not None, else the ``random`` module.

    Sister of :func:`ensure_rng`. Use at call-time accessors that need a
    usable callable API without forcing callers to branch on ``None``:
    callers say ``ctx.rng.choice(...)`` and don't care whether ``ctx.rng``
    is a seeded ``Random`` or the wall-clock ``random`` module. Distinct
    from :func:`ensure_rng` (which gives a fresh ``Random()`` instance);
    use that at instance boundaries that must OWN a Random.
    """
    return rng if rng is not None else random
