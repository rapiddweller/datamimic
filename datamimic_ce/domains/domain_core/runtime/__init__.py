"""Runtime SPOTs for CE determinism: wall-clock resolution.

RNG ownership lives on :class:`BaseDomainGenerator` (a supplied ``rng``
marks a run seeded); there is no separate resolve-rng helper.

* :func:`now_utc_naive` — the only sanctioned wall-clock read in CE.
* :func:`resolve_clock` — returns the deterministic anchor or live UTC,
  anchored once at construction time.
"""

from datamimic_ce.domains.domain_core.runtime.clock import (
    now_utc_naive,
    resolve_clock,
)

__all__ = [
    "now_utc_naive",
    "resolve_clock",
]
