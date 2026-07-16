# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
import warnings

from datamimic_ce.domains.common.literal_generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator

_EAN_UNIQUE_WARNING = (
    "EANGenerator no longer accepts a 'unique' parameter. "
    'Set unique="true" on the owning <key> or <variable> element instead — '
    "cross-row dedup is now handled at the task layer."
)


class EANGenerator(BaseLiteralGenerator):
    """EAN-13 codes via faker.

    Cross-row deduplication belongs to the task layer — set ``unique="true"``
    on the owning ``<key>`` or ``<variable>`` element instead of relying on a
    generator-owned uniqueness flag.
    """

    def __init__(
        self,
        locale: str | None = "en_US",
        rng: random.Random | None = None,
        **kwargs: object,
    ) -> None:
        if "unique" in kwargs:
            warnings.warn(_EAN_UNIQUE_WARNING, UserWarning, stacklevel=2)
        super().__init__(rng=rng)
        self._gen = DataFakerGenerator(method="ean", locale=locale, rng=rng)

    def generate(self) -> str:
        """Generate a random EAN-13 code."""
        return self._gen.generate()
