# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""StateTransitionGenerator: walks a weighted state machine, one state per row.

Surface: engine (datamimic_ce). DSL property proof: the emitted state sequence
only takes legal transitions, starts at the start state, and restarts at the
start after a terminal state.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent

# the machine encoded in state_transition.xml
_LEGAL = {"open": {"paid"}, "paid": {"shipped", "cancelled"}, "shipped": {"delivered"}}
_TERMINALS = {"cancelled", "delivered"}
_START = "open"
_ALL = {"open", "paid", "shipped", "cancelled", "delivered"}


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_walk_follows_legal_transitions():
    states = [r["status"] for r in _run("state_transition.xml")["orders"]]
    assert states[0] == _START
    assert set(states) <= _ALL
    for a, b in zip(states, states[1:], strict=False):
        legal = b in _LEGAL.get(a, set())
        restart = a in _TERMINALS and b == _START
        assert legal or restart, f"illegal step {a}->{b}"
    # the chain actually terminates, and the dominant 0.9 branch is taken
    assert _TERMINALS & set(states)
    assert "shipped" in states


def test_invalid_spec_raises():
    with pytest.raises(Exception, match="transition"):
        _run("state_transition_invalid.xml")
