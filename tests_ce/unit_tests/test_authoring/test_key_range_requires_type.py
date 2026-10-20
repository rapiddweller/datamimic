# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""<key min/max/granularity> shape only a type= draw and are rejected elsewhere.

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
    ("fixture", "line"), [("fx_key_range_with_generator.xml", 4), ("fx_key_range_with_values.xml", 3)]
)
def test_lint_names_the_rule_and_exact_element(fixture: str, line: int) -> None:
    path = _FIXTURES / fixture
    workspace = AuthoringWorkspaceContext(path.parent, PurePosixPath(path.name))
    result = CeDescriptorValidator(workspace, profile_loader=workspace.load_connection_profile).validate(
        path.read_text(encoding="utf-8")
    )
    assert not result.ok
    companion = [item for item in result.diagnostics if item.code == "DM214"]
    assert companion and companion[0].path[2:] == ("/setup/generate/key", "line", line)


def test_engine_rejects_untyped_range_and_keeps_typed_range() -> None:
    with pytest.raises(ValidationError, match="apply only to a type= range draw"):
        KeyModel.model_validate({"name": "n", "generator": "IntegerGenerator", "min": "1", "max": "5"})
    assert KeyModel.model_validate({"name": "n", "type": "int", "min": "1", "max": "5"}).min == "1"
