from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.domain_core.base_entity import IdentifierRegistry
from datamimic_ce.domains.healthcare.generators.hospital_generator import HospitalGenerator
from datamimic_ce.domains.healthcare.models.hospital import Hospital
from datamimic_ce.domains.healthcare.services.hospital_service import HOSPITAL_SCHEMA


class _ScriptedChoiceRandom(Random):
    def __init__(self, values: list[str], events: list[tuple[str, object]] | None = None):
        self.values = iter(values)
        self.choices: list[str] = []
        self.events = events if events is not None else []
        super().__init__(0)

    def choice(self, seq: str) -> str:
        self.choices.append(seq)
        self.events.append(("choice", seq))
        return next(self.values)


class _SwitchingPublicRngHospitalGenerator(HospitalGenerator):
    def __init__(self, first_rng: Random, later_rng: Random):
        self.first_rng = first_rng
        self.later_rng = later_rng
        self.rng_accesses = 0
        super().__init__(dataset="US", rng=Random(19))

    @property
    def rng(self) -> Random:
        self.rng_accesses += 1
        return self.first_rng if self.rng_accesses == 1 else self.later_rng


class _ClaimRecordingHospital(Hospital):
    def __init__(self, generator: HospitalGenerator, events: list[tuple[str, object]]):
        super().__init__(generator)
        self.events = events

    def _claim_identifier(self, name: str, candidate: str) -> str:
        self.events.append(("claim", (name, candidate)))
        return super()._claim_identifier(name, candidate)


class _NamedClaimRecordingHospital(_ClaimRecordingHospital):
    def __init__(self, generator: HospitalGenerator, events: list[tuple[str, object]], name: str):
        super().__init__(generator, events)
        self._stub_name = name

    @property
    def name(self) -> str:
        return self._stub_name


class _ClaimFailingHospital(Hospital):
    def __init__(self, generator: HospitalGenerator):
        super().__init__(generator)
        self.claim_attempts = 0

    def _claim_identifier(self, name: str, candidate: str) -> str:
        self.claim_attempts += 1
        raise RuntimeError(f"claim failed: {name}={candidate}")


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


def test_hospital_id_uses_eight_ordered_public_hex_choices_and_caches() -> None:
    alphabet = "0123456789ABCDEF"
    rng = _ScriptedChoiceRandom(["0"] * 8)
    hospital = Hospital(HospitalGenerator(dataset="US", rng=rng))

    assert hospital.hospital_id == "HOSP-00000000"
    assert rng.choices == [alphabet] * 8
    assert hospital.hospital_id == "HOSP-00000000"
    assert rng.choices == [alphabet] * 8


def test_hospital_id_uses_switching_public_rng_once() -> None:
    first_rng = _ScriptedChoiceRandom(list("01234567"))
    later_rng = _ScriptedChoiceRandom(list("89ABCDEF"))
    generator = _SwitchingPublicRngHospitalGenerator(first_rng, later_rng)
    hospital = Hospital(generator)

    assert hospital.hospital_id == "HOSP-01234567"
    assert generator.rng_accesses == 1
    assert first_rng.choices == ["0123456789ABCDEF"] * 8
    assert later_rng.choices == []
    assert hospital.hospital_id == "HOSP-01234567"
    assert generator.rng_accesses == 1
    assert len(first_rng.choices) == 8


def test_unbound_hospitals_may_keep_duplicate_candidates_and_cache_them() -> None:
    rng = _ScriptedChoiceRandom(["0"] * 16)
    generator = HospitalGenerator(dataset="US", rng=rng)
    first_events: list[tuple[str, object]] = []
    second_events: list[tuple[str, object]] = []
    first = _ClaimRecordingHospital(generator, first_events)
    second = _ClaimRecordingHospital(generator, second_events)

    assert first.hospital_id == "HOSP-00000000"
    assert second.hospital_id == "HOSP-00000000"
    assert len(rng.choices) == 16
    assert first_events == [("claim", ("hospital_id", "HOSP-00000000"))]
    assert second_events == [("claim", ("hospital_id", "HOSP-00000000"))]
    assert first.hospital_id == second.hospital_id == "HOSP-00000000"
    assert len(rng.choices) == 16


def test_bound_collision_claims_after_draws_and_caches_claimed_value() -> None:
    events: list[tuple[str, object]] = []
    rng = _ScriptedChoiceRandom(["0"] * 16, events)
    generator = HospitalGenerator(dataset="US", rng=rng)
    first = _ClaimRecordingHospital(generator, events)
    second = _ClaimRecordingHospital(generator, events)
    registry = IdentifierRegistry()
    for hospital in (first, second):
        hospital._bind_identifier_registry(
            registry,
            HOSPITAL_SCHEMA.entity,
            HOSPITAL_SCHEMA.fields,
            {},
        )

    assert first.hospital_id == "HOSP-00000000"
    assert events[:9] == [("choice", "0123456789ABCDEF")] * 8 + [
        ("claim", ("hospital_id", "HOSP-00000000"))
    ]
    assert second.hospital_id == "HOSP-00000001"
    assert events[9:] == [("choice", "0123456789ABCDEF")] * 8 + [
        ("claim", ("hospital_id", "HOSP-00000000"))
    ]
    assert second.hospital_id == "HOSP-00000001"
    assert len(events) == 18


def test_bound_hospital_id_collision_carries_from_nine_to_hex_a_without_redraws() -> None:
    events: list[tuple[str, object]] = []
    candidate = ["0"] * 7 + ["9"]
    rng = _ScriptedChoiceRandom(candidate * 2, events)
    generator = HospitalGenerator(dataset="US", rng=rng)
    first = _ClaimRecordingHospital(generator, events)
    second = _ClaimRecordingHospital(generator, events)
    registry = IdentifierRegistry()
    for hospital in (first, second):
        hospital._bind_identifier_registry(
            registry,
            HOSPITAL_SCHEMA.entity,
            HOSPITAL_SCHEMA.fields,
            {},
        )

    assert first.hospital_id == "HOSP-00000009"
    assert second.hospital_id == "HOSP-0000000A"
    assert len(rng.choices) == 16
    assert events.count(("claim", ("hospital_id", "HOSP-00000009"))) == 2
    assert sum(event[0] == "choice" for event in events) == 16


def test_claim_exception_propagates_and_does_not_cache_hospital_id() -> None:
    rng = _ScriptedChoiceRandom(["0"] * 16)
    hospital = _ClaimFailingHospital(HospitalGenerator(dataset="US", rng=rng))

    for _ in range(2):
        with pytest.raises(RuntimeError, match="claim failed: hospital_id=HOSP-00000000"):
            _ = hospital.hospital_id

    assert hospital.claim_attempts == 2
    assert len(rng.choices) == 16


def test_short_website_fallback_uses_and_caches_claimed_hospital_id() -> None:
    events: list[tuple[str, object]] = []
    rng = _ScriptedChoiceRandom(["0"] * 16, events)
    generator = HospitalGenerator(dataset="US", rng=rng)
    registry = IdentifierRegistry()
    first = _NamedClaimRecordingHospital(generator, events, "X")
    fallback = _NamedClaimRecordingHospital(generator, events, "X")
    for hospital in (first, fallback):
        hospital._bind_identifier_registry(
            registry,
            HOSPITAL_SCHEMA.entity,
            HOSPITAL_SCHEMA.fields,
            {},
        )

    assert first.hospital_id == "HOSP-00000000"
    assert fallback.website == "https://www.hospitalhosp-00000001.us"
    assert fallback.hospital_id == "HOSP-00000001"
    assert fallback.website == "https://www.hospitalhosp-00000001.us"
    assert len(rng.choices) == 16
    assert events[-1] == ("claim", ("hospital_id", "HOSP-00000000"))
    assert sum(event[0] == "claim" for event in events) == 2


def test_long_website_name_does_not_generate_or_claim_hospital_id() -> None:
    events: list[tuple[str, object]] = []
    rng = _ScriptedChoiceRandom([], events)
    hospital = _NamedClaimRecordingHospital(
        HospitalGenerator(dataset="US", rng=rng),
        events,
        "City General Health Hospital",
    )

    assert hospital.website == "https://www.citygeneral.us"
    assert hospital.website == "https://www.citygeneral.us"
    assert rng.choices == []
    assert events == []


@pytest.mark.parametrize(
    ("order", "expected", "rng_fingerprint"),
    [
        (
            ("hospital_id", "type"),
            {"hospital_id": "HOSP-6826160B", "type": "Long-term Care"},
            "8cadb49476c9a1d6380da35e407d65c6edb08ed48844ac19ff45069081f37e08",
        ),
        (
            ("type", "hospital_id"),
            {"type": "Veterans", "hospital_id": "HOSP-6826160B"},
            "cc7dd72a07ce9b2bf49212356221bca04f11d3fa6af0c368c05e4630bedd2fe3",
        ),
    ],
)
def test_seeded_hospital_id_and_type_preserve_access_order(order, expected, rng_fingerprint):
    rng = Random(71)
    hospital = Hospital(HospitalGenerator(dataset="US", rng=rng))

    assert {name: getattr(hospital, name) for name in order} == expected
    state_after_reads = rng.getstate()
    assert {name: getattr(hospital, name) for name in order} == expected
    assert rng.getstate() == state_after_reads
    assert _rng_fingerprint(rng) == rng_fingerprint
