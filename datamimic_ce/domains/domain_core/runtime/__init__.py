"""Runtime SPOTs for CE determinism.

* :func:`spawn_rng` / :func:`derive_child_seed` — fork a reproducible child RNG.
* :func:`now_utc_naive` / :func:`resolve_clock` — sanctioned wall-clock reads.
* :func:`from_epoch_utc` / :func:`to_epoch_utc` — timezone-independent epoch conversion.
"""

from datamimic_ce.domains.domain_core.runtime.clock import (
    from_epoch_utc,
    now_utc_naive,
    resolve_clock,
    to_epoch_utc,
)
from datamimic_ce.domains.domain_core.runtime.rng import derive_child_seed, spawn_rng

__all__ = [
    "derive_child_seed",
    "from_epoch_utc",
    "now_utc_naive",
    "resolve_clock",
    "spawn_rng",
    "to_epoch_utc",
]
