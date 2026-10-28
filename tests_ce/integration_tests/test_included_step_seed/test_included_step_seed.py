# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Each included step draws from its own seeded stream (#463). The descriptors beside this module are the cases.
They are not scenarios because Build refuses their shape: an include inside a <generate> ("Bounded XML includes
require literal setup-level workspace paths") and a step that runs twice ("Product names must be globally unique
for bounded capture"). tests_ce/scenarios/s29_included_step_streams holds the Build-ready cases."""

from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def _draws(filename: str) -> dict[str, list[object]]:
    engine = DataMimicTest(_DIR, filename, capture_test_result=True)
    engine.test_with_timer()
    return {name: [row["draw"] for row in rows] for name, rows in (engine.capture_result() or {}).items()}


def test_entry_keeps_the_stream_it_had_before_the_steps_got_their_own() -> None:
    draws = _draws("two_steps.xml")
    # The rows of rngSeed="7" before #463: the entry stream is Random(rngSeed), and a step does not advance it.
    assert draws["before_steps"] == [295639350, 865768827, 835129426]
    assert draws["after_steps"] == [461684537, 413628448, 168562010]


def test_two_steps_differ_from_each_other_and_from_the_entry() -> None:
    draws = _draws("two_steps.xml")
    assert len(set(draws["before_steps"] + draws["first"] + draws["second"])) == 9
    assert _draws("two_steps.xml") == draws


def test_another_seed_changes_every_step() -> None:
    seven, eight = _draws("two_steps.xml"), _draws("two_steps_other_seed.xml")
    assert all(set(seven[name]).isdisjoint(eight[name]) for name in ("first", "second"))


def test_unseeded_steps_differ_between_runs() -> None:
    first_run, second_run = _draws("two_steps_unseeded.xml"), _draws("two_steps_unseeded.xml")
    assert first_run["first"] != second_run["first"]
    assert first_run["second"] != second_run["second"]


@pytest.mark.parametrize(
    ("filename", "count"),
    [
        ("same_step_twice.xml", 6),
        ("step_per_row.xml", 9),  # pageSize="1": the run counter of the step survives the pages
        ("shared_step_two_parents.xml", 6),
        # A library generator gets a deep copy of the step context, which must keep the step stream.
        ("context_generator_steps.xml", 6),
        ("library_in_steps.xml", 6),  # a library executed inside a step draws from the step stream
    ],
)
def test_each_run_of_a_step_draws_its_own_values_and_replays(filename: str, count: int) -> None:
    draws = _draws(filename)
    values = [value for rows in draws.values() for value in rows]
    assert len(set(values)) == count == len(values)
    assert _draws(filename) == draws
