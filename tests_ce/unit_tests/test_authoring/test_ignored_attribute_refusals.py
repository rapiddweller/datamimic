# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""An attribute that the runtime of an element does not read is refused, not ignored (#465, #466, #468).

tests_ce/scenarios/s41_element_attributes, s26 and s27 prove the same refusals through Build."""

from pathlib import Path, PurePosixPath

import pytest
from pydantic import ValidationError

from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.engine.dsl.model.values.scalar.element_model import ElementModel
from datamimic_ce.engine.dsl.model.values.scalar.key_model import KeyModel
from datamimic_ce.engine.dsl.model.values.variables.variable_model import VariableModel
from datamimic_ce.engine.dsl.statements.values.scalar.key_statement import GeneratorArguments

_UNSUPPORTED = (
    "nullQuota and mimeType are not supported on an <element>. "
    "The element runtime does not read them and would ignore them without a message. Use a <key>."
)
_DISTRIBUTION = (
    "distribution is not supported on an <element>: it shapes a numeric range, and an element has no range. "
    "Use a <key>."
)
_RANGE = "min, max and granularity on an <element> need generator= as the only value source."
_LENGTH = "minLength and maxLength on an <element> need generator= as the only value source."
_KEY_MIME = '\'mimeType\' on a <key> needs type="binary" or generator="BinaryGenerator"'


def _lint_codes(tmp_path: Path, body: str) -> set[str]:
    path = tmp_path / "model.xml"
    body = f'<key name="parent" constant="p">{body}</key>' if body.startswith("<element") else body
    path.write_text(f'<setup rngSeed="1"><generate name="g" count="2">{body}</generate></setup>', encoding="utf-8")
    workspace = AuthoringWorkspaceContext(tmp_path, PurePosixPath(path.name))
    result = CeDescriptorValidator(workspace, profile_loader=workspace.load_connection_profile).validate(
        path.read_text(encoding="utf-8")
    )
    return {item.rule or item.code for item in result.diagnostics}


@pytest.mark.parametrize(
    ("attributes", "message"),
    [
        ({"values": "'a', 'b'", "nullQuota": "0.5"}, _UNSUPPORTED),
        ({"type": "binary", "mimeType": "image/png"}, _UNSUPPORTED),
        ({"type": "int", "distribution": "random", "min": "1", "max": "9"}, _DISTRIBUTION),
        ({"type": "int", "min": "1", "max": "9"}, _RANGE),
        ({"values": "1, 2", "granularity": "1"}, _RANGE),
        ({"generator": "IntegerGenerator", "type": "int", "min": "1"}, _RANGE),
        ({"values": "'a', 'b'", "minLength": "1"}, _LENGTH),
        ({"type": "string", "maxLength": "4"}, _LENGTH),
    ],
)
def test_element_refuses_attributes_it_ignores(attributes: dict[str, str], message: str) -> None:
    with pytest.raises(ValidationError, match=message.replace("(", r"\(").replace(")", r"\)")):
        ElementModel.model_validate({"name": "n", **attributes})


def test_element_keeps_weights_and_unique_on_values() -> None:
    model = ElementModel.model_validate({"name": "n", "values": "a, b", "weights": "0, 1", "unique": "false"})
    assert (model.weights, model.unique) == ("0, 1", False)
    assert ElementModel.model_validate({"name": "n", "values": "a, b", "unique": "true"}).unique is True


def test_element_keeps_generator_arguments() -> None:
    model = ElementModel.model_validate({"name": "n", "generator": "IntegerGenerator", "min": "1", "max": "9"})
    assert (model.min, model.max) == ("1", "9")


@pytest.mark.parametrize(
    ("body", "codes"),
    [
        ('<element name="e" values="1, 2" nullQuota="0.5"/>', {"DM218"}),
        ('<element name="e" type="binary" mimeType="image/png"/>', {"DM218"}),
        ('<element name="e" type="int" min="1" max="9" distribution="random"/>', {"DM218"}),
        ('<element name="e" type="int" min="1" max="9"/>', {"DM214"}),
        ('<element name="e" values="1, 2" minLength="1"/>', {"DM218"}),
        ('<variable name="v" generator="IntegerGenerator" min="1" max="9" distribution="random"/>', {"DM218"}),
        ('<variable name="v" generator="StringGenerator" mimeType="image/png"/>', {"DM103"}),
        ('<key name="k" values="1, 2" mimeType="image/png"/>', {"DM214"}),
        ('<key name="k" type="int" mimeType="image/png"/>', {"DM220"}),
        ('<key name="k" type="binary" script="\'hello\'" mimeType="image/png"/>', {"DM218"}),
        ('<key name="k" type="binary" constant="hello" mimeType="image/png"/>', {"DM218"}),
    ],
)
def test_lint_names_the_rule(tmp_path: Path, body: str, codes: set[str]) -> None:
    assert codes <= _lint_codes(tmp_path, body)


@pytest.mark.parametrize(
    "body",
    [
        '<element name="e" generator="IntegerGenerator" min="1" max="9"/>',
        '<element name="e" values="1, 2" weights="1, 1" unique="false"/>',
        '<element name="e" values="1, 2, 3" unique="true"/>',
        '<key name="k" type="binary" minLength="8" maxLength="8" mimeType="image/png"/>',
        '<key name="k" generator="BinaryGenerator" mimeType="image/png" minLength="8" maxLength="8"/>',
        '<variable name="v" source="x.csv" distribution="random"/>',
    ],
)
def test_lint_accepts_the_valid_form(tmp_path: Path, body: str) -> None:
    assert not _lint_codes(tmp_path, body) & {"DM214", "DM218", "DM220"}


def test_variable_refuses_distribution_beside_generator() -> None:
    with pytest.raises(ValidationError, match="'distribution' on a <variable> shapes a type= range"):
        VariableModel.model_validate({"name": "v", "generator": "IntegerGenerator", "distribution": "random"})


def test_variable_refuses_mime_type_as_unknown_attribute() -> None:
    with pytest.raises(ValidationError, match="invalid attribute 'mimeType'"):
        VariableModel.model_validate({"name": "v", "generator": "BinaryGenerator", "mimeType": "image/png"})


def test_variable_keeps_source_distribution() -> None:
    assert VariableModel.model_validate({"name": "v", "source": "x.csv", "distribution": "random"}).distribution


@pytest.mark.parametrize(
    "attributes",
    [{"values": "1, 2", "mimeType": "image/png"}, {"type": "int", "mimeType": "image/png"}],
)
def test_key_refuses_mime_type_without_binary(attributes: dict[str, str]) -> None:
    with pytest.raises(ValidationError, match='needs type="binary" or generator="BinaryGenerator"'):
        KeyModel.model_validate({"name": "k", **attributes})


@pytest.mark.parametrize(
    "attributes",
    [{"type": "binary", "mimeType": "image/png"}, {"generator": "BinaryGenerator", "mimeType": "image/png"}],
)
def test_key_keeps_mime_type_on_binary(attributes: dict[str, str]) -> None:
    assert KeyModel.model_validate({"name": "k", **attributes}).mime_type == "image/png"


def test_generator_arguments_write_the_mime_type() -> None:
    model = KeyModel.model_validate(
        {"name": "k", "generator": "BinaryGenerator", "mimeType": "image/png", "minLength": "8"}
    )
    assert GeneratorArguments.of(model).written() == [
        ("minLength", "min_len", "8"),
        ("mimeType", "mime_type", "image/png"),
    ]
