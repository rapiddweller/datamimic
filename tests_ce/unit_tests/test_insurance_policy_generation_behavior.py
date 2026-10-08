from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.domain_core.base_entity import IdentifierRegistry
from datamimic_ce.domains.insurance.generators.insurance_policy_generator import InsurancePolicyGenerator
from datamimic_ce.domains.insurance.models.insurance_coverage import InsuranceCoverage
from datamimic_ce.domains.insurance.models.insurance_policy import InsurancePolicy
from datamimic_ce.domains.insurance.services.insurance_policy_service import INSURANCE_POLICY_SCHEMA


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


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


class _CoverageCountRandom(Random):
    def __init__(self, count: int = 2) -> None:
        super().__init__(1)
        self.count = count
        self.randint_calls: list[tuple[int, int]] = []
        self.fail_next_count = False

    def randint(self, a: int, b: int) -> int:
        self.randint_calls.append((a, b))
        if self.fail_next_count:
            self.fail_next_count = False
            raise RuntimeError("scripted coverage-count failure")
        return self.count


def _policy(seed: int) -> tuple[InsurancePolicy, InsurancePolicyGenerator, Random]:
    rng = Random(seed)
    generator = InsurancePolicyGenerator(dataset="US", rng=rng)
    return InsurancePolicy(generator), generator, rng


def test_id_first_and_coverages_first_preserve_seeded_outputs_and_rng_state() -> None:
    id_first, _, id_first_rng = _policy(821)
    assert _rng_fingerprint(id_first_rng) == "af2d806447e7ca42c5783759f392ea74af2a8c0916babd85aeaab1226cad5742"
    assert id_first.id == "31c25662-4fa3-47a4-b8c1-0809552f2210"
    assert _rng_fingerprint(id_first_rng) == "8b8c7322354c617d6fcd5aaa3379761c41a8280d552b0ff004bd6a6d351b9d44"
    assert len(id_first.coverages) == 2
    assert _rng_fingerprint(id_first_rng) == "c3ca00beebd8e25e48ce7b523d8695f65704435ad0e16542f2e20d783795f37b"

    coverages_first, _, coverages_first_rng = _policy(821)
    assert _rng_fingerprint(coverages_first_rng) == "af2d806447e7ca42c5783759f392ea74af2a8c0916babd85aeaab1226cad5742"
    assert len(coverages_first.coverages) == 2
    assert _rng_fingerprint(coverages_first_rng) == "4723b2dcffdc5d710ad0e0cee668df87194b02231b11bed124dfabab2f3c9a5f"
    assert coverages_first.id == "f1474be9-31c2-4662-8fa3-37a4b8c10809"
    assert _rng_fingerprint(coverages_first_rng) == "661b1ba65fa3db7d3da469943e6bc19086746c575f5f0f914c3c9af4d44fed26"


def test_policy_id_is_lazy_cached_and_reads_public_rng_once() -> None:
    class RngObservedGenerator(InsurancePolicyGenerator):
        rng_reads = 0

        @property
        def rng(self) -> Random:
            self.rng_reads += 1
            return self._rng

    rng = Random(821)
    generator = RngObservedGenerator(dataset="US", rng=rng)
    policy = InsurancePolicy(generator)
    generator.rng_reads = 0

    assert "id" not in policy.field_cache
    assert generator.rng_reads == 0
    assert policy.id == "31c25662-4fa3-47a4-b8c1-0809552f2210"
    assert generator.rng_reads == 1
    state_after_id = rng.getstate()
    assert policy.id == "31c25662-4fa3-47a4-b8c1-0809552f2210"
    assert rng.getstate() == state_after_id
    assert generator.rng_reads == 1


def test_unbound_policies_may_keep_duplicate_id_candidates() -> None:
    rng = _FixedBitsRandom()
    generator = InsurancePolicyGenerator(dataset="US", rng=rng)
    rng.bit_requests.clear()
    first, second = InsurancePolicy(generator), InsurancePolicy(generator)

    assert first.id == "00000000-0000-4000-8000-000000000000"
    assert second.id == "00000000-0000-4000-8000-000000000000"
    assert rng.bit_requests == [128, 128]


def test_bound_policy_id_collision_is_claimed_without_redraw() -> None:
    rng = _FixedBitsRandom()
    generator = InsurancePolicyGenerator(dataset="US", rng=rng)
    rng.bit_requests.clear()
    registry = IdentifierRegistry()
    first, second = InsurancePolicy(generator), InsurancePolicy(generator)
    for policy in (first, second):
        policy._bind_identifier_registry(registry, "InsurancePolicy", INSURANCE_POLICY_SCHEMA.fields, {})

    assert first.id == "00000000-0000-4000-8000-000000000000"
    assert second.id == "00000000-0000-4000-8000-000000000001"
    assert rng.bit_requests == [128, 128]


def test_policy_id_retries_after_generation_failure_without_caching_partial_result() -> None:
    rng = _FixedBitsRandom()
    generator = InsurancePolicyGenerator(dataset="US", rng=rng)
    rng.bit_requests.clear()
    rng.fail_next_uuid = True
    policy = InsurancePolicy(generator)

    with pytest.raises(RuntimeError, match="scripted UUID draw failure"):
        _ = policy.id
    assert "id" not in policy.field_cache

    assert policy.id == "00000000-0000-4000-8000-000000000000"
    assert rng.bit_requests == [128, 128]


def test_policy_id_retries_after_claim_failure() -> None:
    class ClaimFailsOncePolicy(InsurancePolicy):
        claim_calls = 0

        def _claim_identifier(self, name: str, candidate: str) -> str:
            self.claim_calls += 1
            if self.claim_calls == 1:
                raise RuntimeError("scripted claim failure")
            return super()._claim_identifier(name, candidate)

    rng = _FixedBitsRandom()
    generator = InsurancePolicyGenerator(dataset="US", rng=rng)
    rng.bit_requests.clear()
    policy = ClaimFailsOncePolicy(generator)

    with pytest.raises(RuntimeError, match="scripted claim failure"):
        _ = policy.id
    assert "id" not in policy.field_cache

    assert policy.id == "00000000-0000-4000-8000-000000000000"
    assert rng.bit_requests == [128, 128]
    assert policy.claim_calls == 2


def test_policy_id_candidate_generation_delegates_to_generator() -> None:
    class CandidateGenerator(InsurancePolicyGenerator):
        calls = 0

        def generate_id_candidate(self) -> str:
            self.calls += 1
            return "00000000-0000-4000-8000-000000000042"

    generator = CandidateGenerator(dataset="US", rng=Random(821))
    policy = InsurancePolicy(generator)

    assert policy.id == "00000000-0000-4000-8000-000000000042"
    assert generator.calls == 1


def test_policy_coverages_count_is_lazy_cached_and_uses_one_public_rng_draw() -> None:
    class RngObservedGenerator(InsurancePolicyGenerator):
        rng_reads = 0

        @property
        def rng(self) -> Random:
            self.rng_reads += 1
            return self._rng

    rng = _CoverageCountRandom(count=2)
    generator = RngObservedGenerator(dataset="US", rng=rng)
    policy = InsurancePolicy(generator)
    generator.rng_reads = 0
    rng.randint_calls.clear()

    assert "coverages" not in policy.field_cache
    assert generator.rng_reads == 0
    assert len(policy.coverages) == 2
    assert generator.rng_reads == 1
    assert rng.randint_calls == [(1, 3)]
    cached_coverages = policy.coverages
    assert len(cached_coverages) == 2
    assert policy.coverages is cached_coverages
    assert generator.rng_reads == 1
    assert rng.randint_calls == [(1, 3)]


def test_policy_coverages_retries_after_count_draw_failure_without_caching() -> None:
    rng = _CoverageCountRandom(count=1)
    generator = InsurancePolicyGenerator(dataset="US", rng=rng)
    policy = InsurancePolicy(generator)
    rng.randint_calls.clear()
    rng.fail_next_count = True

    with pytest.raises(RuntimeError, match="scripted coverage-count failure"):
        _ = policy.coverages
    assert "coverages" not in policy.field_cache

    assert len(policy.coverages) == 1
    assert rng.randint_calls == [(1, 3), (1, 3)]


def test_policy_coverage_count_generation_delegates_to_generator() -> None:
    class CoverageCountGenerator(InsurancePolicyGenerator):
        calls = 0

        def generate_coverage_count(self) -> int:
            self.calls += 1
            return 2

    generator = CoverageCountGenerator(dataset="US", rng=Random(821))
    policy = InsurancePolicy(generator)

    assert len(policy.coverages) == 2
    assert generator.calls == 1


@pytest.mark.parametrize("count", [1, 3])
def test_policy_coverage_count_builds_distinct_children_on_shared_generator(count: int) -> None:
    rng = _CoverageCountRandom(count=count)
    generator = InsurancePolicyGenerator(dataset="US", rng=rng)
    policy = InsurancePolicy(generator)

    coverages = policy.coverages

    assert len(coverages) == count
    assert len({id(coverage) for coverage in coverages}) == count
    assert all(isinstance(coverage, InsuranceCoverage) for coverage in coverages)
    assert all(
        coverage.insurance_coverage_generator is generator.insurance_coverage_generator for coverage in coverages
    )


def test_policies_sharing_generator_have_separate_mutable_coverage_lists() -> None:
    rng = _CoverageCountRandom(count=1)
    generator = InsurancePolicyGenerator(dataset="US", rng=rng)
    first, second = InsurancePolicy(generator), InsurancePolicy(generator)

    first_coverages = first.coverages
    second_coverages = second.coverages

    assert first_coverages is not second_coverages
    assert first_coverages[0] is not second_coverages[0]
    first_coverages.clear()
    assert len(second.coverages) == 1


def test_constructing_coverages_does_not_draw_from_shared_coverage_generator() -> None:
    rng = _CoverageCountRandom(count=2)
    generator = InsurancePolicyGenerator(dataset="US", rng=rng)
    coverage_rng = generator.insurance_coverage_generator.rng
    state_before = coverage_rng.getstate()
    policy = InsurancePolicy(generator)

    coverages = policy.coverages

    assert len(coverages) == 2
    assert coverage_rng.getstate() == state_before
    assert all("coverage_data" not in coverage.field_cache for coverage in coverages)


def test_policy_coverage_count_draw_precedes_each_child_generator_lookup() -> None:
    events: list[tuple[str, object]] = []

    class EventRandom(_CoverageCountRandom):
        def randint(self, a: int, b: int) -> int:
            events.append(("count_draw", (a, b)))
            return super().randint(a, b)

    class EventGenerator(InsurancePolicyGenerator):
        @property
        def insurance_coverage_generator(self):
            events.append(("child_generator", None))
            return self._insurance_coverage_generator

    rng = EventRandom(count=3)
    generator = EventGenerator(dataset="US", rng=rng)
    policy = InsurancePolicy(generator)
    events.clear()

    assert len(policy.coverages) == 3
    assert events == [
        ("count_draw", (1, 3)),
        ("child_generator", None),
        ("child_generator", None),
        ("child_generator", None),
    ]


def test_policy_coverage_count_failure_does_not_lookup_child_generator() -> None:
    class CountingGenerator(InsurancePolicyGenerator):
        child_lookups = 0

        @property
        def insurance_coverage_generator(self):
            self.child_lookups += 1
            return self._insurance_coverage_generator

    rng = _CoverageCountRandom(count=1)
    generator = CountingGenerator(dataset="US", rng=rng)
    policy = InsurancePolicy(generator)
    rng.randint_calls.clear()
    rng.fail_next_count = True

    with pytest.raises(RuntimeError, match="scripted coverage-count failure"):
        _ = policy.coverages

    assert "coverages" not in policy.field_cache
    assert generator.child_lookups == 0
    assert rng.randint_calls == [(1, 3)]


def test_policy_coverage_child_lookup_failure_retries_without_caching_partial_list() -> None:
    class FailsSecondChildLookupGenerator(InsurancePolicyGenerator):
        child_lookups = 0

        @property
        def insurance_coverage_generator(self):
            self.child_lookups += 1
            if self.child_lookups == 2:
                raise RuntimeError("scripted child-generator lookup failure")
            return self._insurance_coverage_generator

    rng = _CoverageCountRandom(count=2)
    generator = FailsSecondChildLookupGenerator(dataset="US", rng=rng)
    policy = InsurancePolicy(generator)
    rng.randint_calls.clear()

    with pytest.raises(RuntimeError, match="scripted child-generator lookup failure"):
        _ = policy.coverages
    assert "coverages" not in policy.field_cache
    assert rng.randint_calls == [(1, 3)]
    assert generator.child_lookups == 2

    coverages = policy.coverages
    assert len(coverages) == 2
    assert len({id(coverage) for coverage in coverages}) == 2
    assert all(
        coverage.insurance_coverage_generator is generator._insurance_coverage_generator for coverage in coverages
    )
    assert rng.randint_calls == [(1, 3), (1, 3)]
    assert generator.child_lookups == 4
