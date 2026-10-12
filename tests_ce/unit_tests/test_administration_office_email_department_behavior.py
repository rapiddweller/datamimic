from __future__ import annotations

from random import Random

import pytest

from datamimic_ce.domains.domain_core.property_cache import property_cache
from datamimic_ce.domains.public_sector.generators.administration_office_generator import AdministrationOfficeGenerator
from datamimic_ce.domains.public_sector.models.administration_office import AdministrationOffice


class _ObservedGenerator(AdministrationOfficeGenerator):
    def __init__(self, events: list[object]) -> None:
        self.events = events
        super().__init__(dataset="US", rng=Random(153))


class _TrackedWebsite(str):
    def __new__(cls, value: str, events: list[object]):
        instance = super().__new__(cls, value)
        instance.events = events
        return instance

    def replace(self, old: str, new: str, count: int = -1) -> str:
        self.events.append(("replace", old, new))
        return super().replace(old, new, count)


class _TrackedOfficeType(str):
    def __new__(cls, value: str, events: list[object]):
        instance = super().__new__(cls, value)
        instance.events = events
        return instance

    def lower(self) -> str:
        self.events.append("lower")
        return super().lower()


class _InputOffice(AdministrationOffice):
    def __init__(
        self,
        generator: AdministrationOfficeGenerator,
        events: list[object],
        office_type: str,
        website: str = "https://www.example.test/path",
        fail: str | None = None,
    ) -> None:
        super().__init__(generator)
        self.events = events
        self.office_type = office_type
        self.website_value = website
        self.fail = fail
        self.failed = False

    @property
    @property_cache
    def website(self) -> str:
        self.events.append("website")
        if self.fail == "website" and not self.failed:
            self.failed = True
            raise RuntimeError("scripted website failure")
        return _TrackedWebsite(self.website_value, self.events)

    @property
    @property_cache
    def type(self) -> str:
        self.events.append("type")
        if self.fail == "type" and not self.failed:
            self.failed = True
            raise RuntimeError("scripted office type failure")
        return _TrackedOfficeType(self.office_type, self.events)


@pytest.mark.parametrize(
    ("office_type", "department"),
    [
        ("TAX Motor Social", "tax"),
        ("Motor Social", "dmv"),
        ("Motor Vehicle", "dmv"),
        ("DMV Office", "dmv"),
        ("Social Permit", "socialservices"),
        ("Social Services", "socialservices"),
        ("Welfare Office", "socialservices"),
        ("Permit Election", "permits"),
        ("Permit Office", "permits"),
        ("Licensing", "permits"),
        ("Election Health", "elections"),
        ("Election Board", "elections"),
        ("Health Housing", "health"),
        ("Health Department", "health"),
        ("Housing Environment", "housing"),
        ("Housing Office", "housing"),
        ("Environment Planning", "environment"),
        ("Environment Agency", "environment"),
        ("Planning and Development", "planning"),
        ("Development Agency", "planning"),
        ("Unknown", "info"),
        ("", "info"),
    ],
)
def test_email_department_priority_aliases_case_and_cache(office_type: str, department: str) -> None:
    events: list[object] = []
    office = _InputOffice(_ObservedGenerator(events), events, office_type)

    assert office.email == f"{department}@example.test/path"
    assert events == [
        "website",
        ("replace", "https://www.", ""),
        "type",
        "lower",
    ]
    assert office.email == f"{department}@example.test/path"
    assert len(events) == 4


@pytest.mark.parametrize(
    ("failure", "first_events", "retry_events"),
    [
        (
            "website",
            ["website"],
            ["website", ("replace", "https://www.", ""), "type", "lower"],
        ),
        (
            "type",
            ["website", ("replace", "https://www.", ""), "type"],
            [("replace", "https://www.", ""), "type", "lower"],
        ),
    ],
)
def test_email_input_failure_is_uncached_and_retry_reuses_successful_inputs(
    failure: str,
    first_events: list[object],
    retry_events: list[object],
) -> None:
    events: list[object] = []
    office = _InputOffice(_ObservedGenerator(events), events, "Tax Office", fail=failure)

    error_message = "scripted website failure" if failure == "website" else "scripted office type failure"
    with pytest.raises(RuntimeError, match=error_message):
        _ = office.email
    assert "email" not in office.field_cache
    assert events == first_events

    assert office.email == "tax@example.test/path"
    assert "email" in office.field_cache
    assert events == first_events + retry_events
    assert office.email == "tax@example.test/path"
    assert events == first_events + retry_events


def test_offices_sharing_generator_cache_email_per_entity() -> None:
    events: list[object] = []
    generator = _ObservedGenerator(events)
    first = _InputOffice(generator, events, "Tax Office", "https://www.first.test")
    second = _InputOffice(generator, events, "DMV Office", "https://www.second.test")

    assert first.email == "tax@first.test"
    assert second.email == "dmv@second.test"
    assert first.email == "tax@first.test"
    assert second.email == "dmv@second.test"
    assert events == [
        "website",
        ("replace", "https://www.", ""),
        "type",
        "lower",
        "website",
        ("replace", "https://www.", ""),
        "type",
        "lower",
    ]


def test_email_department_delegates_lowercase_type_after_website_processing() -> None:
    events: list[object] = []

    class CandidateGenerator(_ObservedGenerator):
        def get_email_department(self, office_type_lower: str) -> str:
            events.append(("get_email_department", office_type_lower))
            return "delegated"

    office = _InputOffice(CandidateGenerator(events), events, "TaX Office")

    assert office.email == "delegated@example.test/path"
    assert events == [
        "website",
        ("replace", "https://www.", ""),
        "type",
        "lower",
        ("get_email_department", "tax office"),
    ]


def test_generator_email_department_is_rng_free() -> None:
    class NoRngGenerator(AdministrationOfficeGenerator):
        @property
        def rng(self) -> Random:
            raise AssertionError("email department selection must not access RNG")

    rng = Random(153)
    generator = NoRngGenerator(dataset="US", rng=rng)
    initial_state = rng.getstate()

    assert generator.get_email_department("social permit") == "socialservices"
    assert rng.getstate() == initial_state
