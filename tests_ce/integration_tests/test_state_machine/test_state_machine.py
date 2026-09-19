# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""<state-machine>: define a weighted state machine once, reference it by name.

Surface: engine (datamimic_ce). Proves the named machine resolves as a generator,
walks only legal transitions, each referencing field gets its own walk, the walk is
seed-reproducible under <setup rngSeed>, and the weights are honoured.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent

_LEGAL = {"open": {"paid"}, "paid": {"shipped", "cancelled"}, "shipped": {"delivered"}}
_TERMINALS = {"cancelled", "delivered"}
_START = "open"
_ALL = {"open", "paid", "shipped", "cancelled", "delivered"}

# complex_machine.xml: 3-way branch, self-loop (review->review), convergent paths.
_C_LEGAL = {
    "received": {"review"},
    "review": {"approved", "rejected", "review"},
    "approved": {"paid"},
    "paid": {"closed"},
    "rejected": {"closed"},
}
_C_TERMINALS = {"closed"}
_C_START = "received"
_C_ALL = {"received", "review", "approved", "rejected", "paid", "closed"}


def _run(filename: str, key: str = "status", gen: str = "orders") -> list[str]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return [r[key] for r in engine.capture_result()[gen]]


def _assert_legal_walk(states, legal, terminals, start, allowed) -> None:
    assert states[0] == start
    assert set(states) <= allowed
    for a, b in zip(states, states[1:], strict=False):
        ok = b in legal.get(a, set()) or (a in terminals and b == start)
        assert ok, f"illegal step {a}->{b}"


def test_named_machine_resolves_and_walks_legally():
    engine = DataMimicTest(test_dir=_TEST_DIR, filename="state_machine.xml", capture_test_result=True)
    engine.test_with_timer()
    out = engine.capture_result()
    orders = [r["status"] for r in out["orders"]]
    more = [r["status"] for r in out["more"]]
    _assert_legal_walk(orders, _LEGAL, _TERMINALS, _START, _ALL)
    _assert_legal_walk(more, _LEGAL, _TERMINALS, _START, _ALL)
    # each referencing field walks independently -> both start at the start state
    assert orders[0] == more[0] == _START
    assert _TERMINALS & set(orders)


def test_complex_machine_walks_legally_with_self_loop_and_convergence():
    states = _run("complex_machine.xml", gen="claims")
    _assert_legal_walk(states, _C_LEGAL, _C_TERMINALS, _C_START, _C_ALL)
    # every reachable state (incl. the self-loop and both convergent branches) shows up
    assert set(states) == _C_ALL
    # the self-loop actually fires: 'review' is sometimes followed by 'review'
    assert any(a == "review" and b == "review" for a, b in zip(states, states[1:], strict=False))


def test_seed_makes_the_walk_reproducible():
    # same rngSeed -> identical sequence on every run
    assert _run("complex_machine.xml", gen="claims") == _run("complex_machine.xml", gen="claims")
    # a different rngSeed -> a different sequence (the seed really drives the walk)
    assert _run("complex_machine.xml", gen="claims") != _run("complex_machine_seed99.xml", gen="claims")


def test_weights_are_honoured_under_seed():
    states = _run("complex_machine.xml", gen="claims")
    # distribution of the state that follows each 'review' (the 0.5/0.3/0.2 branch)
    branches = Counter(b for a, b in zip(states, states[1:], strict=False) if a == "review")
    total = sum(branches.values())
    assert total > 100  # enough samples for a meaningful ratio
    assert abs(branches["approved"] / total - 0.5) < 0.1
    assert abs(branches["rejected"] / total - 0.3) < 0.1
    assert abs(branches["review"] / total - 0.2) < 0.1
