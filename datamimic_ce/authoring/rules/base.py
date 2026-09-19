# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Rule contract for the DSL linter. Rules walk the lxml tree via LintContext and
emit Diagnostics; they never raise. The engine parse (phase 2) stays the authority."""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import ClassVar

from lxml import etree

from datamimic_ce.authoring.diagnostics import Diagnostic, Severity
from datamimic_ce.authoring.schema import SchemaIndex
from datamimic_ce.authoring.xml_loader import element_path
from datamimic_ce.constants.element_constants import EL_COMMENT


class LintContext:
    def __init__(self, root: etree._Element, schemas: SchemaIndex, base_dir: Path | None = None):
        self.root = root
        self.schemas = schemas
        self.base_dir = base_dir  # descriptor dir; None for inline XML without one

    def iter(self, *tags: str) -> Iterator[etree._Element]:
        """All elements (document order); with tags, only those. Comments are never yielded."""
        for element in self.root.iter():
            if not isinstance(element.tag, str) or element.tag == EL_COMMENT:
                continue  # lxml yields XML comments/PIs with non-str tags
            if not tags or element.tag in tags:
                yield element

    def diag(
        self,
        rule: "type[Rule]",
        element: etree._Element,
        message: str,
        fix_hint: str,
        *,
        severity: Severity | None = None,
    ) -> Diagnostic:
        return Diagnostic(
            rule=rule.id,
            severity=severity or rule.severity,
            message=message,
            fix_hint=fix_hint,
            element=str(element.tag),
            path=element_path(element),
            name=element.get("name") or element.get("id"),
            line=element.sourceline,
            docs=rule.docs,
        )


class Rule(ABC):
    id: ClassVar[str]
    severity: ClassVar[Severity]
    docs: ClassVar[str | None] = None

    @abstractmethod
    def check(self, ctx: LintContext) -> Iterable[Diagnostic]: ...
