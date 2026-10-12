from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.domain_core.base_entity import IdentifierRegistry
from datamimic_ce.domains.healthcare.generators.doctor_generator import DoctorGenerator
from datamimic_ce.domains.healthcare.models.doctor import Doctor
from datamimic_ce.domains.healthcare.services.doctor_service import DOCTOR_SCHEMA


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class FixedRandom(Random):
    def __init__(self, value: float) -> None:
        self.value = value
        self.draws = 0
        super().__init__(0)

    def random(self) -> float:
        self.draws += 1
        return self.value

    def getrandbits(self, k: int) -> int:
        return super().getrandbits(k)


class PublicRngOverrideDoctorGenerator(DoctorGenerator):
    def __init__(self, *, public_rng: Random, **kwargs) -> None:
        super().__init__(**kwargs)
        self._public_rng = public_rng

    @property
    def rng(self) -> Random:
        return self._public_rng


class ScriptedIntegerRandom(Random):
    def __init__(self, values: list[int]) -> None:
        self.values = iter(values)
        self.bounds: list[tuple[int, int]] = []
        super().__init__(0)

    def randint(self, a: int, b: int) -> int:
        self.bounds.append((a, b))
        return next(self.values)


class ScriptedCredentialRandom(Random):
    def __init__(self, letters: list[str], digits: list[int]) -> None:
        self.letters = iter(letters)
        self.digits = iter(digits)
        self.calls: list[tuple[str, object]] = []
        super().__init__(0)

    def choice(self, seq: str) -> str:
        self.calls.append(("choice", seq))
        return next(self.letters)

    def randint(self, a: int, b: int) -> int:
        self.calls.append(("randint", (a, b)))
        return next(self.digits)


class ScriptedOfficeHoursRandom(Random):
    def __init__(self, probabilities: list[float], hours: list[int], events: list[tuple[str, object]] | None = None):
        self.probabilities = iter(probabilities)
        self.hours = iter(hours)
        self.events = events if events is not None else []
        super().__init__(0)

    def random(self) -> float:
        value = next(self.probabilities)
        self.events.append(("random", value))
        return value

    def randint(self, a: int, b: int) -> int:
        value = next(self.hours)
        self.events.append(("randint", (a, b)))
        assert a <= value <= b
        return value


class FailingOnceOfficeHoursRandom(Random):
    def __init__(self) -> None:
        self.failed = False
        super().__init__(0)

    def random(self) -> float:
        if not self.failed:
            self.failed = True
            raise RuntimeError("office-hours draw failed")
        return 1.0


class ScriptedHexRandom(Random):
    def __init__(self, values: list[str], events: list[tuple[str, object]] | None = None) -> None:
        self.values = iter(values)
        self.calls: list[str] = []
        self.events = events if events is not None else []
        super().__init__(0)

    def choice(self, seq: str) -> str:
        self.calls.append(seq)
        self.events.append(("choice", seq))
        return next(self.values)


class SwitchingPublicRngDoctorGenerator(DoctorGenerator):
    def __init__(self, *, first_rng: Random, later_rng: Random, rng: Random) -> None:
        self.first_rng = first_rng
        self.later_rng = later_rng
        self.rng_accesses = 0
        super().__init__(dataset="US", rng=rng)

    @property
    def rng(self) -> Random:
        self.rng_accesses += 1
        return self.first_rng if self.rng_accesses == 1 else self.later_rng


class ClaimRecordingDoctor(Doctor):
    def __init__(self, generator: DoctorGenerator, events: list[tuple[str, object]]) -> None:
        super().__init__(generator)
        self.events = events

    def _claim_identifier(self, name: str, candidate: str) -> str:
        self.events.append(("claim", (name, candidate)))
        return super()._claim_identifier(name, candidate)


class ClaimFailingDoctor(Doctor):
    def __init__(self, generator: DoctorGenerator) -> None:
        super().__init__(generator)
        self.claim_attempts = 0

    def _claim_identifier(self, name: str, candidate: str) -> str:
        self.claim_attempts += 1
        raise RuntimeError(f"claim failed: {name}={candidate}")


def test_seeded_acceptance_and_full_rng_state_are_stable() -> None:
    rng = Random(20261007)
    doctor = Doctor(DoctorGenerator(dataset="US", rng=rng))

    assert doctor.accepting_new_patients is True
    assert _rng_fingerprint(rng) == "b3b5bcc9cc01b571ad313962330c0dfd4e25bd6618071b6a76fc28e73400da42"


def test_acceptance_threshold_is_strict() -> None:
    rng = FixedRandom(0.8)
    doctor = Doctor(DoctorGenerator(dataset="US", rng=rng))
    draws_before_read = rng.draws

    assert doctor.accepting_new_patients is False
    assert rng.draws == draws_before_read + 1


def test_repeated_acceptance_read_uses_property_cache() -> None:
    rng = FixedRandom(0.2)
    doctor = Doctor(DoctorGenerator(dataset="US", rng=rng))
    draws_before_read = rng.draws

    assert doctor.accepting_new_patients is True
    state_after_first_read = rng.getstate()
    assert doctor.accepting_new_patients is True
    assert rng.draws == draws_before_read + 1
    assert rng.getstate() == state_after_first_read


def test_doctors_sharing_generator_keep_independent_property_caches() -> None:
    rng = FixedRandom(0.9)
    generator = SwitchingPublicRngDoctorGenerator(first_rng=rng, later_rng=rng, rng=Random(2))
    first = Doctor(generator)
    second = Doctor(generator)

    draws_before_reads = rng.draws
    assert first.accepting_new_patients is False
    rng.value = 0.2
    assert second.accepting_new_patients is True
    state_after_both_reads = rng.getstate()
    assert rng.draws == draws_before_reads + 2
    assert first.accepting_new_patients is False
    assert second.accepting_new_patients is True
    assert rng.draws == draws_before_reads + 2
    assert rng.getstate() == state_after_both_reads


def test_acceptance_uses_overridden_public_rng_accessor() -> None:
    internal_rng = Random(0)
    public_rng = FixedRandom(0.2)
    doctor = Doctor(
        PublicRngOverrideDoctorGenerator(
            dataset="US",
            rng=internal_rng,
            public_rng=public_rng,
        )
    )
    internal_state = internal_rng.getstate()
    public_draws_before_read = public_rng.draws

    assert doctor.accepting_new_patients is True
    assert public_rng.draws == public_draws_before_read + 1
    assert internal_rng.getstate() == internal_state


def test_npi_number_preserves_ten_ordered_draws_and_leading_zeroes() -> None:
    rng = ScriptedIntegerRandom([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    doctor = Doctor(DoctorGenerator(dataset="US", rng=rng))

    assert doctor.npi_number == "0123456789"
    assert rng.bounds == [(0, 9)] * 10
    assert doctor.npi_number == "0123456789"
    assert rng.bounds == [(0, 9)] * 10


def test_npi_number_reads_switching_public_rng_once_and_caches() -> None:
    first_rng = ScriptedIntegerRandom([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    later_rng = ScriptedIntegerRandom([9] * 10)
    generator = SwitchingPublicRngDoctorGenerator(
        first_rng=first_rng,
        later_rng=later_rng,
        rng=Random(19),
    )
    doctor = Doctor(generator)

    assert doctor.npi_number == "0123456789"
    assert generator.rng_accesses == 1
    assert first_rng.bounds == [(0, 9)] * 10
    assert later_rng.bounds == []
    assert doctor.npi_number == "0123456789"
    assert generator.rng_accesses == 1
    assert first_rng.bounds == [(0, 9)] * 10


def test_doctors_sharing_generator_keep_independent_npi_caches() -> None:
    rng = ScriptedIntegerRandom([0] * 10 + [9] * 10)
    generator = DoctorGenerator(dataset="US", rng=rng)
    first = Doctor(generator)
    second = Doctor(generator)

    assert first.npi_number == "0000000000"
    assert second.npi_number == "9999999999"
    assert rng.bounds == [(0, 9)] * 20
    assert first.npi_number == "0000000000"
    assert second.npi_number == "9999999999"
    assert rng.bounds == [(0, 9)] * 20


def test_doctor_generator_construction_rng_derivation_baseline() -> None:
    rng = Random(20261007)
    assert _rng_fingerprint(rng) == "5b2f8e83e593409a4f59574b4ef73b31e527195f33ac579050ce0f50ef101591"

    DoctorGenerator(dataset="US", rng=rng)

    assert _rng_fingerprint(rng) == "7685fea106ae5340e4a4c150e23f1f00242618b4d6d81c2f24ce6b284647bf24"


def test_seeded_npi_first_preserves_output_and_rng_order() -> None:
    rng = Random(20261007)
    generator = DoctorGenerator(dataset="US", rng=rng)
    assert _rng_fingerprint(rng) == "7685fea106ae5340e4a4c150e23f1f00242618b4d6d81c2f24ce6b284647bf24"
    doctor = Doctor(generator)

    assert doctor.npi_number == "9991428811"
    assert _rng_fingerprint(rng) == "2d26f172a5a8a0d545e7b883d1253b58be020e5fa0bdd9e60d45c065f99b51b2"
    assert doctor.accepting_new_patients is True
    assert _rng_fingerprint(rng) == "8efa014b4bba3ba83bd35ec3253cd019fe4fbae88e3b395342729283ce8c1487"


def test_seeded_acceptance_first_preserves_npi_output_and_rng_order() -> None:
    rng = Random(20261007)
    generator = DoctorGenerator(dataset="US", rng=rng)
    assert _rng_fingerprint(rng) == "7685fea106ae5340e4a4c150e23f1f00242618b4d6d81c2f24ce6b284647bf24"
    doctor = Doctor(generator)

    assert doctor.accepting_new_patients is True
    assert _rng_fingerprint(rng) == "b3b5bcc9cc01b571ad313962330c0dfd4e25bd6618071b6a76fc28e73400da42"
    assert doctor.npi_number == "9142881170"
    assert _rng_fingerprint(rng) == "a109175244eac52cd054771324e562305008cccd82b4954717d9d21964356cc9"


def test_license_number_preserves_order_format_and_leading_zeroes() -> None:
    rng = ScriptedCredentialRandom(["A", "Z"], [0, 0, 0, 0, 0, 9])
    doctor = Doctor(DoctorGenerator(dataset="US", rng=rng))

    assert doctor.license_number == "AZ-000009"
    assert rng.calls == [
        ("choice", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        ("choice", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        *(('randint', (0, 9)),) * 6,
    ]
    assert doctor.license_number == "AZ-000009"
    assert len(rng.calls) == 8


def test_license_number_uses_switching_public_rng_once_and_caches() -> None:
    first_rng = ScriptedCredentialRandom(["A", "Z"], [0, 0, 0, 0, 0, 9])
    later_rng = ScriptedCredentialRandom(["X", "Y"], [9] * 6)
    generator = SwitchingPublicRngDoctorGenerator(first_rng=first_rng, later_rng=later_rng, rng=Random(19))
    doctor = Doctor(generator)

    assert doctor.license_number == "AZ-000009"
    assert generator.rng_accesses == 1
    assert len(first_rng.calls) == 8
    assert later_rng.calls == []
    assert doctor.license_number == "AZ-000009"
    assert generator.rng_accesses == 1
    assert len(first_rng.calls) == 8


def test_doctors_sharing_generator_keep_independent_license_caches() -> None:
    rng = ScriptedCredentialRandom(["A", "B", "C", "D"], [0] * 6 + [1] * 6)
    generator = DoctorGenerator(dataset="US", rng=rng)
    first = Doctor(generator)
    second = Doctor(generator)

    assert first.license_number == "AB-000000"
    assert second.license_number == "CD-111111"
    assert len(rng.calls) == 16
    assert first.license_number == "AB-000000"
    assert second.license_number == "CD-111111"
    assert len(rng.calls) == 16


def test_seeded_license_first_preserves_output_and_npi_order() -> None:
    rng = Random(20261007)
    generator = DoctorGenerator(dataset="US", rng=rng)
    assert _rng_fingerprint(rng) == "7685fea106ae5340e4a4c150e23f1f00242618b4d6d81c2f24ce6b284647bf24"
    doctor = Doctor(generator)

    assert doctor.license_number == "TT-914288"
    assert _rng_fingerprint(rng) == "aadc6fed366cdde23aa2f29b52dbda579bb49713b3037d8dd2157cadaeec286f"
    assert doctor.npi_number == "1170318221"
    assert _rng_fingerprint(rng) == "c02580ba657949334eeb314102e58bb38f453c81445911bf301bea8479ee367d"


def test_seeded_npi_first_preserves_license_output_and_rng_order() -> None:
    rng = Random(20261007)
    generator = DoctorGenerator(dataset="US", rng=rng)
    assert _rng_fingerprint(rng) == "7685fea106ae5340e4a4c150e23f1f00242618b4d6d81c2f24ce6b284647bf24"
    doctor = Doctor(generator)

    assert doctor.npi_number == "9991428811"
    assert _rng_fingerprint(rng) == "2d26f172a5a8a0d545e7b883d1253b58be020e5fa0bdd9e60d45c065f99b51b2"
    assert doctor.license_number == "PA-318221"
    assert _rng_fingerprint(rng) == "c02580ba657949334eeb314102e58bb38f453c81445911bf301bea8479ee367d"


def test_doctor_id_uses_eight_ordered_public_hex_choices_and_caches() -> None:
    alphabet = "0123456789ABCDEF"
    rng = ScriptedHexRandom(["0"] * 8)
    doctor = Doctor(DoctorGenerator(dataset="US", rng=rng))

    assert doctor.doctor_id == "DOC-00000000"
    assert rng.calls == [alphabet] * 8
    assert doctor.doctor_id == "DOC-00000000"
    assert rng.calls == [alphabet] * 8


def test_doctor_id_uses_switching_public_rng_once() -> None:
    first_rng = ScriptedHexRandom(list("01234567"))
    later_rng = ScriptedHexRandom(list("89ABCDEF"))
    generator = SwitchingPublicRngDoctorGenerator(first_rng=first_rng, later_rng=later_rng, rng=Random(19))
    doctor = Doctor(generator)

    assert doctor.doctor_id == "DOC-01234567"
    assert generator.rng_accesses == 1
    assert first_rng.calls == ["0123456789ABCDEF"] * 8
    assert later_rng.calls == []
    assert doctor.doctor_id == "DOC-01234567"
    assert generator.rng_accesses == 1
    assert first_rng.calls == ["0123456789ABCDEF"] * 8


def test_unbound_doctors_may_keep_duplicate_candidates_and_cache_them() -> None:
    rng = ScriptedHexRandom(["0"] * 16)
    generator = DoctorGenerator(dataset="US", rng=rng)
    first_events: list[tuple[str, object]] = []
    second_events: list[tuple[str, object]] = []
    first = ClaimRecordingDoctor(generator, first_events)
    second = ClaimRecordingDoctor(generator, second_events)

    assert first.doctor_id == "DOC-00000000"
    assert second.doctor_id == "DOC-00000000"
    assert rng.calls == ["0123456789ABCDEF"] * 16
    assert first_events == [("claim", ("doctor_id", "DOC-00000000"))]
    assert second_events == [("claim", ("doctor_id", "DOC-00000000"))]
    assert first.doctor_id == "DOC-00000000"
    assert second.doctor_id == "DOC-00000000"
    assert len(first_events) == len(second_events) == 1
    assert rng.calls == ["0123456789ABCDEF"] * 16


def test_bound_doctor_collision_claims_after_draws_and_caches_allocation() -> None:
    events: list[tuple[str, object]] = []
    rng = ScriptedHexRandom(list("00000009" * 2), events)
    generator = DoctorGenerator(dataset="US", rng=rng)
    first = ClaimRecordingDoctor(generator, events)
    second = ClaimRecordingDoctor(generator, events)
    registry = IdentifierRegistry()
    for doctor in (first, second):
        doctor._bind_identifier_registry(registry, DOCTOR_SCHEMA.entity, DOCTOR_SCHEMA.fields, {})

    assert first.doctor_id == "DOC-00000009"
    assert events[:9] == [("choice", "0123456789ABCDEF")] * 8 + [
        ("claim", ("doctor_id", "DOC-00000009"))
    ]
    assert second.doctor_id == "DOC-0000000A"
    assert events[9:] == [("choice", "0123456789ABCDEF")] * 8 + [
        ("claim", ("doctor_id", "DOC-00000009"))
    ]
    assert second.doctor_id == "DOC-0000000A"
    assert len(events) == 18


def test_doctor_id_claim_exception_propagates_and_does_not_cache() -> None:
    rng = ScriptedHexRandom(["0"] * 16)
    doctor = ClaimFailingDoctor(DoctorGenerator(dataset="US", rng=rng))

    for _ in range(2):
        with pytest.raises(RuntimeError, match="claim failed: doctor_id=DOC-00000000"):
            _ = doctor.doctor_id

    assert doctor.claim_attempts == 2
    assert rng.calls == ["0123456789ABCDEF"] * 16


def test_seeded_doctor_id_and_npi_access_order_keep_full_rng_fingerprints() -> None:
    doctor_first_rng = Random(20261007)
    doctor_first_generator = DoctorGenerator(dataset="US", rng=doctor_first_rng)
    assert _rng_fingerprint(doctor_first_rng) == "7685fea106ae5340e4a4c150e23f1f00242618b4d6d81c2f24ce6b284647bf24"
    doctor_first = Doctor(doctor_first_generator)

    assert doctor_first.doctor_id == "DOC-38433F06"
    assert _rng_fingerprint(doctor_first_rng) == "bc28922b8ed7e92adca18efbe2006719bd31c014f7e6accb004dad8bb8c3f186"
    assert doctor_first.npi_number == "1822153597"
    assert _rng_fingerprint(doctor_first_rng) == "55c40e2ee640267391ac759117e1faa6097a1aeb5a274c2187bc15ec8369b522"

    npi_first_rng = Random(20261007)
    npi_first_generator = DoctorGenerator(dataset="US", rng=npi_first_rng)
    assert _rng_fingerprint(npi_first_rng) == "7685fea106ae5340e4a4c150e23f1f00242618b4d6d81c2f24ce6b284647bf24"
    npi_first = Doctor(npi_first_generator)

    assert npi_first.npi_number == "9991428811"
    assert _rng_fingerprint(npi_first_rng) == "2d26f172a5a8a0d545e7b883d1253b58be020e5fa0bdd9e60d45c065f99b51b2"
    assert npi_first.doctor_id == "DOC-F063553A"
    assert _rng_fingerprint(npi_first_rng) == "34264c376090f799197d6d5f6dcac8a0f5e33ab30140e90f3729357f5e9f2570"


def test_office_hours_follow_weekday_weekend_order_and_only_draw_hours_when_open() -> None:
    events: list[tuple[str, object]] = []
    rng = ScriptedOfficeHoursRandom(
        [0.899999, 0.9, 0.1, 0.95, 0.5, 0.299999, 0.3],
        [7, 19, 8, 16, 10, 18, 11, 17],
        events,
    )
    doctor = Doctor(
        SwitchingPublicRngDoctorGenerator(first_rng=rng, later_rng=Random(1), rng=Random(2))
    )

    assert doctor.office_hours == {
        "Monday": "07:00 - 19:00",
        "Tuesday": "Closed",
        "Wednesday": "08:00 - 16:00",
        "Thursday": "Closed",
        "Friday": "10:00 - 18:00",
        "Saturday": "11:00 - 17:00",
        "Sunday": "Closed",
    }
    assert events == [
        ("random", 0.899999),
        ("randint", (7, 10)),
        ("randint", (16, 19)),
        ("random", 0.9),
        ("random", 0.1),
        ("randint", (7, 10)),
        ("randint", (16, 19)),
        ("random", 0.95),
        ("random", 0.5),
        ("randint", (7, 10)),
        ("randint", (16, 19)),
        ("random", 0.299999),
        ("randint", (8, 11)),
        ("randint", (14, 17)),
        ("random", 0.3),
    ]


def test_office_hours_uses_public_rng_once_and_caches_the_same_mapping() -> None:
    first_rng = ScriptedOfficeHoursRandom([0.9] * 7, [])
    later_rng = ScriptedOfficeHoursRandom([0.0] * 7, [7, 16] * 5 + [8, 14] * 2)
    generator = SwitchingPublicRngDoctorGenerator(first_rng=first_rng, later_rng=later_rng, rng=Random(19))
    doctor = Doctor(generator)

    first_read = doctor.office_hours
    weekdays_and_weekend = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    assert first_read == {day: "Closed" for day in weekdays_and_weekend}
    assert doctor.office_hours is first_read
    assert generator.rng_accesses == 1
    assert len(first_rng.events) == 7
    assert later_rng.events == []


def test_doctors_sharing_generator_keep_independent_office_hours_caches() -> None:
    rng = ScriptedOfficeHoursRandom([0.9] * 7 + [0.0] * 7, [7, 16] * 5 + [8, 14] * 2)
    generator = SwitchingPublicRngDoctorGenerator(first_rng=rng, later_rng=rng, rng=Random(2))
    first = Doctor(generator)
    second = Doctor(generator)

    first_hours = first.office_hours
    second_hours = second.office_hours
    assert first_hours is not second_hours
    assert set(first_hours.values()) == {"Closed"}
    assert all(value != "Closed" for value in second_hours.values())
    assert first.office_hours is first_hours
    assert second.office_hours is second_hours
    assert len(rng.events) == 28


def test_office_hours_generation_failure_propagates_and_retries_without_caching() -> None:
    rng = FailingOnceOfficeHoursRandom()
    generator = SwitchingPublicRngDoctorGenerator(first_rng=rng, later_rng=rng, rng=Random(19))
    doctor = Doctor(generator)

    with pytest.raises(RuntimeError, match="office-hours draw failed"):
        _ = doctor.office_hours

    assert doctor.office_hours == {
        day: "Closed" for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    }
    assert generator.rng_accesses == 2


def test_seeded_office_hours_access_order_preserves_outputs_and_rng_state() -> None:
    office_first_rng = Random(20261007)
    office_first = Doctor(DoctorGenerator(dataset="US", rng=office_first_rng))
    assert office_first.office_hours == {
        "Monday": "07:00 - 18:00",
        "Tuesday": "08:00 - 16:00",
        "Wednesday": "10:00 - 16:00",
        "Thursday": "07:00 - 17:00",
        "Friday": "09:00 - 17:00",
        "Saturday": "Closed",
        "Sunday": "Closed",
    }
    assert office_first.accepting_new_patients is False
    assert _rng_fingerprint(office_first_rng) == "f8a79b83fd07721acb2e3a19195f11fe2965fa237a4ca7ec929a3115364f7c74"

    acceptance_first_rng = Random(20261007)
    acceptance_first = Doctor(DoctorGenerator(dataset="US", rng=acceptance_first_rng))
    assert acceptance_first.accepting_new_patients is True
    assert acceptance_first.office_hours == {
        "Monday": "07:00 - 18:00",
        "Tuesday": "08:00 - 16:00",
        "Wednesday": "10:00 - 16:00",
        "Thursday": "07:00 - 17:00",
        "Friday": "09:00 - 17:00",
        "Saturday": "Closed",
        "Sunday": "Closed",
    }
    assert _rng_fingerprint(acceptance_first_rng) == "55c40e2ee640267391ac759117e1faa6097a1aeb5a274c2187bc15ec8369b522"


def test_office_hours_property_delegates_to_generator_and_caches() -> None:
    class FixedOfficeHoursGenerator(DoctorGenerator):
        def __init__(self) -> None:
            super().__init__(dataset="US", rng=Random(1))
            self.calls = 0
            self.hours = {"Monday": "09:00 - 17:00"}

        def generate_office_hours(self) -> dict[str, str]:
            self.calls += 1
            return self.hours

    generator = FixedOfficeHoursGenerator()
    doctor = Doctor(generator)

    assert doctor.office_hours is generator.hours
    assert doctor.office_hours is generator.hours
    assert generator.calls == 1
