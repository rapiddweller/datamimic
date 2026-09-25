from types import SimpleNamespace

import pytest

from datamimic_ce.domains.shared.services.person_service import PersonService
from datamimic_ce.domains.domain_core.base_entity import BaseEntity
from datamimic_ce.domains.shared.entity_registry import get_entity_service_class, list_entity_specs
from datamimic_ce.engine.runtime.tasks.variable_task import VariableTask


def test_dotted_service_alias_resolves_through_entity_registry():
    alias = "shared.services.person_service.PersonService"
    assert get_entity_service_class(alias) is PersonService


def test_unregistered_dotted_alias_is_rejected():
    assert get_entity_service_class("unrelated.module.PersonService") is None


def test_unknown_dotted_entity_is_rejected():
    context = SimpleNamespace(root=SimpleNamespace(demographic_context=None, derive_seeded_rng=lambda: None))
    statement = SimpleNamespace(
        age_min=None,
        age_max=None,
        conditions_include=None,
        conditions_exclude=None,
        rng_seed=None,
    )

    with pytest.raises(ValueError, match="not supported in the domain architecture"):
        VariableTask._get_entity_generator(context, "shared.models.UnknownEntity", "en", "US", 1, statement)


def test_builtin_entity_inventory_is_complete():
    assert [spec.service_cls.__name__ for spec in list_entity_specs()] == [
        "AddressService",
        "CityService",
        "CompanyService",
        "CountryService",
        "PersonService",
        "OrderService",
        "ProductService",
        "BankAccountService",
        "BankService",
        "CreditCardService",
        "TransactionService",
        "DoctorService",
        "HospitalService",
        "MedicalDeviceService",
        "MedicalProcedureService",
        "PatientService",
        "InsuranceCompanyService",
        "InsuranceCoverageService",
        "InsurancePolicyService",
        "InsuranceProductService",
        "AdministrationOfficeService",
        "EducationalInstitutionService",
        "PoliceOfficerService",
    ]


def test_entity_field_alias_reads_the_declared_record_value():
    class ExampleEntity(BaseEntity):
        def __init__(self) -> None:
            super().__init__()
            self.unrelated_property_reads = 0

        @property
        def given_name(self) -> str:
            return "Ada"

        @property
        def expensive(self) -> str:
            self.unrelated_property_reads += 1
            raise AssertionError("unrelated property was evaluated")

        def to_dict(self) -> dict[str, object]:
            return {"given_name": self.given_name, "expensive": self.expensive}

    entity = ExampleEntity()
    assert entity.givenName == "Ada"
    assert entity.unrelated_property_reads == 0
