"""Lossless CE grammar projection, independent of runtime execution."""

import json

import pytest
from pydantic import ValidationError

from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
from datamimic_ce.authoring.domain.dm_json import DmJsonCodecError, DmJsonDocumentV1, DmJsonNodeV1


@pytest.fixture
def codec():
    return CeDmJsonCodec()


def test_canonical_alias_scalar_order_and_comments(codec):
    xml = (
        '<!-- root --><setup rngSeed="7"><!-- rows --><iterate source="in.csv" '
        'count="0" name="rows"><id constant="1" name="id"/></iterate></setup>'
    )
    document = codec.decompile(xml)
    node = document.root.children[0]
    assert node.kind == "generate"
    assert node.properties["traversal_count"] == 0
    assert node.comment == "rows"
    compiled = codec.compile(document)
    assert compiled.xml == (
        '<!--root-->\n<setup rngSeed="7">\n    <!--rows-->\n    <generate name="ro'
        'ws" source="in.csv" count="0">\n        <key name="id" constant="1"/>\n '
        "   </generate>\n</setup>"
    )
    assert codec.compile(codec.decompile(compiled.xml)) == compiled
    assert "comment" not in document.root.children[0].children[0].model_dump(mode="json")
    assert "comment" not in json.loads(document.model_dump_json())["root"]["children"][0]["children"][0]


@pytest.mark.parametrize(
    "body, kind, value",
    [
        ("<echo/>", None, None),
        ("<echo> hi </echo>", "text", " hi "),
        ('<execute uri="x.py"/>', "uri", "x.py"),
        ('<execute type="python" script="code"/>', "script", "code"),
        ("<execute>print(1)</execute>", "inline", "print(1)"),
    ],
)
def test_content_modes(codec, body, kind, value):
    document = codec.decompile("<setup>" + body + "</setup>")
    content = document.root.children[0].content
    assert (content.kind.value if content else None) == kind
    assert (content.value if content else None) == value
    assert codec.decompile(codec.compile(document).xml) == document


@pytest.mark.parametrize(
    "xml,path",
    [
        ('<!DOCTYPE setup [<!ENTITY x "x">]><setup/>', ("xml",)),
        ('<!DOCTYPE setup SYSTEM "http://invalid/test"><setup/>', ("xml",)),
        ("<setup><?test lost?></setup>", ("root",)),
        ("<setup><echo>before<echo/>after</echo></setup>", ("root", "children", 0)),
        ('<setup><echo bad="1"/></setup>', ("root", "children", 0, "properties", "bad")),
        ("<setup><unknown/></setup>", ("root", "children", 0, "kind")),
        ('<setup><execute uri="a.py">print(1)</execute></setup>', ("root", "children", 0, "content")),
        ("<setup><!-- trailing --></setup>", ("root", "children")),
        ('<setup defaultLocale="en" default_locale="de"/>', ("root", "properties", "default_locale")),
    ],
)
def test_rejects_lost_semantics_at_exact_paths(codec, xml, path):
    with pytest.raises(DmJsonCodecError) as error:
        codec.decompile(xml)
    assert error.value.path == path


def test_properties_and_constraints(codec):
    with pytest.raises(DmJsonCodecError):
        codec.decompile(
            '<setup><generate name="x" count="1"><key name="id" constant="x" values="a,b"/></generate></setup>'
        )
    with pytest.raises(DmJsonCodecError):
        codec.decompile('<setup><generate name="x" count="1" offset="-1" source="x.csv"/></setup>')
    with pytest.raises(DmJsonCodecError):
        codec.decompile('<setup><generate name="x" source="x.csv" maxCount="0"/></setup>')


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


def test_transport_root_and_non_finite_rejected():
    with pytest.raises(ValidationError):
        DmJsonDocumentV1(root=DmJsonNodeV1(kind="key"))
    with pytest.raises(ValidationError):
        DmJsonNodeV1(kind="key", properties={"constant": float("nan")})


@pytest.mark.parametrize("text", [" ", "\n ", "  hi  "])
def test_echo_whitespace_is_semantic(codec, text):
    document = codec.decompile("<setup><echo>" + text + "</echo></setup>")
    assert document.root.children[0].content.value == text
    assert codec.decompile(codec.compile(document).xml) == document


def test_duplicate_containers_and_alias_constraints(codec):
    for xml in (
        '<setup><include uri="part.xml"><setup/><setup/></include></setup>',
        '<setup><iterate name="x" count="1"/></setup>',
    ):
        with pytest.raises(DmJsonCodecError):
            codec.decompile(xml)


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


def test_invalid_xml_characters_have_typed_property_path(codec):
    document = DmJsonDocumentV1(root=DmJsonNodeV1(kind="setup", properties={"default_locale": "bad\x00"}))
    with pytest.raises(DmJsonCodecError) as error:
        codec.compile(document)
    assert error.value.path == ("root", "properties", "default_locale")


def test_count_free_timeseries_is_lossless(codec):
    document = codec.decompile(
        '<setup><generate name="ticks" start="2025-01-01T00:00:00" end="2025-01'
        '-02T00:00:00" interval="PT1H"><key name="time" script="ts.now"/></gene'
        "rate></setup>"
    )
    assert "count" not in document.root.children[0].properties
    assert "count=" not in codec.compile(document).xml


def test_workspace_validator_uses_logical_path_and_never_writes(tmp_path):
    from pathlib import PurePosixPath

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


def test_workspace_rechecks_symlink_containment(tmp_path):
    from pathlib import PurePosixPath

    from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
    from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext

    context = AuthoringWorkspaceContext(tmp_path, PurePosixPath("sub/logical.xml"))
    (tmp_path / "sub").symlink_to(tmp_path.parent, target_is_directory=True)
    validator = CeDescriptorValidator(context, profile_loader=lambda path, environment: {})
    assert not validator.validate("<setup/>").ok
    with pytest.raises(ValueError):
        context.resolve_descriptor_path(PurePosixPath("../outside.xml"))


def test_shared_frozen_ee_codec_goldens(codec):
    from pathlib import Path

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


def test_registered_but_invalid_child_has_exact_path(codec):
    with pytest.raises(DmJsonCodecError) as error:
        codec.decompile('<setup><key name="id" constant="1"/></setup>')
    assert error.value.path == ("root", "children", 0, "kind")


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


@pytest.mark.parametrize(
    "declaration", ["", '<?xml version="1.0" encoding="UTF-8"?>', '<?xml version="1.0" encoding="ISO-8859-1"?>']
)
def test_decompile_preserves_already_decoded_unicode(codec, declaration):
    document = codec.decompile(declaration + "<setup><echo>café</echo></setup>")

    assert document.root.children[0].content.value == "café"
    assert "café" in codec.compile(document).xml
