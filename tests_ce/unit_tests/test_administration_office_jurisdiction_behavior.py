from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.public_sector.generators.administration_office_generator import AdministrationOfficeGenerator
from datamimic_ce.domains.public_sector.models.administration_office import AdministrationOffice


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class _Address:
    def __init__(self, events: list[object], *, fail: str | None = None) -> None:
        self.events = events
        self.fail = fail
        self.failed = False

    @property
    def city(self) -> str:
        self.events.append("city")
        if self.fail == "city" and not self.failed:
            self.failed = True
            raise RuntimeError("scripted city failure")
        return "Springfield"

    @property
    def state(self) -> str:
        self.events.append("state")
        if self.fail == "state" and not self.failed:
            self.failed = True
            raise RuntimeError("scripted state failure")
        return "PA"


class _ObservedGenerator(AdministrationOfficeGenerator):
    def __init__(
        self,
        rng: Random,
        events: list[object],
        buckets: list[str | Exception] | None = None,
    ) -> None:
        self.events = events
        self.rng_reads = 0
        self.buckets = list(buckets or [])
        super().__init__(dataset="US", rng=rng)

    @property
    def rng(self) -> Random:
        self.rng_reads += 1
        self.events.append("rng")
        return self._rng

    def pick_jurisdiction_bucket(self) -> str:
        self.events.append("bucket")
        result = self.buckets.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class _InputOffice(AdministrationOffice):
    def __init__(
        self,
        generator: AdministrationOfficeGenerator,
        events: list[object],
        office_type: str,
        *,
        fail: str | None = None,
    ) -> None:
        super().__init__(generator)
        self.events = events
        self._address = _Address(events, fail=fail)
        self.office_type = office_type
        self.fail = fail
        self.failed = False

    @property
    def type(self) -> str:
        self.events.append("type")
        if self.fail == "type" and not self.failed:
            self.failed = True
            raise RuntimeError("scripted type failure")
        return self.office_type

    @property
    def address(self) -> _Address:
        return self._address


@pytest.mark.parametrize(
    ("office_type", "expected"),
    [
        ("Municipal County State Federal", "City of Springfield"),
        ("City County State Federal", "City of Springfield"),
        ("County State Federal", "Springfield County"),
        ("State Federal", "State of PA"),
        ("Federal", "Federal"),
    ],
)
def test_direct_jurisdiction_branches_preserve_precedence_inputs_and_avoid_rng(
    office_type: str,
    expected: str,
) -> None:
    events: list[object] = []
    rng = Random(71)
    generator = _ObservedGenerator(rng, events, buckets=[AssertionError("direct branch used bucket")])
    office = _InputOffice(generator, events, office_type)
    initial_state = rng.getstate()

    assert office.jurisdiction == expected
    assert events == ["type", "city", "state"]
    assert generator.rng_reads == 0
    assert rng.getstate() == initial_state
    assert office.jurisdiction == expected
    assert events == ["type", "city", "state"]


@pytest.mark.parametrize(
    ("bucket", "expected"),
    [
        ("city", "City of Springfield"),
        ("county", "Springfield County"),
        ("state", "State of PA"),
        ("unknown", "Federal"),
    ],
)
def test_fallback_bucket_mapping_and_unknown_value(bucket: str, expected: str) -> None:
    events: list[object] = []
    generator = _ObservedGenerator(Random(71), events, buckets=[bucket])
    office = _InputOffice(generator, events, "Special Agency")

    assert office.jurisdiction == expected
    assert events == ["type", "city", "state", "bucket"]
    assert generator.rng_reads == 0


@pytest.mark.parametrize(
    ("bucket", "city_fails", "state_fails", "expected"),
    [
        ("city", False, True, "City of Springfield"),
        ("unknown", True, True, "Federal"),
    ],
)
def test_fallback_formats_only_the_value_selected_by_bucket(
    bucket: str,
    city_fails: bool,
    state_fails: bool,
    expected: str,
) -> None:
    class GuardedText(str):
        def __new__(cls, value: str, *, fail_format: bool = False):
            instance = super().__new__(cls, value)
            instance.fail_format = fail_format
            return instance

        def __format__(self, format_spec: str) -> str:
            if self.fail_format:
                raise AssertionError(f"unexpected formatting of {str(self)!r}")
            return super().__format__(format_spec)

    events: list[object] = []
    generator = _ObservedGenerator(Random(71), events, buckets=[bucket])

    assert generator.generate_jurisdiction(
        "Special Agency",
        GuardedText("Springfield", fail_format=city_fails),
        GuardedText("PA", fail_format=state_fails),
    ) == expected
    assert events == ["bucket"]


@pytest.mark.parametrize("failure", ["type", "city", "state"])
def test_jurisdiction_input_failure_is_uncached_and_precedes_bucket(failure: str) -> None:
    events: list[object] = []
    generator = _ObservedGenerator(Random(71), events, buckets=["city"])
    office = _InputOffice(generator, events, "Special Agency", fail=failure)

    with pytest.raises(RuntimeError, match=f"scripted {failure} failure"):
        _ = office.jurisdiction
    assert "jurisdiction" not in office.field_cache
    assert "bucket" not in events
    assert generator.rng_reads == 0

    assert office.jurisdiction == "City of Springfield"
    assert generator.events.count("bucket") == 1


def test_fallback_bucket_failure_is_uncached_and_retries_inputs_and_bucket() -> None:
    events: list[object] = []
    generator = _ObservedGenerator(
        Random(71), events, buckets=[RuntimeError("scripted bucket failure"), "county"]
    )
    office = _InputOffice(generator, events, "Special Agency")

    with pytest.raises(RuntimeError, match="scripted bucket failure"):
        _ = office.jurisdiction
    assert "jurisdiction" not in office.field_cache

    assert office.jurisdiction == "Springfield County"
    assert events == [
        "type",
        "city",
        "state",
        "bucket",
        "type",
        "city",
        "state",
        "bucket",
    ]


def test_offices_sharing_generator_cache_jurisdictions_independently() -> None:
    events: list[object] = []
    generator = _ObservedGenerator(Random(71), events, buckets=["city", "state"])
    first = _InputOffice(generator, events, "Special Agency")
    second = _InputOffice(generator, events, "Special Agency")

    assert first.jurisdiction == "City of Springfield"
    assert first.jurisdiction == "City of Springfield"
    assert second.jurisdiction == "State of PA"
    assert second.jurisdiction == "State of PA"
    assert events == ["type", "city", "state", "bucket", "type", "city", "state", "bucket"]


def test_jurisdiction_delegates_after_type_city_and_state_resolution() -> None:
    events: list[object] = []

    class CandidateGenerator(_ObservedGenerator):
        def generate_jurisdiction(self, office_type: str, city: str, state: str) -> str:
            events.append(("generate_jurisdiction", office_type, city, state))
            return "Candidate jurisdiction"

    generator = CandidateGenerator(Random(71), events)
    office = _InputOffice(generator, events, "Special Agency")

    assert office.jurisdiction == "Candidate jurisdiction"
    assert events == [
        "type",
        "city",
        "state",
        ("generate_jurisdiction", "Special Agency", "Springfield", "PA"),
    ]


def test_jurisdiction_first_name_first_and_website_first_preserve_seeded_outputs_and_states() -> None:
    jurisdiction_first_rng = Random(701)
    jurisdiction_first_generator = AdministrationOfficeGenerator(dataset="US", rng=jurisdiction_first_rng)
    jurisdiction_first = AdministrationOffice(jurisdiction_first_generator)
    address = jurisdiction_first.address
    assert _fingerprint(jurisdiction_first_rng) == "5bfc9860f39a4f496cbc2cc7571ec69957881959c9bb617b6e6ef7f97cfa2a48"
    assert _fingerprint(address._row.city_generator.rng) == (
        "e6e1b39b8c4546afa42207d310cd481afc2ee3a1a4f133ad172ba4a55615fca9"
    )
    assert jurisdiction_first.jurisdiction == "City of New vineyard"
    assert _fingerprint(jurisdiction_first_rng) == "54c93ad2529a250c288bd2559a710031000d3eefe32aa5aa7156adc4501a73b4"
    assert _fingerprint(address._row.city_generator.rng) == (
        "4d314811c1ee65937154968b06f3d0e91ea7f12e99034325e2bdcd7484129f69"
    )
    assert jurisdiction_first.name == "City of New vineyard Government Office"
    assert jurisdiction_first.website == "https://www.newvineyard.gov"
    assert _fingerprint(jurisdiction_first_rng) == "57a776cc51cef6741c572750872d8a00b3b72ef1ebd2566f83ca774337fbe9ac"

    name_first_rng = Random(701)
    name_first_generator = AdministrationOfficeGenerator(dataset="US", rng=name_first_rng)
    name_first = AdministrationOffice(name_first_generator)
    name_address = name_first.address
    assert name_first.name == "City of New vineyard Government Office"
    assert _fingerprint(name_first_rng) == "57a776cc51cef6741c572750872d8a00b3b72ef1ebd2566f83ca774337fbe9ac"
    assert _fingerprint(name_address._row.city_generator.rng) == (
        "4d314811c1ee65937154968b06f3d0e91ea7f12e99034325e2bdcd7484129f69"
    )

    website_first_rng = Random(701)
    website_first_generator = AdministrationOfficeGenerator(dataset="US", rng=website_first_rng)
    website_first = AdministrationOffice(website_first_generator)
    website_address = website_first.address
    assert website_first.website == "https://www.newvineyard.gov"
    assert _fingerprint(website_first_rng) == "54c93ad2529a250c288bd2559a710031000d3eefe32aa5aa7156adc4501a73b4"
    assert website_first.name == "City of New vineyard Government Office"
    assert _fingerprint(website_first_rng) == "57a776cc51cef6741c572750872d8a00b3b72ef1ebd2566f83ca774337fbe9ac"
    assert _fingerprint(website_address._row.city_generator.rng) == (
        "4d314811c1ee65937154968b06f3d0e91ea7f12e99034325e2bdcd7484129f69"
    )
