"""Shared hardened XML loading for runtime and authoring boundaries."""

from __future__ import annotations

import re
from pathlib import Path

from lxml import etree


class DTDForbiddenError(ValueError):
    """Raised before an internal DTD subset can resolve custom entities."""


def _parser() -> etree.XMLParser:
    return etree.XMLParser(
        load_dtd=False,
        no_network=True,
        recover=False,
        remove_comments=True,
        remove_pis=True,
        resolve_entities=False,
        huge_tree=False,
    )


def _preflight_text(source: bytes) -> str:
    """Decode enough XML syntax to recognize a DTD before libxml sees entities."""

    if source.startswith((b"\x00\x00\xfe\xff", b"\xff\xfe\x00\x00")):
        encoding = "utf-32"
    elif source.startswith((b"\xfe\xff", b"\xff\xfe")):
        encoding = "utf-16"
    elif source.startswith(b"\xef\xbb\xbf"):
        encoding = "utf-8-sig"
    elif source.startswith(b"\x00\x00\x00<"):
        encoding = "utf-32-be"
    elif source.startswith(b"<\x00\x00\x00"):
        encoding = "utf-32-le"
    elif source.startswith(b"\x00<"):
        encoding = "utf-16-be"
    elif source.startswith(b"<\x00"):
        encoding = "utf-16-le"
    else:
        # XML declarations for ASCII-compatible encodings keep markup bytes ASCII.
        # Ignoring non-ASCII decode errors is safe because only markup is inspected.
        encoding = "utf-8"
    return source.decode(encoding, errors="ignore")


def _doctype_has_internal_subset(text: str, start: int) -> bool:
    """Return whether a DOCTYPE declaration contains an unquoted ``[``."""

    quote: str | None = None
    for character in text[start:]:
        if quote is not None:
            if character == quote:
                quote = None
            continue
        if character in {'"', "'"}:
            quote = character
        elif character == "[":
            return True
        elif character == ">":
            return False
    return False


def _reject_unsafe_doctype_before_parse(source: bytes) -> None:
    text = _preflight_text(source)
    # Avoid rejecting harmless documentation strings while remaining conservative
    # about any real markup declaration before entity expansion can occur.
    without_comments = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    without_cdata = re.sub(r"<!\[CDATA\[.*?\]\]>", "", without_comments, flags=re.DOTALL)
    normalized = without_cdata.upper()
    doctype_start = normalized.find("<!DOCTYPE")
    if doctype_start >= 0 and _doctype_has_internal_subset(without_cdata, doctype_start):
        raise DTDForbiddenError(
            "DTD declarations with internal subsets and custom XML entities are not allowed"
        )


def parse_xml_source(xml: str | bytes) -> etree._Element:
    """Parse XML without internal DTD subsets, entity expansion, or network access.

    External DTD references remain compatible with DbUnit fixtures, but are never
    loaded or fetched by the parser.
    """

    source = xml.encode("utf-8") if isinstance(xml, str) else xml
    _reject_unsafe_doctype_before_parse(source)
    return etree.fromstring(source, parser=_parser())


def parse_xml_file(path: Path) -> etree._Element:
    """Parse one XML file through the same policy used for inline authoring XML."""

    source = path.read_bytes()
    _reject_unsafe_doctype_before_parse(source)
    return etree.fromstring(source, parser=_parser(), base_url=str(path))


__all__ = ["DTDForbiddenError", "parse_xml_file", "parse_xml_source"]
