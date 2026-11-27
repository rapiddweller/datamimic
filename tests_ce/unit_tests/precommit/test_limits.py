# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import pytest

from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
from datamimic_ce.authoring.domain.requests import BuildRequestV5
from datamimic_ce.authoring.projection.acceptance import project_acceptance


def test_condition_branches_all_count_into_the_declared_total() -> None:
    xml = (
        '<setup rngSeed="1"><generate name="p" count="6"><key name="id" generator="IncrementGenerator"/>'
        '<condition><if condition="id % 2 == 1"><generate name="c1" count="2"><key name="x" constant="1"/></generate>'
        '</if><else><generate name="c2" count="2"><key name="x" constant="1"/></generate></else></condition>'
        "</generate></setup>"
    )
    assert project_acceptance(BuildRequestV5(), CeDmJsonCodec().decompile(xml)).declared_rows == 30


def _source_parent(parent_count: int, grandchildren: str = "") -> str:
    return (
        '<setup rngSeed="1"><generate name="parents" source="rows.csv" distribution="ordered" '
        f'count="{parent_count}"><key name="id" script="int(this.id)"/>'
        f'<generate name="children" count="2"><key name="parent_id" script="parent.id"/>{grandchildren}</generate>'
        "</generate></setup>"
    )


@pytest.mark.parametrize(
    ("xml", "declared_rows"),
    [
        pytest.param(_source_parent(6), 18, id="source-parent-6-children-2"),
        pytest.param(
            _source_parent(3, '<generate name="grandchildren" count="2"><key name="x" constant="1"/></generate>'),
            21,
            id="two-levels-3-2-2",
        ),
        pytest.param(_source_parent(0), 0, id="source-parent-count-0"),
    ],
)
def test_source_free_children_of_a_source_parent_multiply_its_bound(xml: str, declared_rows: int) -> None:
    assert project_acceptance(BuildRequestV5(), CeDmJsonCodec().decompile(xml)).declared_rows == declared_rows
