# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.engine.dsl.model.values.scalar.key_model import KeyModel
from datamimic_ce.engine.dsl.parsers.base.client_config import ConnectionProfileLoader
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement, xml_tag
from datamimic_ce.engine.dsl.statements.composite_statement import CompositeStatement
from datamimic_ce.engine.dsl.statements.statement import Statement
from datamimic_ce.engine.dsl.statements.values.scalar.key_statement import KeyStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_ID, EL_KEY


class KeyParser(StatementParser):
    """
    Parse element "key" (or its alias "id") into KeyStatement
    """

    # <id> is a human-readable alias of <key>: same parser, model, statement and
    # valid sub-elements. The dispatch table routes both tags here.
    _VALID_TAGS = frozenset({EL_KEY, EL_ID})

    def __init__(
        self,
        element: XmlElement,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_KEY,  # sub-elements resolve under <key> for both tags
        )

    def _validate_element_tag(self) -> None:
        """Accept both <key> and its alias <id> (base only checks a single tag)."""
        if self._element.tag not in self._VALID_TAGS:
            raise ValueError(f"Expect element tag '{EL_KEY}' or '{EL_ID}', but got '{xml_tag(self._element)}'")

    def parse(
        self,
        descriptor_dir: Path,
        parent_stmt: Statement,
        *,
        profile_loader: ConnectionProfileLoader,
    ) -> KeyStatement:
        """
        Parse element "attribute" into AttributeStatement
        :return:
        """
        from datamimic_ce.engine.dsl.parsers.base.dispatch import parse_sub_elements

        if not isinstance(parent_stmt, CompositeStatement):
            raise TypeError("<key> requires a composite parent statement")
        key_stmt = KeyStatement(self.validate_attributes(KeyModel), parent_stmt)
        sub_stmt_list = parse_sub_elements(
            descriptor_dir,
            self._element,
            self._properties,
            parent_stmt=key_stmt,
            profile_loader=profile_loader,
        )
        key_stmt.sub_statements = sub_stmt_list

        return key_stmt
