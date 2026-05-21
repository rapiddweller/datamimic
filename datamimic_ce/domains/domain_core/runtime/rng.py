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
    rng: random.Random | None = None,
    seeded_mode: bool | None = None,
) -> tuple[random.Random, bool]:
    """Resolve a canonical ``(rng, seeded_mode)`` pair for a generator.

    Two channels, kept separate:

    * ``rng`` is the state-carrier / transport.
    * ``seeded_mode`` is the policy. Passing an ``rng`` alone does NOT
      imply deterministic mode.

    Precedence:

    * explicit ``seeded_mode`` wins. ``seeded_mode=True`` requires an
      ``rng`` (deterministic mode must not silently fall back to
      wall-clock); ``seeded_mode=False`` returns a CSPRNG-seeded Random.
    * lone ``rng`` → transport only, mode ``False``.
    * nothing → fresh non-deterministic Random, mode ``False``.
    """
    if seeded_mode is not None:
        if rng is not None:
            return rng, seeded_mode
        if seeded_mode:
            raise ValueError(
                "resolve_rng(seeded_mode=True) requires rng= "
                "(deterministic mode must not fall back to wall-clock)."
            )
        return random.Random(secrets.randbits(64)), False
    if rng is not None:
        return rng, False
    return random.Random(), False
