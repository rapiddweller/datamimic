# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A product with count 0 ran and holds no rows; only a run that executed nothing is "not executed" (#734)."""

from pathlib import Path

import pytest

from datamimic_ce.authoring.domain.diagnostics import AuthoringSystemDiagnosticCode
from tests_ce.authoring_project import build_project

_ZERO = '<generate name="zero" count="0"><key name="x" constant="1"/></generate>'
_ONE = '<generate name="one" count="1"><key name="x" constant="1"/></generate>'


def _expect(product: str, count: int) -> dict[str, object]:
    return {"kind": "exact_count", "subject": {"kind": "product", "product": product}, "count": count}


def _build(tmp_path: Path, body: str, *expectations: dict[str, object]):
    return build_project(tmp_path, f'<setup rngSeed="1">{body}</setup>', version="5.0", expectations=list(expectations))


def _not_executed(result) -> bool:
    return any(item.code == AuthoringSystemDiagnosticCode.NOT_EXECUTED for item in result.diagnostics)


@pytest.mark.parametrize(
    ("body", "expectations"),
    [
        (_ZERO, [_expect("zero", 0)]),
        (_ZERO + _ONE, [_expect("zero", 0), _expect("one", 1)]),
        (_ONE, [_expect("one", 1)]),
    ],
    ids=["only_count_zero", "count_zero_and_one", "count_one"],
)
def test_a_run_with_a_captured_product_is_executed(tmp_path: Path, body: str, expectations: list[dict[str, object]]):
    result = _build(tmp_path, body, *expectations)
    assert result.outcome == "ready", result.diagnostics
    assert not _not_executed(result)


def test_a_failing_expectation_on_a_count_zero_product_is_not_reported_as_not_executed(tmp_path: Path):
    result = _build(tmp_path, _ZERO, _expect("zero", 1))
    assert result.outcome == "rejected"
    assert not _not_executed(result)


def test_a_setup_without_a_product_is_still_not_executed(tmp_path: Path):
    result = _build(tmp_path, "")
    assert result.outcome == "rejected"
    assert _not_executed(result)
