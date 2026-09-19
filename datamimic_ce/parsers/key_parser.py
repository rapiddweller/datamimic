# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from typing import cast
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_ID, EL_KEY
from datamimic_ce.model.key_model import KeyModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.statement import Statement


class KeyParser(StatementParser):
    """
    Parse element "key" (or its alias "id") into KeyStatement
    """

    # <id> is a human-readable alias of <key>: same parser, model, statement and
    # valid sub-elements. The dispatch in ParserUtil routes both tags here.
    _VALID_TAGS = frozenset({EL_KEY, EL_ID})

    def __init__(
        self,
        element: Element,
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
            raise ValueError(f"Expect element tag '{EL_KEY}' or '{EL_ID}', but got '{self._element.tag}'")

    def parse(self, descriptor_dir: Path, parent_stmt: Statement) -> KeyStatement:
        """
        Parse element "attribute" into AttributeStatement
        :return:
        """
        from datamimic_ce.parsers.parser_util import ParserUtil

        key_stmt = KeyStatement(self.validate_attributes(KeyModel), cast(CompositeStatement, parent_stmt))
        sub_stmt_list = ParserUtil.parse_sub_elements(
            descriptor_dir,
            self._element,
            self._properties,
            parent_stmt=key_stmt,
        )
        key_stmt.sub_statements = sub_stmt_list

        return key_stmt
