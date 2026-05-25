"""Runtime SPOTs for CE determinism.

Two channels, one rule each:

* **Call time** — tasks executing under a ``GenIterContext`` read randomness
  through ``ctx.rng`` (always usable: a seeded ``Random`` child of
  ``<setup rngSeed>`` or the ``random`` module when unseeded). No helper
  needed; no duck typing.
* **Construction time** — code building a generator under a ``SetupContext``
  calls ``setup_ctx.derive_seeded_rng()`` and falls back to the ``random``
  module when it returns ``None``. Two sites in the codebase; intentionally
  inlined, no helper.

Primitives:

* :func:`derive_child_seed` — draw a reproducible child seed (int) from a parent RNG.
* :func:`spawn_rng` — fork a reproducible child RNG from a parent (built on
  :func:`derive_child_seed`; used by generators, the setup root seed, and demographics).
* :func:`now_utc_naive` — the only sanctioned wall-clock read in CE.
* :func:`resolve_clock` — returns the deterministic anchor or live UTC,
  anchored once at construction time.
"""

from datamimic_ce.domains.domain_core.runtime.clock import (
    now_utc_naive,
    resolve_clock,
)
from datamimic_ce.domains.domain_core.runtime.rng import derive_child_seed, spawn_rng

__all__ = [
    "derive_child_seed",
    "now_utc_naive",
    "resolve_clock",
    "spawn_rng",
]
