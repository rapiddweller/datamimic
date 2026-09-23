# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support: info@rapiddweller.com

"""Registry for built-in domain entity services."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from datamimic_ce.domains.domain_core.attribute_catalog import FieldSpec
from datamimic_ce.domains.domain_core.base_domain_service import BaseDomainService

_DOMAINS_PREFIX = "datamimic_ce.domains."


@dataclass(frozen=True)
class EntitySpec:
    entity: str
    service_cls: type[BaseDomainService]
    module: str
    attributes: tuple[FieldSpec, ...]


_ENTITY_REGISTRY: dict[str, EntitySpec] = {}
_CLASS_TO_SPEC: dict[type[BaseDomainService], EntitySpec] = {}
_LOADED = False


def _ensure_loaded() -> None:
    global _LOADED
    if not _LOADED:
        auto_register_entities()
        _LOADED = True


def auto_register_entities() -> None:
    """Register the built-in entity services and their schema declarations."""
    for service_cls in _builtin_services():
        _register_service_class(service_cls)


def _builtin_services() -> tuple[type[BaseDomainService], ...]:
    # Preserve package traversal order and first-alias wins with an explicit inventory.
    from datamimic_ce.domains.common.services.address_service import AddressService
    from datamimic_ce.domains.common.services.city_service import CityService
    from datamimic_ce.domains.common.services.company_service import CompanyService
    from datamimic_ce.domains.common.services.country_service import CountryService
    from datamimic_ce.domains.common.services.person_service import PersonService
    from datamimic_ce.domains.ecommerce.services.order_service import OrderService
    from datamimic_ce.domains.ecommerce.services.product_service import ProductService
    from datamimic_ce.domains.finance.services.bank_account_service import BankAccountService
    from datamimic_ce.domains.finance.services.bank_service import BankService
    from datamimic_ce.domains.finance.services.credit_card_service import CreditCardService
    from datamimic_ce.domains.finance.services.transaction_service import TransactionService
    from datamimic_ce.domains.healthcare.services.doctor_service import DoctorService
    from datamimic_ce.domains.healthcare.services.hospital_service import HospitalService
    from datamimic_ce.domains.healthcare.services.medical_device_service import MedicalDeviceService
    from datamimic_ce.domains.healthcare.services.medical_procedure_service import MedicalProcedureService
    from datamimic_ce.domains.healthcare.services.patient_service import PatientService
    from datamimic_ce.domains.insurance.services.insurance_company_service import InsuranceCompanyService
    from datamimic_ce.domains.insurance.services.insurance_coverage_service import InsuranceCoverageService
    from datamimic_ce.domains.insurance.services.insurance_policy_service import InsurancePolicyService
    from datamimic_ce.domains.insurance.services.insurance_product_service import InsuranceProductService
    from datamimic_ce.domains.public_sector.services.administration_office_service import AdministrationOfficeService
    from datamimic_ce.domains.public_sector.services.educational_institution_service import (
        EducationalInstitutionService,
    )
    from datamimic_ce.domains.public_sector.services.police_officer_service import PoliceOfficerService

    return (
        AddressService, CityService, CompanyService, CountryService, PersonService,
        OrderService, ProductService, BankAccountService, BankService, CreditCardService,
        TransactionService, DoctorService, HospitalService, MedicalDeviceService,
        MedicalProcedureService, PatientService, InsuranceCompanyService,
        InsuranceCoverageService, InsurancePolicyService, InsuranceProductService,
        AdministrationOfficeService, EducationalInstitutionService, PoliceOfficerService,
    )


def _entity_name_for(cls: type[BaseDomainService]) -> str:
    name = cls.__name__
    return name[:-7] if name.endswith("Service") else name


def _register_service_class(cls: type[BaseDomainService]) -> None:
    if cls in _CLASS_TO_SPEC:
        return
    entity_name = _entity_name_for(cls)
    spec = EntitySpec(
        entity=entity_name,
        service_cls=cls,
        module=cls.__module__,
        attributes=cls.attribute_specs(),
    )
    _CLASS_TO_SPEC[cls] = spec
    for alias in _aliases_for(cls, entity_name):
        _ENTITY_REGISTRY.setdefault(alias, spec)


def _aliases_for(cls: type[BaseDomainService], entity_name: str) -> tuple[str, ...]:
    service_name = cls.__name__
    module = cls.__module__
    aliases = [entity_name, service_name, f"{module}.{service_name}"]
    if module.startswith(_DOMAINS_PREFIX):
        aliases.append(f"{module[len(_DOMAINS_PREFIX) : ]}.{service_name}")
    return tuple(alias for alias in aliases if alias)


def list_entity_specs() -> tuple[EntitySpec, ...]:
    _ensure_loaded()
    return tuple(_CLASS_TO_SPEC.values())


def get_entity_spec(name: str) -> EntitySpec | None:
    _ensure_loaded()
    spec = _ENTITY_REGISTRY.get(name)
    if spec is not None:
        return spec
    if name.startswith(_DOMAINS_PREFIX):
        return _ENTITY_REGISTRY.get(name[len(_DOMAINS_PREFIX) :])
    return None


def get_entity_service_class(name: str) -> Callable[..., BaseDomainService] | None:
    spec = get_entity_spec(name)
    return spec.service_cls if spec else None
