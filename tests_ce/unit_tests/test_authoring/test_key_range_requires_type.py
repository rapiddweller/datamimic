# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""<key min/max/granularity> are accepted only where a type= range draw or a generator= consumes them.

Next to values= they would be silently ignored. Next to generator= they are the generator's arguments
(#456); tests_ce/scenarios/s26_key_generator_attributes proves that form and its refusals."""

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
        ("fx_key_range_with_values.xml", "DM214", 3),
        ("fx_key_range_with_values.xml", "DM218", 3),
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
    ("attributes", "reason"),
    [
        ({"values": "1, 2", "min": "1", "max": "5"}, "apply to type= or generator= only"),
        ({"generator": "IntegerGenerator", "min": "1", "distribution": "cumulated"}, "write it in the call"),
        ({"type": "string", "min": "1", "max": "5"}, "requires type='int', 'float', or 'decimal', not 'string'"),
        ({"type": "float", "granularity": "0.5"}, "'granularity' on a <key> needs a range"),
        ({"type": "int", "min": "1", "max": "9", "granularity": "2"}, "requires type='float' or 'decimal'"),
    ],
)
def test_engine_rejects_range_attributes_no_draw_consumes(attributes: dict[str, str], reason: str) -> None:
    with pytest.raises(ValidationError, match=reason):
        KeyModel.model_validate({"name": "n", **attributes})


def test_engine_keeps_typed_range() -> None:
    assert KeyModel.model_validate({"name": "n", "type": "int", "min": "1", "max": "5"}).min == "1"
    assert KeyModel.model_validate({"name": "n", "type": "decimal", "min": "0", "granularity": "0.01"}).granularity
