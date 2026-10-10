from datamimic_ce.domains.api import iter_generator_capabilities as domain_generator_capabilities
from datamimic_ce.domains.domain_core.contracts.generation import GeneratorCapability
from datamimic_ce.domains.registry.generators import describe_generator_type, generator_namespace
from datamimic_ce.engine.runtime.api import iter_generator_capabilities as runtime_generator_capabilities


def test_builtin_generator_inventory_is_complete():
    assert list(generator_namespace()) == [
        "AcademicTitleGenerator",
        "BinaryGenerator",
        "BirthdateGenerator",
        "BooleanGenerator",
        "CNPJGenerator",
        "ColorGenerator",
        "CompanyNameGenerator",
        "CPFGenerator",
        "DataFakerGenerator",
        "DateTimeGenerator",
        "DepartmentNameGenerator",
        "DomainGenerator",
        "EANGenerator",
        "EmailAddressGenerator",
        "FamilyNameGenerator",
        "FloatGenerator",
        "GenderGenerator",
        "GivenNameGenerator",
        "HashGenerator",
        "IncrementGenerator",
        "IntegerGenerator",
        "NobilityTitleGenerator",
        "PasswordGenerator",
        "PhoneNumberGenerator",
        "PrefixedIdGenerator",
        "SectorGenerator",
        "SSNGenerator",
        "StateTransitionGenerator",
        "StreetNameGenerator",
        "StringGenerator",
        "TokenGenerator",
        "UrlGenerator",
        "UUIDGenerator",
    ]


def test_generator_capability_preserves_signature_order_and_uses_empty_fallback() -> None:
    class OrderedGenerator:
        def __init__(self, first: str, second: int = 2, *, third: bool = False) -> None: ...

    assert describe_generator_type(OrderedGenerator) == GeneratorCapability(
        name="OrderedGenerator",
        parameters=("first", "second", "third"),
    )
    assert describe_generator_type(dict) == GeneratorCapability(name="dict", parameters=())


def test_global_increment_remains_in_the_public_generator_capability_union() -> None:
    capability_list = [*domain_generator_capabilities(), *runtime_generator_capabilities()]
    names = [capability.name for capability in capability_list]
    capabilities = {capability.name: capability.parameters for capability in capability_list}

    assert len(names) == len(set(names))
    assert set(capabilities) == {*generator_namespace(), "GlobalIncrementGenerator", "SequenceTableGenerator"}
    assert capabilities["GlobalIncrementGenerator"] == ()
