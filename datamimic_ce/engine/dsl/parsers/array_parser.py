# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pydantic import ValidationError

from datamimic_ce.engine.dsl.constants.attribute_constants import ATTR_NAME
from datamimic_ce.engine.dsl.constants.data_type_constants import DATA_TYPE_LITERAL
from datamimic_ce.engine.dsl.constants.element_constants import EL_ARRAY
from datamimic_ce.engine.dsl.model.array_model import ArrayModel
from datamimic_ce.engine.dsl.model.value_model import ValueModel
from datamimic_ce.engine.dsl.parsers.statement_parser import StatementParser
from datamimic_ce.engine.dsl.statements.array_statement import ArrayStatement
from datamimic_ce.engine.dsl.xml import XmlElement, xml_tag


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
            raise ValueError(
                f"<array> '{model.name}' has child elements but is not type='{DATA_TYPE_LITERAL}' - "
                f"sub-elements are only valid for a literal array"
            )
        return ArrayStatement(model)

    def _parse_literal_values(self) -> list[str]:
        from datamimic_ce.engine.dsl.parsers.parser_util import ParserUtil

        parsed_values: list[str] = []
        for child in self._element:
            attributes: dict[str, object] = dict(child.attrib)
            attributes = ParserUtil.retrieve_element_attributes(attributes, self._properties)
            try:
                value_model = ValueModel.model_validate(attributes)
            except ValidationError as err:
                raise ValueError(
                    f"Invalid <{xml_tag(child)}> inside <array> '{self._element.get(ATTR_NAME)}': {err}"
                ) from err
            parsed_values.append(value_model.constant)

        if not parsed_values:
            raise ValueError(
                f"<array> '{self._element.get(ATTR_NAME)}' with type='{DATA_TYPE_LITERAL}' "
                f"must have at least one <value> child"
            )
        return parsed_values
