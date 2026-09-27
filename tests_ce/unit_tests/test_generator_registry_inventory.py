from datamimic_ce.domains.domain_core.contracts.generation import GeneratorCapability
from datamimic_ce.domains.registry.generators import describe_generator_type
from datamimic_ce.domains.shared.literal_generators.registry import generator_namespace


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
        "GlobalIncrementGenerator",
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
