from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.shared.demographics.sampler import DemographicSample
from datamimic_ce.domains.shared.generators.person_generator import PersonGenerator
from datamimic_ce.domains.shared.literal_generators.temporal.birthdate_generator import BirthdateGenerator
from datamimic_ce.domains.shared.models.person import Person


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


def _person(age: int | None, seed: int = 150) -> tuple[PersonGenerator, Person, list[DemographicSample]]:
    generator = PersonGenerator(dataset="US", rng=Random(seed))
    reserved: list[DemographicSample] = []
    sample = DemographicSample(age=age, sex=None, conditions=frozenset())

    def reserve() -> DemographicSample:
        reserved.append(sample)
        return sample

    generator.reserve_demographic_sample = reserve
    return generator, Person(generator), reserved


def test_person_birthdate_delegates_reserved_age_to_generator() -> None:
    expected = datetime(2000, 1, 2)

    class CandidateGenerator(PersonGenerator):
        def generate_birthdate(self, sample_age: int | None) -> datetime:
            assert sample_age == 0
            return expected

    generator = CandidateGenerator(dataset="US", rng=Random(150))
    sample = DemographicSample(age=0, sex=None, conditions=frozenset())
    generator.reserve_demographic_sample = lambda: sample
    person = Person(generator)

    assert person.birthdate == expected


@pytest.mark.parametrize("age", [None, 0, 32])
def test_birthdate_policy_selects_only_the_matching_generation_path(age: int | None, monkeypatch) -> None:
    generator, person, reserved = _person(age)
    events: list[str] = []
    expected = datetime(2000 + (age or 0), 1, 2)

    def constrained(requested_age: int) -> datetime:
        events.append(f"constrained:{requested_age}")
        return expected

    def fallback() -> datetime:
        events.append("fallback")
        return expected

    monkeypatch.setattr(generator, "generate_birthdate_for_age", constrained)
    monkeypatch.setattr(generator.birthdate_generator, "generate", fallback)

    assert person.birthdate == expected
    assert person.birthdate == expected
    assert reserved == [person.demographic_sample]
    assert events == (["fallback"] if age is None else [f"constrained:{age}"])


def test_constrained_birthdate_failure_retries_with_reserved_sample_and_fresh_derived_rng(
    monkeypatch,
) -> None:
    generator, person, reserved = _person(32)
    original = BirthdateGenerator.generate
    calls = 0
    child_rngs: list[Random] = []

    def fail_after_generation_once(birthdate_generator: BirthdateGenerator) -> datetime:
        nonlocal calls
        calls += 1
        child_rngs.append(birthdate_generator.rng)
        if calls == 1:
            original(birthdate_generator)
            raise RuntimeError("constrained birthdate failed")
        return original(birthdate_generator)

    monkeypatch.setattr(BirthdateGenerator, "generate", fail_after_generation_once)
    parent_before = _fingerprint(generator._rng)

    with pytest.raises(RuntimeError, match="constrained birthdate failed"):
        _ = person.birthdate
    assert "birthdate" not in person.field_cache
    after_failure = _fingerprint(generator._rng)
    assert reserved == [person.demographic_sample]
    assert after_failure != parent_before

    result = person.birthdate
    assert isinstance(result, datetime)
    assert person.birthdate is result
    assert "birthdate" in person.field_cache
    assert calls == 2
    assert len(child_rngs) == 2
    assert child_rngs[0] is not child_rngs[1]
    assert _fingerprint(generator._rng) != after_failure
    assert len(reserved) == 1


def test_fallback_birthdate_failure_retries_existing_stream_and_caches_success() -> None:
    generator, person, _ = _person(None)
    birthdate_rng = generator.birthdate_generator._date_generator.rng
    parent_before = _fingerprint(generator._rng)
    fallback_before = _fingerprint(birthdate_rng)
    original = generator.birthdate_generator.generate
    calls = 0

    def fail_after_consuming_stream() -> datetime:
        nonlocal calls
        calls += 1
        if calls == 1:
            original()
            raise RuntimeError("fallback birthdate failed")
        return original()

    generator.birthdate_generator.generate = fail_after_consuming_stream
    with pytest.raises(RuntimeError, match="fallback birthdate failed"):
        _ = person.birthdate
    assert "birthdate" not in person.field_cache
    assert _fingerprint(generator._rng) == parent_before
    assert _fingerprint(birthdate_rng) != fallback_before

    result = person.birthdate
    assert person.birthdate is result
    assert calls == 2


def test_shared_generator_person_birthdates_cache_per_entity() -> None:
    generator = PersonGenerator(dataset="US", rng=Random(150))
    samples = iter(
        [
            DemographicSample(age=32, sex=None, conditions=frozenset()),
            DemographicSample(age=32, sex=None, conditions=frozenset()),
        ]
    )
    generator.reserve_demographic_sample = lambda: next(samples)
    first = Person(generator)
    second = Person(generator)
    before = _fingerprint(generator._rng)

    first_date = first.birthdate
    after_first = _fingerprint(generator._rng)
    assert first.birthdate is first_date
    assert _fingerprint(generator._rng) == after_first

    second_date = second.birthdate
    assert second.birthdate is second_date
    assert first.birthdate is first_date
    assert after_first != before
    assert _fingerprint(generator._rng) != after_first


def test_seeded_birthdate_first_and_gender_first_keep_outputs_and_rng_states() -> None:
    birthdate_first_generator, birthdate_first, _ = _person(32)
    assert _fingerprint(birthdate_first_generator._rng) == (
        "ec340241ae403e05b4367352f91408c587965a41a1597bf12b9371d08e64f166"
    )
    assert birthdate_first.birthdate == datetime(1992, 9, 19, 5, 50, 27)
    assert _fingerprint(birthdate_first_generator._rng) == (
        "04f537796f8bbf795ac15761ca4d1768ce4d34e0dbc4b91b9d0df4b13a8df827"
    )
    birthdate_first_gender = birthdate_first.gender
    assert birthdate_first_gender in {"female", "male", "other"}

    gender_first_generator, gender_first, _ = _person(32)
    assert gender_first.gender == birthdate_first_gender
    assert _fingerprint(gender_first_generator._rng) == (
        "ec340241ae403e05b4367352f91408c587965a41a1597bf12b9371d08e64f166"
    )
    assert gender_first.birthdate == datetime(1992, 9, 19, 5, 50, 27)
    assert _fingerprint(gender_first_generator._rng) == (
        "04f537796f8bbf795ac15761ca4d1768ce4d34e0dbc4b91b9d0df4b13a8df827"
    )
    assert _fingerprint(gender_first_generator.gender_generator.rng) == (
        "449bd4fc6e70d885613f20ffb68a25e79d45d2e685bb0cc0a26d45a9c1b9dcb8"
    )
