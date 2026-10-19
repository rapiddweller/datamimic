# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from pydantic import ValidationError

from datamimic_ce.engine.dsl.model.values.references.reference_field_model import ReferenceFieldModel
from datamimic_ce.engine.dsl.model.values.references.reference_model import ReferenceModel
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement, xml_tag
from datamimic_ce.engine.dsl.statements.base.statement import Statement
from datamimic_ce.engine.dsl.statements.values.references.reference_statement import ReferenceField, ReferenceStatement
from datamimic_ce.engine.dsl.vocabulary.constants.attribute_constants import ATTR_SOURCE_KEY
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_COMMENT, EL_FIELD, EL_REFERENCE
from datamimic_ce.errors import DescriptorLocation, IssueCode, parser_validation_error


class ReferenceParser(StatementParser):
    """Parse element "reference" (single-field legacy, or composite with <field> children)."""

    def __init__(self, element: XmlElement, properties: dict):
        super().__init__(element, properties, valid_element_tag=EL_REFERENCE)

    def parse(self, parent_stmt: Statement) -> ReferenceStatement:
        model = self.validate_attributes(ReferenceModel)
        fields = self._parse_fields()
        name = model.name
        if fields and model.source_key is not None:
            raise parser_validation_error(
                code=IssueCode.PARSER_VALIDATION_FAILED,
                details=f"<reference> '{name}': '{ATTR_SOURCE_KEY}' is not allowed when <{EL_FIELD}> children exist",
                location=DescriptorLocation(EL_REFERENCE, attribute=ATTR_SOURCE_KEY),
            )
        if not fields and model.source_key is None:
            raise parser_validation_error(
                code=IssueCode.PARSER_VALIDATION_FAILED,
                details=f"<reference> '{name}': define '{ATTR_SOURCE_KEY}' or at least one <{EL_FIELD}> child",
                location=DescriptorLocation(EL_REFERENCE, attribute=ATTR_SOURCE_KEY),
            )
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
                raise parser_validation_error(
                    code=IssueCode.PARSER_INVALID_CHILD,
                    element_tag=EL_REFERENCE,
                    child_tag=xml_tag(child),
                    expected=f"<{EL_FIELD}>",
                    location=DescriptorLocation(EL_REFERENCE),
                )
            try:
                field_model = ReferenceFieldModel(**child.attrib)
            except ValidationError as error:
                validation_errors: tuple[dict[str, object], ...] = tuple(
                    {"loc": tuple(detail["loc"]), "type": detail["type"], "msg": detail["msg"]}
                    for detail in error.errors(include_input=False, include_context=False)
                )
                raise parser_validation_error(
                    code=IssueCode.PARSER_VALIDATION_FAILED,
                    details=f"Invalid <{EL_FIELD}> attributes in <{EL_REFERENCE}>",
                    validation_errors=validation_errors,
                    location=DescriptorLocation(EL_FIELD),
                ) from error
            if field_model.source_key in seen:
                raise parser_validation_error(
                    code=IssueCode.PARSER_VALIDATION_FAILED,
                    details=f"<{EL_FIELD}> has duplicate sourceKey '{field_model.source_key}'",
                    location=DescriptorLocation(EL_FIELD, attribute=ATTR_SOURCE_KEY),
                )
            seen.add(field_model.source_key)
            fields.append(ReferenceField(target=field_model.target, source_key=field_model.source_key))
        return fields
