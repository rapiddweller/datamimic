# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""The run's seed SPOT: one place decides "derived from <setup rngSeed>, else random for this run"."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class RunSeed:
    """``value`` is ``<setup rngSeed>`` (None = unseeded). ``run_entropy`` is drawn once per run and stands
    in for the seed when there is none; it travels with the context to every worker, so values keyed from
    it (e.g. the Hash converter key) still agree across the workers of one unseeded run."""

    value: int | None
    run_entropy: bytes

    @classmethod
    def create(cls, value: int | None) -> RunSeed:
        return cls(value=value, run_entropy=secrets.token_bytes(32))

    @property
    def seeded(self) -> bool:
        return self.value is not None

    def key_for(self, purpose: str) -> bytes:
        """A 32-byte key for ``purpose``: replays with the seed, random per run without one."""
        material = str(self.value).encode() if self.value is not None else self.run_entropy
        return hashlib.sha256(purpose.encode() + b"|" + material).digest()

    def int_for(self, purpose: str) -> int:
        """A non-negative 63-bit int for ``purpose``, keyed like :meth:`key_for`."""
        return int.from_bytes(self.key_for(purpose)[:8], "big") >> 1
