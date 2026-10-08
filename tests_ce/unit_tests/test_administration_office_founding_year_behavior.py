from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.public_sector.generators.administration_office_generator import AdministrationOfficeGenerator
from datamimic_ce.domains.public_sector.models.administration_office import AdministrationOffice

REFERENCE_NOW = datetime(2026, 10, 7)


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class _EndpointRandom(Random):
    def __init__(self, *, upper: bool, events: list[object]) -> None:
        super().__init__(0)
        self.upper = upper
        self.events = events
        self.bounds: list[tuple[int, int]] = []

    def randint(self, a: int, b: int) -> int:
        self.bounds.append((a, b))
        self.events.append(("randint", a, b))
        return b if self.upper else a


class _ScriptedRandom(Random):
    def __init__(self, values: list[int | Exception], events: list[object]) -> None:
        super().__init__(19)
        self.values = list(values)
        self.events = events
        self.bounds: list[tuple[int, int]] = []

    def randint(self, a: int, b: int) -> int:
        self.bounds.append((a, b))
        self.events.append(("randint", a, b))
        value = self.values.pop(0)
        if isinstance(value, Exception):
            super().randint(a, b)
            raise value
        return value


class _ObservedOfficeGenerator(AdministrationOfficeGenerator):
    def __init__(
        self,
        rng: Random,
        events: list[object],
        types: list[str | Exception],
        reference_now: datetime = REFERENCE_NOW,
    ) -> None:
        self.events = events
        self.types = list(types)
        self._public_reference_now = reference_now
        self.rng_reads = 0
        super().__init__(dataset="US", rng=rng, reference_now=REFERENCE_NOW)

    @property
    def reference_now(self) -> datetime:
        self.events.append(("reference_now", self._public_reference_now.year))
        return self._public_reference_now

    @property
    def rng(self) -> Random:
        self.rng_reads += 1
        self.events.append("rng")
        return self._rng

    def pick_office_type(self) -> str:
        self.events.append("type")
        result = self.types.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


@pytest.mark.parametrize(
    ("office_type", "bounds"),
    [
        ("Federal State County", (20, 200)),
        ("State County", (15, 150)),
        ("County", (10, 100)),
        ("Municipal", (5, 75)),
        ("Unclassified", (5, 75)),
    ],
)
@pytest.mark.parametrize("upper", [False, True])
def test_founding_year_preserves_type_precedence_inclusive_bounds_and_access_order(
    office_type: str,
    bounds: tuple[int, int],
    upper: bool,
) -> None:
    events: list[object] = []
    rng = _EndpointRandom(upper=upper, events=events)
    generator = _ObservedOfficeGenerator(rng, events, [office_type])
    office = AdministrationOffice(generator)
    expected_age = bounds[1] if upper else bounds[0]

    assert office.founding_year == REFERENCE_NOW.year - expected_age
    assert events == [
        ("reference_now", REFERENCE_NOW.year),
        "type",
        "rng",
        ("randint", *bounds),
    ]
    assert rng.bounds == [bounds]
    assert office.founding_year == REFERENCE_NOW.year - expected_age
    assert len(events) == 4


def test_type_failure_happens_after_public_clock_and_before_rng_then_retries() -> None:
    events: list[object] = []
    rng = _EndpointRandom(upper=False, events=events)
    generator = _ObservedOfficeGenerator(
        rng,
        events,
        [RuntimeError("scripted office type failure"), "Federal"],
    )
    office = AdministrationOffice(generator)

    with pytest.raises(RuntimeError, match="scripted office type failure"):
        _ = office.founding_year
    assert "founding_year" not in office.field_cache
    assert events == [("reference_now", 2026), "type"]
    assert rng.bounds == []

    assert office.founding_year == 2006
    assert office.founding_year == 2006
    assert events == [
        ("reference_now", 2026),
        "type",
        ("reference_now", 2026),
        "type",
        "rng",
        ("randint", 20, 200),
    ]
    assert rng.bounds == [(20, 200)]


def test_founding_year_uses_public_reference_now_override_not_private_clock() -> None:
    events: list[object] = []
    rng = _EndpointRandom(upper=False, events=events)
    generator = _ObservedOfficeGenerator(rng, events, ["Federal"])
    public_now = datetime(2040, 3, 4)
    generator._public_reference_now = public_now
    office = AdministrationOffice(generator)

    assert generator._reference_now == REFERENCE_NOW
    assert office.founding_year == 2020
    assert events == [
        ("reference_now", public_now.year),
        "type",
        "rng",
        ("randint", 20, 200),
    ]


def test_existing_generator_founding_year_helper_uses_private_clock_and_rng_path() -> None:
    events: list[object] = []
    rng = _EndpointRandom(upper=False, events=events)
    generator = _ObservedOfficeGenerator(rng, events, [])
    generator._public_reference_now = datetime(2040, 3, 4)

    assert generator.pick_founding_year("Federal") == REFERENCE_NOW.year - 20
    assert events == [("randint", 20, 200)]
    assert generator.rng_reads == 0


def test_model_resolves_founding_year_inputs_before_generator_delegation() -> None:
    events: list[object] = []
    rng = _EndpointRandom(upper=False, events=events)

    class CandidateGenerator(_ObservedOfficeGenerator):
        def generate_founding_year(self, office_type: str, current_year: int) -> int:
            events.append(("generate_founding_year", office_type, current_year))
            return 1987

    generator = CandidateGenerator(rng, events, ["County"])
    office = AdministrationOffice(generator)

    assert office.founding_year == 1987
    assert events == [
        ("reference_now", REFERENCE_NOW.year),
        "type",
        ("generate_founding_year", "County", REFERENCE_NOW.year),
    ]
    assert generator.rng_reads == 0


def test_rng_failure_leaves_founding_year_uncached_and_retries_without_rollback() -> None:
    events: list[object] = []
    rng = _ScriptedRandom([RuntimeError("scripted founding-year draw failure"), 20], events)
    generator = _ObservedOfficeGenerator(rng, events, ["Federal"])
    office = AdministrationOffice(generator)
    initial_state = rng.getstate()

    with pytest.raises(RuntimeError, match="scripted founding-year draw failure"):
        _ = office.founding_year
    assert "founding_year" not in office.field_cache
    assert rng.bounds == [(20, 200)]
    assert rng.getstate() != initial_state

    assert office.founding_year == 2006
    assert office.founding_year == 2006
    assert rng.bounds == [(20, 200), (20, 200)]
    assert events == [
        ("reference_now", 2026),
        "type",
        "rng",
        ("randint", 20, 200),
        ("reference_now", 2026),
        "rng",
        ("randint", 20, 200),
    ]


def test_offices_sharing_generator_keep_independent_founding_year_caches() -> None:
    events: list[object] = []
    rng = _EndpointRandom(upper=False, events=events)
    generator = _ObservedOfficeGenerator(rng, events, ["County", "County"])
    first = AdministrationOffice(generator)
    second = AdministrationOffice(generator)

    assert first.founding_year == 2016
    rng.upper = True
    assert second.founding_year == 1926
    assert first.founding_year == 2016
    assert second.founding_year == 1926
    assert rng.bounds == [(10, 100), (10, 100)]


def test_seeded_founding_year_first_and_office_id_first_preserve_rng_fingerprints() -> None:
    class CountyOffice(AdministrationOffice):
        @property
        def type(self) -> str:
            return "County"

    founding_first_rng = Random(151)
    founding_first = CountyOffice(
        AdministrationOfficeGenerator(dataset="US", rng=founding_first_rng, reference_now=REFERENCE_NOW)
    )
    assert _fingerprint(founding_first_rng) == (
        "55d01895ce566175d88a213c2129c9f77196aa26d99930847400cd3955815bb0"
    )
    assert founding_first.founding_year == 1943
    assert _fingerprint(founding_first_rng) == (
        "a5b8402bfaf764de9313ab2011156118eaa12cb0920404bb5269f63529b1da59"
    )
    assert founding_first.office_id == "ADM-3EF2E3C9"
    assert _fingerprint(founding_first_rng) == (
        "a295896a6ef9e6fec6c44b61b9563897e62f72b923c015a3ebba0e21c29de64a"
    )

    id_first_rng = Random(151)
    id_first = CountyOffice(AdministrationOfficeGenerator(dataset="US", rng=id_first_rng, reference_now=REFERENCE_NOW))
    assert id_first.office_id == "ADM-3EF2E3C9"
    assert _fingerprint(id_first_rng) == (
        "a295896a6ef9e6fec6c44b61b9563897e62f72b923c015a3ebba0e21c29de64a"
    )
    assert id_first.founding_year == 1931
    assert _fingerprint(id_first_rng) == (
        "a7f25ca7bb5709c5709993edc7ad8ffc944c7e69819df220964a6bff6b1bb350"
    )
