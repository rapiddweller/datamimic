"""Public DSL types and generator capability projection."""

import inspect

from datamimic_ce.engine.dsl.contracts import GeneratorCapability
from datamimic_ce.engine.dsl.enums.dbms_enums import Dbms
from datamimic_ce.engine.dsl.enums.distribution_enums import NumberDistribution
from datamimic_ce.engine.dsl.statements.key_statement import KeyStatement
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
    "GeneratorCapability",
    "KeyStatement",
    "NumberDistribution",
    "Statement",
    "VariableStatement",
    "describe_generator_type",
]
