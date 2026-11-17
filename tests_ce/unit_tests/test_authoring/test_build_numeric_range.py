# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Range expectations distinguish numeric captures from numeric-looking CSV text."""

from pathlib import Path

import pytest

from datamimic_ce.authoring.domain.requests import RejectedBuild
from tests_ce.authoring_project import build_project


# Numeric-looking text must be distinguished from numeric values; the second case proves the authored cast.
@pytest.mark.parametrize(
    ("value", "cast", "rejected", "message"),
    [
        ("42", "", True, "are not numbers; range requires numeric captured values"),
        ("42", "int(", False, None),
        ("142", "int(", True, "are outside the range"),
        ("adult", "", True, "are not numbers; range requires numeric captured values"),
    ],
)
def test_build_range_requires_numeric_captured_values(
    tmp_path: Path, value: str, cast: str, rejected: bool, message: str | None
) -> None:
    data = tmp_path / "ages.csv"
    data.write_text(f"age\n{value}\n", encoding="utf-8")
    expression = f"{cast}row.age)" if cast else "row.age"
    result = build_project(
        tmp_path,
        '<setup rngSeed="1"><generate name="rows" count="1">'
        '<variable name="row" source="ages.csv" distribution="ordered"/>'
        f'<key name="age" script="{expression}"/>'
        "</generate></setup>",
        expectations=[
            {
                "kind": "range",
                "subject": {"kind": "product", "product": "rows"},
                "field": "age",
                "minimum": 1,
                "maximum": 100,
            }
        ],
    )

    assert isinstance(result, RejectedBuild) is rejected
    if rejected:
        [diagnostic] = result.diagnostics
        assert diagnostic.code == "range"
        assert "product 'rows'" in diagnostic.message and "values for 'age'" in diagnostic.message
        assert message in diagnostic.message
    else:
        assert result.outcome == "ready"
