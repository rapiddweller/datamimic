"""RNG derivation SPOT for CE determinism.

A single place for the "fork a reproducible child RNG from a parent" operation,
so seeded runs derive child RNGs the same way everywhere (generators, the setup
root seed, demographic sampling).
"""

from __future__ import annotations

import random as _stdlib_random
from random import Random
from typing import Any


def derive_child_seed(parent: Random) -> int:
    """Draw a reproducible child seed (int) from ``parent``."""
    return parent.randrange(2**63)


def spawn_rng(parent: Random) -> Random:
    """Fork a reproducible child ``Random`` from ``parent``."""
    return Random(derive_child_seed(parent))


def resolve_rng(ctx: Any) -> Any:
    """Return the RNG to use for randomness driven by ``ctx``.

    - ``GenIterContext`` (anything exposing ``.rng``): use its already-resolved
      RNG (seeded child of ``<setup rngSeed>`` or the ``random`` module when
      unseeded).
    - ``SetupContext`` (or any context whose ``.root`` exposes
      ``derive_seeded_rng``): fork a fresh child from the model-wide seed;
      fall back to the ``random`` module when the root is unseeded.
    - Anything else: ``random`` module.

    Always returns an object exposing the standard ``Random`` callable API
    (``random``, ``choice``, ``choices``, ``randint``, ``sample``, ``uniform``,
    ``shuffle``). Callers must not branch on the return value.
    """
    rng = getattr(ctx, "rng", None)
    if rng is not None:
        return rng
    root = getattr(ctx, "root", ctx)
    derive = getattr(root, "derive_seeded_rng", None)
    if callable(derive):
        derived = derive()
        if derived is not None:
            return derived
    return _stdlib_random
