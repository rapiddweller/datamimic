"""RNG ownership SPOT for CE.

Two channels — keep them separate:

* ``rng`` is the **state-carrier / transport**. Passing an ``rng`` does NOT
  by itself imply deterministic mode.
* ``seeded_mode`` is the **policy / semantic channel**. Only an explicit
  ``seeded_mode=True`` activates deterministic RNG behaviour.

This separation matches EE's ADR-030 contract. Mixing the two channels
(e.g. ``rng is not None ⇒ deterministic``) is forbidden — there is no
silent promotion path.

Public surface:

* :func:`resolve_rng` — canonical entry point for generators.
* :func:`spawn_rng` — fork a deterministic child from a parent RNG.
* :func:`derive_child_seed` — derive a stable child seed from a namespace
  and a name. Uses SHA-256 so the result is process-independent
  (unlike :func:`hash`, which depends on ``PYTHONHASHSEED``).
"""

from __future__ import annotations

import hashlib
import random
import secrets
from typing import Final

_INT64_BOUND: Final[int] = 2**63
_MAX_DETERMINISTIC_SEED_FROM_STR: Final[int] = 2**64


def _canonicalise_seed(seed: int | str | bytes | None) -> int | None:
    """Normalise a caller-supplied seed value to an integer.

    * ``int`` values are returned modulo 2**64 so we don't carry arbitrary
      magnitudes around.
    * ``str`` / ``bytes`` values are hashed with SHA-256 — process-stable,
      independent of ``PYTHONHASHSEED``.
    * ``None`` returns ``None`` (caller must decide what that means).
    """
    if seed is None:
        return None
    if isinstance(seed, int):
        # mask to 64 bits so int and (str-of-the-same-number) coexist sanely
        return seed & (_MAX_DETERMINISTIC_SEED_FROM_STR - 1)
    if isinstance(seed, bytes):
        digest = hashlib.sha256(seed).digest()
    else:
        digest = hashlib.sha256(str(seed).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def resolve_rng(
    *,
    seed: int | str | bytes | None = None,
    rng: random.Random | None = None,
    seeded_mode: bool | None = None,
) -> random.Random:
    """Return a :class:`random.Random` honouring the determinism policy.

    The policy ladder (highest priority first):

    1. ``seeded_mode is True`` — return a deterministic Random.
       * if ``seed`` is supplied → seed from it
       * elif ``rng`` is supplied → return it (caller already chose state)
       * else → raise; seeded mode without a seed source is a contract
         violation, not a silent fallback to wall-clock.

    2. ``seeded_mode is False`` — return a non-deterministic Random
       (CSPRNG-seeded). Any ``seed`` / ``rng`` argument is ignored.

    3. ``seeded_mode is None`` (legacy / unspecified):
       * if ``seed`` is supplied → seed from it (treat as seeded — same
         intent as if the caller had said seeded_mode=True)
       * elif ``rng`` is supplied → return it (transport-only; caller is
         responsible for whether the upstream state is deterministic)
       * else → return an unseeded Random (live wall-clock seeded by
         CPython default — matches today's CE behaviour).

    The ``None`` branch is the bridge for existing CE callers that pass
    only ``rng=...``. New code SHOULD pass ``seeded_mode=True`` explicitly.
    """
    if seeded_mode is True:
        canon = _canonicalise_seed(seed)
        if canon is not None:
            return random.Random(canon)
        if rng is not None:
            return rng
        raise ValueError(
            "resolve_rng(seeded_mode=True) requires a seed or an rng "
            "(deterministic mode must not fall back to wall-clock)."
        )

    if seeded_mode is False:
        # Non-deterministic on purpose: CSPRNG-grade seeding.
        return random.Random(secrets.randbits(64))

    # seeded_mode is None — legacy bridge.
    canon = _canonicalise_seed(seed)
    if canon is not None:
        return random.Random(canon)
    if rng is not None:
        return rng
    return random.Random()


def derive_child_seed(parent: random.Random, namespace: str, name: str) -> int:
    """Derive a deterministic child seed from a parent RNG plus a label.

    The label (namespace + name) makes the child seed reproducible: as long
    as the same parent state, namespace, and name are used, the same child
    seed comes out. SHA-256 keeps this independent of ``PYTHONHASHSEED``
    (unlike :func:`hash`).
    """
    parent_token = parent.getrandbits(64)
    digest = hashlib.sha256(
        f"{namespace}/{name}/{parent_token}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def spawn_rng(parent: random.Random, *, namespace: str = "child", name: str = "") -> random.Random:
    """Fork a deterministic child :class:`random.Random` from ``parent``.

    Use this instead of the ad-hoc ``random.Random(self._rng.randrange(2**63))``
    pattern that's scattered through CE generators. The single seam means
    architecture-gates can enforce it.
    """
    return random.Random(derive_child_seed(parent, namespace, name))
