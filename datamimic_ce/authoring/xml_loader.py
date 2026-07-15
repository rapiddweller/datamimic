# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""lxml-based descriptor loading for the linter: line numbers + element paths.

Hardened for untrusted inline XML (MCP input): no entity resolution, no network.
The engine keeps its own stdlib ElementTree parse — this tree is only for diagnostics.
"""

from pathlib import Path

from lxml import etree

from datamimic_ce.authoring.diagnostics import Diagnostic
from datamimic_ce.authoring.rule_catalog import RuleSeverity

RULE_XML_LOAD = "DM001"

_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, recover=False)


def element_path(element: etree._Element) -> str:
    """Stable address for diagnostics, e.g. '/setup/generate[2]/key[3]'."""
    return element.getroottree().getpath(element)


def load_source(xml: str) -> tuple["etree._Element | None", Diagnostic | None]:
    """Parse inline descriptor XML. Returns (root, None) or (None, DM001 diagnostic)."""
    try:
        root = etree.fromstring(xml.encode("utf-8"), parser=_PARSER)
    except etree.XMLSyntaxError as err:
        return None, _syntax_diagnostic(err)
    return root, None


def load_file(path: Path) -> tuple["etree._Element | None", Diagnostic | None]:
    """Parse a descriptor file. Returns (root, None) or (None, DM001 diagnostic)."""
    try:
        tree = etree.parse(str(path), parser=_PARSER)
    except OSError as err:
        return None, Diagnostic(
            rule=RULE_XML_LOAD,
            severity=RuleSeverity.ERROR,
            message=f"Cannot read descriptor: {err}",
            fix_hint="Check that the path exists and is readable.",
            element="setup",
            path="/",
        )
    except etree.XMLSyntaxError as err:
        return None, _syntax_diagnostic(err)
    return tree.getroot(), None


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
