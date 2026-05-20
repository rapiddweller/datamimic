"""Runtime SPOTs for CE determinism: RNG ownership and wall-clock.

* :func:`resolve_rng` — canonical entry point. ``rng`` is the transport;
  ``seeded_mode`` is the policy channel.
* :func:`now_utc_naive` — the only sanctioned wall-clock read in CE.
* :func:`resolve_clock` — returns the deterministic anchor or live UTC,
  anchored once at construction time.
"""

from datamimic_ce.domains.domain_core.runtime.clock import (
    now_utc_naive,
    resolve_clock,
)
from datamimic_ce.domains.domain_core.runtime.rng import resolve_rng

__all__ = [
    "now_utc_naive",
    "resolve_clock",
    "resolve_rng",
]
