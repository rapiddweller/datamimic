# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce._compat import StrEnum


class NumberDistribution(StrEnum):
    """Sampling distribution / sequence for ranged numeric generators (IntegerGenerator/
    FloatGenerator), reachable natively via <key type="int" min= max= distribution="...">.

    UNIFORM/CUMULATED/RANDOM_WALK draw per row (rng-bound); the rest are
    deterministic SEQUENCES - positional, unique until exhausted, and they END
    (StopIteration) instead of wrapping. Positional sequences are single-process only:
    multiprocessing chunks would restart the sequence per worker and emit duplicates,
    so that combination is rejected loudly (see GenerateTask).
    """

    UNIFORM = "uniform"
    CUMULATED = "cumulated"  # symmetric bell, mean = midpoint
    STEP = "step"  # min, min+d, min+2d, ... (d = granularity; ends past max)
    INCREMENT = "increment"  # legacy alias: step with d=1
    RANDOM_WALK = "randomWalk"  # starts at min, random step in [1,2]*d per row, saturates at max
    SHUFFLE = "shuffle"  # strided unique walk: 1,3,5,2,4 over 1..5 (stride 2), ends when covered
    WEDGE = "wedge"  # min, max, min+d, max-d, ... converging on the middle, then ends
    BIT_REVERSE = "bitreverse"  # bit-reversed counter order: 0,4,2,6,1,5,3,7 over 0..7
    FIBONACCI = "fibonacci"  # recurrence values within [min,max]; ends when the next exceeds max
    PADOVAN = "padovan"  # like fibonacci with a(n) = a(n-2) + a(n-3), seeds 1,1,1


#: Deterministic positional sequences - unique-until-exhausted, restart per process, therefore
#: rejected under multiprocessing (a worker chunk would replay the same values).
POSITIONAL_NUMBER_SEQUENCES: frozenset[NumberDistribution] = frozenset(
    {
        NumberDistribution.STEP,
        NumberDistribution.INCREMENT,
        NumberDistribution.SHUFFLE,
        NumberDistribution.WEDGE,
        NumberDistribution.BIT_REVERSE,
        NumberDistribution.FIBONACCI,
        NumberDistribution.PADOVAN,
    }
)


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
