# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Deterministic numeric sequences over a [min, max] granularity grid, exposed through
``distribution=`` on ranged numeric generators: positional walks (step/increment, shuffle,
wedge, bitreverse), recurrence series (fibonacci, padovan), and a saturating randomWalk.
Positional sequences are unique until exhausted and END (StopIteration) instead of wrapping.

Implemented as iterator classes with plain-data state (cursor ints, an rng) rather than
Python generator objects: context namespaces are deep-copied during script evaluation, and a
held generator object cannot be copied/pickled - a cursor survives the copy at the exact
position it had."""

import random
from decimal import Decimal

from datamimic_ce.enums.distribution_enums import POSITIONAL_NUMBER_SEQUENCES, NumberDistribution


def _grid_size(min_v: float, max_v: float, granularity: float) -> int:
    """Number of grid points min, min+g, ..., <= max. Decimal so a float span like
    (99.99-0.49)/0.10 = 994.999... does not drop the top point."""
    return int((Decimal(str(max_v)) - Decimal(str(min_v))) / Decimal(str(granularity))) + 1


class _GridSequence:
    """Base: maps grid indices k -> values; subclasses advance a plain-int cursor."""

    def __init__(self, min_v: float, max_v: float, granularity: float, integral: bool):
        self._min = min_v
        self._granularity = granularity
        self._integral = integral
        self._steps = _grid_size(min_v, max_v, granularity)

    def _value_at(self, k: int) -> int | float:
        if self._integral:
            return int(self._min) + k * int(self._granularity)
        return float(Decimal(str(self._min)) + k * Decimal(str(self._granularity)))

    def __iter__(self):
        return self


class _StepSequence(_GridSequence):
    """min, min+g, min+2g, ... ends past max (never wraps)."""

    def __init__(self, *args):
        super().__init__(*args)
        self._pos = 0

    def __next__(self) -> int | float:
        if self._pos >= self._steps:
            raise StopIteration
        value = self._value_at(self._pos)
        self._pos += 1
        return value


class _ShuffleSequence(_GridSequence):
    """Strided unique walk (stride 2): offsets 0,2,4,... then 1,3,5,... - every grid point
    exactly once, e.g. 1,3,5,2,4 over 1..5."""

    _STRIDE = 2

    def __init__(self, *args):
        super().__init__(*args)
        self._offset = 0
        self._k = 0

    def __next__(self) -> int | float:
        if self._offset >= self._STRIDE:
            raise StopIteration
        value = self._value_at(self._k)
        self._k += self._STRIDE
        if self._k >= self._steps:
            self._offset += 1
            self._k = self._offset
        return value


class _WedgeSequence(_GridSequence):
    """min, max, min+g, max-g, ... converging on the middle point, then ends."""

    def __init__(self, *args):
        super().__init__(*args)
        self._lo = 0
        self._hi = self._steps - 1
        self._from_low = True

    def __next__(self) -> int | float:
        if self._lo > self._hi:
            raise StopIteration
        if self._lo == self._hi:
            value = self._value_at(self._lo)
            self._lo += 1
            return value
        if self._from_low:
            value = self._value_at(self._lo)
            self._lo += 1
        else:
            value = self._value_at(self._hi)
            self._hi -= 1
        self._from_low = not self._from_low
        return value


class _BitReverseSequence(_GridSequence):
    """Bit-reversed counter order (0,4,2,6,1,5,3,7 over 0..7), skipping points past the range."""

    def __init__(self, *args):
        super().__init__(*args)
        self._bits = max((self._steps - 1).bit_length(), 1)
        self._cursor = 0

    def __next__(self) -> int | float:
        while self._cursor < (1 << self._bits):
            k = int(f"{self._cursor:0{self._bits}b}"[::-1], 2)
            self._cursor += 1
            if k < self._steps:
                return self._value_at(k)
        raise StopIteration


class _RandomWalkSequence(_GridSequence):
    """Starts at min, advances by a seeded random step of 1..2 grid points per draw, and
    saturates at max. Infinite by design (rng-driven, so it also runs under multiprocessing -
    each worker walks its own valid path)."""

    def __init__(self, min_v: float, max_v: float, granularity: float, integral: bool, rng: random.Random):
        super().__init__(min_v, max_v, granularity, integral)
        self._rng = rng
        self._k = 0

    def __next__(self) -> int | float:
        value = self._value_at(self._k)
        self._k = min(self._k + self._rng.randint(1, 2), self._steps - 1)
        return value


class _RecurrenceSequence:
    """Recurrence VALUES within [min, max]: ends once the next value exceeds max; values below
    min are skipped so a min > 0 range still yields the in-range tail."""

    def __init__(self, distribution: NumberDistribution, min_v: float, max_v: float):
        self._min = min_v
        self._max = max_v
        if distribution is NumberDistribution.FIBONACCI:
            self._window = [0, 1]  # a(n) = a(n-1) + a(n-2)
            self._pending = [0, 1]
        else:  # PADOVAN: a(n) = a(n-2) + a(n-3), seeds 1, 1, 1
            self._window = [1, 1, 1]
            self._pending = [1, 1, 1]
        self._is_fibonacci = distribution is NumberDistribution.FIBONACCI

    def __iter__(self):
        return self

    def __next__(self) -> int:
        while True:
            if self._pending:
                value = self._pending.pop(0)
            else:
                if self._is_fibonacci:
                    value = self._window[-1] + self._window[-2]
                    self._window = [self._window[-1], value]
                else:
                    value = self._window[1] + self._window[0]
                    self._window = [self._window[1], self._window[2], value]
            if value > self._max:
                raise StopIteration
            if value >= self._min:
                return value


def finite_number_sequence_capacity(
    distribution: NumberDistribution,
    min_v: float,
    max_v: float,
    granularity: float,
) -> int | None:
    """Return the exact output capacity of a finite positional sequence.

    This lives beside the iterator implementations so authoring analysis does
    not reproduce their exhaustion semantics. Non-finite distributions return
    ``None``. Invalid ranges are left to the runtime model/generator validators.
    """
    if distribution not in POSITIONAL_NUMBER_SEQUENCES:
        return None
    if min_v > max_v or granularity <= 0:
        return None
    if distribution in (NumberDistribution.FIBONACCI, NumberDistribution.PADOVAN):
        sequence = _RecurrenceSequence(distribution, min_v, max_v)
        count = 0
        for _ in sequence:
            count += 1
        return count
    return _grid_size(min_v, max_v, granularity)


def build_number_sequence(
    distribution: NumberDistribution,
    min_v: float,
    max_v: float,
    granularity: float,
    rng: random.Random,
    integral: bool,
):
    """Value iterator for a sequence-type NumberDistribution. Exhaustion raises StopIteration -
    the engine treats it like a source running dry (the row loop ends)."""
    if distribution in (NumberDistribution.FIBONACCI, NumberDistribution.PADOVAN):
        return _RecurrenceSequence(distribution, min_v, max_v)
    if distribution is NumberDistribution.RANDOM_WALK:
        return _RandomWalkSequence(min_v, max_v, granularity, integral, rng)
    sequence_classes = {
        NumberDistribution.STEP: _StepSequence,
        NumberDistribution.INCREMENT: _StepSequence,
        NumberDistribution.SHUFFLE: _ShuffleSequence,
        NumberDistribution.WEDGE: _WedgeSequence,
        NumberDistribution.BIT_REVERSE: _BitReverseSequence,
    }
    return sequence_classes[distribution](min_v, max_v, granularity, integral)
