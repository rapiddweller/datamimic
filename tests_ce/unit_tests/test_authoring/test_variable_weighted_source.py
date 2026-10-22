"""Weighted scalar variables preserve casting, weights and seeded replay."""

import pytest

from datamimic_ce.authoring.domain.requests import ReadyBuild
from datamimic_ce.errors import IssueCode
from tests_ce.authoring_project import build_project


@pytest.mark.parametrize(
    ("value_type", "contents", "expected", "scripted"),
    [
        ("int", "0|0\n7|1\n9|3\n", {7, 9}, False),
        ("string", "000|0\n007|1\n009|3\n", {"007", "009"}, False),
        ("int", "{2 + 5}|1\n", {7}, True),
    ],
)
def test_scalar_weighted_variable_builds_with_casting_and_replay(tmp_path, value_type, contents, expected, scripted):
    (tmp_path / "choices.wgt.csv").write_text(contents, encoding="utf-8")
    result = build_project(
        tmp_path,
        f'<setup rngSeed="7"><generate name="rows" count="32">'
        f'<variable name="choice" type="{value_type}" source="choices.wgt.csv" sourceScripted="{scripted}"/>'
        '<key name="value" script="choice"/></generate></setup>',
        max_count=32,
        sample_rows=32,
        expectations=[
            {"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": 32},
            {
                "kind": "allowed_values",
                "subject": {"kind": "product", "product": "rows"},
                "field": "value",
                "values": sorted(expected),
            },
        ],
        verification={"deterministic_replay": True},
    )
    assert isinstance(result, ReadyBuild), result
    assert {row["value"] for row in result.evidence[0].rows} == expected
    assert result.evidence[0].capture.complete
    assert result.verification.deterministic_replay.status == "passed"


@pytest.mark.parametrize("flags", ['unique="true"', 'storage="data"', 'distribution="ordered"'])
def test_scalar_weighted_source_does_not_silently_ignore_pool_options(tmp_path, flags):
    (tmp_path / "choices.wgt.csv").write_text("7|1\n9|3\n", encoding="utf-8")
    result = build_project(
        tmp_path,
        f'<setup rngSeed="7"><generate name="rows" count="4">'
        f'<variable name="choice" type="int" source="choices.wgt.csv" {flags}/>'
        '<key name="value" script="choice"/></generate></setup>',
    )
    assert result.outcome == "rejected", result
    assert any(
        diagnostic.ce_error is not None and diagnostic.ce_error.issue_code is IssueCode.TASK_VARIABLE_SOURCE_UNSUPPORTED
        for diagnostic in result.diagnostics
    ), result
