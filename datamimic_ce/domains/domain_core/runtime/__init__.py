"""Runtime SPOTs for CE determinism.

RNG ownership lives on :class:`BaseDomainGenerator` (a supplied ``rng`` marks a
run seeded); there is no resolve-rng helper. The only shared RNG primitive is the
child-derivation below.

* :func:`spawn_rng` — fork a reproducible child RNG from a parent (the single
  derivation used by generators, the setup root seed, and demographics).
* :func:`now_utc_naive` — the only sanctioned wall-clock read in CE.
* :func:`resolve_clock` — returns the deterministic anchor or live UTC,
  anchored once at construction time.
"""

from datamimic_ce.domains.domain_core.runtime.clock import (
    now_utc_naive,
    resolve_clock,
)
from datamimic_ce.domains.domain_core.runtime.rng import spawn_rng

__all__ = [
    "now_utc_naive",
    "resolve_clock",
    "spawn_rng",
]
