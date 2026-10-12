from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.public_sector.generators.educational_institution_generator import (
    EducationalInstitutionGenerator,
)
from datamimic_ce.domains.public_sector.models.educational_institution import EducationalInstitution


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class _ChoiceRandom(Random):
    def __init__(self, events: list[object], *, fail_once: bool = False) -> None:
        super().__init__(17)
        self.events = events
        self.fail_once = fail_once

    def choice(self, sequence):
        self.events.append(("choice", tuple(sequence)))
        if self.fail_once:
            self.fail_once = False
            raise RuntimeError("scripted name choice failure")
        return sequence[0]


class _ObservedGenerator(EducationalInstitutionGenerator):
    def __init__(self, rng: Random, events: list[object]) -> None:
        self.events = events
        self.rng_reads = 0
        super().__init__(dataset="US", rng=rng)

    @property
    def rng(self) -> Random:
        self.rng_reads += 1
        self.events.append("rng")
        return self._rng


class _FixedAddress:
    def __init__(self, events: list[object], *, fail: str | None = None) -> None:
        self.events = events
        self.fail = fail
        self.failed = False

    @property
    def city(self) -> str:
        self.events.append("city")
        if self.fail == "city" and not self.failed:
            self.failed = True
            raise RuntimeError("scripted city input failure")
        return "Springfield"

    @property
    def state(self) -> str:
        self.events.append("state")
        if self.fail == "state" and not self.failed:
            self.failed = True
            raise RuntimeError("scripted state input failure")
        return "PA"


class _InputInstitution(EducationalInstitution):
    def __init__(
        self,
        generator: EducationalInstitutionGenerator,
        events: list[object],
        institution_type: str,
        level: str,
        *,
        fail: str | None = None,
    ) -> None:
        super().__init__(generator)
        self.events = events
        self._address = _FixedAddress(events, fail=fail)
        self.institution_type = institution_type
        self._level = level
        self.fail = fail
        self.failed = False

    @property
    def address(self) -> _FixedAddress:
        return self._address

    @property
    def type(self) -> str:
        self.events.append("type")
        if self.fail == "type" and not self.failed:
            self.failed = True
            raise RuntimeError("scripted type input failure")
        return self.institution_type

    @property
    def level(self) -> str:
        self.events.append("level")
        if self.fail == "level" and not self.failed:
            self.failed = True
            raise RuntimeError("scripted level input failure")
        return self._level


def _candidates(city: str, state: str, institution_type: str, level: str) -> list[str]:
    if "University" in institution_type:
        return [
            f"{city} University",
            f"University of {city}",
            f"{state} State University",
            f"{city} Technical University",
            f"{city} Metropolitan University",
        ]
    if "College" in institution_type:
        return [
            f"{city} College",
            f"{city} Community College",
            f"{state} College",
            f"{city} Technical College",
            f"{city} Liberal Arts College",
        ]
    if "School" in institution_type:
        if "Elementary" in level:
            return [
                f"{city} Elementary School",
                f"{city} Primary School",
                f"{city} Academy",
                f"Washington Elementary School of {city}",
                "Lincoln Elementary School",
            ]
        if "Middle" in level:
            return [
                f"{city} Middle School",
                f"{city} Intermediate School",
                f"{city} Junior High School",
                "Jefferson Middle School",
                "Roosevelt Middle School",
            ]
        if "High" in level:
            return [
                f"{city} High School",
                f"{city} Senior High School",
                f"{state} High School",
                "Kennedy High School",
                "Roosevelt High School",
            ]
        return [
            f"{city} Academy",
            f"{city} School",
            f"{city} {level} School",
            f"{state} Academy",
            f"Central School of {city}",
        ]
    return [
        f"{city} Education Center",
        f"{city} Learning Institute",
        f"{city} Academy",
        f"{state} Institute",
        f"Central Institute of {city}",
    ]


@pytest.mark.parametrize(
    ("institution_type", "level"),
    [
        ("University", "Graduate"),
        ("College", "Higher Education"),
        ("Public School", "Elementary"),
        ("Public School", "Middle School"),
        ("Public School", "High School"),
        ("Public School", "Other"),
        ("Vocational Institute", "Career"),
    ],
)
def test_name_preserves_all_candidate_lists_and_input_choice_order(
    institution_type: str,
    level: str,
) -> None:
    events: list[object] = []
    rng = _ChoiceRandom(events)
    generator = _ObservedGenerator(rng, events)
    institution = _InputInstitution(generator, events, institution_type, level)
    candidates = _candidates("Springfield", "PA", institution_type, level)

    assert institution.name == candidates[0]
    assert events == ["city", "state", "type", "level", "rng", ("choice", tuple(candidates))]
    assert generator.rng_reads == 1
    assert institution.name == candidates[0]
    assert events == ["city", "state", "type", "level", "rng", ("choice", tuple(candidates))]


@pytest.mark.parametrize(
    ("institution_type", "level", "expected_index"),
    [
        ("University College School", "Elementary Middle High", 0),
        ("College School", "Elementary", 0),
        ("School", "Elementary Middle High", 0),
        ("School", "Middle High", 0),
        ("School", "High", 0),
    ],
)
def test_name_mixed_labels_keep_university_college_school_and_level_precedence(
    institution_type: str,
    level: str,
    expected_index: int,
) -> None:
    events: list[object] = []
    generator = _ObservedGenerator(_ChoiceRandom(events), events)
    institution = _InputInstitution(generator, events, institution_type, level)
    expected = _candidates("Springfield", "PA", institution_type, level)[expected_index]

    assert institution.name == expected
    assert events[3] == "level"
    assert events[-1] == ("choice", tuple(_candidates("Springfield", "PA", institution_type, level)))


@pytest.mark.parametrize("failure", ["city", "state", "type", "level"])
def test_name_input_failure_is_uncached_and_precedes_rng(failure: str) -> None:
    events: list[object] = []
    generator = _ObservedGenerator(_ChoiceRandom(events), events)
    institution = _InputInstitution(generator, events, "University", "Graduate", fail=failure)

    with pytest.raises(RuntimeError, match="scripted .* input failure"):
        _ = institution.name
    assert "name" not in institution.field_cache
    assert "rng" not in events
    assert generator.rng_reads == 0

    assert institution.name == "Springfield University"
    assert generator.rng_reads == 1


def test_name_choice_failure_is_uncached_and_retries() -> None:
    events: list[object] = []
    rng = _ChoiceRandom(events, fail_once=True)
    generator = _ObservedGenerator(rng, events)
    institution = _InputInstitution(generator, events, "University", "Graduate")

    with pytest.raises(RuntimeError, match="scripted name choice failure"):
        _ = institution.name
    assert "name" not in institution.field_cache

    assert institution.name == "Springfield University"
    assert generator.rng_reads == 2
    assert events == [
        "city",
        "state",
        "type",
        "level",
        "rng",
        ("choice", tuple(_candidates("Springfield", "PA", "University", "Graduate"))),
        "city",
        "state",
        "type",
        "level",
        "rng",
        ("choice", tuple(_candidates("Springfield", "PA", "University", "Graduate"))),
    ]


def test_name_delegates_after_resolving_city_state_type_and_level() -> None:
    events: list[object] = []

    class CandidateGenerator(_ObservedGenerator):
        def generate_name(self, city: str, state: str, institution_type: str, level: str) -> str:
            events.append(("generate_name", city, state, institution_type, level))
            return "Candidate"

    generator = CandidateGenerator(Random(44), events)
    institution = _InputInstitution(generator, events, "University", "Graduate")

    assert institution.name == "Candidate"
    assert events == [
        "city",
        "state",
        "type",
        "level",
        ("generate_name", "Springfield", "PA", "University", "Graduate"),
    ]


def test_name_first_and_website_first_preserve_seeded_outputs_and_rng_states() -> None:
    name_first_rng = Random(44)
    name_first_generator = EducationalInstitutionGenerator(dataset="US", rng=name_first_rng)
    name_first = EducationalInstitution(name_first_generator)
    address = name_first.address
    assert _fingerprint(name_first_rng) == "092d529825b02dd3c7fdb06cc222d08f5df8c09d343b24154991ffea64fd6bad"
    assert _fingerprint(address._row.city_generator.rng) == (
        "21c9630dbb020eb5cc089aecaa09fdb0be0ae4af7a6747150d1cf9f9b71ff9b3"
    )
    assert name_first.name == "Mingoville Elementary School"
    assert name_first.website == "https://www.mingovilleelementaryschool.k12.us"
    assert _fingerprint(name_first_rng) == "baab853cce7da97c3e28256216369d8ce988608caf229e151a5400fd8ee17a57"
    assert _fingerprint(address._row.city_generator.rng) == (
        "eff1682863b58763d4c7c65560d69368240d7dd86fbc355780295faab405a459"
    )

    website_first_rng = Random(44)
    website_first_generator = EducationalInstitutionGenerator(dataset="US", rng=website_first_rng)
    website_first = EducationalInstitution(website_first_generator)
    website_address = website_first.address
    assert website_first.website == "https://www.mingovilleelementaryschool.k12.us"
    assert website_first.name == "Mingoville Elementary School"
    assert _fingerprint(website_first_rng) == "baab853cce7da97c3e28256216369d8ce988608caf229e151a5400fd8ee17a57"
    assert _fingerprint(website_address._row.city_generator.rng) == (
        "eff1682863b58763d4c7c65560d69368240d7dd86fbc355780295faab405a459"
    )
