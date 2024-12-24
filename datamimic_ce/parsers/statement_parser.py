# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
from abc import ABC, abstractmethod
from typing import Any, TypeVar
from xml.etree.ElementTree import Element

from pydantic import BaseModel, ValidationError

from datamimic_ce.constants.attribute_constants import ATTR_ID, ATTR_NAME
from datamimic_ce.constants.element_constants import EL_DATABASE, EL_MONGODB
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class StatementParser(ABC):
    """
    Super class of all element parser
    """

    # Define a type variable T, which is a subclass of BaseModel
    BaseModelRelativeClass = TypeVar("BaseModelRelativeClass", bound=BaseModel)

    def __init__(
        self,
        element: Element,
        env_properties: dict[str, str] | None,
        valid_element_tag: str,
        class_factory_util: BaseClassFactoryUtil,
    ):
        self._class_factory_util = class_factory_util
        valid_sub_elements = self._class_factory_util.get_parser_util_cls().get_valid_sub_elements_set_by_tag(
            valid_element_tag
        )

        self._element: Element = element
        self._properties = env_properties
        self._valid_element_tag = valid_element_tag
        self._valid_sub_elements = valid_sub_elements

        # Validate XML element
        self._validate_element_tag()
        self._validate_sub_elements(valid_sub_elements)
        self._validate_statement_name()

    @property
    def properties(self) -> dict[str, str] | None:
        return self._properties

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
            "IncrementGenerator" "DateTimeGenerator",
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
                f"Element <{self._element.tag}> name '{ele_name}' is a reserved name, please use another name"
            )

    def _validate_element_tag(self) -> None:
        """
        Validate element tag
        :return:
        """
        if self._element.tag != self._valid_element_tag:
            raise ValueError(f"Expect element tag name '{self._valid_element_tag}', but got '{self._element.tag}'")

    def _validate_sub_elements(self, valid_sub_ele_set: set, composite_stmt: CompositeStatement | None = None) -> None:
        """
        Validate sub elements
        :return:
        """
        # Return if valid_sub_ele_set has not been set
        if valid_sub_ele_set is None:
            return
        if len(valid_sub_ele_set) == 0 and len(self._element) > 0:
            raise ValueError(
                f"""Element <{self._element.tag}>{" inside element " + f"'{composite_stmt.name}'" 
                if composite_stmt is not None else ''} does not accept any sub-elements"""
            )
        for child in self._element:
            if child.tag not in valid_sub_ele_set:
                raise ValueError(
                    f"Element <{self._element.tag}> get invalid child <{child.tag}>"
                    f", expects: {', '.join(map(lambda ele: f'<{ele}>', self._valid_sub_elements))}, "
                )

    def validate_attributes(
        self, model: type[BaseModelRelativeClass], fulfilled_credentials: dict | None = None
    ) -> BaseModelRelativeClass:
        """
        Validate XML model attributes
        :return:
        """
        original_attributes = fulfilled_credentials or copy.deepcopy(self._element.attrib)
        # Retrieve config value from properties files
        from datamimic_ce.parsers.parser_util import ParserUtil

        attributes = ParserUtil.retrieve_element_attributes(original_attributes, self._properties)
        try:
            return model(**attributes)
        except ValidationError as err:
            if self._element.tag in [
                EL_MONGODB,
                EL_DATABASE,
            ]:
                msg_err = (
                    f"Failed while parsing <{self._element.tag}> "
                    f"'{self._element.get(ATTR_NAME) or self._element.get(ATTR_ID)}' configuration. "
                    f"Please make sure all required attributes "
                    f"are provided in either XML or environment settings:"
                )
            else:
                msg_err = (
                    f"Failed while parsing attributes of element <{self._element.tag}> "
                    f"naming '{self._element.get(ATTR_NAME) or self._element.get(ATTR_ID)}':"
                )
            for err_detail in err.errors():
                loc_list = err_detail.get("loc")
                loc = loc_list[0] if loc_list is not None and len(loc_list) > 0 else None
                msg = err_detail.get("msg")
                new_msg = f"\n - {msg}" if loc == "__root__" else f"\n - {loc}: {msg}"
                msg_err = msg_err + new_msg
            raise ValueError(msg_err) from err
