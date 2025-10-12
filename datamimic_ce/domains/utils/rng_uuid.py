# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Helpers for generating UUID values with caller-provided RNGs."""

from __future__ import annotations

import uuid
from random import Random


def uuid4_from_random(rng: Random) -> str:
    """Return a UUIDv4 string generated from the supplied RNG.

    Python's ``uuid.uuid4()`` always pulls from the global RNG/os entropy which
    breaks determinism when we inject ``rngSeed``. This helper mirrors the UUIDv4
    bit layout while sourcing randomness from the caller-controlled ``Random``.
    """

    value = rng.getrandbits(128)
    # Enforce UUID version/variant bits so downstream validators accept the value.
    value &= ~(0xF << 76)
    value |= 0x4 << 76  # Set version 4
    value &= ~(0x3 << 62)
    value |= 0x2 << 62  # Set RFC 4122 variant
    return str(uuid.UUID(int=value))
