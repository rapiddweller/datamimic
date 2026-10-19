# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pydantic import ValidationError

from datamimic_ce.engine.dsl.model.values.scalar.value_model import ValueModel
from datamimic_ce.engine.dsl.model.values.structured.array_model import ArrayModel
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement, xml_tag
from datamimic_ce.engine.dsl.statements.values.structured.array_statement import ArrayStatement
from datamimic_ce.engine.dsl.vocabulary.constants.attribute_constants import ATTR_NAME
from datamimic_ce.engine.dsl.vocabulary.constants.data_type_constants import DATA_TYPE_LITERAL
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_ARRAY
from datamimic_ce.errors import IssueCode, parser_validation_error


class ArrayParser(StatementParser):
    def __init__(
        self,
        element: XmlElement,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_ARRAY,
        )

    def parse(self, **kwargs) -> ArrayStatement:
        """
        Parse element "array" to ArrayStatement
        :return:
        """
        model = self.validate_attributes(ArrayModel)

        if model.type == DATA_TYPE_LITERAL:
            return ArrayStatement(model, self._parse_literal_values())
        if len(self._element) > 0:
            raise parser_validation_error(
                code=IssueCode.PARSER_ARRAY_SUBELEMENTS_NOT_ALLOWED,
                name=model.name,
                data_type=DATA_TYPE_LITERAL,
            )
        return ArrayStatement(model)

    def _parse_literal_values(self) -> list[str]:
        from datamimic_ce.engine.dsl.parsers.base.dispatch import retrieve_element_attributes

        parsed_values: list[str] = []
        for child in self._element:
            attributes: dict[str, object] = dict(child.attrib)
            attributes = retrieve_element_attributes(attributes, self._properties)
            try:
                value_model = ValueModel.model_validate(attributes)
            except ValidationError as err:
                raise parser_validation_error(
                    code=IssueCode.PARSER_ARRAY_VALUE_INVALID,
                    child_tag=xml_tag(child),
                    name=self._element.get(ATTR_NAME),
                    details="; ".join(item["msg"] for item in err.errors()),
                ) from err
            parsed_values.append(value_model.constant)

        if not parsed_values:
            raise parser_validation_error(
                code=IssueCode.PARSER_ARRAY_LITERAL_EMPTY,
                name=self._element.get(ATTR_NAME),
            )
        return parsed_values
