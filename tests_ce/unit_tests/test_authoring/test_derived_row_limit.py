# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Build derives its row limit from the declared counts (#426). Each case is a DSL project; the boundaries are
parametrized here because the scenario runner holds one positive project per directory."""

from pathlib import Path

import pytest

from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId
from datamimic_ce.authoring.domain.requests import RejectedBuild
from datamimic_ce.errors import IssueCode
from tests_ce.authoring_project import build_project


def _flat(*counts: int) -> str:
    products = "".join(
        f'<generate name="p{index}" count="{count}"><key name="id" generator="IncrementGenerator"/></generate>'
        for index, count in enumerate(counts)
    )
    return f'<setup rngSeed="1">{products}</setup>'


def _limits(result: object) -> dict[str, int]:
    return {item.name: item.capture.limit for item in result.evidence}  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("counts", "limit"),
    [
        pytest.param((2, 2), 10, id="total-below-default-keeps-default"),
        pytest.param((5, 8, 12), 25, id="three-products-25-rows"),
        pytest.param((0, 4), 10, id="zero-count-product"),
        pytest.param((400, 600), 1000, id="total-at-ceiling"),
    ],
)
def test_omitted_max_count_derives_the_limit_from_literal_counts(
    tmp_path: Path, counts: tuple[int, ...], limit: int
) -> None:
    result = build_project(tmp_path, _flat(*counts))

    assert result.outcome == "ready", result.diagnostics
    assert set(_limits(result).values()) == {limit}


def test_nested_counts_multiply_into_the_derived_limit(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><generate name="parents" count="5"><key name="id" generator="IncrementGenerator"/>'
        '<generate name="children" count="3"><key name="parent_id" script="parent.id"/></generate>'
        "</generate></setup>"
    )

    result = build_project(tmp_path, xml)

    assert result.outcome == "ready", result.diagnostics
    assert _limits(result) == {"parents": 20, "children": 20}


def test_time_series_ticks_count_into_the_derived_limit(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><generate name="readings" count="2" start="2026-01-01T00:00:00" '
        'end="2026-01-01T06:00:00" interval="PT1H"><key name="value" type="int" min="1" max="9"/></generate></setup>'
    )

    result = build_project(tmp_path, xml)

    assert result.outcome == "ready", result.diagnostics
    assert _limits(result) == {"readings": 12}


def test_declared_total_above_the_ceiling_is_rejected_before_execution(tmp_path: Path) -> None:
    result = build_project(tmp_path, _flat(400, 601))

    assert isinstance(result, RejectedBuild)
    [diagnostic] = result.diagnostics
    assert (diagnostic.code, diagnostic.expected, diagnostic.actual) == (AuthoringRuleId.LIMIT, 1000, 1001)
    assert "at most 1000" in str(diagnostic.remediation)


def test_explicit_max_count_with_a_total_above_the_ceiling_names_both_bounds(tmp_path: Path) -> None:
    """Following the remediation must lead to a Build that passes: max_count cannot go above 1000."""
    result = build_project(tmp_path, _flat(700, 800), max_count=500)

    assert isinstance(result, RejectedBuild)
    [diagnostic] = result.diagnostics
    assert (diagnostic.code, diagnostic.expected, diagnostic.actual) == (AuthoringRuleId.LIMIT, 500, 1500)
    assert diagnostic.path == ("acceptance/build.json", "max_count")
    assert diagnostic.message == (
        "The products declare 1500 rows in total, above max_count 500 and above the Build ceiling of 1000 rows."
    )
    assert diagnostic.remediation == (
        "Reduce the counts so that all products together declare at most 1000 rows, and set max_count to at least "
        "that total or remove it; max_count cannot go above 1000."
    )


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


def _with_source(tmp_path: Path, generated: int) -> str:
    (tmp_path / "rows.csv").write_text("id\n" + "".join(f"{row}\n" for row in range(1, 7)), encoding="utf-8")
    return (
        f'<setup rngSeed="1"><generate name="generated" count="{generated}">'
        '<key name="id" generator="IncrementGenerator"/></generate>'
        '<generate name="read" source="rows.csv" distribution="ordered"><key name="copy" script="id"/></generate>'
        "</setup>"
    )


def test_a_product_without_literal_count_keeps_the_default_limit(tmp_path: Path) -> None:
    result = build_project(tmp_path, _with_source(tmp_path, 4))

    assert result.outcome == "ready", result.diagnostics
    assert set(_limits(result).values()) == {10}


def test_runtime_total_overrun_names_the_limit_without_capture_noise(tmp_path: Path) -> None:
    result = build_project(tmp_path, _with_source(tmp_path, 5))

    assert isinstance(result, RejectedBuild)
    [diagnostic] = result.diagnostics
    assert diagnostic.ce_error is not None
    assert diagnostic.ce_error.issue_code is IssueCode.TASK_TOTAL_ROW_BUDGET_EXCEEDED
    assert diagnostic.expected == 10
    assert "all products together" in diagnostic.message
    # No number is known here, so the remediation names which total to count and why Build could not derive it.
    assert diagnostic.remediation == (
        "Build derives max_count only when every product has a literal count or reads a memstore back. "
        "Set max_count to the rows of all products together, or reduce the rows."
    )


_READBACK_ROLES = (
    {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
    {
        "product": "readback",
        "field": "id",
        "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
    },
)


def _memstore(produced: int, readback_count: str = "") -> str:
    producer = (
        f'<generate name="parents" count="{produced}" target="mem"><key name="id" generator="IncrementGenerator"/>'
        "</generate>"
    )
    readback = (
        f'<generate name="readback" source="mem" type="parents" distribution="ordered"{readback_count}>'
        '<key name="id" script="this.id"/></generate>'
    )
    return f'<setup rngSeed="7"><memstore id="mem"/>{producer}{readback}</setup>'


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


def test_file_source_with_a_literal_count_counts_into_the_derived_limit(tmp_path: Path) -> None:
    (tmp_path / "rows.csv").write_text("id\n" + "".join(f"{row}\n" for row in range(1, 7)), encoding="utf-8")
    xml = (
        '<setup rngSeed="1"><generate name="generated" count="8"><key name="id" generator="IncrementGenerator"/>'
        '</generate><generate name="read" source="rows.csv" distribution="ordered" count="6">'
        '<key name="copy" script="id"/></generate></setup>'
    )

    result = build_project(tmp_path, xml)

    assert result.outcome == "ready", result.diagnostics
    assert set(_limits(result).values()) == {14}


def test_condition_branches_all_count_into_the_declared_total() -> None:
    """Build counts every <condition> branch in full: 6 + 6x2 + 6x2 = 30, while a run makes 18 rows. A limit that is
    too high is safe; one that is too low would refuse a valid project."""
    from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
    from datamimic_ce.authoring.domain.requests import BuildRequestV5
    from datamimic_ce.authoring.projection.acceptance import project_acceptance

    xml = (
        '<setup rngSeed="1"><generate name="p" count="6"><key name="id" generator="IncrementGenerator"/>'
        '<condition><if condition="id % 2 == 1"><generate name="c1" count="2"><key name="x" constant="1"/></generate>'
        '</if><else><generate name="c2" count="2"><key name="x" constant="1"/></generate></else></condition>'
        "</generate></setup>"
    )

    spec = project_acceptance(BuildRequestV5(), CeDmJsonCodec().decompile(xml))

    assert spec.declared_rows == 30


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
