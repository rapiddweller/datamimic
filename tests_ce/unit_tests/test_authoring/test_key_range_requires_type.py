# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""<key min/max/granularity> shape only a type= draw and need type= as the only value source.

Next to generator= or values= they were silently ignored: a seeded DateTimeGenerator
then produced one constant date for every row while lint and Build reported ready."""

from pathlib import Path, PurePosixPath

import pytest
from pydantic import ValidationError

from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.engine.dsl.model.values.scalar.key_model import KeyModel

_FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("fixture", "rule", "line"),
    [
        ("fx_key_range_with_generator.xml", "DM214", 4),
        ("fx_key_range_with_values.xml", "DM214", 3),
        ("fx_key_range_with_typed_generator.xml", "DM218", 4),
    ],
)
def test_lint_names_the_rule_and_exact_element(fixture: str, rule: str, line: int) -> None:
    path = _FIXTURES / fixture
    workspace = AuthoringWorkspaceContext(path.parent, PurePosixPath(path.name))
    result = CeDescriptorValidator(workspace, profile_loader=workspace.load_connection_profile).validate(
        path.read_text(encoding="utf-8")
    )
    assert not result.ok
    named = [item for item in result.diagnostics if item.code == rule]
    assert named and named[0].path[2:] == ("/setup/generate/key", "line", line)


@pytest.mark.parametrize(
    "attributes",
    [
        {"generator": "IntegerGenerator", "min": "1", "max": "5"},
        {"type": "int", "generator": "IncrementGenerator", "min": "1", "max": "5"},
    ],
)
def test_engine_rejects_range_that_is_not_the_only_value_source(attributes: dict[str, str]) -> None:
    with pytest.raises(ValidationError, match="apply only when type= is its only value source"):
        KeyModel.model_validate({"name": "n", **attributes})


def test_engine_keeps_typed_range() -> None:
    assert KeyModel.model_validate({"name": "n", "type": "int", "min": "1", "max": "5"}).min == "1"
