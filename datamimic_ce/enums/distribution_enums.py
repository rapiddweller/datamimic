# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from enum import StrEnum


class NumberDistribution(StrEnum):
    """Sampling distribution for ranged numeric generators (IntegerGenerator/FloatGenerator).

    Referenced by name from the DSL generator string, e.g.
    generator="IntegerGenerator(min=1, max=27, distribution=NumberDistribution.CUMULATED)".
    CUMULATED mirrors Benerator's CumulatedLong/DoubleGenerator (symmetric bell, mean=midpoint).
    """

    UNIFORM = "uniform"
    CUMULATED = "cumulated"


class SourceDistribution(StrEnum):
    """Distribution for selecting rows from a source on <variable>/<generate>/<nestedKey>
    (the ``distribution`` attribute), distinct from NumberDistribution which shapes a
    single numeric value.

    RANDOM = shuffled permutation, ORDERED = sequential, CUMULATED = bell-weighted index
    (with replacement, middle of the load order favored). All three are accepted on
    <variable>, <generate> and <nestedKey>.
    """

    RANDOM = "random"
    ORDERED = "ordered"
    CUMULATED = "cumulated"

    @property
    def loads_all(self) -> bool:
        """ORDERED paginates the source sequentially; RANDOM (shuffle) and CUMULATED (bell)
        must load ALL rows first. Single source of truth for the load-vs-paginate decision."""
        return self is not SourceDistribution.ORDERED

    @classmethod
    def coerce(cls, value: "str | None") -> "SourceDistribution":
        """Normalize a parsed distribution string to a member; absent = RANDOM (load-all
        default). Raises ValueError on an unknown value."""
        return cls(value) if value else cls.RANDOM
