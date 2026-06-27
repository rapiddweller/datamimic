# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from enum import Enum


class NumberDistribution(str, Enum):
    """Sampling distribution for ranged numeric generators (IntegerGenerator/FloatGenerator).

    Referenced by name from the DSL generator string, e.g.
    generator="IntegerGenerator(min=1, max=27, distribution=NumberDistribution.CUMULATED)".
    CUMULATED mirrors Benerator's CumulatedLong/DoubleGenerator (symmetric bell, mean=midpoint).
    """

    UNIFORM = "uniform"
    CUMULATED = "cumulated"


class SourceDistribution(str, Enum):
    """Distribution for selecting rows from a source on <variable>/<generate>
    (the ``distribution`` attribute), distinct from NumberDistribution which shapes a
    single numeric value.

    RANDOM = shuffled permutation, ORDERED = sequential, CUMULATED = bell-weighted index
    (with replacement, middle of the load order favored). CUMULATED is accepted on
    <variable> only.
    """

    RANDOM = "random"
    ORDERED = "ordered"
    CUMULATED = "cumulated"

    @classmethod
    def coerce(cls, value: "str | None") -> "SourceDistribution":
        """Normalize a parsed distribution string to a member; absent = RANDOM (load-all
        default). Raises ValueError on an unknown value."""
        return cls(value) if value else cls.RANDOM
