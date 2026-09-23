"""Public DSL types and generator capability projection."""

import inspect

from datamimic_ce.engine.dsl.constants.attribute_constants import (
    ATTR_CONSTANT,
    ATTR_DISTRIBUTION,
    ATTR_ENTITY,
    ATTR_GENERATOR,
    ATTR_SCRIPT,
    ATTR_SOURCE,
    ATTR_TYPE,
    ATTR_UNIQUE,
    ATTR_VALUES,
    META_SELECTOR,
    META_TARGET_ENTITY,
    META_TYPE,
)
from datamimic_ce.engine.dsl.constants.convention_constants import NAME_SEPARATOR
from datamimic_ce.engine.dsl.constants.data_type_constants import (
    DATA_TYPE_BINARY,
    DATA_TYPE_BOOL,
    DATA_TYPE_DECIMAL,
    DATA_TYPE_DICT,
    DATA_TYPE_FLOAT,
    DATA_TYPE_INT,
    DATA_TYPE_LIST,
    DATA_TYPE_LITERAL,
    DATA_TYPE_STRING,
)
from datamimic_ce.engine.dsl.constants.element_constants import (
    EL_COMMENT,
    EL_CONDITION,
    EL_DATABASE,
    EL_ELEMENT,
    EL_ELSE,
    EL_ELSE_IF,
    EL_GENERATE,
    EL_ID,
    EL_IF,
    EL_INCLUDE,
    EL_ITERATE,
    EL_KEY,
    EL_MEMSTORE,
    EL_MONGODB,
    EL_NESTED_KEY,
    EL_REFERENCE,
    EL_SETUP,
    EL_VARIABLE,
)
from datamimic_ce.engine.dsl.constants.exporter_constants import (
    EXPORTER_CONSOLE_EXPORTER,
    EXPORTER_CSV,
    EXPORTER_DBUNIT,
    EXPORTER_FIXED_WIDTH,
    EXPORTER_JSON,
    EXPORTER_LOG_EXPORTER,
    EXPORTER_TEST_RESULT_EXPORTER,
    EXPORTER_TXT,
    EXPORTER_XLSX,
    EXPORTER_XML,
)
from datamimic_ce.engine.dsl.contracts import EntityValue, GeneratorCapability, StateTransitionRule
from datamimic_ce.engine.dsl.enums.converter_enums import ConverterEnum, SupportHash, SupportOutputFormat
from datamimic_ce.engine.dsl.enums.dbms_enums import Dbms
from datamimic_ce.engine.dsl.enums.distribution_enums import (
    POSITIONAL_NUMBER_SEQUENCES,
    NumberDistribution,
    SourceDistribution,
)
from datamimic_ce.engine.dsl.enums.faker_enums import UnsupportedMethod
from datamimic_ce.engine.dsl.enums.operation_enums import ExportOperation
from datamimic_ce.engine.dsl.model.constraints import (
    COUNT_XOR_MAX,
    COUNT_XOR_MIN,
    EXIST_COUNT,
    KEY_DISTRIBUTION_VALUES,
    SOURCE_DISTRIBUTION_VALUES,
    WEIGHTS_REQUIRE_VALUES,
    AllOrNone,
    AllowedValuesWhen,
    Constraint,
    DynamicSourceKind,
    Forbids,
    ForbidsWhenValue,
    MutuallyExclusive,
    MutuallyExclusiveWhen,
    RequiredOneOf,
    Requires,
    RequiresWhenValue,
    SourceFileFormat,
    ValidValues,
    element_constraints,
    is_source_file,
    resolved_allowed,
    resolved_values,
    rule_registry_revision,
    serialize_constraints,
    serialize_source_capability,
    source_allows_client,
    source_allows_memstore,
    source_capabilities,
    source_dynamic_kind,
    source_file_format,
    source_file_format_for,
    supported_source_file_formats,
)
from datamimic_ce.engine.dsl.model.element_registry import (
    canonical_tag,
    element_aliases,
    get_model_class,
    get_valid_children,
    list_element_tags,
    registry_revision,
)
from datamimic_ce.engine.dsl.model.model_util import ModelUtil
from datamimic_ce.engine.dsl.parsers.descriptor_parser import DescriptorParser
from datamimic_ce.engine.dsl.properties import parse_properties
from datamimic_ce.engine.dsl.statements.array_statement import ArrayStatement
from datamimic_ce.engine.dsl.statements.assert_statement import AssertStatement
from datamimic_ce.engine.dsl.statements.composite_statement import CompositeStatement
from datamimic_ce.engine.dsl.statements.condition_statement import ConditionStatement
from datamimic_ce.engine.dsl.statements.database_statement import DatabaseStatement
from datamimic_ce.engine.dsl.statements.demographics_statement import DemographicsStatement
from datamimic_ce.engine.dsl.statements.echo_statement import EchoStatement
from datamimic_ce.engine.dsl.statements.element_statement import ElementStatement
from datamimic_ce.engine.dsl.statements.else_if_statement import ElseIfStatement
from datamimic_ce.engine.dsl.statements.else_statement import ElseStatement
from datamimic_ce.engine.dsl.statements.execute_statement import ExecuteStatement
from datamimic_ce.engine.dsl.statements.generate_statement import GenerateStatement
from datamimic_ce.engine.dsl.statements.generator_statement import GeneratorStatement
from datamimic_ce.engine.dsl.statements.if_statement import IfStatement
from datamimic_ce.engine.dsl.statements.include_statement import IncludeStatement
from datamimic_ce.engine.dsl.statements.item_statement import ItemStatement
from datamimic_ce.engine.dsl.statements.key_statement import KeyStatement
from datamimic_ce.engine.dsl.statements.list_statement import ListStatement
from datamimic_ce.engine.dsl.statements.memstore_statement import MemstoreStatement
from datamimic_ce.engine.dsl.statements.mongodb_statement import MongoDBStatement
from datamimic_ce.engine.dsl.statements.nested_key_statement import NestedKeyStatement
from datamimic_ce.engine.dsl.statements.reference_statement import ReferenceStatement
from datamimic_ce.engine.dsl.statements.setup_statement import SetupStatement
from datamimic_ce.engine.dsl.statements.state_machine_statement import StateMachineStatement
from datamimic_ce.engine.dsl.statements.statement import Statement
from datamimic_ce.engine.dsl.statements.statement_util import StatementUtil
from datamimic_ce.engine.dsl.statements.variable_statement import VariableStatement
from datamimic_ce.engine.dsl.statements.while_statement import WhileStatement
from datamimic_ce.engine.dsl.timeseries import TimeSeriesConfig
from datamimic_ce.engine.dsl.xml import DTDForbiddenError, parse_xml_file, parse_xml_source


def describe_generator_type(generator_type: type) -> GeneratorCapability:
    try:
        internal = {"self", "context", "stmt", "qualified_key"}
        parameters = tuple(
            parameter for parameter in inspect.signature(generator_type).parameters if parameter not in internal
        )
    except (TypeError, ValueError):
        parameters = ()
    return GeneratorCapability(name=generator_type.__name__, parameters=parameters)


__all__ = [
    "ATTR_CONSTANT",
    "ATTR_DISTRIBUTION",
    "ATTR_ENTITY",
    "ATTR_GENERATOR",
    "ATTR_SCRIPT",
    "ATTR_SOURCE",
    "ATTR_TYPE",
    "ATTR_UNIQUE",
    "ATTR_VALUES",
    "AllOrNone",
    "AllowedValuesWhen",
    "ArrayStatement",
    "AssertStatement",
    "CompositeStatement",
    "ConditionStatement",
    "Constraint",
    "ConverterEnum",
    "COUNT_XOR_MAX",
    "COUNT_XOR_MIN",
    "DATA_TYPE_BINARY",
    "DATA_TYPE_BOOL",
    "DATA_TYPE_DECIMAL",
    "DATA_TYPE_DICT",
    "DATA_TYPE_FLOAT",
    "DATA_TYPE_INT",
    "DATA_TYPE_LIST",
    "DATA_TYPE_LITERAL",
    "DATA_TYPE_STRING",
    "DatabaseStatement",
    "DemographicsStatement",
    "Dbms",
    "DescriptorParser",
    "DTDForbiddenError",
    "DynamicSourceKind",
    "EXIST_COUNT",
    "EchoStatement",
    "EL_COMMENT",
    "EL_CONDITION",
    "EL_DATABASE",
    "EL_ELEMENT",
    "EL_ELSE",
    "EL_ELSE_IF",
    "EL_GENERATE",
    "EL_ID",
    "EL_IF",
    "EL_INCLUDE",
    "EL_ITERATE",
    "EL_KEY",
    "EL_MEMSTORE",
    "EL_MONGODB",
    "EL_NESTED_KEY",
    "EL_REFERENCE",
    "EL_SETUP",
    "EL_VARIABLE",
    "ElementStatement",
    "ElseIfStatement",
    "ElseStatement",
    "EntityValue",
    "ExecuteStatement",
    "ExportOperation",
    "Forbids",
    "ForbidsWhenValue",
    "EXPORTER_CONSOLE_EXPORTER",
    "EXPORTER_CSV",
    "EXPORTER_DBUNIT",
    "EXPORTER_FIXED_WIDTH",
    "EXPORTER_JSON",
    "EXPORTER_LOG_EXPORTER",
    "EXPORTER_TEST_RESULT_EXPORTER",
    "EXPORTER_TXT",
    "EXPORTER_XLSX",
    "EXPORTER_XML",
    "GeneratorCapability",
    "GenerateStatement",
    "GeneratorStatement",
    "IfStatement",
    "IncludeStatement",
    "ItemStatement",
    "KeyStatement",
    "KEY_DISTRIBUTION_VALUES",
    "ListStatement",
    "MemstoreStatement",
    "META_SELECTOR",
    "META_TARGET_ENTITY",
    "META_TYPE",
    "ModelUtil",
    "MongoDBStatement",
    "MutuallyExclusive",
    "MutuallyExclusiveWhen",
    "NAME_SEPARATOR",
    "NestedKeyStatement",
    "NumberDistribution",
    "POSITIONAL_NUMBER_SEQUENCES",
    "ReferenceStatement",
    "RequiredOneOf",
    "Requires",
    "RequiresWhenValue",
    "resolved_allowed",
    "resolved_values",
    "serialize_constraints",
    "serialize_source_capability",
    "SetupStatement",
    "SourceDistribution",
    "SOURCE_DISTRIBUTION_VALUES",
    "SourceFileFormat",
    "source_allows_client",
    "source_allows_memstore",
    "source_capabilities",
    "source_dynamic_kind",
    "source_file_format",
    "source_file_format_for",
    "supported_source_file_formats",
    "Statement",
    "StatementUtil",
    "StateMachineStatement",
    "StateTransitionRule",
    "SupportHash",
    "SupportOutputFormat",
    "TimeSeriesConfig",
    "UnsupportedMethod",
    "ValidValues",
    "VariableStatement",
    "WEIGHTS_REQUIRE_VALUES",
    "WhileStatement",
    "canonical_tag",
    "describe_generator_type",
    "element_aliases",
    "element_constraints",
    "get_model_class",
    "get_valid_children",
    "is_source_file",
    "list_element_tags",
    "parse_properties",
    "parse_xml_file",
    "parse_xml_source",
    "registry_revision",
    "rule_registry_revision",
]
