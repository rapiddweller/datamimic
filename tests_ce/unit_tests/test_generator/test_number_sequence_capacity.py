# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""The authoring capacity API must stay identical to runtime iterator exhaustion."""

import random

import pytest

from datamimic_ce.enums.distribution_enums import POSITIONAL_NUMBER_SEQUENCES, NumberDistribution
from datamimic_ce.utils.number_sequences import build_number_sequence, finite_number_sequence_capacity


@pytest.mark.parametrize("distribution", sorted(POSITIONAL_NUMBER_SEQUENCES, key=lambda item: item.value))
def test_finite_capacity_matches_runtime_iterator(distribution: NumberDistribution) -> None:
    sequence = build_number_sequence(
        distribution,
        min_v=1,
        max_v=20,
        granularity=1,
        rng=random.Random(1),
        integral=True,
    )
    assert finite_number_sequence_capacity(distribution, 1, 20, 1) == len(list(sequence))


@pytest.mark.parametrize(
    ("distribution", "minimum", "maximum", "granularity", "integral"),
    (
        (NumberDistribution.STEP, 1, 9, 1, True),
        (NumberDistribution.SHUFFLE, 0.5, 2.0, 0.25, False),
        (NumberDistribution.WEDGE, 0.1, 1.0, 0.1, False),
        (NumberDistribution.FIBONACCI, 5, 100, 1, True),
        (NumberDistribution.PADOVAN, 5, 100, 1, True),
    ),
)
def test_representative_capacity_matches_runtime_iterator(
    distribution: NumberDistribution,
    minimum: float,
    maximum: float,
    granularity: float,
    integral: bool,
) -> None:
    sequence = build_number_sequence(
        distribution,
        min_v=minimum,
        max_v=maximum,
        granularity=granularity,
        rng=random.Random(1),
        integral=integral,
    )
    assert finite_number_sequence_capacity(
        distribution,
        minimum,
        maximum,
        granularity,
    ) == len(list(sequence))


@pytest.mark.parametrize(
    "distribution",
    [member for member in NumberDistribution if member not in POSITIONAL_NUMBER_SEQUENCES],
)
def test_non_finite_distribution_has_no_capacity(distribution: NumberDistribution) -> None:
    assert finite_number_sequence_capacity(distribution, 1, 20, 1) is None
