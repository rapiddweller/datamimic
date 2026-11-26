# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Build derives its row limit from declared counts (#426). Each case is a DSL project; the boundaries are
parametrized here because the scenario runner holds one positive project per directory."""

from pathlib import Path

from datamimic_ce.authoring.domain.common import MAX_AUTHORING_MAX_COUNT
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId
from datamimic_ce.authoring.domain.requests import RejectedBuild
from datamimic_ce.errors import IssueCode
from tests_ce.authoring_project import build_project
from tests_ce.derived_limit_fixtures import _flat, _limits


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
    result = build_project(tmp_path, _flat(400, MAX_AUTHORING_MAX_COUNT - 399))

    assert isinstance(result, RejectedBuild)
    [diagnostic] = result.diagnostics
    limit = MAX_AUTHORING_MAX_COUNT
    assert (diagnostic.code, diagnostic.expected, diagnostic.actual) == (AuthoringRuleId.LIMIT, limit, limit + 1)
    assert f"at most {limit}" in str(diagnostic.remediation)


def test_explicit_max_count_with_a_total_above_the_ceiling_names_both_bounds(tmp_path: Path) -> None:
    """Following the remediation must lead to a Build that passes: max_count cannot go above the ceiling."""
    limit = MAX_AUTHORING_MAX_COUNT
    result = build_project(tmp_path, _flat(700, limit + 800), max_count=500)

    assert isinstance(result, RejectedBuild)
    [diagnostic] = result.diagnostics
    assert (diagnostic.code, diagnostic.expected, diagnostic.actual) == (AuthoringRuleId.LIMIT, 500, limit + 1500)
    assert diagnostic.path == ("acceptance/build.json", "max_count")
    assert diagnostic.message == (
        f"The products declare {limit + 1500} rows in total, above max_count 500 and above the Build ceiling of "
        f"{limit} rows."
    )
    assert diagnostic.remediation == (
        f"Reduce the counts so that all products together declare at most {limit} rows, and set max_count to at "
        f"least that total or remove it; max_count cannot go above {limit}."
    )


def _exact(product: str, count: int) -> dict[str, object]:
    return {"kind": "exact_count", "subject": {"kind": "product", "product": product}, "count": count}


def _with_source(tmp_path: Path, generated: int) -> str:
    (tmp_path / "rows.csv").write_text("id\n" + "".join(f"{row}\n" for row in range(1, 7)), encoding="utf-8")
    return (
        f'<setup rngSeed="1"><generate name="generated" count="{generated}">'
        '<key name="id" generator="IncrementGenerator"/></generate>'
        '<generate name="read" source="rows.csv" distribution="ordered"><key name="copy" script="id"/></generate>'
        "</setup>"
    )


def test_a_product_without_literal_count_keeps_the_default_limit(tmp_path: Path) -> None:
    result = build_project(tmp_path, _with_source(tmp_path, 4), expectations=[_exact("read", 6)])

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
        "Build derives max_count only when every product has a literal count or reads a memstore back from a "
        'literal producer. Otherwise add "max_count": <the rows of all products together> at the top level '
        'of acceptance/build.json, beside "expectations" (authoring run and dry-run take --max-count). A higher '
        'value is safe, up to the Build ceiling: if you do not know the total, set "max_count": 2000. Or reduce '
        "the rows."
    )


def test_file_source_with_a_literal_count_counts_into_the_derived_limit(tmp_path: Path) -> None:
    (tmp_path / "rows.csv").write_text("id\n" + "".join(f"{row}\n" for row in range(1, 7)), encoding="utf-8")
    xml = (
        '<setup rngSeed="1"><generate name="generated" count="8"><key name="id" generator="IncrementGenerator"/>'
        '</generate><generate name="read" source="rows.csv" distribution="ordered" count="6">'
        '<key name="copy" script="id"/></generate></setup>'
    )

    result = build_project(tmp_path, xml, expectations=[_exact("generated", 8), _exact("read", 6)])

    assert result.outcome == "ready", result.diagnostics
    assert set(_limits(result).values()) == {14}
