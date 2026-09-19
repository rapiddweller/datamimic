# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Unit tests for StateTransitionGenerator: spec parsing and weighted sampling.

The weighted-distribution check needs a seeded rng, which the DSL cannot inject
into a literal generator (literal generators are not <setup rngSeed>-bound), so
that one assertion lives here rather than in a DSL file.
"""

from __future__ import annotations

import random

import pytest

from datamimic_ce.domains.common.literal_generators.state_transition_generator import StateTransitionGenerator


def test_weighted_branch_distribution():
    gen = StateTransitionGenerator("paid->shipped:0.9, paid->cancelled:0.1", rng=random.Random(42))
    # walk emits: paid, <branch>, paid, <branch>, ... (each terminal restarts at 'paid')
    branches = [s for s in (gen.generate() for _ in range(4000)) if s != "paid"]
    shipped = branches.count("shipped")
    ratio = shipped / len(branches)
    assert 0.85 <= ratio <= 0.95, f"shipped ratio {ratio} off 0.9"
    assert set(branches) == {"shipped", "cancelled"}


def test_start_is_first_source_and_terminal_restarts():
    gen = StateTransitionGenerator("a->b, b->c")  # c is terminal
    seq = [gen.generate() for _ in range(6)]
    assert seq == ["a", "b", "c", "a", "b", "c"]


@pytest.mark.parametrize("bad", ["open", "a->b, oops", "->b", "a->"])
def test_invalid_spec_raises(bad):
    with pytest.raises(ValueError, match="transition"):
        StateTransitionGenerator(bad)
