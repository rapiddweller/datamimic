# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import re
from pathlib import Path
from typing import Any, cast
from xml.etree.ElementTree import Element

from datamimic_ce.config import settings
from datamimic_ce.constants.attribute_constants import ATTR_ENVIRONMENT, ATTR_ID, ATTR_SYSTEM
from datamimic_ce.constants.element_constants import (
    EL_ARRAY,
    EL_CONDITION,
    EL_DATABASE,
    EL_ECHO,
    EL_ELEMENT,
    EL_ELSE,
    EL_ELSE_IF,
    EL_EXECUTE,
    EL_GENERATE,
    EL_GENERATOR,
    EL_IF,
    EL_INCLUDE,
    EL_ITEM,
    EL_KEY,
    EL_LIST,
    EL_MEMSTORE,
    EL_MONGODB,
    EL_NESTED_KEY,
    EL_REFERENCE,
    EL_SETUP,
    EL_VARIABLE,
)
from datamimic_ce.logger import logger
from datamimic_ce.parsers.array_parser import ArrayParser
from datamimic_ce.parsers.condition_parser import ConditionParser
from datamimic_ce.parsers.database_parser import DatabaseParser
from datamimic_ce.parsers.echo_parser import EchoParser
from datamimic_ce.parsers.element_parser import ElementParser
from datamimic_ce.parsers.else_if_parser import ElseIfParser
from datamimic_ce.parsers.else_parser import ElseParser
from datamimic_ce.parsers.execute_parser import ExecuteParser
from datamimic_ce.parsers.generate_parser import GenerateParser
from datamimic_ce.parsers.generator_parser import GeneratorParser
from datamimic_ce.parsers.if_parser import IfParser
from datamimic_ce.parsers.include_parser import IncludeParser
from datamimic_ce.parsers.item_parser import ItemParser
from datamimic_ce.parsers.key_parser import KeyParser
from datamimic_ce.parsers.list_parser import ListParser
from datamimic_ce.parsers.memstore_parser import MemstoreParser
from datamimic_ce.parsers.nested_key_parser import NestedKeyParser
from datamimic_ce.parsers.reference_parser import ReferenceParser
from datamimic_ce.parsers.variable_parser import VariableParser
from datamimic_ce.statements.array_statement import ArrayStatement
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.condition_statement import ConditionStatement
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.include_statement import IncludeStatement
from datamimic_ce.statements.nested_key_statement import NestedKeyStatement
from datamimic_ce.statements.setup_statement import SetupStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.utils.file_util import FileUtil


class ParserUtil:
    @staticmethod
    def get_element_tag_by_statement(stmt: Statement) -> str:
        if isinstance(stmt, ArrayStatement):
            return EL_ARRAY
        elif isinstance(stmt, ConditionStatement):
            return EL_CONDITION
        elif isinstance(stmt, SetupStatement):
            return EL_SETUP
        elif isinstance(stmt, NestedKeyStatement):
            return EL_NESTED_KEY
        elif isinstance(stmt, GenerateStatement):
            return EL_GENERATE
        else:
            raise ValueError(f"Cannot get element tag for statement {stmt.__class__.__name__}")

    @staticmethod
    def get_valid_sub_elements_set_by_tag(ele_tag: str) -> set | None:
        # return None mean that element can have all kind of sub element,
        # check StatementParser._validate_sub_elements for detail
        valid_sub_element_dict = {
            EL_SETUP: {
                EL_MONGODB,
                EL_GENERATE,
                EL_DATABASE,
                EL_INCLUDE,
                EL_MEMSTORE,
                EL_EXECUTE,
                EL_ECHO,
                EL_VARIABLE,
                EL_GENERATOR,
            },
            EL_NESTED_KEY: {
                EL_KEY,
                EL_VARIABLE,
                EL_NESTED_KEY,
                EL_EXECUTE,
                EL_LIST,
                EL_ECHO,
                EL_ELEMENT,
                EL_ARRAY,
                EL_CONDITION,
            },
            EL_CONDITION: {EL_IF, EL_ELSE_IF, EL_ELSE},
            EL_GENERATE: {
                EL_GENERATE,
                EL_KEY,
                EL_VARIABLE,
                EL_REFERENCE,
                EL_NESTED_KEY,
                EL_LIST,
                EL_ARRAY,
                EL_ECHO,
                EL_CONDITION,
                EL_INCLUDE,
            },
            EL_INCLUDE: {EL_SETUP},
            EL_ITEM: {EL_KEY, EL_NESTED_KEY, EL_LIST, EL_ARRAY},
            EL_KEY: {EL_ELEMENT},
            EL_LIST: {EL_ITEM},
            EL_IF: None,
            EL_ELSE_IF: None,
            EL_ELSE: None,
        }

        return valid_sub_element_dict.get(ele_tag, set())

    @staticmethod
    def get_parser_by_element(class_factory_util: BaseClassFactoryUtil, element: Element, properties: dict):
        """
        Parser factory: Creating parser based on element
        :param element:
        :param properties:
        :return:
        """
        tag = element.tag
        if tag == EL_MONGODB:
            from datamimic_ce.parsers.mongodb_parser import MongoDBParser

            return MongoDBParser(class_factory_util, element, properties)
        elif tag == EL_GENERATE:
            from datamimic_ce.parsers.generate_parser import GenerateParser

            return GenerateParser(class_factory_util, element, properties)
        elif tag == EL_KEY:
            from datamimic_ce.parsers.key_parser import KeyParser

            return KeyParser(class_factory_util, element, properties)
        elif tag == EL_DATABASE:
            return DatabaseParser(class_factory_util, element, properties)
        elif tag == EL_VARIABLE:
            return VariableParser(class_factory_util, element, properties)
        elif tag == EL_NESTED_KEY:
            return NestedKeyParser(class_factory_util, element, properties)
        elif tag == EL_INCLUDE:
            return IncludeParser(class_factory_util, element, properties)
        elif tag == EL_MEMSTORE:
            return MemstoreParser(class_factory_util, element, properties)
        elif tag == EL_EXECUTE:
            return ExecuteParser(class_factory_util, element, properties)
        elif tag == EL_REFERENCE:
            return ReferenceParser(class_factory_util, element, properties)
        elif tag == EL_LIST:
            return ListParser(class_factory_util, element, properties)
        elif tag == EL_ITEM:
            return ItemParser(class_factory_util, element, properties)
        elif tag == EL_IF:
            return IfParser(class_factory_util, element=element, properties=properties)
        elif tag == EL_CONDITION:
            return ConditionParser(class_factory_util, element=element, properties=properties)
        elif tag == EL_ELSE_IF:
            return ElseIfParser(class_factory_util, element=element, properties=properties)
        elif tag == EL_ELSE:
            return ElseParser(class_factory_util, element=element, properties=properties)
        elif tag == EL_ARRAY:
            return ArrayParser(class_factory_util, element=element, properties=properties)
        elif tag == EL_ECHO:
            return EchoParser(class_factory_util, element=element, properties=properties)
        elif tag == EL_ELEMENT:
            return ElementParser(class_factory_util, element=element, properties=properties)
        elif tag == EL_GENERATOR:
            return GeneratorParser(class_factory_util, element=element, properties=properties)
        else:
            raise ValueError(f"Cannot get parser for element <{tag}>")

    def parse_sub_elements(
        self,
        class_factory_util: BaseClassFactoryUtil,
        descriptor_dir: Path,
        element: Element,
        properties: dict,
        parent_stmt: Statement,
    ) -> list[Statement]:
        """
        Parse sub-elements of composite element into list of Statement
        :param class_factory_util:
        :param descriptor_dir:
        :param element:
        :param properties:
        :param parent_stmt:
        :return:
        """
        result = []

        # Create a copied props for possible updating later, prevent updating original props dict
        copied_props = copy.deepcopy(properties) or {}

        for child_ele in element:
            parser = self.get_parser_by_element(class_factory_util, child_ele, copied_props)
            # TODO: add more child-element-able parsers such as
            #  attribute, reference, part,... (i.e. elements which have attribute 'name')
            stmt: Statement
            if isinstance(parser, VariableParser | GenerateParser | NestedKeyParser | ElementParser):
                if isinstance(parser, VariableParser) and element.tag == "setup":
                    stmt = parser.parse(parent_stmt=parent_stmt, has_parent_setup=True)
                elif isinstance(parser, GenerateParser | NestedKeyParser):
                    stmt = parser.parse(descriptor_dir=descriptor_dir, parent_stmt=parent_stmt)
                else:
                    stmt = parser.parse(parent_stmt=parent_stmt)
            else:
                if isinstance(
                    parser,
                    MemstoreParser
                    | ExecuteParser
                    | IncludeParser
                    | ReferenceParser
                    | ArrayParser
                    | EchoParser
                    | GeneratorParser,
                ):
                    stmt = parser.parse()
                elif isinstance(parser, KeyParser):
                    stmt = parser.parse(descriptor_dir=descriptor_dir, parent_stmt=parent_stmt)
                elif isinstance(parser, ConditionParser):
                    stmt = parser.parse(
                        descriptor_dir=descriptor_dir, parent_stmt=cast(CompositeStatement, parent_stmt)
                    )
                elif isinstance(parser, IfParser | ElseIfParser | ElseParser):
                    stmt = parser.parse(
                        descriptor_dir=descriptor_dir, parent_stmt=cast(ConditionStatement, parent_stmt)
                    )
                else:
                    stmt = parser.parse(descriptor_dir=descriptor_dir)

            if stmt is None:
                raise ValueError(f"Cannot parse element <{child_ele.tag}>")

            # Early execute some kinds of statement, such as <include>
            if isinstance(stmt, IncludeStatement):
                new_props = stmt.early_execute(descriptor_dir)
                copied_props.update(new_props)

            result.append(stmt)

        return result

    @staticmethod
    def retrieve_element_attributes(attributes: dict[str, Any], properties: dict[str, str] | None) -> dict[str, str]:
        """
        Retrieve element's attributes using environment properties
        :param attributes:
        :param properties:
        :return:
        """
        if properties is None:
            return attributes

        # Look up element's attributes defined as variable then evaluate them
        for key, value in attributes.items():
            if type(value) is str and re.match(r"^\{[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)*\}$", value) is not None:
                prop_key = value[1:-1]

                if "." not in prop_key:
                    # single-level prop_key
                    attributes[key] = properties.get(prop_key, value)
                else:
                    # prop_key with dot mean that properties have nested level
                    prop_keys = prop_key.split(".")
                    temp_value: dict | None = copy.deepcopy(properties)
                    for k in prop_keys:
                        if temp_value:
                            temp_value = temp_value.get(k)
                        if temp_value is None:
                            break
                    attributes[key] = temp_value or value

        return attributes

    @staticmethod
    def fulfill_credentials_v2(
        descriptor_dir: Path,
        descriptor_attr: dict,
        env_props: dict[str, str] | None,
        system_type: str,
    ) -> dict:
        """

        Fulfill credentials by getting from descriptor attributes, user's conf file or env file
        :param descriptor_dir:
        :param descriptor_attr:
        :param env_props:
        :param system_type:
        :param nullable:
        :return:
        """

        environment = (
            descriptor_attr.get(ATTR_ENVIRONMENT)
            or ("local" if settings.RUNTIME_ENVIRONMENT == "development" else None)
            or "environment"
        )
        system = descriptor_attr.get(ATTR_SYSTEM)

        if system is None:
            # Use id's value as fallback of attribute system
            if system_type in ["db", "mongo", "kafka", "dwh", "object-storage"]:
                system = descriptor_attr.get(ATTR_ID)
            else:
                raise ValueError(f"System type '{system_type}' is not supported")

        # Load configs from file env.properties
        conf_props = {}
        # If receiving envs props from platform, load from platform envs only
        if env_props:
            conf_props = env_props
        # else load from env.properties files (for testing purpose only)

        try:
            if environment and system:
                env_props_from_env_file = FileUtil.parse_properties(
                    descriptor_dir / f"conf/{environment}.env.properties"
                )
                # Update env props from env file
                conf_props.update(env_props_from_env_file)
        except FileNotFoundError:
            logger.info(f"Environment file not found {str(descriptor_dir / f'conf/{environment}.env.properties')}")

        credentials = copy.deepcopy(descriptor_attr)

        for attr_key, attr_value in conf_props.items():
            if attr_key.startswith(f"{system}.{system_type}.") and attr_value is not None:
                attr_name = "".join(attr_key.split(".")[2:])
                credentials[attr_name] = attr_value

                if any(pattern in attr_name.lower() for pattern in ["password", "pwd", "pass"]):
                    logger.debug(f"Get value for {attr_name}: ******")
                else:
                    logger.debug(f"Get value for {attr_name}: {attr_value}")

        return credentials
