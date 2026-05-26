"""Runtime SPOTs for CE determinism.

* :func:`spawn_rng` / :func:`derive_child_seed` — fork a reproducible child RNG.
* :func:`now_utc_naive` / :func:`resolve_clock` — sanctioned wall-clock reads.
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
