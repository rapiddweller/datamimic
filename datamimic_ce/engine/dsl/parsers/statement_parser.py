# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
from abc import ABC, abstractmethod
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ValidationError

from datamimic_ce.engine.dsl.constants.attribute_constants import ATTR_ID, ATTR_NAME
from datamimic_ce.engine.dsl.constants.element_constants import EL_COMMENT, EL_DATABASE, EL_MONGODB
from datamimic_ce.engine.dsl.statements.composite_statement import CompositeStatement
from datamimic_ce.engine.dsl.statements.statement import Statement
from datamimic_ce.engine.dsl.xml import XmlElement, xml_tag


class StatementParser(ABC):
    """
    Super class of all element parser
    """

    # Define a type variable T, which is a subclass of BaseModel
    BaseModelRelativeClass = TypeVar("BaseModelRelativeClass", bound=BaseModel)

    def __init__(
        self,
        element: XmlElement,
        env_properties: dict[str, str] | None,
        valid_element_tag: str,
    ):
        from datamimic_ce.engine.dsl.parsers.parser_util import ParserUtil
        # valid_sub_elements = ParserUtil.get_valid_sub_elements_set_by_tag(valid_element_tag)

        self._element: XmlElement = element
        self._properties = env_properties
        self._runtime_environment: Literal["development", "production"] = "production"
        self._valid_element_tag = valid_element_tag
        self._valid_sub_elements = ParserUtil.get_valid_sub_elements_set_by_tag(valid_element_tag)

        # Validate XML element
        self._validate_element_tag()
        self._validate_sub_elements()
        self._validate_statement_name()

    @property
    def properties(self) -> dict[str, str] | None:
        return self._properties

    @property
    def runtime_environment(self) -> Literal["development", "production"]:
        return self._runtime_environment

    def set_runtime_environment(self, value: Literal["development", "production"]) -> None:
        self._runtime_environment = value

    @abstractmethod
    def parse(self, *args, **kwargs: Any) -> Statement:
        """
        Parse Element to Statement
        :return:
        """

    def _validate_statement_name(self) -> None:
        """
        Validate statement name
        :return:
        """
        generator_class_name_list = [
            "CNPJGenerator",
            "CPFGenerator",
            "IncrementGenerator",
            "DateTimeGenerator",
            "DepartmentNameGenerator",
            "BirthdateGenerator",
            "EmailAddressGenerator",
            "DomainGenerator",
            "EANGenerator",
            "SectorGenerator",
            "UUIDGenerator",
            "BooleanGenerator",
            "PhoneNumberGenerator",
            "IntegerGenerator",
            "StringGenerator",
            "FloatGenerator",
            "SSNGenerator",
            "DataFakerGenerator",
            "AcademicTitleGenerator",
            "CompanyNameGenerator",
            "FamilyNameGenerator",
            "GenderGenerator",
            "GivenNameGenerator",
            "StreetNameGenerator",
            "UrlGenerator",
            "SequenceTableGenerator",
            "NobilityTitleGenerator",
        ]
        reserved_name_list = generator_class_name_list
        ele_name = self._element.get(ATTR_NAME, None)
        if ele_name in reserved_name_list:
            raise ValueError(
                f"Element <{xml_tag(self._element)}> name '{ele_name}' is a reserved name, please use another name"
            )

    def _validate_element_tag(self) -> None:
        """
        Validate element tag
        :return:
        """
        tag = xml_tag(self._element)
        if tag != self._valid_element_tag:
            raise ValueError(f"Expect element tag name '{self._valid_element_tag}', but got '{tag}'")

    def set_and_validate_valid_sub_elements(self, valid_sub_ele_set: set | None) -> None:
        """
        Set and validate valid sub elements
        :return:
        """
        self._valid_sub_elements = valid_sub_ele_set
        self._validate_sub_elements()

    def _validate_sub_elements(self, composite_stmt: CompositeStatement | None = None) -> None:
        """
        Validate sub elements
        :return:
        """
        # Return if valid_sub_ele_set has not been set
        if self._valid_sub_elements is None:
            return
        # <comment> is an ignored documentation element accepted in any context.
        non_comment_children = [child for child in self._element if xml_tag(child) != EL_COMMENT]
        if len(self._valid_sub_elements) == 0 and len(non_comment_children) > 0:
            raise ValueError(
                f"""Element <{xml_tag(self._element)}>{
                    " inside element " + f"'{composite_stmt.name}'" if composite_stmt is not None else ""
                } does not accept any sub-elements"""
            )
        for child in non_comment_children:
            if xml_tag(child) not in self._valid_sub_elements:
                raise ValueError(
                    f"Element <{xml_tag(self._element)}> get invalid child <{xml_tag(child)}>"
                    f", expects: {', '.join(map(lambda ele: f'<{ele}>', self._valid_sub_elements))}, "
                )

    def validate_attributes(
        self, model: type[BaseModelRelativeClass], fulfilled_credentials: dict | None = None
    ) -> BaseModelRelativeClass:
        """
        Validate XML model attributes
        :return:
        """
        original_attributes: dict[str, object] = {}
        if fulfilled_credentials:
            original_attributes.update(fulfilled_credentials)
        else:
            original_attributes.update(copy.deepcopy(self._element.attrib))
        # Retrieve config value from properties files
        from datamimic_ce.engine.dsl.parsers.parser_util import ParserUtil

        attributes = ParserUtil.retrieve_element_attributes(original_attributes, self._properties)
        try:
            return model(**attributes)
        except ValidationError as err:
            if xml_tag(self._element) in [
                EL_MONGODB,
                EL_DATABASE,
            ]:
                msg_err = (
                    f"Failed while parsing <{xml_tag(self._element)}> "
                    f"'{self._element.get(ATTR_NAME) or self._element.get(ATTR_ID)}' configuration. "
                    f"Please make sure all required attributes "
                    f"are provided in either XML or environment settings:"
                )
            else:
                msg_err = (
                    f"Failed while parsing attributes of element <{xml_tag(self._element)}> "
                    f"naming '{self._element.get(ATTR_NAME) or self._element.get(ATTR_ID)}':"
                )
            for err_detail in err.errors():
                loc_list = err_detail.get("loc")
                loc = loc_list[0] if loc_list is not None and len(loc_list) > 0 else None
                msg = err_detail.get("msg")
                new_msg = f"\n - {msg}" if loc == "__root__" else f"\n - {loc}: {msg}"
                msg_err = msg_err + new_msg
            raise ValueError(msg_err) from err
