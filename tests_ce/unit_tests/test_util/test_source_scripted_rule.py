# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from datamimic_ce.engine.dsl.api import SourceDistribution
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.tasks.sources import chunk_source_reader, nested
from datamimic_ce.engine.runtime.tasks.sources.chunk_source_reader import ChunkSourceReader

# (statement sourceScripted, setup defaultSourceScripted, effective rule)
RULE = [
    (True, None, True),
    (True, False, True),
    (False, True, False),
    (False, None, False),
    (None, True, True),
    (None, False, False),
    (None, None, False),
]


def _root(default: bool | None, **extra: object) -> SimpleNamespace:
    """A root whose source_scripted is the real SetupContext rule over the given setup default."""
    root = SimpleNamespace(_default_source_scripted=default, **extra)
    root.source_scripted = lambda explicit: SetupContext.source_scripted(root, explicit)  # type: ignore[arg-type]
    return root


@pytest.mark.parametrize(("explicit", "default", "expected"), RULE)
def test_statement_sourcescripted_wins_over_the_setup_default(explicit, default, expected) -> None:
    assert _root(default).source_scripted(explicit) is expected


@pytest.mark.parametrize(("explicit", "default", "expected"), RULE)
def test_chunk_reader_loads_with_the_shared_rule(monkeypatch, explicit, default, expected) -> None:
    root = _root(default, default_separator="|", stable_distribution_seed=Mock())
    stmt = SimpleNamespace(
        source="rows.ent.csv",
        source_script=explicit,
        separator=None,
        distribution=SourceDistribution.ORDERED,
        unique=False,
        full_name="rows",
        name="rows",
        cyclic=False,
        where=None,
        weight_column=None,
    )
    load = Mock(return_value=([{"id": 0}], True))
    monkeypatch.setattr(chunk_source_reader, "load_generate_source", load)

    ChunkSourceReader(SimpleNamespace(root=root), stmt, chunk_start=0, chunk_end=1).read_page(0, 1)

    assert load.call_args.args[4] is expected


@pytest.mark.parametrize(("explicit", "default", "expected"), RULE)
def test_nested_key_templates_with_the_shared_rule(monkeypatch, explicit, default, expected) -> None:
    root = _root(default, default_variable_prefix="[", default_variable_suffix="]")
    stmt = SimpleNamespace(
        source_script=explicit,
        variable_prefix=None,
        variable_suffix=None,
        distribution=SourceDistribution.ORDERED,
        cyclic=False,
        name="n",
    )
    template = Mock(return_value=[{"templated": True}])
    monkeypatch.setattr(nested, "evaluate_source_template", template)

    result = nested.finalize_nested_key_source(SimpleNamespace(root=root), stmt, [{"templated": False}])

    assert template.called is expected
    assert result == [{"templated": expected}]


@pytest.mark.parametrize(
    ("distribution", "unique", "expected"),
    [
        (SourceDistribution.RANDOM, False, True),
        (SourceDistribution.RANDOM, None, True),
        (SourceDistribution.CUMULATED, False, True),
        (SourceDistribution.ORDERED, False, False),
        (SourceDistribution.ORDERED, None, False),
        (SourceDistribution.ORDERED, True, True),
    ],
)
def test_whole_pool_is_distribution_or_unique(distribution, unique, expected) -> None:
    assert distribution.needs_whole_pool(unique) is expected


def test_chunk_reader_reads_an_ordered_unique_source_as_a_whole_pool(monkeypatch) -> None:
    root = _root(False, default_separator="|", stable_distribution_seed=Mock(return_value=1))
    stmt = SimpleNamespace(
        source="rows.ent.csv",
        source_script=None,
        separator=None,
        distribution=SourceDistribution.ORDERED,
        unique=True,
        full_name="rows",
        name="rows",
        cyclic=False,
        where=None,
        weight_column=None,
    )
    load = Mock(return_value=([{"id": 0}, {"id": 1}], True))
    monkeypatch.setattr(chunk_source_reader, "load_generate_source", load)

    ChunkSourceReader(SimpleNamespace(root=root), stmt, chunk_start=0, chunk_end=2).read_page(0, 1)

    assert load.call_args.args[5:8] == (None, None, None)
