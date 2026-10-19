"""Security contracts shared by runtime and authoring XML ingestion."""

from pathlib import Path

import pytest

from datamimic_ce.authoring.adapters.xml_loader import RULE_XML_LOAD, load_source
from datamimic_ce.engine.dsl.parsers.document.descriptor_parser import DescriptorParser
from datamimic_ce.engine.dsl.parsers.input.xml import DTDForbiddenError, parse_xml_file, parse_xml_source
from datamimic_ce.engine.io.api import load_connection_profile
from datamimic_ce.engine.io.files.api import FileUtil
from datamimic_ce.errors import IssueCode, ParserValidationError

_ATTRIBUTE_ENTITY = '<!DOCTYPE setup [<!ENTITY secret "expanded">]><setup value="&secret;"/>'


def test_predefined_entities_remain_supported_without_custom_entities() -> None:
    root = parse_xml_source('<setup value="A &amp; B"/>')

    assert root.attrib["value"] == "A & B"


def test_inline_doctype_is_rejected_before_attribute_entity_expansion() -> None:
    with pytest.raises(DTDForbiddenError, match="DTD declarations"):
        parse_xml_source(_ATTRIBUTE_ENTITY)


def test_inline_doctype_is_rejected_before_text_entity_expansion() -> None:
    xml = '<!DOCTYPE setup [<!ENTITY secret "expanded">]><setup>&secret;</setup>'

    with pytest.raises(DTDForbiddenError, match="DTD declarations"):
        parse_xml_source(xml)


@pytest.mark.parametrize(
    "encoding",
    ["utf-16", "utf-32", "utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be"],
)
def test_encoded_doctype_is_rejected_during_preflight(encoding: str) -> None:
    with pytest.raises(DTDForbiddenError, match="DTD declarations"):
        parse_xml_source(_ATTRIBUTE_ENTITY.encode(encoding))


def test_file_doctype_is_rejected_by_runtime_parser(tmp_path: Path) -> None:
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(_ATTRIBUTE_ENTITY, encoding="utf-8")

    with pytest.raises(ParserValidationError) as caught:
        DescriptorParser.parse(descriptor, None, "production", profile_loader=load_connection_profile)
    assert caught.value.issue_code is IssueCode.PARSER_DESCRIPTOR_INVALID_XML
    assert isinstance(caught.value.__cause__, DTDForbiddenError)
    assert caught.value.location.descriptor_path == "datamimic.xml"

    with pytest.raises(DTDForbiddenError, match="DTD declarations"):
        parse_xml_file(descriptor)


def test_external_doctype_reference_is_accepted_without_loading_it(tmp_path: Path) -> None:
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(
        '<!DOCTYPE setup SYSTEM "missing.dtd"><setup/>',
        encoding="utf-8",
    )

    assert parse_xml_file(descriptor).tag == "setup"


def test_runtime_parser_ignores_comments_and_processing_instructions(tmp_path: Path) -> None:
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(
        '<?xml version="1.0"?><setup><!-- documentation --><?runtime ignored?></setup>',
        encoding="utf-8",
    )

    setup = DescriptorParser.parse(descriptor, None, "production", profile_loader=load_connection_profile)

    assert setup.sub_statements == []


def test_authoring_loader_projects_doctype_rejection_as_diagnostic() -> None:
    root, diagnostic = load_source(_ATTRIBUTE_ENTITY)

    assert root is None
    assert diagnostic is not None
    assert diagnostic.rule == RULE_XML_LOAD
    assert "Unsafe XML" in diagnostic.message


def test_dbunit_runtime_source_rejects_custom_entities(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.xml"
    dataset.write_text(
        '<!DOCTYPE dataset [<!ENTITY secret "expanded">]><dataset><customer name="&secret;"/></dataset>',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="DTD declarations"):
        FileUtil.read_dbunit_to_dict_list(dataset, "customer")


@pytest.mark.parametrize(
    "declaration", ["", '<?xml version="1.0" encoding="UTF-8"?>', '<?xml version="1.0" encoding="ISO-8859-1"?>']
)
def test_inline_unicode_is_not_redecoded_using_a_byte_encoding(declaration: str) -> None:
    root = parse_xml_source(declaration + '<setup value="café"/>')

    assert root.attrib["value"] == "café"


def test_bytes_and_files_keep_their_declared_encoding(tmp_path: Path) -> None:
    xml = '<?xml version="1.0" encoding="ISO-8859-1"?><setup value="café"/>'.encode("iso-8859-1")
    descriptor = tmp_path / "latin1.xml"
    descriptor.write_bytes(xml)

    assert parse_xml_source(xml).attrib["value"] == "café"
    assert parse_xml_file(descriptor).attrib["value"] == "café"
