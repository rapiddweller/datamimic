"""Security contracts shared by runtime and authoring XML ingestion."""

from pathlib import Path

import pytest

from datamimic_ce.authoring.xml_loader import RULE_XML_LOAD, load_source
from datamimic_ce.parsers.descriptor_parser import DescriptorParser
from datamimic_ce.utils.file_util import FileUtil
from datamimic_ce.utils.secure_xml import DTDForbiddenError, parse_xml_file, parse_xml_source

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

    with pytest.raises(DTDForbiddenError, match="DTD declarations"):
        DescriptorParser.parse(descriptor, None)

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

    setup = DescriptorParser.parse(descriptor, None)

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
        '<!DOCTYPE dataset [<!ENTITY secret "expanded">]>'
        '<dataset><customer name="&secret;"/></dataset>',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="DTD declarations"):
        FileUtil.read_dbunit_to_dict_list(dataset, "customer")
