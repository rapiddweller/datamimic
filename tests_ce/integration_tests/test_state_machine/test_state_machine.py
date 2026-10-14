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

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

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


def _run_xml(tmp_path, declarations, fields, *, count=8, page_size=2, tail="", seed=17):
    descriptor = tmp_path / "aliases.xml"
    descriptor.write_text(
        f'<setup rngSeed="{seed}">{declarations}'
        f'<generate name="rows" count="{count}" pageSize="{page_size}" target="">'
        f'{fields}</generate>{tail}</setup>'
    )
    engine = DataMimicTest(test_dir=tmp_path, filename=descriptor.name, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


_MACHINE = '''<state-machine id="life" start="open">
    <transition from="open" to="closed"/>
</state-machine>'''
_ALIAS = '<generator name="alias" generator="life"/>'


def test_named_alias_keys_and_variables_share_one_walk_across_pages(tmp_path):
    fields = '''<key name="first" generator="alias"/>
        <variable name="step" generator="alias"/>
        <key name="second" script="step"/>
        <key name="third" generator="alias"/>'''
    captured = _run_xml(tmp_path, _MACHINE + _ALIAS, fields, count=5)
    rows = captured["rows"]
    # Three draws per row from one two-state walk; a page rebuild must not restart it.
    assert [[r["first"], r["second"], r["third"]] for r in rows] == [
        ["open", "closed", "open"],
        ["closed", "open", "closed"],
        ["open", "closed", "open"],
        ["closed", "open", "closed"],
        ["open", "closed", "open"],
    ]
    assert captured == _run_xml(tmp_path, _MACHINE + _ALIAS, fields, count=5)
    assert captured == _run_xml(tmp_path, _MACHINE + _ALIAS, fields, count=5, page_size=3)


def test_direct_machine_walkers_stay_independent_from_alias_instance(tmp_path):
    fields = '''<key name="alias" generator="alias"/>
        <key name="direct" generator="life"/>
        <variable name="step" generator="life"/>
        <key name="direct_variable" script="step"/>'''
    captured = _run_xml(tmp_path, _MACHINE + _ALIAS, fields)
    expected = ["open", "closed"] * 4
    assert [r["alias"] for r in captured["rows"]] == expected
    assert [r["direct"] for r in captured["rows"]] == expected
    assert [r["direct_variable"] for r in captured["rows"]] == expected


def test_alias_chains_continue_shared_walk_in_later_generates(tmp_path):
    declarations = _MACHINE + _ALIAS + '<generator name="second_alias" generator="alias"/>'
    tail = '''<generate name="later" count="2" pageSize="1" target="">
        <key name="state" generator="second_alias"/>
    </generate>'''
    captured = _run_xml(tmp_path, declarations, '<key name="state" generator="alias"/>', count=3, tail=tail)
    assert [r["state"] for r in captured["rows"]] == ["open", "closed", "open"]
    assert [r["state"] for r in captured["later"]] == ["closed", "open"]


def test_named_scalar_instance_shares_only_when_explicitly_referenced(tmp_path):
    declarations = '<generator name="scalar" generator="IntegerGenerator(min=1,max=999)"/>'
    fields = '''<key name="named" generator="scalar"/>
        <variable name="next" generator="scalar"/>
        <key name="named_variable" script="next"/>
        <key name="ordinary_a" generator="IntegerGenerator(min=1,max=999)"/>
        <key name="ordinary_b" generator="IntegerGenerator(min=1,max=999)"/>'''
    rows = _run_xml(tmp_path, declarations, fields, count=5)["rows"]
    single = _run_xml(tmp_path, declarations, '<key name="value" generator="scalar"/>', count=10)["rows"]
    assert [value for r in rows for value in (r["named"], r["named_variable"])] == [r["value"] for r in single]
    assert [r["ordinary_a"] for r in rows] != [r["ordinary_b"] for r in rows]
    assert [r["ordinary_a"] for r in rows] != [r["named"] for r in rows]


@pytest.mark.parametrize(
    "declarations,fields,tail",
    [
        (_MACHINE, '<key name="state" generator="unknown"/>', ""),
        (_ALIAS + _MACHINE, '<key name="state" generator="alias"/>', ""),
        (_MACHINE, '<key name="state" generator="alias"/>', _ALIAS),
    ],
)
def test_alias_unknown_and_forward_names_fail_at_use(tmp_path, declarations, fields, tail):
    with pytest.raises(ValueError, match="Cannot create generator"):
        _run_xml(tmp_path, declarations, fields, tail=tail)


def test_duplicate_generator_declaration_keeps_first_registration(tmp_path):
    declarations = _MACHINE + _ALIAS + '<generator name="alias" generator="IntegerGenerator(min=7,max=7)"/>'
    rows = _run_xml(tmp_path, declarations, '<key name="state" generator="alias"/>', count=3)["rows"]
    assert [r["state"] for r in rows] == ["open", "closed", "open"]


def test_existing_machine_name_is_not_replaced_by_generator_declaration(tmp_path):
    declarations = _MACHINE + '<generator name="life" generator="IntegerGenerator(min=7,max=7)"/>'
    fields = '<key name="first" generator="life"/><key name="second" generator="life"/>'
    rows = _run_xml(tmp_path, declarations, fields, count=3)["rows"]
    assert [(r["first"], r["second"]) for r in rows] == [
        ("open", "open"), ("closed", "closed"), ("open", "open")
    ]


def test_later_machine_definition_replaces_alias_name(tmp_path):
    declarations = '<generator name="life" generator="IntegerGenerator(min=7,max=7)"/>' + _MACHINE
    rows = _run_xml(tmp_path, declarations, '<key name="state" generator="life"/>', count=3)["rows"]
    assert [r["state"] for r in rows] == ["open", "closed", "open"]


def test_builtin_generator_name_collision_stays_reserved(tmp_path):
    declarations = _MACHINE + '<generator name="IntegerGenerator" generator="life"/>'
    fields = '''<key name="state" generator="IntegerGenerator"/>
        <key name="scalar" generator="IntegerGenerator(min=7,max=7)"/>'''
    with pytest.raises(ValueError, match="reserved name"):
        _run_xml(tmp_path, declarations, fields, count=3)


def test_weighted_alias_seed_replays_across_pages(tmp_path):
    machine = '''<state-machine id="life" start="open">
        <transition from="open" to="paid" weight="0.6"/>
        <transition from="open" to="cancelled" weight="0.4"/>
        <transition from="paid" to="closed"/>
    </state-machine>'''
    fields = '<key name="state" generator="alias"/>'
    first = _run_xml(tmp_path, machine + _ALIAS, fields, count=80)
    assert first == _run_xml(tmp_path, machine + _ALIAS, fields, count=80, page_size=7)
    assert first != _run_xml(tmp_path, machine + _ALIAS, fields, count=80, seed=99)
    states = [row["state"] for row in first["rows"]]
    _assert_legal_walk(
        states, {"open": {"paid", "cancelled"}, "paid": {"closed"}},
        {"cancelled", "closed"}, "open", {"open", "paid", "cancelled", "closed"},
    )


def test_named_alias_continues_through_nested_parent_and_page_boundaries(tmp_path):
    fields = '''<generate name="children" count="3" pageSize="2" target="">
        <key name="state" generator="alias"/>
    </generate>'''
    captured = _run_xml(tmp_path, _MACHINE + _ALIAS, fields, count=3)
    assert [r["state"] for r in captured["children"]] == ["open", "closed"] * 4 + ["open"]


def test_named_global_increment_alias_initializes_declaration_scope(tmp_path):
    declarations = '''<generator name="counter" generator="GlobalIncrementGenerator"/>
        <generator name="second" generator="counter"/>'''
    fields = '''<key name="id" generator="counter"/>
        <variable name="next" generator="second"/>
        <key name="next_id" script="next"/>
        <generate name="children" count="2" pageSize="1" target="">
            <key name="id" generator="counter"/>
            <key name="direct" generator="GlobalIncrementGenerator"/>
        </generate>'''
    # Seeded/single-process on the common base: this declaration/lookup regression
    # must work independently of global-counter worker scheduling (#276).
    captured = _run_xml(tmp_path, declarations, fields, count=5)
    rows, children = captured["rows"], captured["children"]
    assert [row["id"] for row in rows] == [1, 5, 9, 13, 17]
    assert [row["next_id"] for row in rows] == [2, 6, 10, 14, 18]
    assert [row["id"] for row in children] == [3, 4, 7, 8, 11, 12, 15, 16, 19, 20]
    assert [row["direct"] for row in children] == list(range(1, 11))
    assert captured == _run_xml(tmp_path, declarations, fields, count=5, page_size=3)


def test_unseeded_named_alias_shares_one_walk_per_worker(tmp_path):
    import os

    markers = tmp_path / "workers"
    markers.mkdir()
    # Wait for both real workers to enter their chunks, so a fast first worker
    # cannot consume both tiny chunks before the second process has started.
    (tmp_path / "helpers.py").write_text(
        "def worker_pid():\n"
        "    import os, time\n"
        "    from pathlib import Path\n"
        f"    markers = Path({str(markers)!r})\n"
        "    (markers / str(os.getpid())).touch()\n"
        "    deadline = time.monotonic() + 15\n"
        "    while len(list(markers.iterdir())) < 2:\n"
        "        if time.monotonic() > deadline:\n"
        "            raise RuntimeError('second alias worker did not start')\n"
        "        time.sleep(0.01)\n"
        "    return os.getpid()\n"
    )
    machine = '<state-machine id="life" start="s0">' + "".join(
        f'<transition from="s{i}" to="s{i+1}"/>' for i in range(12)
    ) + '</state-machine>'
    descriptor = tmp_path / "worker_alias.xml"
    descriptor.write_text(
        '<setup multiprocessing="True" numProcess="2">'
        '<execute type="python" uri="helpers.py"/>' + machine + _ALIAS +
        '<generate name="rows" count="8" pageSize="2" mpPlatform="multiprocessing" target="">'
        '<key name="pid" script="worker_pid()"/>'
        '<key name="first" generator="alias"/>'
        '<variable name="next" generator="alias"/>'
        '<key name="second" script="next"/>'
        '<key name="direct" generator="life"/>'
        '</generate></setup>'
    )
    engine = DataMimicTest(test_dir=tmp_path, filename=descriptor.name, capture_test_result=True)
    engine.test_with_timer()
    rows = engine.capture_result()["rows"]
    pids = {row["pid"] for row in rows}
    assert len(pids) == 2
    assert os.getpid() not in pids
    for pid in pids:
        worker_rows = [row for row in rows if row["pid"] == pid]
        assert [(row["first"], row["second"]) for row in worker_rows] == [
            ("s0", "s1"), ("s2", "s3"), ("s4", "s5"), ("s6", "s7")
        ]
        assert [row["direct"] for row in worker_rows] == ["s0", "s1", "s2", "s3"]
