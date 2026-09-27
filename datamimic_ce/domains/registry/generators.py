"""Generator capability metadata derived from registered domain generators."""

import inspect

from datamimic_ce.domains.domain_core.contracts.generation import GeneratorCapability


def describe_generator_type(generator_type: type) -> GeneratorCapability:
    try:
        internal = {"self", "context", "stmt", "qualified_key"}
        parameters = tuple(
            parameter for parameter in inspect.signature(generator_type).parameters if parameter not in internal
        )
    except (TypeError, ValueError):
        parameters = ()
    return GeneratorCapability(name=generator_type.__name__, parameters=parameters)
