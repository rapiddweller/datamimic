# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Schema, parser and workspace boundaries of the DM JSON codec."""

import json
from pathlib import Path, PurePosixPath

import pytest

from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1


@pytest.fixture
def codec():
    return CeDmJsonCodec()


def test_schema_uses_ce_registry(codec):
    schema = codec.document_schema()
    nodes = schema["$defs"]["DmJsonNodeV1"]["discriminator"]["mapping"]
    assert "generate" in nodes and "echo" in nodes and "condition" in nodes
    assert "kafka" not in nodes and "redis" not in nodes
    assert (
        schema["$defs"]["DmJsonNode_GENERATE"]["properties"]["properties"]["oneOf"][0]["properties"]["traversal_limit"][
            "minimum"
        ]
        == 1
    )


def test_descriptor_relative_in_memory_parser(tmp_path):
    from datamimic_ce.engine.dsl.api import DescriptorParser

    descriptor = tmp_path / "logical.xml"
    seen = []

    def loader(path, environment):
        seen.append((path, environment))
        return {}

    xml = (
        '<setup><database id="db" dbms="postgresql"/><generate name="x" count="'
        '1"><key name="id" constant="1"/></generate></setup>'
    )
    descriptor.write_text(xml)
    file_result = DescriptorParser.parse(descriptor, {}, "development", profile_loader=loader)
    descriptor.unlink()
    inline_result = DescriptorParser.parse_xml(xml, descriptor, {}, "development", profile_loader=loader)
    assert type(inline_result) is type(file_result)
    assert seen == [(tmp_path, "local"), (tmp_path, "local")]
    assert not descriptor.exists()


def test_schema_accepts_canonical_document_and_rejects_bad_root(codec):
    from jsonschema import Draft202012Validator

    schema = codec.document_schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    document = codec.decompile('<setup><generate name="x" count="1"><key name="id" constant="1"/></generate></setup>')
    validator.validate(document.model_dump(mode="json"))
    assert list(
        validator.iter_errors({"version": "1", "root": {"kind": "key", "properties": {"name": "id", "constant": "1"}}})
    )


def test_workspace_validator_uses_logical_path_and_never_writes(tmp_path):
    from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
    from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext

    context = AuthoringWorkspaceContext(tmp_path, PurePosixPath("nested/logical.xml"))
    validator = CeDescriptorValidator(context, profile_loader=lambda path, environment: {})
    assert validator.validate('<setup><generate name="x" count="1"><key name="id" constant="1"/></generate></setup>').ok
    failed = validator.validate(
        '<setup><generate name="x" count="1"><key name="id" type="not-a-type"/></generate></setup>'
    )
    assert not failed.ok
    [parser] = [item for item in failed.diagnostics if item.ce_error is not None]
    assert "nested/logical.xml" in parser.path
    assert str(tmp_path) not in failed.model_dump_json()
    assert list(tmp_path.iterdir()) == []


def test_workspace_rechecks_symlink_containment(tmp_path, require_symlinks):
    from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
    from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext

    context = AuthoringWorkspaceContext(tmp_path, PurePosixPath("sub/logical.xml"))
    (tmp_path / "sub").symlink_to(tmp_path.parent, target_is_directory=True)
    validator = CeDescriptorValidator(context, profile_loader=lambda path, environment: {})
    assert not validator.validate("<setup/>").ok
    with pytest.raises(ValueError):
        context.resolve_descriptor_path(PurePosixPath("../outside.xml"))


def test_shared_frozen_ee_codec_goldens(codec):
    fixtures = json.loads((Path(__file__).parent / "fixtures" / "dm_json_codec_goldens.json").read_text())
    assert len(fixtures) == 5
    for name, golden in fixtures.items():
        document = DmJsonDocumentV1.model_validate(golden["document"])
        compiled = codec.compile(document)
        assert compiled.xml == golden["xml"], name
        assert compiled.document.model_dump(mode="json") == golden["document"], name
        assert codec.decompile(golden["xml"]).model_dump(mode="json") == golden["document"], name


def test_codec_compile_does_not_certify_parser_validity(tmp_path, codec):
    from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
    from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext

    document = codec.decompile('<setup><generate count="1"><key name="id" constant="1"/></generate></setup>')
    xml = codec.compile(document).xml
    validator = CeDescriptorValidator(AuthoringWorkspaceContext(tmp_path), profile_loader=lambda path, environment: {})
    assert not validator.validate(xml).ok


def test_parser_errors_carry_logical_descriptor_path(tmp_path):
    from datamimic_ce.engine.dsl.api import DescriptorParser
    from datamimic_ce.errors.base import ParserValidationError

    with pytest.raises(ParserValidationError) as error:
        DescriptorParser.parse_xml(
            '<setup><generate name="x" count="1"><key name="id" type="bad"/></generate></setup>',
            tmp_path / "not-written.xml",
            {},
            "development",
            profile_loader=lambda path, env: {},
            logical_descriptor_path="nested/project.xml",
        )
    assert error.value.location.descriptor_path == "nested/project.xml"
    assert error.value.validation_errors
