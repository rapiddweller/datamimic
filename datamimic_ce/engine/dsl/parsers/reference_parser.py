# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from datamimic_ce.engine.dsl.constants.attribute_constants import ATTR_SOURCE_KEY
from datamimic_ce.engine.dsl.constants.element_constants import EL_COMMENT, EL_FIELD, EL_REFERENCE
from datamimic_ce.engine.dsl.model.reference_field_model import ReferenceFieldModel
from datamimic_ce.engine.dsl.model.reference_model import ReferenceModel
from datamimic_ce.engine.dsl.parsers.statement_parser import StatementParser
from datamimic_ce.engine.dsl.statements.reference_statement import ReferenceField, ReferenceStatement
from datamimic_ce.engine.dsl.statements.statement import Statement
from datamimic_ce.engine.dsl.xml import XmlElement, xml_tag


class ReferenceParser(StatementParser):
    """Parse element "reference" (single-field legacy, or composite with <field> children)."""

    def __init__(self, element: XmlElement, properties: dict):
        super().__init__(element, properties, valid_element_tag=EL_REFERENCE)

    def parse(self, parent_stmt: Statement) -> ReferenceStatement:
        model = self.validate_attributes(ReferenceModel)
        fields = self._parse_fields()
        name = model.name
        if fields and model.source_key is not None:
            raise ValueError(
                f"<reference> '{name}': '{ATTR_SOURCE_KEY}' is not allowed when <{EL_FIELD}> children exist"
            )
        if not fields and model.source_key is None:
            raise ValueError(f"<reference> '{name}': define '{ATTR_SOURCE_KEY}' or at least one <{EL_FIELD}> child")
        # Normalise the legacy single-field form to one ReferenceField.
        if not fields:
            fields = [ReferenceField(target=name, source_key=str(model.source_key))]
        return ReferenceStatement(model, fields, parent_stmt)

    def _parse_fields(self) -> list[ReferenceField]:
        fields: list[ReferenceField] = []
        seen: set[str] = set()
        for child in self._element:
            if child.tag == EL_COMMENT:
                continue
            if xml_tag(child) != EL_FIELD:
                raise ValueError(f"<{EL_REFERENCE}> only accepts <{EL_FIELD}> children, got <{xml_tag(child)}>")
            field_model = ReferenceFieldModel(**child.attrib)
            if field_model.source_key in seen:
                raise ValueError(f"<{EL_FIELD}> has duplicate sourceKey '{field_model.source_key}'")
            seen.add(field_model.source_key)
            fields.append(ReferenceField(target=field_model.target, source_key=field_model.source_key))
        return fields
