from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.domain_core.base_entity import IdentifierRegistry
from datamimic_ce.domains.healthcare.generators.patient_generator import PatientGenerator
from datamimic_ce.domains.healthcare.models.patient import Patient
from datamimic_ce.domains.healthcare.services.patient_service import PATIENT_SCHEMA


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class ScriptedChoiceRandom(Random):
    def __init__(self, values: list[str]) -> None:
        self.values = iter(values)
        self.calls: list[str] = []
        super().__init__(0)

    def choice(self, seq: str) -> str:
        self.calls.append(seq)
        return next(self.values)


class RepeatedChoiceRandom(Random):
    def __init__(self, value: str) -> None:
        self.value = value
        self.calls: list[str] = []
        super().__init__(0)

    def choice(self, seq: str) -> str:
        self.calls.append(seq)
        return self.value


class ScriptedIntegerRandom(Random):
    def __init__(self, values: list[int]) -> None:
        self.values = iter(values)
        self.bounds: list[tuple[int, int]] = []
        super().__init__(0)

    def randint(self, a: int, b: int) -> int:
        self.bounds.append((a, b))
        return next(self.values)


class RepeatedIntegerRandom(Random):
    def __init__(self, value: int) -> None:
        self.value = value
        self.bounds: list[tuple[int, int]] = []
        super().__init__(0)

    def randint(self, a: int, b: int) -> int:
        self.bounds.append((a, b))
        return self.value


class ScriptedPolicyRandom(Random):
    def __init__(self) -> None:
        self.events: list[tuple[str, object]] = []
        self.choices = iter("ABC")
        self.digits = iter([0, 1, 2, 3, 4, 5, 6, 7])
        super().__init__(0)

    def choice(self, seq: str) -> str:
        self.events.append(("choice", seq))
        return next(self.choices)

    def randint(self, a: int, b: int) -> int:
        self.events.append(("randint", (a, b)))
        return next(self.digits)


class PolicyWithoutProviderPatient(Patient):
    def _claim_identifier(self, field_name: str, candidate: str) -> str:
        raise AssertionError(f"{field_name} must not claim {candidate}")

    @property
    def insurance_provider(self) -> str:
        raise AssertionError("policy number generation must not resolve the provider")


class ScriptedUniformRandom(Random):
    def __init__(self, value: float, events: list[tuple[str, object]]) -> None:
        self.value = value
        self.bounds: list[tuple[float, float]] = []
        self.events = events
        super().__init__(0)

    def uniform(self, a: float, b: float) -> float:
        self.bounds.append((a, b))
        self.events.append(("uniform", (a, b)))
        return self.value


class QueuedUniformRandom(Random):
    def __init__(self, values: list[float], events: list[tuple[str, object]]) -> None:
        self.values = iter(values)
        self.bounds: list[tuple[float, float]] = []
        self.events = events
        super().__init__(0)

    def uniform(self, a: float, b: float) -> float:
        self.bounds.append((a, b))
        self.events.append(("uniform", (a, b)))
        return next(self.values)


class SwitchingPublicRngPatientGenerator(PatientGenerator):
    def __init__(self, *, first_rng: Random, later_rng: Random, rng: Random) -> None:
        self.first_rng = first_rng
        self.later_rng = later_rng
        self.rng_accesses = 0
        super().__init__(dataset="US", rng=rng)

    @property
    def rng(self) -> Random:
        self.rng_accesses += 1
        return self.first_rng if self.rng_accesses == 1 else self.later_rng


class RecordingPublicRngPatientGenerator(PatientGenerator):
    def __init__(self, *, public_rng: Random, events: list[tuple[str, object]]) -> None:
        self.public_rng = public_rng
        self.events = events
        self.rng_accesses = 0
        super().__init__(dataset="US", rng=Random(1))

    @property
    def rng(self) -> Random:
        self.rng_accesses += 1
        self.events.append(("rng", None))
        return self.public_rng


class FixedDemographicPatient(Patient):
    def __init__(
        self,
        generator: PatientGenerator,
        *,
        gender: str,
        age: int,
        events: list[tuple[str, object]],
    ) -> None:
        super().__init__(generator)
        self._fixed_gender = gender
        self._fixed_age = age
        self._events = events

    @property
    def gender(self) -> str:
        self._events.append(("gender", None))
        return self._fixed_gender

    @property
    def age(self) -> int:
        self._events.append(("age", None))
        return self._fixed_age


class FailingGenderPatient(Patient):
    def __init__(self, generator: PatientGenerator, events: list[tuple[str, object]]) -> None:
        super().__init__(generator)
        self._events = events

    @property
    def gender(self) -> str:
        self._events.append(("gender", None))
        raise RuntimeError("gender resolution failed")


def test_patient_id_candidate_uses_one_public_rng_and_eight_ordered_hex_choices() -> None:
    rng = ScriptedChoiceRandom(list("00ABCDEF"))
    later_rng = ScriptedChoiceRandom(list("12345678"))
    generator = SwitchingPublicRngPatientGenerator(first_rng=rng, later_rng=later_rng, rng=Random(2))

    assert generator.generate_patient_id_candidate() == "PAT-00ABCDEF"
    assert generator.rng_accesses == 1
    assert rng.calls == ["0123456789ABCDEF"] * 8
    assert later_rng.calls == []


def test_patient_id_is_cached_and_unbound_duplicate_candidates_are_not_claimed() -> None:
    rng = RepeatedChoiceRandom("0")
    generator = PatientGenerator(dataset="US", rng=rng)
    first = Patient(generator)
    second = Patient(generator)

    assert first.patient_id == "PAT-00000000"
    assert second.patient_id == "PAT-00000000"
    calls_after_both = len(rng.calls)
    assert calls_after_both == 16
    assert first.patient_id == "PAT-00000000"
    assert second.patient_id == "PAT-00000000"
    assert len(rng.calls) == calls_after_both


def test_bound_patient_id_claims_after_eight_draws_and_uses_collision_suffix_without_redraw() -> None:
    events: list[tuple[str, object]] = []
    rng = OrderedChoiceRandom("0", events)
    generator = PatientGenerator(dataset="US", rng=rng)
    first = ClaimRecordingPatient(generator, events)
    second = ClaimRecordingPatient(generator, events)
    registry = IdentifierRegistry()
    for patient in (first, second):
        patient._bind_identifier_registry(registry, PATIENT_SCHEMA.entity, PATIENT_SCHEMA.fields, {})

    assert first.patient_id == "PAT-00000000"
    claim = ("claim", ("patient_id", "PAT-00000000"))
    assert events[:9] == [("choice", "0123456789ABCDEF")] * 8 + [claim]
    assert second.patient_id == "PAT-00000001"
    assert events[9:] == [("choice", "0123456789ABCDEF")] * 8 + [claim]
    assert second.patient_id == "PAT-00000001"
    assert len(events) == 18


def test_patient_id_claim_failure_propagates_and_is_not_cached() -> None:
    rng = RepeatedChoiceRandom("0")
    patient = ClaimFailingPatient(PatientGenerator(dataset="US", rng=rng))

    for _ in range(2):
        with pytest.raises(RuntimeError, match="claim failed: patient_id=PAT-00000000"):
            _ = patient.patient_id

    assert patient.claim_attempts == 2
    assert rng.calls == ["0123456789ABCDEF"] * 16


class ClaimRejectingPatient(Patient):
    def _claim_identifier(self, field_name: str, candidate: str) -> str:
        raise AssertionError(f"{field_name} must not claim {candidate}")


class ClaimRecordingPatient(Patient):
    def __init__(self, generator: PatientGenerator, events: list[tuple[str, object]]) -> None:
        super().__init__(generator)
        self.events = events

    def _claim_identifier(self, field_name: str, candidate: str) -> str:
        self.events.append(("claim", (field_name, candidate)))
        return super()._claim_identifier(field_name, candidate)


class ClaimFailingPatient(Patient):
    def __init__(self, generator: PatientGenerator) -> None:
        super().__init__(generator)
        self.claim_attempts = 0

    def _claim_identifier(self, field_name: str, candidate: str) -> str:
        self.claim_attempts += 1
        raise RuntimeError(f"claim failed: {field_name}={candidate}")


class OrderedChoiceRandom(Random):
    def __init__(self, value: str, events: list[tuple[str, object]]) -> None:
        self.value = value
        self.events = events
        super().__init__(0)

    def choice(self, seq: str) -> str:
        self.events.append(("choice", seq))
        return self.value


def test_medical_record_number_uses_one_public_rng_and_eight_ordered_hex_choices() -> None:
    rng = ScriptedChoiceRandom(list("00ABCDEF"))
    generator = SwitchingPublicRngPatientGenerator(first_rng=rng, later_rng=Random(1), rng=Random(2))
    patient = Patient(generator)

    assert patient.medical_record_number == "MRN-00ABCDEF"
    assert generator.rng_accesses == 1
    assert rng.calls == ["0123456789ABCDEF"] * 8


def test_medical_record_number_uses_first_rng_when_public_accessor_switches() -> None:
    first_rng = ScriptedChoiceRandom(list("00ABCDEF"))
    later_rng = ScriptedChoiceRandom(list("12345678"))
    generator = SwitchingPublicRngPatientGenerator(first_rng=first_rng, later_rng=later_rng, rng=Random(3))
    patient = Patient(generator)

    assert patient.medical_record_number == "MRN-00ABCDEF"
    assert patient.medical_record_number == "MRN-00ABCDEF"
    assert generator.rng_accesses == 1
    assert first_rng.calls == ["0123456789ABCDEF"] * 8
    assert later_rng.calls == []


def test_medical_record_number_duplicates_are_allowed_and_patient_caches_are_independent() -> None:
    rng = RepeatedChoiceRandom("0")
    generator = PatientGenerator(dataset="US", rng=rng)
    first = ClaimRejectingPatient(generator)
    second = ClaimRejectingPatient(generator)

    assert first.medical_record_number == "MRN-00000000"
    assert second.medical_record_number == "MRN-00000000"
    calls_after_both = len(rng.calls)
    assert calls_after_both == 16
    assert first.medical_record_number == "MRN-00000000"
    assert second.medical_record_number == "MRN-00000000"
    assert len(rng.calls) == calls_after_both


def test_ssn_uses_one_public_rng_and_nine_ordered_digit_draws_then_caches() -> None:
    rng = ScriptedIntegerRandom([0, 0, 1, 2, 3, 4, 5, 6, 7])
    later_rng = ScriptedIntegerRandom([8] * 9)
    generator = SwitchingPublicRngPatientGenerator(first_rng=rng, later_rng=later_rng, rng=Random(2))
    patient = Patient(generator)

    assert patient.ssn == "001-23-4567"
    assert generator.rng_accesses == 1
    assert rng.bounds == [(0, 9)] * 9
    assert later_rng.bounds == []
    assert patient.ssn == "001-23-4567"
    assert generator.rng_accesses == 1
    assert rng.bounds == [(0, 9)] * 9
    assert later_rng.bounds == []


def test_ssn_duplicates_are_allowed_and_patient_caches_are_independent() -> None:
    rng = RepeatedIntegerRandom(0)
    generator = PatientGenerator(dataset="US", rng=rng)
    first = ClaimRejectingPatient(generator)
    second = ClaimRejectingPatient(generator)

    assert first.ssn == "000-00-0000"
    assert second.ssn == "000-00-0000"
    bounds_after_both = len(rng.bounds)
    assert bounds_after_both == 18
    assert first.ssn == "000-00-0000"
    assert second.ssn == "000-00-0000"
    assert len(rng.bounds) == bounds_after_both


def test_insurance_policy_number_uses_ordered_choices_and_digit_draws() -> None:
    rng = ScriptedPolicyRandom()
    generator = SwitchingPublicRngPatientGenerator(first_rng=rng, later_rng=Random(1), rng=Random(2))

    assert generator.generate_insurance_policy_number() == "ABC-01234567"
    assert generator.rng_accesses == 1
    assert rng.events == [
        *(('choice', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(3)),
        *(('randint', (0, 9)) for _ in range(8)),
    ]


def test_insurance_policy_number_allows_duplicates_and_caches_per_patient() -> None:
    rng = ScriptedPolicyRandom()
    generator = PatientGenerator(dataset="US", rng=rng)
    first = PolicyWithoutProviderPatient(generator)
    second = PolicyWithoutProviderPatient(generator)

    assert first.insurance_policy_number == "ABC-01234567"
    first_events = list(rng.events)
    assert first.insurance_policy_number == "ABC-01234567"
    assert rng.events == first_events

    # The shared generator may produce the same candidate; each Patient owns its cache.
    rng.choices = iter("ABC")
    rng.digits = iter([0, 1, 2, 3, 4, 5, 6, 7])
    assert second.insurance_policy_number == "ABC-01234567"
    events_after_both = list(rng.events)
    assert len(events_after_both) == 22
    assert first.insurance_policy_number == "ABC-01234567"
    assert second.insurance_policy_number == "ABC-01234567"
    assert rng.events == events_after_both


@pytest.mark.parametrize(
    ("age", "gender", "expected_bounds"),
    [
        (17, "Male", (175, 195)),
        (17, "Unrecognized", (171.6, 191.6)),
        (18, "Male", (160, 190)),
        (18, "Unrecognized", (150, 175)),
    ],
)
def test_height_uses_demographics_then_one_public_rng_draw_and_caches(
    age: int, gender: str, expected_bounds: tuple[float, float]
) -> None:
    events: list[tuple[str, object]] = []
    draw = expected_bounds[0] + 0.06
    rng = ScriptedUniformRandom(draw, events)
    generator = RecordingPublicRngPatientGenerator(public_rng=rng, events=events)
    patient = FixedDemographicPatient(generator, gender=gender, age=age, events=events)

    assert patient.height_cm == round(draw, 1)
    assert events == [
        ("gender", None),
        ("age", None),
        ("rng", None),
        ("uniform", expected_bounds),
    ]
    assert generator.rng_accesses == 1
    assert rng.bounds == [expected_bounds]
    assert patient.height_cm == round(draw, 1)
    assert generator.rng_accesses == 1
    assert rng.bounds == [expected_bounds]
    assert len(events) == 4


def test_patients_sharing_generator_keep_independent_height_caches() -> None:
    events: list[tuple[str, object]] = []
    rng = ScriptedUniformRandom(170.04, events)
    generator = RecordingPublicRngPatientGenerator(public_rng=rng, events=events)
    first = FixedDemographicPatient(generator, gender="Female", age=40, events=events)
    second = FixedDemographicPatient(generator, gender="Female", age=40, events=events)

    assert first.height_cm == 170.0
    assert second.height_cm == 170.0
    assert generator.rng_accesses == 2
    assert rng.bounds == [(150, 175), (150, 175)]
    events_after_both = list(events)
    assert first.height_cm == 170.0
    assert second.height_cm == 170.0
    assert events == events_after_both


def test_height_gender_failure_does_not_read_public_rng() -> None:
    events: list[tuple[str, object]] = []
    rng = ScriptedUniformRandom(170.0, events)
    generator = RecordingPublicRngPatientGenerator(public_rng=rng, events=events)
    patient = FailingGenderPatient(generator, events)

    with pytest.raises(RuntimeError, match="gender resolution failed"):
        _ = patient.height_cm

    assert events == [("gender", None)]
    assert generator.rng_accesses == 0
    assert rng.bounds == []


@pytest.mark.parametrize(
    ("age", "bmi_bounds", "bmi_draw", "expected_weight"),
    [
        (17, (16, 24), 20, 64.8),
        (18, (18.5, 29.9), 24, 77.8),
    ],
)
def test_weight_generator_uses_age_boundary_height_and_two_ordered_draws(
    age: int,
    bmi_bounds: tuple[float, float],
    bmi_draw: float,
    expected_weight: float,
) -> None:
    events: list[tuple[str, object]] = []
    rng = QueuedUniformRandom([bmi_draw, 0], events)
    generator = RecordingPublicRngPatientGenerator(public_rng=rng, events=events)

    assert generator.generate_weight_kg(age, 180) == expected_weight
    assert events == [
        ("rng", None),
        ("uniform", bmi_bounds),
        ("uniform", (-(bmi_draw * 3.24 * 0.1), bmi_draw * 3.24 * 0.1)),
    ]
    assert generator.rng_accesses == 1
    assert rng.bounds == [bmi_bounds, (-(bmi_draw * 3.24 * 0.1), bmi_draw * 3.24 * 0.1)]


@pytest.mark.parametrize(
    ("age", "height_bounds", "bmi_bounds", "bmi_draw", "expected_weight"),
    [
        (17, (175, 195), (16, 24), 20, 64.8),
        (18, (160, 190), (18.5, 29.9), 24, 77.8),
    ],
)
def test_patient_resolves_age_then_height_before_weight_rng(
    age: int,
    height_bounds: tuple[float, float],
    bmi_bounds: tuple[float, float],
    bmi_draw: float,
    expected_weight: float,
) -> None:
    events: list[tuple[str, object]] = []
    rng = QueuedUniformRandom([180, bmi_draw, 0], events)
    generator = RecordingPublicRngPatientGenerator(public_rng=rng, events=events)
    patient = FixedDemographicPatient(generator, gender="Male", age=age, events=events)

    assert patient.weight_kg == expected_weight
    assert events == [
        ("age", None),
        ("gender", None),
        ("age", None),
        ("rng", None),
        ("uniform", height_bounds),
        ("rng", None),
        ("uniform", bmi_bounds),
        ("uniform", (-(bmi_draw * 3.24 * 0.1), bmi_draw * 3.24 * 0.1)),
    ]
    assert generator.rng_accesses == 2


def test_seeded_height_first_and_weight_first_keep_outputs_and_rng_states() -> None:
    height_first_rng = Random(20261007)
    assert _rng_fingerprint(height_first_rng) == "5b2f8e83e593409a4f59574b4ef73b31e527195f33ac579050ce0f50ef101591"
    height_first_generator = PatientGenerator(dataset="US", rng=height_first_rng)
    assert _rng_fingerprint(height_first_rng) == "c0c35cd265fa8b6c6dab3aadaf406ff4d62a4980bf8a7e989d3079bf9f7a49b8"
    height_first = Patient(height_first_generator)

    assert height_first.height_cm == 170.5
    assert _rng_fingerprint(height_first_rng) == "2d26f172a5a8a0d545e7b883d1253b58be020e5fa0bdd9e60d45c065f99b51b2"
    assert height_first.weight_kg == 76.4
    assert _rng_fingerprint(height_first_rng) == "a109175244eac52cd054771324e562305008cccd82b4954717d9d21964356cc9"

    weight_first_rng = Random(20261007)
    weight_first_generator = PatientGenerator(dataset="US", rng=weight_first_rng)
    assert _rng_fingerprint(weight_first_rng) == "c0c35cd265fa8b6c6dab3aadaf406ff4d62a4980bf8a7e989d3079bf9f7a49b8"
    weight_first = Patient(weight_first_generator)

    assert weight_first.weight_kg == 76.4
    assert weight_first.height_cm == 170.5
    assert _rng_fingerprint(weight_first_rng) == "a109175244eac52cd054771324e562305008cccd82b4954717d9d21964356cc9"


def test_seeded_medical_record_number_and_field_order_keep_full_rng_fingerprints() -> None:
    mrn_rng = Random(20261007)
    assert _rng_fingerprint(mrn_rng) == "5b2f8e83e593409a4f59574b4ef73b31e527195f33ac579050ce0f50ef101591"
    mrn_generator = PatientGenerator(dataset="US", rng=mrn_rng)
    assert _rng_fingerprint(mrn_rng) == "c0c35cd265fa8b6c6dab3aadaf406ff4d62a4980bf8a7e989d3079bf9f7a49b8"
    mrn_patient = Patient(mrn_generator)

    assert mrn_patient.medical_record_number == "MRN-3F063553"
    assert _rng_fingerprint(mrn_rng) == "c02580ba657949334eeb314102e58bb38f453c81445911bf301bea8479ee367d"

    mrn_first_rng = Random(20261007)
    mrn_first_generator = PatientGenerator(dataset="US", rng=mrn_first_rng)
    assert _rng_fingerprint(mrn_first_rng) == "c0c35cd265fa8b6c6dab3aadaf406ff4d62a4980bf8a7e989d3079bf9f7a49b8"
    mrn_first_patient = Patient(mrn_first_generator)

    assert mrn_first_patient.medical_record_number == "MRN-3F063553"
    assert _rng_fingerprint(mrn_first_rng) == "c02580ba657949334eeb314102e58bb38f453c81445911bf301bea8479ee367d"
    assert mrn_first_patient.ssn == "535-97-3095"
    assert _rng_fingerprint(mrn_first_rng) == "842d58b377762d06c5a68fab497d56861e0638cef5344de0fe58c04b0987eb34"

    ssn_rng = Random(20261007)
    ssn_generator = PatientGenerator(dataset="US", rng=ssn_rng)
    assert _rng_fingerprint(ssn_rng) == "c0c35cd265fa8b6c6dab3aadaf406ff4d62a4980bf8a7e989d3079bf9f7a49b8"
    ssn_patient = Patient(ssn_generator)

    assert ssn_patient.ssn == "170-31-8221"
    assert ssn_patient.medical_record_number == "MRN-A6BF70A8"
    assert _rng_fingerprint(ssn_rng) == "d8b4354d57cf07c6a3fb57a0c40771decaeecbad0294bdc33d845c202ba18241"
