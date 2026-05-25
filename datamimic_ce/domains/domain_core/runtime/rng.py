"""RNG forking SPOT.

One place for the "fork a reproducible child RNG from a parent" operation.
"""

from __future__ import annotations

from random import Random


def derive_child_seed(parent: Random) -> int:
    """Draw a reproducible child seed (int) from ``parent``."""
    return parent.randrange(2**63)


def spawn_rng(parent: Random) -> Random:
    """Fork a reproducible child ``Random`` from ``parent``."""
    return Random(derive_child_seed(parent))
