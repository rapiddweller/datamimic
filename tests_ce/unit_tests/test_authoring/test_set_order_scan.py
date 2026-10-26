# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The static set-order scan behind DM319 and the replay causes (#425). Python-only because each row is one input
partition of a classifier, and the mutant needs to change the replay hash seeds. The DSL proof is
tests_ce/scenarios/s17_set_hash_order: its negatives are rejected by the replay under other hash seeds, sorted(...)
and a membership test stay ready."""

import shutil
from pathlib import Path

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
from datamimic_ce.authoring.domain.proof import VerificationGateStatus
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, BuildResult, ReadyBuild, RejectedBuild
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
        "sorted({'a', 'bb'}, key=len)[0]",
        "min({'a', 'bb'}, key=len)",
        "list({'a': 1}.keys() - {'b': 2}.keys())[0]",
        "list({'a': 1}.items() | {'b': 2}.items())",
        "list(list({'a', 'b'}))",
        "list({None, 1})",
        "list({1, 'a'})",
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
        "bool({'a'} & {'b'})",
        "bool(set(x) & set(y))",
        "{'a', 'b'}.issubset(x)",
        "{'a'}.isdisjoint(x)",
        "x.issuperset({'a', 'b'})",
        "len(list(set(x)))",
        "len(tuple({'a', 'b'}))",
        "sorted(list({'a', 'b'}))",
        "list(set([3, 1, 2]))",
        "list({3, 1.5, True})",
        "sorted({'a', 'bb'})",
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
        (f'<setup rngSeed="7"><generate name="g" count="1">{_SORTED_KEY}</generate></setup>', (ReplayCause.OTHER,)),
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


_S17 = Path(__file__).resolve().parents[2] / "scenarios" / "s17_set_hash_order"
_SET_ORDER_NEGATIVES = ("set_order", "two_element_set", "sorted_key_tie", "dict_view_difference")


def _build_negative(name: str, tmp_path: Path) -> BuildResult:
    project = tmp_path / name
    shutil.copytree(_S17, project)
    shutil.copytree(_S17 / "negative" / name, project, dirs_exist_ok=True)
    return create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()


@pytest.mark.parametrize("name", _SET_ORDER_NEGATIVES)
def test_the_replay_under_other_hash_seeds_rejects_each_s17_negative_and_names_a_cause(
    name: str, tmp_path: Path
) -> None:
    built = _build_negative(name, tmp_path)
    assert isinstance(built, RejectedBuild)
    assert built.verification.deterministic_replay.status is VerificationGateStatus.FAILED
    assert ReplayCause.SET_ORDER.failure_message() in [item.message for item in built.diagnostics]


@pytest.mark.parametrize("name", _SET_ORDER_NEGATIVES)
def test_mutant_replays_under_the_first_hash_seed_accept_each_s17_negative(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The negative control: with the first run's hash seed in every replay, nothing tells the runs apart, so
    each rejection above comes from the hash seed change and not from acceptance."""
    from datamimic_ce.authoring.application import build

    monkeypatch.setattr(build, "_REPLAY_HASH_SEEDS", (build._FIRST_RUN_HASH_SEED,) * len(build._REPLAY_HASH_SEEDS))
    assert isinstance(_build_negative(name, tmp_path), ReadyBuild)
