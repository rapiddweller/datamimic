from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.healthcare.generators.hospital_generator import HospitalGenerator
from datamimic_ce.domains.healthcare.models.hospital import Hospital


class _ScriptedRandom(Random):
    def __init__(self, values: list[float]):
        super().__init__(0)
        self.values = iter(values)
        self.draw_count = 0

    def random(self) -> float:
        self.draw_count += 1
        return next(self.values)


class _PublicRngHospitalGenerator(HospitalGenerator):
    def __init__(self, public_rng: Random):
        self._public_rng = public_rng
        super().__init__(dataset="US", rng=Random(19))

    @property
    def rng(self) -> Random:
        return self._public_rng


class _RngMustNotBeReadHospitalGenerator(HospitalGenerator):
    @property
    def rng(self) -> Random:
        raise AssertionError("Teaching status must not read the RNG")


class _FixedTypeHospital(Hospital):
    def __init__(self, generator: HospitalGenerator, hospital_type: str):
        super().__init__(generator)
        self._fixed_type = hospital_type

    @property
    def type(self) -> str:
        return self._fixed_type


class _OrderedHospitalGenerator(_PublicRngHospitalGenerator):
    def __init__(self, events: list[str], public_rng: Random):
        self.events = events
        super().__init__(public_rng)

    def get_hospital_type(self) -> str:
        self.events.append("type")
        return "Specialty"

    @property
    def rng(self) -> Random:
        self.events.append("rng")
        return self._public_rng


@pytest.mark.parametrize(
    ("hospital_type", "draw", "expected"),
    [
        ("Specialty", 0.299999, True),
        ("Specialty", 0.3, False),
        ("General", 0.899999, True),
        ("General", 0.9, False),
        ("Unlisted", 0.899999, True),
        ("Unlisted", 0.9, False),
    ],
)
def test_emergency_services_preserves_strict_threshold_and_type_override(
    hospital_type: str, draw: float, expected: bool
) -> None:
    rng = _ScriptedRandom([draw])
    hospital = _FixedTypeHospital(_PublicRngHospitalGenerator(rng), hospital_type)

    assert hospital.emergency_services is expected
    assert rng.draw_count == 1
    assert hospital.emergency_services is expected
    assert rng.draw_count == 1


def test_emergency_services_resolves_type_before_public_rng() -> None:
    events: list[str] = []
    rng = _ScriptedRandom([0.2])
    hospital = Hospital(_OrderedHospitalGenerator(events, rng))

    assert hospital.emergency_services is True
    assert events == ["type", "rng"]
    assert rng.draw_count == 1


def test_shared_generator_keeps_independent_emergency_service_caches() -> None:
    rng = _ScriptedRandom([0.2, 0.95])
    generator = _PublicRngHospitalGenerator(rng)
    specialty = _FixedTypeHospital(generator, "Specialty")
    unknown = _FixedTypeHospital(generator, "Unlisted")

    assert specialty.emergency_services is True
    assert unknown.emergency_services is False
    assert rng.draw_count == 2
    assert specialty.emergency_services is True
    assert unknown.emergency_services is False
    assert rng.draw_count == 2


def test_seeded_hospital_type_and_emergency_sequence_preserves_type_anti_repeat() -> None:
    rng = Random(1)
    generator = HospitalGenerator(dataset="US", rng=rng)
    first = Hospital(generator)
    second = Hospital(generator)

    assert (first.type, first.emergency_services) == ("Specialty", False)
    assert (second.type, second.emergency_services) == ("Psychiatric", True)
    assert sha256(repr(rng.getstate()).encode()).hexdigest() == (
        "e3abf7fcf6c5cfed49d3d2b6b5fb66e8a6001e75b464754e0865e25f64204dcf"
    )


@pytest.mark.parametrize(
    ("hospital_type", "draw", "expected"),
    [
        ("Teaching", 0.99, True),
        ("General", 0.299999, True),
        ("General", 0.3, False),
        ("Unlisted", 0.099999, True),
        ("Unlisted", 0.1, False),
    ],
)
def test_teaching_status_preserves_strict_thresholds_and_cache(
    hospital_type: str, draw: float, expected: bool
) -> None:
    rng = _ScriptedRandom([draw])
    generator = _PublicRngHospitalGenerator(rng)
    hospital = _FixedTypeHospital(generator, hospital_type)

    assert hospital.teaching_status is expected
    assert rng.draw_count == (0 if hospital_type == "Teaching" else 1)
    assert hospital.teaching_status is expected
    assert rng.draw_count == (0 if hospital_type == "Teaching" else 1)


def test_teaching_type_returns_true_without_public_rng_access() -> None:
    hospital = _FixedTypeHospital(
        _RngMustNotBeReadHospitalGenerator(dataset="US", rng=Random(1)), "Teaching"
    )

    assert hospital.teaching_status is True
    assert hospital.teaching_status is True


def test_teaching_status_resolves_type_before_rng_and_uses_public_accessor() -> None:
    events: list[str] = []
    rng = _ScriptedRandom([0.2])
    hospital = Hospital(_OrderedHospitalGenerator(events, rng))

    assert hospital.teaching_status is False
    assert events == ["type", "rng"]
    assert rng.draw_count == 1


def test_shared_generator_keeps_independent_teaching_status_caches() -> None:
    rng = _ScriptedRandom([0.2, 0.95])
    generator = _PublicRngHospitalGenerator(rng)
    general = _FixedTypeHospital(generator, "General")
    unknown = _FixedTypeHospital(generator, "Unlisted")

    assert general.teaching_status is True
    assert unknown.teaching_status is False
    assert rng.draw_count == 2
    assert general.teaching_status is True
    assert unknown.teaching_status is False
    assert rng.draw_count == 2


def test_seeded_teaching_first_preserves_type_anti_repeat_and_rng_state() -> None:
    rng = Random(2)
    generator = HospitalGenerator(dataset="US", rng=rng)
    first = Hospital(generator)
    second = Hospital(generator)

    assert first.teaching_status is False
    assert first.emergency_services is True
    assert (first.type, second.type) == ("Veterans", "Community")
    assert sha256(repr(rng.getstate()).encode()).hexdigest() == (
        "a2e5314b5e35cc2353fdb5c80cc9c0dd4f9dc2d429c789a564575a607b37cb3a"
    )


def test_seeded_emergency_first_preserves_type_anti_repeat_and_rng_state() -> None:
    rng = Random(2)
    generator = HospitalGenerator(dataset="US", rng=rng)
    first = Hospital(generator)
    second = Hospital(generator)

    assert first.emergency_services is True
    assert first.teaching_status is False
    assert (first.type, second.type) == ("Veterans", "Community")
    assert sha256(repr(rng.getstate()).encode()).hexdigest() == (
        "a2e5314b5e35cc2353fdb5c80cc9c0dd4f9dc2d429c789a564575a607b37cb3a"
    )
