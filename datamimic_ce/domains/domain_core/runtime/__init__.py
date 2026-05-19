"""Runtime SPOTs for CE determinism: RNG ownership and wall-clock.

This package is the single source of truth for two cross-cutting runtime
concerns in CE:

* **RNG ownership** — every generator that wants deterministic output must
  obtain its randomness through :func:`resolve_rng`. The two channels
  ``rng`` (state-carrier) and ``seeded_mode`` (policy) are kept separate
  so that "deterministic" is an explicit, audited decision and never an
  accidental side-effect of "an rng was passed".

* **Wall-clock** — :func:`now_utc_naive` is the only sanctioned wall-clock
  read in CE production code. :func:`resolve_clock` returns a fixed
  ``DETERMINISTIC_ANCHOR`` when the generator runs in seeded mode.

Public API mirrors the EE contract vocabulary (ADR-030 / ADR-031) so the
two cores can converge on a shared discipline later without renaming.
"""

from datamimic_ce.domains.domain_core.runtime.clock import (
    DETERMINISTIC_ANCHOR,
    now_utc_naive,
    resolve_clock,
)
from datamimic_ce.domains.domain_core.runtime.rng import (
    derive_child_seed,
    resolve_rng,
    spawn_rng,
)

__all__ = [
    "DETERMINISTIC_ANCHOR",
    "derive_child_seed",
    "now_utc_naive",
    "resolve_clock",
    "resolve_rng",
    "spawn_rng",
]
