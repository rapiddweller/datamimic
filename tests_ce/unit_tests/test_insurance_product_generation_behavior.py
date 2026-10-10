from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.domain_core.base_entity import IdentifierRegistry
from datamimic_ce.domains.insurance.generators.insurance_product_generator import InsuranceProductGenerator
from datamimic_ce.domains.insurance.models.insurance_product import InsuranceProduct
from datamimic_ce.domains.insurance.services.insurance_product_service import INSURANCE_PRODUCT_SCHEMA


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


def _product(seed: int) -> tuple[InsuranceProduct, InsuranceProductGenerator, Random]:
    rng = Random(seed)
    generator = InsuranceProductGenerator(dataset="US", rng=rng)
    return InsuranceProduct(generator), generator, rng


class _FixedBitsRandom(Random):
    def __init__(self) -> None:
        super().__init__(1)
        self.bit_requests: list[int] = []
        self.fail_next_uuid = False

    def getrandbits(self, k: int) -> int:
        self.bit_requests.append(k)
        if k == 128 and self.fail_next_uuid:
            self.fail_next_uuid = False
            raise RuntimeError("scripted UUID draw failure")
        return 0


def test_id_first_product_data_first_and_coverages_first_preserve_seeded_outputs_and_rng_state() -> None:
    id_first, _, id_first_rng = _product(821)
    assert _rng_fingerprint(id_first_rng) == "9179bcdc83f32c5221f9d10b8ca08d4d6680685a635d42884f30e5a38a9b4eab"
    assert id_first.id == "f0dd2833-5c7b-41d9-8296-57e04de74b47"
    assert _rng_fingerprint(id_first_rng) == "a6d772081d3559c3512952858f70d84da2685d3252da691a76d007ebe77134da"
    assert id_first.product_data == {
        "type": "Life Insurance",
        "code": "LIFE",
        "description": "Provides financial benefit to dependents after policyholder's death",
    }
    assert _rng_fingerprint(id_first_rng) == "9a0f7da6cc0f317d1ab84f9737326ab5907124acb698b1ca735606651d1ba920"
    assert len(id_first.coverages) == 3
    assert _rng_fingerprint(id_first_rng) == "355ae9cede8203d1526fa2a470433cdcc3ecbabc3a784d63508de5383a6cc52c"

    data_first, _, data_first_rng = _product(821)
    assert _rng_fingerprint(data_first_rng) == "9179bcdc83f32c5221f9d10b8ca08d4d6680685a635d42884f30e5a38a9b4eab"
    assert data_first.product_data == {
        "type": "Health Insurance",
        "code": "HLTH",
        "description": "Covers medical expenses for illnesses and injuries",
    }
    assert _rng_fingerprint(data_first_rng) == "19c21dc68f8619ca4774235b539f96f140b52e8af021f484244d581a5bc02366"
    assert data_first.id == "18f2b889-3b0d-4db4-b0dd-28335c7b61d9"
    assert _rng_fingerprint(data_first_rng) == "9a0f7da6cc0f317d1ab84f9737326ab5907124acb698b1ca735606651d1ba920"
    assert len(data_first.coverages) == 3
    assert _rng_fingerprint(data_first_rng) == "355ae9cede8203d1526fa2a470433cdcc3ecbabc3a784d63508de5383a6cc52c"

    coverages_first, _, coverages_first_rng = _product(821)
    assert _rng_fingerprint(coverages_first_rng) == "9179bcdc83f32c5221f9d10b8ca08d4d6680685a635d42884f30e5a38a9b4eab"
    assert len(coverages_first.coverages) == 1
    assert _rng_fingerprint(coverages_first_rng) == "19c21dc68f8619ca4774235b539f96f140b52e8af021f484244d581a5bc02366"
    assert coverages_first.id == "18f2b889-3b0d-4db4-b0dd-28335c7b61d9"
    assert _rng_fingerprint(coverages_first_rng) == "9a0f7da6cc0f317d1ab84f9737326ab5907124acb698b1ca735606651d1ba920"
    assert coverages_first.product_data == {
        "type": "Boat Insurance",
        "code": "BOAT",
        "description": "Covers watercraft and related liabilities",
    }
    assert _rng_fingerprint(coverages_first_rng) == "355ae9cede8203d1526fa2a470433cdcc3ecbabc3a784d63508de5383a6cc52c"


def test_product_id_is_lazy_cached_and_reads_public_rng_once() -> None:
    class RngObservedGenerator(InsuranceProductGenerator):
        rng_reads = 0

        @property
        def rng(self) -> Random:
            self.rng_reads += 1
            return self._rng

    rng = Random(821)
    generator = RngObservedGenerator(dataset="US", rng=rng)
    product = InsuranceProduct(generator)
    generator.rng_reads = 0

    assert "id" not in product.field_cache
    assert generator.rng_reads == 0
    assert product.id == "f0dd2833-5c7b-41d9-8296-57e04de74b47"
    assert generator.rng_reads == 1
    state_after_id = rng.getstate()
    assert product.id == "f0dd2833-5c7b-41d9-8296-57e04de74b47"
    assert rng.getstate() == state_after_id
    assert generator.rng_reads == 1


def test_unbound_products_may_keep_duplicate_id_candidates() -> None:
    rng = _FixedBitsRandom()
    generator = InsuranceProductGenerator(dataset="US", rng=rng)
    rng.bit_requests.clear()
    first, second = InsuranceProduct(generator), InsuranceProduct(generator)

    assert first.id == "00000000-0000-4000-8000-000000000000"
    assert second.id == "00000000-0000-4000-8000-000000000000"
    assert rng.bit_requests == [128, 128]


def test_bound_product_id_collision_is_claimed_without_redraw() -> None:
    rng = _FixedBitsRandom()
    generator = InsuranceProductGenerator(dataset="US", rng=rng)
    rng.bit_requests.clear()
    registry = IdentifierRegistry()
    first, second = InsuranceProduct(generator), InsuranceProduct(generator)
    for product in (first, second):
        product._bind_identifier_registry(registry, "InsuranceProduct", INSURANCE_PRODUCT_SCHEMA.fields, {})

    assert first.id == "00000000-0000-4000-8000-000000000000"
    assert second.id == "00000000-0000-4000-8000-000000000001"
    assert rng.bit_requests == [128, 128]


def test_product_id_retries_after_generation_failure_without_caching_partial_result() -> None:
    rng = _FixedBitsRandom()
    generator = InsuranceProductGenerator(dataset="US", rng=rng)
    rng.bit_requests.clear()
    rng.fail_next_uuid = True
    product = InsuranceProduct(generator)

    with pytest.raises(RuntimeError, match="scripted UUID draw failure"):
        _ = product.id
    assert "id" not in product.field_cache

    assert product.id == "00000000-0000-4000-8000-000000000000"
    assert rng.bit_requests == [128, 128]


def test_product_id_retries_generation_after_claim_failure() -> None:
    class ClaimFailsOnceProduct(InsuranceProduct):
        claim_calls = 0

        def _claim_identifier(self, name: str, candidate: str) -> str:
            self.claim_calls += 1
            if self.claim_calls == 1:
                raise RuntimeError("scripted claim failure")
            return super()._claim_identifier(name, candidate)

    rng = _FixedBitsRandom()
    generator = InsuranceProductGenerator(dataset="US", rng=rng)
    rng.bit_requests.clear()
    product = ClaimFailsOnceProduct(generator)

    with pytest.raises(RuntimeError, match="scripted claim failure"):
        _ = product.id
    assert "id" not in product.field_cache

    assert product.id == "00000000-0000-4000-8000-000000000000"
    assert rng.bit_requests == [128, 128]
    assert product.claim_calls == 2


def test_product_id_candidate_generation_delegates_to_generator() -> None:
    class CandidateGenerator(InsuranceProductGenerator):
        calls = 0

        def generate_id_candidate(self) -> str:
            self.calls += 1
            return "00000000-0000-4000-8000-000000000042"

    generator = CandidateGenerator(dataset="US", rng=Random(821))
    product = InsuranceProduct(generator)

    assert product.id == "00000000-0000-4000-8000-000000000042"
    assert generator.calls == 1
