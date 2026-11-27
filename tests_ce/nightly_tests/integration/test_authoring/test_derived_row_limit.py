# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from pathlib import Path

import pytest

from datamimic_ce.authoring.domain.common import MAX_AUTHORING_MAX_COUNT
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId
from datamimic_ce.authoring.domain.requests import RejectedBuild
from tests_ce.authoring_project import build_project
from tests_ce.derived_limit_fixtures import _READBACK_ROLES, _flat, _limits, _memstore


@pytest.mark.parametrize(
    ("counts", "limit"),
    [
        pytest.param((2, 2), 10, id="total-below-default-keeps-default"),
        pytest.param((5, 8, 12), 25, id="three-products-25-rows"),
        pytest.param((0, 4), 10, id="zero-count-product"),
        pytest.param((400, MAX_AUTHORING_MAX_COUNT - 400), MAX_AUTHORING_MAX_COUNT, id="total-at-ceiling"),
    ],
)
def test_omitted_max_count_derives_the_limit_from_literal_counts(
    tmp_path: Path, counts: tuple[int, ...], limit: int
) -> None:
    result = build_project(tmp_path, _flat(*counts))

    assert result.outcome == "ready", result.diagnostics
    assert set(_limits(result).values()) == {limit}


@pytest.mark.parametrize(
    ("max_count", "outcome"),
    [
        pytest.param(24, "rejected", id="total-minus-one"),
        pytest.param(25, "ready", id="total"),
        pytest.param(26, "ready", id="total-plus-one"),
    ],
)
def test_explicit_max_count_is_checked_against_the_declared_total(tmp_path: Path, max_count: int, outcome: str) -> None:
    result = build_project(tmp_path, _flat(5, 8, 12), max_count=max_count)

    assert result.outcome == outcome, result.diagnostics
    if isinstance(result, RejectedBuild):
        [diagnostic] = result.diagnostics
        assert (diagnostic.code, diagnostic.expected, diagnostic.actual) == (AuthoringRuleId.LIMIT, 24, 25)
        assert diagnostic.path == ("acceptance/build.json", "max_count")
        assert "Set max_count to at least 25" in str(diagnostic.remediation)
    else:
        assert set(_limits(result).values()) == {max_count}


@pytest.mark.parametrize(
    ("xml", "limit"),
    [
        pytest.param(_memstore(6), 12, id="readback-without-count-reads-the-producer-rows"),
        pytest.param(_memstore(7, ' count="9"'), 16, id="readback-literal-count-bounds-its-rows"),
    ],
)
def test_memstore_readback_counts_into_the_derived_limit(tmp_path: Path, xml: str, limit: int) -> None:
    result = build_project(tmp_path, xml, product_roles=_READBACK_ROLES)

    assert result.outcome == "ready", result.diagnostics
    assert set(_limits(result).values()) == {limit}


@pytest.mark.parametrize(
    ("readback_count", "limit"),
    [
        pytest.param("", 10, id="readback-without-count-of-a-source-producer-is-unknown"),
        pytest.param(' count="8"', 16, id="readback-literal-count-still-bounds-it"),
    ],
)
def test_memstore_producer_with_a_source_bounds_only_by_literal_counts(
    tmp_path: Path, readback_count: str, limit: int
) -> None:
    """The producer reads 3 file rows under count 8: its rows are not known, only bounded by its count."""
    (tmp_path / "rows.csv").write_text("id\n1\n2\n3\n", encoding="utf-8")
    xml = (
        '<setup rngSeed="7" defaultSeparator=","><memstore id="mem"/>'
        '<generate name="parents" source="rows.csv" distribution="ordered" count="8" target="mem">'
        '<key name="id" script="int(this.id)"/></generate>'
        f'<generate name="readback" source="mem" type="parents" distribution="ordered"{readback_count}>'
        '<key name="id" script="this.id"/></generate></setup>'
    )

    result = build_project(tmp_path, xml, product_roles=_READBACK_ROLES)

    assert result.outcome == "ready", result.diagnostics
    assert set(_limits(result).values()) == {limit}
