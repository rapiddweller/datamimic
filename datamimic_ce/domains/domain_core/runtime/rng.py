"""RNG ownership SPOT for CE.

Two channels — keep them separate:

* ``rng`` is the **state-carrier / transport**. Passing an ``rng`` does NOT
  by itself imply deterministic mode.
* ``seeded_mode`` is the **policy / semantic channel**. Only an explicit
  ``seeded_mode=True`` (or an explicit ``seed=``) activates deterministic
  behaviour.

This separation matters because some generators in CE
(``DateTimeGenerator``, password / token / hash generators) branch on the
policy: deterministic mode anchors the reference clock and uses the
caller's RNG; non-deterministic mode uses live wall-clock and CSPRNG.
"""

from __future__ import annotations

import random
import secrets


def resolve_rng(
    *,
    seed: int | None = None,
    rng: random.Random | None = None,
    seeded_mode: bool | None = None,
) -> tuple[random.Random, bool]:
    """Resolve a canonical ``(rng, seeded_mode)`` pair for a generator.

    Precedence:

    * ``seed`` (explicit) → always seeded; an injected ``seeded_mode=False``
      does not veto an explicit seed.
    * explicit ``seeded_mode`` → that wins; ``seeded_mode=True`` requires
      either ``seed`` or ``rng`` (no silent wall-clock fallback to mode).
    * lone ``rng`` → transport only; mode is ``False``.
    * nothing → fresh non-deterministic Random, mode ``False``.
    """
    if seed is not None:
        return (rng if rng is not None else random.Random(seed)), True
    if seeded_mode is not None:
        if rng is not None:
            return rng, seeded_mode
        if seeded_mode:
            raise ValueError(
                "resolve_rng(seeded_mode=True) requires seed= or rng= "
                "(deterministic mode must not fall back to wall-clock)."
            )
        return random.Random(secrets.randbits(64)), False
    if rng is not None:
        return rng, False
    return random.Random(), False
