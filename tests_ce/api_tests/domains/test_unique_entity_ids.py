from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Sequence
from random import Random
from typing import TypeVar

import pytest

from datamimic_ce.domains.domain_core.attribute_catalog import field
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.domain_core.base_entity import BaseEntity
from datamimic_ce.domains.ecommerce.services.order_service import OrderService
from datamimic_ce.domains.ecommerce.services.product_service import ProductService
from datamimic_ce.domains.finance.services.transaction_service import TransactionService
from datamimic_ce.domains.healthcare.services.doctor_service import DoctorService
from datamimic_ce.domains.healthcare.services.hospital_service import HospitalService
from datamimic_ce.domains.healthcare.services.medical_device_service import MedicalDeviceService
from datamimic_ce.domains.healthcare.services.medical_procedure_service import MedicalProcedureService
from datamimic_ce.domains.healthcare.services.patient_service import PatientService
from datamimic_ce.domains.insurance.services.insurance_company_service import InsuranceCompanyService
from datamimic_ce.domains.insurance.services.insurance_policy_service import InsurancePolicyService
from datamimic_ce.domains.insurance.services.insurance_product_service import InsuranceProductService
from datamimic_ce.domains.public_sector.services.administration_office_service import AdministrationOfficeService
from datamimic_ce.domains.public_sector.services.educational_institution_service import EducationalInstitutionService
from datamimic_ce.domains.public_sector.services.police_officer_service import PoliceOfficerService

_T = TypeVar("_T")


class _CollidingRandom(Random):
    """Return identical ID candidates twice, then let retry candidates differ."""

    def __init__(self) -> None:
        super().__init__(0)
        self.calls: defaultdict[str, int] = defaultdict(int)

    def _call(self, name: str) -> int:
        call = self.calls[name]
        self.calls[name] += 1
        return call

    def reset(self) -> None:
        self.calls.clear()

    def choice(self, seq: Sequence[_T]) -> _T:
        return seq[0] if self._call("choice") < 64 else seq[-1]

    def randint(self, a: int, b: int) -> int:
        return a if self._call("randint") < 64 else b

    def getrandbits(self, k: int) -> int:
        call = self._call("getrandbits")
        return 0 if call < 2 else call

    def random(self) -> float:
        call = self._call("random")
        return 0.0 if call < 64 else 0.5


_SERVICE_IDS = (
    (
        PatientService,
        "patient_id",
        lambda entity: entity.patient_id,
        r"PAT-[0-9A-F]{8}",
        ("PAT-12DD272D", "PAT-1371C171"),
    ),
    (DoctorService, "doctor_id", lambda entity: entity.doctor_id, r"DOC-[0-9A-F]{8}", ("DOC-23B1612D", "DOC-D272D137")),
    (
        HospitalService,
        "hospital_id",
        lambda entity: entity.hospital_id,
        r"HOSP-[0-9A-F]{8}",
        ("HOSP-23B1612D", "HOSP-D272D137"),
    ),
    (
        MedicalDeviceService,
        "device_id",
        lambda entity: entity.device_id,
        r"DEV-[0-9]{8}",
        ("DEV-01815908", "DEV-30166131"),
    ),
    (
        MedicalProcedureService,
        "procedure_id",
        lambda entity: entity.procedure_id,
        r"PROC-[0-9A-F]{8}",
        ("PROC-A4C123B1", "PROC-612DD272"),
    ),
    (
        OrderService,
        "order_id",
        lambda entity: entity.order_id,
        r"ORD[A-Z0-9]{8}",
        ("ORD8GXD6NCF", "ORD0EPF91DH"),
    ),
    (
        ProductService,
        "product_id",
        lambda entity: entity.product_id,
        r"PROD[A-Z0-9]{8}",
        ("PRODJZDE8GXD", "PRODCF10EPF9"),
    ),
    (
        TransactionService,
        "transaction_id",
        lambda entity: entity.transaction_id,
        r"[A-Z0-9]{16}",
        ("EH60KVJ50CE9UVW5", "EFR4EDT2SYWB3WKH"),
    ),
    (
        InsuranceCompanyService,
        "id",
        lambda entity: entity.id,
        r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        ("6513270e-269e-4d37-b2a7-4de452e6b438", "d23f0824-128b-4f33-8c5c-7fd0a6a3a450"),
    ),
    (
        InsuranceProductService,
        "id",
        lambda entity: entity.id,
        r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        ("d23f0824-128b-4f33-8c5c-7fd0a6a3a450", "9531985d-5d9d-49f8-9818-e811892f902b"),
    ),
    (
        InsurancePolicyService,
        "id",
        lambda entity: entity.id,
        r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        ("3d9c1724-11e2-4b8f-ab0d-549b6f03675a", "0f21ddb6-6cad-4a26-8d11-6ece1738f7d9"),
    ),
    (
        AdministrationOfficeService,
        "office_id",
        lambda entity: entity.office_id,
        r"ADM-[0-9A-F]{8}",
        ("ADM-12DD272D", "ADM-1371C171"),
    ),
    (
        EducationalInstitutionService,
        "institution_id",
        lambda entity: entity.institution_id,
        r"EDU-[0-9A-F]{8}",
        ("EDU-B1612DD2", "EDU-72D1371C"),
    ),
    (
        PoliceOfficerService,
        "officer_id",
        lambda entity: entity.officer_id,
        r"OFF-[0-9A-F]{8}",
        ("OFF-12DD272D", "OFF-1371C171"),
    ),
)

_COLLISION_TEST_SERVICES = tuple(case for case in _SERVICE_IDS if case[0] is not TransactionService)


@pytest.mark.parametrize(("service_type", "field_name", "get_id", "id_pattern", "_expected"), _COLLISION_TEST_SERVICES)
def test_service_batch_keeps_ids_unique_after_candidate_collision(
    service_type, field_name: str, get_id, id_pattern: str, _expected
) -> None:
    rng = _CollidingRandom()
    service = service_type(rng=rng)
    rng.reset()

    identifiers = [get_id(entity) for entity in service.generate_batch(3)]

    assert any(count >= 2 for count in rng.calls.values()), "test RNG did not supply repeated candidate components"
    assert identifiers[0] != identifiers[1], f"{service_type.__name__} kept a colliding candidate"
    assert len(identifiers) == len(set(identifiers))
    assert all(re.fullmatch(id_pattern, identifier) for identifier in identifiers)


@pytest.mark.parametrize(("service_type", "_field_name", "get_id", "_pattern", "expected"), _SERVICE_IDS)
def test_collision_free_seeded_ids_keep_exact_values_and_replay(
    service_type, _field_name, get_id, _pattern, expected
) -> None:
    first = [get_id(entity) for entity in service_type(rng=Random(7)).generate_batch(2)]
    second = [get_id(entity) for entity in service_type(rng=Random(7)).generate_batch(2)]

    assert tuple(first) == expected
    assert second == first


@pytest.mark.parametrize(("service_type", "field_name", "_get_id", "id_pattern", "_expected"), _SERVICE_IDS)
def test_schema_declares_only_the_approved_unique_identifier(
    service_type, field_name: str, _get_id, id_pattern: str, _expected
) -> None:
    declarations = {
        spec.name: spec.unique_identifier_format
        for spec in service_type.attribute_specs()
        if spec.unique_identifier_format is not None
    }

    expected_format = "uuid4" if field_name == "id" else id_pattern
    assert declarations == {field_name: expected_format}


def test_nested_policy_company_and_product_ids_are_unique_after_collision(monkeypatch: pytest.MonkeyPatch) -> None:
    from datamimic_ce.domains.insurance.models import insurance_company, insurance_product

    def duplicate_then_unique():
        calls = 0

        def candidate(_rng):
            nonlocal calls
            calls += 1
            value = 1 if calls < 3 else calls
            return f"00000000-0000-4000-8000-{value:012d}"

        return candidate

    monkeypatch.setattr(insurance_company, "uuid4_from_random", duplicate_then_unique())
    monkeypatch.setattr(insurance_product, "uuid4_from_random", duplicate_then_unique())
    service = InsurancePolicyService(rng=Random(7))
    policies = service.generate_batch(3)

    company_ids = [policy.company.id for policy in policies]
    product_ids = [policy.product.id for policy in policies]

    assert len(company_ids) == len(set(company_ids))
    assert len(product_ids) == len(set(product_ids))


def test_transaction_ids_are_unique_after_regex_generator_collision(monkeypatch: pytest.MonkeyPatch) -> None:
    from datamimic_ce.domains.common.literal_generators.string_generator import StringGenerator

    calls = 0

    def candidate(_pattern: str, *, rng: Random) -> str:
        nonlocal calls
        calls += 1
        return "A" * 16 if calls < 3 else "B" * 16

    monkeypatch.setattr(StringGenerator, "rnd_str_from_regex", staticmethod(candidate))
    identifiers = [entity.transaction_id for entity in TransactionService(rng=Random(1)).generate_batch(3)]

    assert calls >= 3
    assert len(identifiers) == len(set(identifiers))


def test_finite_identifier_format_exhaustion_is_explicit() -> None:
    class TinyEntity(BaseEntity):
        def __init__(self, generator: BaseDomainGenerator) -> None:
            super().__init__(generator)
            self._candidate = "ONLYA"

        @property
        def entity_id(self) -> str:
            return self._claim_identifier("entity_id", self._candidate)

        def to_dict(self) -> dict[str, object]:
            return {"entity_id": self.entity_id}

    attributes = (field("entity_id", str, "test ID", unique_identifier_format="ONLY[A]{1}"),)
    first = TinyEntity(BaseDomainGenerator(rng=Random(1)))
    second = TinyEntity(BaseDomainGenerator(rng=Random(1)))
    registry: dict[tuple[str, str], set[str]] = {}
    first._bind_identifier_registry(registry, "TinyEntity", attributes, {})
    second._bind_identifier_registry(registry, "TinyEntity", attributes, {})

    assert first.entity_id == "ONLYA"
    with pytest.raises(ValueError, match="exhausted"):
        _ = second.entity_id
