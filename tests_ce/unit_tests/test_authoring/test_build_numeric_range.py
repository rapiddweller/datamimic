# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Build range type checks use an inline descriptor because the acceptance error is the scenario."""

from datamimic_ce.authoring.domain.requests import RejectedBuild
from tests_ce.authoring_project import build_project


def test_build_rejects_range_expectations_on_text_values(tmp_path) -> None:
    result = build_project(
        tmp_path,
        '<setup rngSeed="1"><generate name="rows" count="1"><key name="age" constant="adult"/></generate></setup>',
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

    assert isinstance(result, RejectedBuild)
    [diagnostic] = result.diagnostics
    assert diagnostic.code == "range"
    assert diagnostic.path == ("expectations", 0)
    assert "product 'rows' field 'age'" in diagnostic.message
    assert "numeric captured values" in diagnostic.message
