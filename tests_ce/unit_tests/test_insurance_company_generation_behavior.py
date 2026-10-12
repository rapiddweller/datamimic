from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.domain_core.base_entity import IdentifierRegistry
from datamimic_ce.domains.insurance.generators.insurance_company_generator import InsuranceCompanyGenerator
from datamimic_ce.domains.insurance.models.insurance_company import InsuranceCompany
from datamimic_ce.domains.insurance.services.insurance_company_service import INSURANCE_COMPANY_SCHEMA


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


def _company(seed: int) -> tuple[InsuranceCompany, InsuranceCompanyGenerator, Random]:
    rng = Random(seed)
    generator = InsuranceCompanyGenerator(dataset="US", rng=rng)
    return InsuranceCompany(generator), generator, rng


class _FixedBitsRandom(Random):
    def __init__(self) -> None:
        super().__init__(1)
        self.calls = 0
        self.fail_next = False

    def getrandbits(self, k: int) -> int:
        assert k == 128
        self.calls += 1
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("scripted UUID draw failure")
        return 0


def test_company_id_is_lazy_cached_and_reads_public_rng_once() -> None:
    class RngObservedGenerator(InsuranceCompanyGenerator):
        rng_reads = 0

        @property
        def rng(self) -> Random:
            self.rng_reads += 1
            return self._rng

    rng = Random(947)
    generator = RngObservedGenerator(dataset="US", rng=rng)
    company = InsuranceCompany(generator)
    generator.rng_reads = 0

    assert "id" not in company.field_cache
    assert generator.rng_reads == 0
    assert company.id == "e9eb3c75-46d0-46ca-b11a-796932f26875"
    assert generator.rng_reads == 1
    state_after_id = rng.getstate()
    assert company.id == "e9eb3c75-46d0-46ca-b11a-796932f26875"
    assert rng.getstate() == state_after_id
    assert generator.rng_reads == 1


def test_id_first_and_company_data_first_preserve_seeded_values_and_rng_states() -> None:
    id_first, _, id_first_rng = _company(947)
    assert _rng_fingerprint(id_first_rng) == "13ea712baf02db38fefab3399ad4089f9af6b9baa41ca3162220af10943b080a"
    assert id_first.id == "e9eb3c75-46d0-46ca-b11a-796932f26875"
    assert _rng_fingerprint(id_first_rng) == "0cc04eaa6654064e8caf4dba2e8bdc791f17d190567f59c51305faa8e97ad2e3"
    assert id_first.company_data == {
        "name": "Allstate",
        "code": "ALST",
        "founded_year": "1931",
        "headquarters": "Northfield Township, IL",
        "website": "www.allstate.com",
    }
    assert _rng_fingerprint(id_first_rng) == "2bd92d72c86f278cc2360930ca52ea56db2f8f09dce3b5b3a03aa000ed53b103"

    data_first, _, data_first_rng = _company(947)
    assert _rng_fingerprint(data_first_rng) == "13ea712baf02db38fefab3399ad4089f9af6b9baa41ca3162220af10943b080a"
    assert data_first.company_data == {
        "name": "Geico",
        "code": "GEICO",
        "founded_year": "1936",
        "headquarters": "Chevy Chase, MD",
        "website": "www.geico.com",
    }
    assert _rng_fingerprint(data_first_rng) == "efc7dc87efee2dd86b4d5bf62d5870032db3912dbe087aecd1f47fd5da903613"
    assert data_first.id == "83feb99e-5b42-414a-a9eb-3c7546d086ca"
    assert _rng_fingerprint(data_first_rng) == "2bd92d72c86f278cc2360930ca52ea56db2f8f09dce3b5b3a03aa000ed53b103"


def test_bound_company_id_collision_is_claimed_without_redrawing() -> None:
    rng = _FixedBitsRandom()
    generator = InsuranceCompanyGenerator(dataset="US", rng=rng)
    registry = IdentifierRegistry()
    first, second = InsuranceCompany(generator), InsuranceCompany(generator)
    for company in (first, second):
        company._bind_identifier_registry(registry, "InsuranceCompany", INSURANCE_COMPANY_SCHEMA.fields, {})

    assert first.id == "00000000-0000-4000-8000-000000000000"
    assert second.id == "00000000-0000-4000-8000-000000000001"
    assert rng.calls == 2


def test_unbound_companies_may_keep_duplicate_id_candidates() -> None:
    rng = _FixedBitsRandom()
    generator = InsuranceCompanyGenerator(dataset="US", rng=rng)
    first, second = InsuranceCompany(generator), InsuranceCompany(generator)

    assert first.id == "00000000-0000-4000-8000-000000000000"
    assert second.id == "00000000-0000-4000-8000-000000000000"
    assert rng.calls == 2


def test_company_id_retries_after_rng_failure_without_caching_partial_result() -> None:
    rng = _FixedBitsRandom()
    rng.fail_next = True
    company = InsuranceCompany(InsuranceCompanyGenerator(dataset="US", rng=rng))

    with pytest.raises(RuntimeError, match="scripted UUID draw failure"):
        _ = company.id
    assert "id" not in company.field_cache

    assert company.id == "00000000-0000-4000-8000-000000000000"
    assert rng.calls == 2
    assert company.id == "00000000-0000-4000-8000-000000000000"
    assert rng.calls == 2


def test_company_id_candidate_generation_delegates_to_generator() -> None:
    class CandidateGenerator(InsuranceCompanyGenerator):
        calls = 0

        def generate_id_candidate(self) -> str:
            self.calls += 1
            return "00000000-0000-4000-8000-000000000042"

    generator = CandidateGenerator(dataset="US", rng=Random(53))
    company = InsuranceCompany(generator)

    assert company.id == "00000000-0000-4000-8000-000000000042"
    assert generator.calls == 1
