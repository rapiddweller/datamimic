# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Descriptor loading for diagnostics through the shared secure XML boundary."""

from pathlib import Path

from lxml import etree

from datamimic_ce.authoring.diagnostics import Diagnostic
from datamimic_ce.authoring.rule_catalog import RuleSeverity
from datamimic_ce.utils.secure_xml import DTDForbiddenError, parse_xml_file, parse_xml_source

RULE_XML_LOAD = "DM001"

def element_path(element: etree._Element) -> str:
    """Stable address for diagnostics, e.g. '/setup/generate[2]/key[3]'."""
    return element.getroottree().getpath(element)


def load_source(xml: str) -> tuple["etree._Element | None", Diagnostic | None]:
    """Parse inline descriptor XML. Returns (root, None) or (None, DM001 diagnostic)."""
    try:
        root = parse_xml_source(xml)
    except DTDForbiddenError as err:
        return None, _unsafe_xml_diagnostic(err)
    except etree.XMLSyntaxError as err:
        return None, _syntax_diagnostic(err)
    return root, None


def load_file(path: Path) -> tuple["etree._Element | None", Diagnostic | None]:
    """Parse a descriptor file. Returns (root, None) or (None, DM001 diagnostic)."""
    try:
        root = parse_xml_file(path)
    except OSError as err:
        return None, Diagnostic(
            rule=RULE_XML_LOAD,
            severity=RuleSeverity.ERROR,
            message=f"Cannot read descriptor: {err}",
            fix_hint="Check that the path exists and is readable.",
            element="setup",
            path="/",
        )
    except DTDForbiddenError as err:
        return None, _unsafe_xml_diagnostic(err)
    except etree.XMLSyntaxError as err:
        return None, _syntax_diagnostic(err)
    return root, None


def _unsafe_xml_diagnostic(err: DTDForbiddenError) -> Diagnostic:
    return Diagnostic(
        rule=RULE_XML_LOAD,
        severity=RuleSeverity.ERROR,
        message=f"Unsafe XML is not allowed: {err}",
        fix_hint="Remove the DOCTYPE and use only the five predefined XML entities.",
        element="setup",
        path="/",
    )


def _syntax_diagnostic(err: etree.XMLSyntaxError) -> Diagnostic:
    return Diagnostic(
        rule=RULE_XML_LOAD,
        severity=RuleSeverity.ERROR,
        message=f"XML is not well-formed: {err.msg}",
        fix_hint="Fix the XML syntax first — close every tag, quote every attribute value.",
        element="setup",
        path="/",
        line=err.lineno,
    )
