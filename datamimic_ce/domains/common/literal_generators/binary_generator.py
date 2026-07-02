# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator


class BinaryGenerator(BaseLiteralGenerator):
    """Generate random ``bytes`` of a length in [min_len, max_len] (defaults 1..16).

    Backs ``<key type="binary" minLength=... maxLength=...>``. Deterministic under a seeded rng
    (``rng.randbytes``). Raw bytes stay in the product (DBs take them natively); file exporters
    base64-encode them at the export boundary.
    """

    def __init__(
        self,
        min_len: int | None = None,
        max_len: int | None = None,
        rng: random.Random | None = None,
    ):
        super().__init__(rng=rng)
        # One bound given -> the other defaults sensibly, mirroring StringGenerator.
        if min_len is None and max_len is None:
            lo, hi = 1, 16
        elif min_len is None:
            hi = int(max_len)  # type: ignore[arg-type]
            lo = min(1, hi)
        elif max_len is None:
            lo = hi = int(min_len)
        else:
            lo, hi = int(min_len), int(max_len)
        if lo < 0 or hi < 0:
            raise ValueError(f"BinaryGenerator lengths must be >= 0, got min={lo}, max={hi}")
        if lo > hi:
            raise ValueError(f"BinaryGenerator min length {lo} exceeds max length {hi}")
        self._min_len = lo
        self._max_len = hi

    def generate(self) -> bytes:
        return self.rng.randbytes(self.rng.randint(self._min_len, self._max_len))
