# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

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
    assert node.children[0].kind == "id", "<id> marks a createTable primary key, so its spelling survives"
    assert node.properties["traversal_count"] == 0
    assert node.comment == "rows"
    compiled = codec.compile(document)
    assert compiled.xml == (
        '<!--root-->\n<setup rngSeed="7">\n    <!--rows-->\n    <generate name="ro'
        'ws" source="in.csv" count="0">\n        <id name="id" constant="1"/>\n '
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


def test_registered_but_invalid_child_has_exact_path(codec):
    with pytest.raises(DmJsonCodecError) as error:
        codec.decompile('<setup><key name="id" constant="1"/></setup>')
    assert error.value.path == ("root", "children", 0, "kind")


@pytest.mark.parametrize(
    "declaration", ["", '<?xml version="1.0" encoding="UTF-8"?>', '<?xml version="1.0" encoding="ISO-8859-1"?>']
)
def test_decompile_preserves_already_decoded_unicode(codec, declaration):
    document = codec.decompile(declaration + "<setup><echo>café</echo></setup>")

    assert document.root.children[0].content.value == "café"
    assert "café" in codec.compile(document).xml
