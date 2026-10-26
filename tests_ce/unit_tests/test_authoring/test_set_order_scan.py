# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The static set-order scan behind DM319 and the forced replay (#425). Python-only because each row is one input
partition of a classifier; the DSL proof is tests_ce/scenarios/s17_set_hash_order (list(...) is rejected by the
replay with another hash seed, sorted(...) and a membership test stay ready)."""

import pytest

from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
from datamimic_ce.authoring.domain.script_semantics import ReplayCause, iterates_a_set, replay_causes

_SET_KEY = "<key name=\"flag\" script=\"list({'a', 'b'}).index('a')\"/>"
_SORTED_KEY = "<key name=\"flag\" script=\"sorted({'a', 'b'}).index('a')\"/>"


@pytest.mark.parametrize(
    "script",
    [
        "list({'a', 'b'})",
        "tuple({'a', 'b'})[0]",
        "[x for x in {'a', 'b'}]",
        "','.join({'a', 'b'})",
        "str({'a', 'b'})",
        "{'a', 'b'}",
        "list(set(['a', 'b']))",
        "list({x for x in 'ab'})",
        "list({'a'} | {'b'})",
        "list(frozenset({'a', 'b'}))",
    ],
)
def test_order_dependent_set_reads_are_found(script: str) -> None:
    assert iterates_a_set(script)


@pytest.mark.parametrize(
    "script",
    [
        "'a' in {'a', 'b'}",
        "'c' not in {'a', 'b'}",
        "sorted({'a', 'b'})",
        "len({'a', 'b'})",
        "max({'a', 'b'})",
        "{'a'} == {'a'}",
        "sorted({'a'} | {'b'})",
        "1 if {'a'} else 2",
        "not {'a'}",
        "['a', 'b']",
        "{'k': 1}",
        "(",
        "",
    ],
)
def test_order_free_and_set_free_scripts_are_not_found(script: str) -> None:
    assert not iterates_a_set(script)


def _causes(xml: str) -> tuple[ReplayCause, ...]:
    codec = CeDmJsonCodec()
    return replay_causes(codec.compile(codec.decompile(xml)).document)


@pytest.mark.parametrize(
    ("xml", "causes"),
    [
        (f'<setup rngSeed="7"><generate name="g" count="1">{_SET_KEY}</generate></setup>', (ReplayCause.SET_ORDER,)),
        (f'<setup rngSeed="7"><generate name="g" count="1">{_SORTED_KEY}</generate></setup>', ()),
        (f'<setup><generate name="g" count="1">{_SET_KEY}</generate></setup>', ()),
        (
            '<setup rngSeed="7"><execute type="python">x = 1</execute>'
            f'<generate name="g" count="1">{_SORTED_KEY}</generate></setup>',
            (ReplayCause.PYTHON_LIBRARY,),
        ),
        (
            '<setup rngSeed="7"><execute type="python">x = 1</execute>'
            f'<generate name="g" count="1">{_SET_KEY}</generate></setup>',
            (ReplayCause.PYTHON_LIBRARY, ReplayCause.SET_ORDER),
        ),
    ],
)
def test_replay_causes_name_why_a_seeded_model_must_replay(xml: str, causes: tuple[ReplayCause, ...]) -> None:
    assert _causes(xml) == causes
