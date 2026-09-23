"""Public DSL types and generator capability projection."""

import inspect

from datamimic_ce.engine.dsl.contracts import EntityValue, GeneratorCapability, StateTransitionRule
from datamimic_ce.engine.dsl.enums.dbms_enums import Dbms
from datamimic_ce.engine.dsl.enums.distribution_enums import NumberDistribution
from datamimic_ce.engine.dsl.enums.operation_enums import ExportOperation
from datamimic_ce.engine.dsl.parsers.descriptor_parser import DescriptorParser
from datamimic_ce.engine.dsl.properties import parse_properties
from datamimic_ce.engine.dsl.statements.generate_statement import GenerateStatement
from datamimic_ce.engine.dsl.statements.key_statement import KeyStatement
from datamimic_ce.engine.dsl.statements.setup_statement import SetupStatement
from datamimic_ce.engine.dsl.statements.statement import Statement
from datamimic_ce.engine.dsl.statements.variable_statement import VariableStatement


def describe_generator_type(generator_type: type) -> GeneratorCapability:
    try:
        internal = {"self", "context", "stmt", "qualified_key"}
        parameters = tuple(
            parameter
            for parameter in inspect.signature(generator_type).parameters
            if parameter not in internal
        )
    except (TypeError, ValueError):
        parameters = ()
    return GeneratorCapability(name=generator_type.__name__, parameters=parameters)


__all__ = [
    "Dbms",
    "DescriptorParser",
    "ExportOperation",
    "EntityValue",
    "GeneratorCapability",
    "GenerateStatement",
    "KeyStatement",
    "NumberDistribution",
    "Statement",
    "SetupStatement",
    "StateTransitionRule",
    "VariableStatement",
    "describe_generator_type",
    "parse_properties",
]
