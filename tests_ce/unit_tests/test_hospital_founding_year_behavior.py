from datetime import datetime
from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.healthcare.generators.hospital_generator import HospitalGenerator
from datamimic_ce.domains.healthcare.models.hospital import Hospital

REFERENCE_NOW = datetime(2026, 10, 7)


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class EndpointRandom(Random):
    def __init__(self, *, choose_upper: bool, access_log: list[tuple] | None = None) -> None:
        self.choose_upper = choose_upper
        self.bounds: list[tuple[int, int]] = []
        self.access_log = access_log
        super().__init__(0)

    def randint(self, a: int, b: int) -> int:
        self.bounds.append((a, b))
        if self.access_log is not None:
            self.access_log.append(("randint", a, b))
        return b if self.choose_upper else a


class PublicRngOverrideHospitalGenerator(HospitalGenerator):
    def __init__(
        self,
        *,
        public_rng: Random,
        public_reference_now: datetime,
        access_log: list[tuple],
        **kwargs,
    ) -> None:
        self._public_rng = public_rng
        self._public_reference_now = public_reference_now
        self.access_log = access_log
        super().__init__(**kwargs)

    @property
    def rng(self) -> Random:
        self.access_log.append(("rng",))
        return self._public_rng

    @property
    def reference_now(self) -> datetime:
        self.access_log.append(("reference_now", self._public_reference_now.year))
        return self._public_reference_now


@pytest.mark.parametrize(
    ("choose_upper", "expected_year"),
    [(False, 1876), (True, 2021)],
)
def test_founding_year_uses_inclusive_reference_year_bounds(choose_upper: bool, expected_year: int) -> None:
    rng = EndpointRandom(choose_upper=choose_upper)
    hospital = Hospital(
        HospitalGenerator(dataset="US", rng=rng, reference_now=REFERENCE_NOW)
    )

    assert hospital.founding_year == expected_year
    assert rng.bounds == [(REFERENCE_NOW.year - 150, REFERENCE_NOW.year - 5)]


def test_seeded_founding_year_and_full_rng_state_are_stable() -> None:
    rng = Random(20261007)
    hospital = Hospital(HospitalGenerator(dataset="US", rng=rng, reference_now=REFERENCE_NOW))

    assert hospital.founding_year == 2020
    assert _rng_fingerprint(rng) == "8a868470e0017a61c2b8920aa75fffc8cdddc3d56f44563cb812011fe20e5782"


def test_founding_year_property_cache_does_not_draw_again() -> None:
    rng = Random(731)
    hospital = Hospital(HospitalGenerator(dataset="US", rng=rng, reference_now=REFERENCE_NOW))

    first_year = hospital.founding_year
    state_after_first_read = rng.getstate()

    assert hospital.founding_year == first_year
    assert rng.getstate() == state_after_first_read


def test_hospitals_sharing_generator_keep_independent_founding_year_caches() -> None:
    rng = EndpointRandom(choose_upper=False)
    generator = HospitalGenerator(dataset="US", rng=rng, reference_now=REFERENCE_NOW)
    first = Hospital(generator)
    second = Hospital(generator)

    assert first.founding_year == 1876
    rng.choose_upper = True
    assert second.founding_year == 2021
    expected_draws = [(1876, 2021), (1876, 2021)]
    assert rng.bounds == expected_draws

    assert first.founding_year == 1876
    assert second.founding_year == 2021
    assert rng.bounds == expected_draws


def test_founding_year_accessors_are_lazy_ordered_and_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    internal_rng = Random(0)
    access_log: list[tuple] = []
    public_rng = EndpointRandom(choose_upper=False, access_log=access_log)
    hospital = Hospital(
        PublicRngOverrideHospitalGenerator(
            dataset="US",
            rng=internal_rng,
            reference_now=REFERENCE_NOW,
            public_rng=public_rng,
            public_reference_now=REFERENCE_NOW,
            access_log=access_log,
        )
    )

    assert access_log == []
    monkeypatch.setattr(hospital._hospital_generator, "get_hospital_type", lambda: "General")
    assert hospital.type == "General"
    assert access_log == []

    internal_state = internal_rng.getstate()

    assert hospital.founding_year == 1876
    expected_accesses = [
        ("reference_now", REFERENCE_NOW.year),
        ("rng",),
        ("randint", REFERENCE_NOW.year - 150, REFERENCE_NOW.year - 5),
    ]
    assert access_log == expected_accesses
    assert hospital.founding_year == 1876
    assert access_log == expected_accesses
    assert internal_rng.getstate() == internal_state
