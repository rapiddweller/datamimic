"""Runtime SPOTs for CE determinism.

RNG ownership lives on :class:`BaseDomainGenerator` (a supplied ``rng`` marks a
run seeded). Task-level code that does not own an RNG resolves one from its
context via :func:`resolve_rng`.

* :func:`derive_child_seed` — draw a reproducible child seed (int) from a parent RNG.
* :func:`spawn_rng` — fork a reproducible child RNG from a parent (built on
  :func:`derive_child_seed`; used by generators, the setup root seed, and demographics).
* :func:`resolve_rng` — single helper for tasks: returns ``ctx.rng`` when
  available, else a fresh child of ``<setup rngSeed>``, else the ``random`` module.
* :func:`now_utc_naive` — the only sanctioned wall-clock read in CE.
* :func:`resolve_clock` — returns the deterministic anchor or live UTC,
  anchored once at construction time.
"""

from datamimic_ce.domains.domain_core.runtime.clock import (
    now_utc_naive,
    resolve_clock,
)
from datamimic_ce.domains.domain_core.runtime.rng import derive_child_seed, resolve_rng, spawn_rng

__all__ = [
    "derive_child_seed",
    "now_utc_naive",
    "resolve_clock",
    "resolve_rng",
    "spawn_rng",
]
