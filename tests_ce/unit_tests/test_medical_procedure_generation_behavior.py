from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.domain_core.base_entity import IdentifierRegistry
from datamimic_ce.domains.healthcare.generators.medical_procedure_generator import MedicalProcedureGenerator
from datamimic_ce.domains.healthcare.models.medical_procedure import MedicalProcedure
from datamimic_ce.domains.healthcare.services.medical_procedure_service import MEDICAL_PROCEDURE_SCHEMA


def _procedure(seed: int) -> tuple[MedicalProcedure, Random]:
    rng = Random(seed)
    return MedicalProcedure(MedicalProcedureGenerator(dataset="US", rng=rng)), rng


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class _PublicRngMedicalProcedureGenerator(MedicalProcedureGenerator):
    def __init__(self, internal_rng: Random, public_rng: Random):
        self._public_rng = public_rng
        super().__init__(dataset="US", rng=internal_rng)

    @property
    def rng(self) -> Random:
        return self._public_rng


class _ScriptedRandom(Random):
    def __init__(self, values: list[float]):
        super().__init__(0)
        self.values = iter(values)
        self.draw_count = 0

    def random(self) -> float:
        self.draw_count += 1
        return next(self.values)


class _ScriptedIntegerRandom(Random):
    def __init__(self, values: list[int]):
        super().__init__(0)
        self.values = iter(values)
        self.bounds: list[tuple[int, int]] = []

    def randint(self, a: int, b: int) -> int:
        self.bounds.append((a, b))
        return next(self.values)


class _ScriptedChoiceRandom(Random):
    def __init__(self, values: list[str], events: list[tuple[str, object]] | None = None):
        super().__init__(0)
        self.values = iter(values)
        self.calls: list[str] = []
        self.events = events if events is not None else []

    def choice(self, seq: str) -> str:
        self.calls.append(seq)
        self.events.append(("choice", seq))
        return next(self.values)


class _ClaimRecordingMedicalProcedure(MedicalProcedure):
    def __init__(self, generator: MedicalProcedureGenerator, events: list[tuple[str, object]]):
        super().__init__(generator)
        self.events = events

    def _claim_identifier(self, name: str, candidate: str) -> str:
        self.events.append(("claim", (name, candidate)))
        return super()._claim_identifier(name, candidate)


class _ClaimFailingMedicalProcedure(MedicalProcedure):
    def __init__(self, generator: MedicalProcedureGenerator):
        super().__init__(generator)
        self.claim_attempts = 0

    def _claim_identifier(self, name: str, candidate: str) -> str:
        self.claim_attempts += 1
        raise RuntimeError(f"claim failed: {name}={candidate}")


class _FixedProcedureIdGenerator(MedicalProcedureGenerator):
    def __init__(self):
        super().__init__(dataset="US", rng=Random(0))
        self.candidate_calls = 0

    def generate_procedure_id_candidate(self) -> str:
        self.candidate_calls += 1
        return "PROC-00000001"


class _SurgicalOverrideMedicalProcedure(MedicalProcedure):
    @property
    def is_surgical(self) -> bool:
        return True


class _SwitchingRngMedicalProcedureGenerator(MedicalProcedureGenerator):
    def __init__(self, first_rng: Random, later_rng: Random):
        self.first_rng = first_rng
        self.later_rng = later_rng
        self.rng_accesses = 0
        super().__init__(dataset="US", rng=Random(99))

    @property
    def rng(self) -> Random:
        self.rng_accesses += 1
        return self.first_rng if self.rng_accesses == 1 else self.later_rng


@pytest.mark.parametrize(
    ("seed", "is_surgical", "duration_minutes", "state_before", "state_after"),
    [
        (
            1,
            True,
            235,
            "b55f01246d4598a89048ef23011391ca54de147be40488b768da38e08df9ce74",
            "f383b34fe304e61b9271b50e90c00764037c568a073afdb507ec30fc31e39016",
        ),
        (
            2,
            False,
            118,
            "1bde6feb70f9a75d9ffe29acc3576a646cef63e7cfa2a9f42829768e339d204b",
            "9d041a8cfb3fb88012ef5f15d61eaa1033d9fe9f6396703b99460c08730266dc",
        ),
    ],
)
def test_duration_seeded_surgical_branches_are_lazy_and_cached(
    seed, is_surgical, duration_minutes, state_before, state_after
) -> None:
    procedure, rng = _procedure(seed)

    assert _rng_fingerprint(rng) == state_before
    assert procedure.duration_minutes == duration_minutes
    state_after_read = rng.getstate()
    assert _rng_fingerprint(rng) == state_after
    assert procedure.is_surgical is is_surgical
    assert procedure.duration_minutes == duration_minutes
    assert rng.getstate() == state_after_read


@pytest.mark.parametrize(
    ("seed", "is_surgical", "duration_minutes", "state_after_surgical", "state_after_duration"),
    [
        (
            1,
            True,
            235,
            "f24bf6df981b4bc5f555acec893860ee1b8ba957798e1ce93e62ddd0ca62820f",
            "f383b34fe304e61b9271b50e90c00764037c568a073afdb507ec30fc31e39016",
        ),
        (
            2,
            False,
            118,
            "b39b27de735900414d955fb0da4c019d386c8dfe7657cb3ac7e4abae45796ba5",
            "9d041a8cfb3fb88012ef5f15d61eaa1033d9fe9f6396703b99460c08730266dc",
        ),
    ],
)
def test_surgical_flag_before_duration_keeps_seeded_rng_sequence(
    seed, is_surgical, duration_minutes, state_after_surgical, state_after_duration
) -> None:
    procedure, rng = _procedure(seed)

    assert procedure.is_surgical is is_surgical
    assert _rng_fingerprint(rng) == state_after_surgical
    assert procedure.duration_minutes == duration_minutes
    assert _rng_fingerprint(rng) == state_after_duration


@pytest.mark.parametrize(("draw", "expected"), [(0.299999, True), (0.3, False)])
def test_surgical_flag_uses_strict_threshold_and_caches_one_rng_draw(draw: float, expected: bool) -> None:
    rng = _ScriptedRandom([draw])
    procedure = MedicalProcedure(MedicalProcedureGenerator(dataset="US", rng=rng))

    assert procedure.is_surgical is expected
    assert rng.draw_count == 1
    assert procedure.is_surgical is expected
    assert rng.draw_count == 1


def test_shared_generator_keeps_independent_surgical_flag_caches() -> None:
    rng = _ScriptedRandom([0.2, 0.8])
    generator = MedicalProcedureGenerator(dataset="US", rng=rng)
    first = MedicalProcedure(generator)
    second = MedicalProcedure(generator)

    assert first.is_surgical is True
    assert second.is_surgical is False
    assert rng.draw_count == 2
    assert first.is_surgical is True
    assert second.is_surgical is False
    assert rng.draw_count == 2


def test_surgical_flag_uses_public_rng_accessor() -> None:
    internal_rng = _ScriptedRandom([0.1])
    public_rng = _ScriptedRandom([0.9])
    procedure = MedicalProcedure(_PublicRngMedicalProcedureGenerator(internal_rng, public_rng))

    assert procedure.is_surgical is False
    assert public_rng.draw_count == 1
    assert internal_rng.draw_count == 0


@pytest.mark.parametrize(
    ("surgical_draw", "anesthesia_draw", "expected"),
    [
        (0.1, 0.899999, True),
        (0.1, 0.9, False),
        (0.8, 0.199999, True),
        (0.8, 0.2, False),
    ],
)
def test_anesthesia_uses_strict_threshold_after_surgical_draw(
    surgical_draw: float, anesthesia_draw: float, expected: bool
) -> None:
    rng = _ScriptedRandom([surgical_draw, anesthesia_draw])
    procedure = MedicalProcedure(MedicalProcedureGenerator(dataset="US", rng=rng))

    assert procedure.requires_anesthesia is expected
    assert rng.draw_count == 2
    assert procedure.requires_anesthesia is expected
    assert rng.draw_count == 2


def test_cached_surgical_flag_makes_anesthesia_consume_only_one_draw() -> None:
    rng = _ScriptedRandom([0.1, 0.9, 0.1])
    procedure = MedicalProcedure(MedicalProcedureGenerator(dataset="US", rng=rng))

    assert procedure.is_surgical is True
    assert rng.draw_count == 1
    assert procedure.requires_anesthesia is False
    assert rng.draw_count == 2
    assert procedure.requires_anesthesia is False
    assert procedure.is_surgical is True
    assert rng.draw_count == 2


def test_shared_generator_keeps_independent_anesthesia_caches() -> None:
    rng = _ScriptedRandom([0.1, 0.95, 0.8, 0.1])
    generator = MedicalProcedureGenerator(dataset="US", rng=rng)
    first = MedicalProcedure(generator)
    second = MedicalProcedure(generator)

    assert first.requires_anesthesia is False
    assert second.requires_anesthesia is True
    assert rng.draw_count == 4
    assert first.requires_anesthesia is False
    assert second.requires_anesthesia is True
    assert rng.draw_count == 4


def test_anesthesia_uses_public_rng_accessor_and_surgical_override() -> None:
    internal_rng = _ScriptedRandom([0.1])
    public_rng = _ScriptedRandom([0.9])
    generator = _PublicRngMedicalProcedureGenerator(internal_rng, public_rng)
    procedure = _SurgicalOverrideMedicalProcedure(generator)

    assert procedure.requires_anesthesia is False
    assert public_rng.draw_count == 1
    assert internal_rng.draw_count == 0


@pytest.mark.parametrize(
    ("surgical_draw", "preventive_draw", "expected"),
    [
        (0.1, 0.049999, True),
        (0.1, 0.05, False),
        (0.8, 0.299999, True),
        (0.8, 0.3, False),
    ],
)
def test_preventive_flag_uses_strict_branch_threshold_and_caches_draws(
    surgical_draw: float, preventive_draw: float, expected: bool
) -> None:
    rng = _ScriptedRandom([surgical_draw, preventive_draw])
    procedure = MedicalProcedure(MedicalProcedureGenerator(dataset="US", rng=rng))

    assert procedure.is_preventive is expected
    assert rng.draw_count == 2
    assert procedure.is_preventive is expected
    assert procedure.is_surgical is (surgical_draw < 0.3)
    assert rng.draw_count == 2


def test_cached_surgical_flag_makes_preventive_consume_only_one_draw() -> None:
    rng = _ScriptedRandom([0.1, 0.05])
    procedure = MedicalProcedure(MedicalProcedureGenerator(dataset="US", rng=rng))

    assert procedure.is_surgical is True
    assert rng.draw_count == 1
    assert procedure.is_preventive is False
    assert rng.draw_count == 2
    assert procedure.is_preventive is False
    assert rng.draw_count == 2


def test_shared_generator_keeps_independent_preventive_caches() -> None:
    rng = _ScriptedRandom([0.1, 0.01, 0.8, 0.5])
    generator = MedicalProcedureGenerator(dataset="US", rng=rng)
    first = MedicalProcedure(generator)
    second = MedicalProcedure(generator)

    assert first.is_preventive is True
    assert second.is_preventive is False
    assert rng.draw_count == 4
    assert first.is_preventive is True
    assert second.is_preventive is False
    assert rng.draw_count == 4


def test_preventive_uses_public_rng_and_overridden_surgical_property() -> None:
    internal_rng = _ScriptedRandom([0.1])
    public_rng = _ScriptedRandom([0.049])
    generator = _PublicRngMedicalProcedureGenerator(internal_rng, public_rng)
    procedure = _SurgicalOverrideMedicalProcedure(generator)

    assert procedure.is_preventive is True
    assert public_rng.draw_count == 1
    assert internal_rng.draw_count == 0


def test_preventive_first_preserves_seeded_result_and_rng_state() -> None:
    procedure, rng = _procedure(17)

    assert procedure.is_preventive is False
    assert _rng_fingerprint(rng) == "41366acddfd24b8b1f612b4db504237e0a0d0e182f625dcf4729ab01a57934e3"


def test_description_first_preserves_seeded_output_and_rng_state() -> None:
    procedure, rng = _procedure(23)

    assert procedure.description == "A diagnostic procedure to Scanning the Vein and diagnose a medical condition."
    assert _rng_fingerprint(rng) == "178ee4845126485cadb19df6ec48382c51e096f99e0e9595a3eada1d1e0fa472"


@pytest.mark.parametrize(
    ("surgical_draw", "diagnostic_draw", "expected"),
    [
        (0.1, 0.199999, True),
        (0.1, 0.2, False),
        (0.8, 0.699999, True),
        (0.8, 0.7, False),
    ],
)
def test_diagnostic_flag_uses_strict_branch_threshold_and_caches_draws(
    surgical_draw: float, diagnostic_draw: float, expected: bool
) -> None:
    rng = _ScriptedRandom([surgical_draw, diagnostic_draw])
    procedure = MedicalProcedure(MedicalProcedureGenerator(dataset="US", rng=rng))

    assert procedure.is_diagnostic is expected
    assert rng.draw_count == 2
    assert procedure.is_diagnostic is expected
    assert procedure.is_surgical is (surgical_draw < 0.3)
    assert rng.draw_count == 2


def test_cached_surgical_flag_makes_diagnostic_consume_only_one_draw() -> None:
    rng = _ScriptedRandom([0.1, 0.2])
    procedure = MedicalProcedure(MedicalProcedureGenerator(dataset="US", rng=rng))

    assert procedure.is_surgical is True
    assert rng.draw_count == 1
    assert procedure.is_diagnostic is False
    assert rng.draw_count == 2
    assert procedure.is_diagnostic is False
    assert rng.draw_count == 2


def test_shared_generator_keeps_independent_diagnostic_caches() -> None:
    rng = _ScriptedRandom([0.1, 0.1, 0.8, 0.8])
    generator = MedicalProcedureGenerator(dataset="US", rng=rng)
    first = MedicalProcedure(generator)
    second = MedicalProcedure(generator)

    assert first.is_diagnostic is True
    assert second.is_diagnostic is False
    assert rng.draw_count == 4
    assert first.is_diagnostic is True
    assert second.is_diagnostic is False
    assert rng.draw_count == 4


def test_diagnostic_uses_public_rng_and_overridden_surgical_property() -> None:
    internal_rng = _ScriptedRandom([0.1])
    public_rng = _ScriptedRandom([0.199])
    generator = _PublicRngMedicalProcedureGenerator(internal_rng, public_rng)
    procedure = _SurgicalOverrideMedicalProcedure(generator)

    assert procedure.is_diagnostic is True
    assert public_rng.draw_count == 1
    assert internal_rng.draw_count == 0


def test_diagnostic_first_preserves_seeded_result_and_rng_state() -> None:
    procedure, rng = _procedure(31)

    assert procedure.is_diagnostic is True
    assert _rng_fingerprint(rng) == "d3b302e4ad02e9631990b92f85d6401302771b03d99ba07b4cceeee802a86ffd"


def test_name_first_preserves_seeded_output_and_evaluates_diagnostic_for_surgical_name() -> None:
    procedure, rng = _procedure(8)

    assert procedure.name == "Repair Pelvic Heart"
    assert procedure.is_surgical is True
    assert procedure.is_diagnostic is False
    assert _rng_fingerprint(rng) == "7cacf5c8db7b5fe8ebe09bbfa8f0ef1ec3f9196251c4c6049d3601e8da957633"


def test_procedure_code_preserves_leading_zeroes_and_five_ordered_public_draws() -> None:
    rng = _ScriptedIntegerRandom([0, 0, 1, 2, 3])
    procedure = MedicalProcedure(MedicalProcedureGenerator(dataset="US", rng=rng))

    assert procedure.procedure_code == "P00123"
    assert rng.bounds == [(0, 9)] * 5
    assert procedure.procedure_code == "P00123"
    assert rng.bounds == [(0, 9)] * 5


def test_procedure_id_candidate_uses_one_public_rng_and_eight_ordered_hex_choices() -> None:
    first_rng = _ScriptedChoiceRandom(list("00ABCDEF"))
    later_rng = _ScriptedChoiceRandom(list("12345678"))
    generator = _SwitchingRngMedicalProcedureGenerator(first_rng, later_rng)

    assert generator.generate_procedure_id_candidate() == "PROC-00ABCDEF"
    assert generator.rng_accesses == 1
    assert first_rng.calls == ["0123456789ABCDEF"] * 8
    assert later_rng.calls == []


def test_procedure_id_property_caches_per_instance_and_preserves_leading_zeroes() -> None:
    rng = _ScriptedChoiceRandom(list("00ABCDEF12345678"))
    generator = MedicalProcedureGenerator(dataset="US", rng=rng)
    first = MedicalProcedure(generator)
    second = MedicalProcedure(generator)

    assert first.procedure_id == "PROC-00ABCDEF"
    assert second.procedure_id == "PROC-12345678"
    calls_after_both = len(rng.calls)
    assert calls_after_both == 16
    assert first.procedure_id == "PROC-00ABCDEF"
    assert second.procedure_id == "PROC-12345678"
    assert len(rng.calls) == calls_after_both


def test_procedure_id_property_delegates_candidate_generation_and_caches() -> None:
    generator = _FixedProcedureIdGenerator()
    procedure = MedicalProcedure(generator)

    assert procedure.procedure_id == "PROC-00000001"
    assert procedure.procedure_id == "PROC-00000001"
    assert generator.candidate_calls == 1


def test_bound_procedure_id_claims_after_draws_and_caches_collision_suffix_without_redraw() -> None:
    events: list[tuple[str, object]] = []
    rng = _ScriptedChoiceRandom(list("0" * 16), events)
    generator = MedicalProcedureGenerator(dataset="US", rng=rng)
    first = _ClaimRecordingMedicalProcedure(generator, events)
    second = _ClaimRecordingMedicalProcedure(generator, events)
    registry = IdentifierRegistry()
    for procedure in (first, second):
        procedure._bind_identifier_registry(
            registry,
            MEDICAL_PROCEDURE_SCHEMA.entity,
            MEDICAL_PROCEDURE_SCHEMA.fields,
            {},
        )

    assert first.procedure_id == "PROC-00000000"
    claim = ("claim", ("procedure_id", "PROC-00000000"))
    assert events[:9] == [("choice", "0123456789ABCDEF")] * 8 + [claim]
    assert second.procedure_id == "PROC-00000001"
    assert events[9:] == [("choice", "0123456789ABCDEF")] * 8 + [claim]
    assert second.procedure_id == "PROC-00000001"
    assert len(events) == 18


def test_procedure_id_claim_failure_propagates_and_does_not_cache() -> None:
    rng = _ScriptedChoiceRandom(list("0" * 16))
    procedure = _ClaimFailingMedicalProcedure(MedicalProcedureGenerator(dataset="US", rng=rng))

    for _ in range(2):
        with pytest.raises(RuntimeError, match="claim failed: procedure_id=PROC-00000000"):
            _ = procedure.procedure_id

    assert procedure.claim_attempts == 2
    assert rng.calls == ["0123456789ABCDEF"] * 16


def test_seeded_procedure_id_and_procedure_code_keep_access_order_outputs_and_rng_state() -> None:
    id_first, id_first_rng = _procedure(101)
    assert id_first.procedure_id == "PROC-6BE1679F"
    assert id_first.procedure_code == "P35714"
    assert _rng_fingerprint(id_first_rng) == "74d4bada298060975c89f9c16738cf61181a888bbe540fcba9c73fed4b28b785"

    code_first, code_first_rng = _procedure(101)
    assert code_first.procedure_code == "P93857"
    assert code_first.procedure_id == "PROC-1679F6AE"
    assert _rng_fingerprint(code_first_rng) == "e04e62c76410bf5594f3e675691e95e59a0d5ed734604b2acabc922968e8a1dd"


def test_procedure_code_reads_switching_public_rng_once_and_caches() -> None:
    first_rng = _ScriptedIntegerRandom([1, 2, 3, 4, 5])
    later_rng = _ScriptedIntegerRandom([9, 9, 9, 9, 9])
    generator = _SwitchingRngMedicalProcedureGenerator(first_rng, later_rng)
    procedure = MedicalProcedure(generator)

    assert procedure.procedure_code == "P12345"
    assert generator.rng_accesses == 1
    assert first_rng.bounds == [(0, 9)] * 5
    assert later_rng.bounds == []
    assert procedure.procedure_code == "P12345"
    assert generator.rng_accesses == 1
    assert first_rng.bounds == [(0, 9)] * 5


def test_shared_generator_keeps_independent_procedure_code_caches() -> None:
    rng = _ScriptedIntegerRandom([0, 0, 0, 0, 0, 1, 2, 3, 4, 5])
    generator = MedicalProcedureGenerator(dataset="US", rng=rng)
    first = MedicalProcedure(generator)
    second = MedicalProcedure(generator)

    assert first.procedure_code == "P00000"
    assert second.procedure_code == "P12345"
    assert rng.bounds == [(0, 9)] * 10
    assert first.procedure_code == "P00000"
    assert second.procedure_code == "P12345"
    assert rng.bounds == [(0, 9)] * 10


def test_seeded_procedure_code_first_preserves_output_and_rng_state() -> None:
    procedure, rng = _procedure(101)

    assert procedure.procedure_code == "P93857"
    assert _rng_fingerprint(rng) == "6fd6bf02ca8cfe0304c808c9a63b3dcce2e53cd0af627c27b9dfab606f60d30c"


def test_seeded_duration_first_preserves_procedure_code_order_and_rng_state() -> None:
    procedure, rng = _procedure(101)

    assert procedure.duration_minutes == 34
    assert procedure.procedure_code == "P85708"
    assert _rng_fingerprint(rng) == "597f2174e211be30856086f95a7537c6c99c7c5f80b160c8b8a7be4f4066feb6"


@pytest.mark.parametrize(("digits", "expected"), [([1, 0, 0, 0, 0], "10000"), ([9, 9, 9, 9, 9], "99999")])
def test_cpt_code_preserves_first_digit_and_trailing_zeroes(digits: list[int], expected: str) -> None:
    rng = _ScriptedIntegerRandom(digits)
    procedure = MedicalProcedure(MedicalProcedureGenerator(dataset="US", rng=rng))

    assert procedure.cpt_code == expected
    assert rng.bounds == [(1, 9), *([(0, 9)] * 4)]
    assert procedure.cpt_code == expected
    assert rng.bounds == [(1, 9), *([(0, 9)] * 4)]


def test_cpt_code_reads_switching_public_rng_once_and_caches() -> None:
    first_rng = _ScriptedIntegerRandom([1, 2, 3, 4, 5])
    later_rng = _ScriptedIntegerRandom([9, 9, 9, 9, 9])
    generator = _SwitchingRngMedicalProcedureGenerator(first_rng, later_rng)
    procedure = MedicalProcedure(generator)

    assert procedure.cpt_code == "12345"
    assert generator.rng_accesses == 1
    assert first_rng.bounds == [(1, 9), *([(0, 9)] * 4)]
    assert later_rng.bounds == []
    assert procedure.cpt_code == "12345"
    assert generator.rng_accesses == 1
    assert first_rng.bounds == [(1, 9), *([(0, 9)] * 4)]


def test_shared_generator_keeps_independent_cpt_code_caches() -> None:
    rng = _ScriptedIntegerRandom([1, 0, 0, 0, 0, 9, 9, 9, 9, 9])
    generator = MedicalProcedureGenerator(dataset="US", rng=rng)
    first = MedicalProcedure(generator)
    second = MedicalProcedure(generator)

    assert first.cpt_code == "10000"
    assert second.cpt_code == "99999"
    assert rng.bounds == [(1, 9), *([(0, 9)] * 4)] * 2
    assert first.cpt_code == "10000"
    assert second.cpt_code == "99999"
    assert rng.bounds == [(1, 9), *([(0, 9)] * 4)] * 2


def test_seeded_cpt_first_preserves_output_and_rng_state() -> None:
    procedure, rng = _procedure(101)

    assert procedure.cpt_code == "48570"
    assert _rng_fingerprint(rng) == "101a735d8d804e80a08fd2cc474a83f7ff846b616bd1f62d0bce12b42b39f13d"


def test_seeded_procedure_code_first_preserves_cpt_order_and_rng_state() -> None:
    procedure, rng = _procedure(101)

    assert procedure.procedure_code == "P93857"
    assert procedure.cpt_code == "18393"
    assert _rng_fingerprint(rng) == "dbfcad4aada8bd81c3846052d6ef8bd6e2bda1fbe07560877ffa5561aae3886c"


def test_shared_generator_keeps_independent_procedure_duration_caches() -> None:
    rng = Random(1)
    generator = MedicalProcedureGenerator(dataset="US", rng=rng)
    first = MedicalProcedure(generator)
    second = MedicalProcedure(generator)

    assert first.duration_minutes == 235
    state_after_first = rng.getstate()
    assert _rng_fingerprint(rng) == "f383b34fe304e61b9271b50e90c00764037c568a073afdb507ec30fc31e39016"

    assert second.duration_minutes == 42
    state_after_second = rng.getstate()
    assert _rng_fingerprint(rng) == "0a69a066ef0b192e9b0093d6428d5911a744386892157b9a0439e373aea79c59"

    assert first.duration_minutes == 235
    assert second.duration_minutes == 42
    assert rng.getstate() == state_after_second
    assert state_after_first != state_after_second


def test_cost_first_keeps_its_own_duration_and_cost_rng_sequence() -> None:
    procedure, rng = _procedure(1)

    assert procedure.cost == 6188.88
    assert procedure.duration_minutes == 156
    assert _rng_fingerprint(rng) == "43ce745486286d7ccd11d5ea5d8bea8f7c46362dfea84fb545327f4a43cd0a05"


def test_duration_first_keeps_its_own_cost_rng_sequence() -> None:
    procedure, rng = _procedure(1)

    assert procedure.duration_minutes == 235
    assert procedure.cost == 6747.79
    assert _rng_fingerprint(rng) == "4340e9102317cd5a72fd1df9dfbc99dfdcd566744a572ba2b49b7f1767ca36c7"


@pytest.mark.parametrize(
    ("seed", "is_surgical", "requires_anesthesia", "cost", "duration", "rng_state"),
    [
        (
            0,
            False,
            False,
            1126.69,
            43,
            "ce8370719338604df1ecfd10facca5f0c7385d15dfc1e37e68daa55dbb6377d5",
        ),
        (
            1,
            True,
            True,
            6188.88,
            156,
            "43ce745486286d7ccd11d5ea5d8bea8f7c46362dfea84fb545327f4a43cd0a05",
        ),
        (
            2,
            False,
            True,
            2272.62,
            116,
            "fb988ee42ceafc25634da9f34dba8a656ea11d3293342920b67d5631b5e6b63d",
        ),
        (
            59,
            True,
            False,
            4481.21,
            35,
            "309ea51fdcdd29a09f6d9242d020259db737d8db394b469da15e6b77c9550df8",
        ),
    ],
)
def test_cost_first_preserves_all_surgical_and_anesthesia_branches(
    seed, is_surgical, requires_anesthesia, cost, duration, rng_state
) -> None:
    procedure, rng = _procedure(seed)

    assert procedure.cost == cost
    assert procedure.is_surgical is is_surgical
    assert procedure.requires_anesthesia is requires_anesthesia
    assert procedure.duration_minutes == duration
    state_after_cost = rng.getstate()
    assert _rng_fingerprint(rng) == rng_state

    assert procedure.cost == cost
    assert rng.getstate() == state_after_cost


def test_surgical_flag_pre_read_keeps_cost_sequence() -> None:
    procedure, rng = _procedure(1)

    assert procedure.is_surgical is True
    assert _rng_fingerprint(rng) == "f24bf6df981b4bc5f555acec893860ee1b8ba957798e1ce93e62ddd0ca62820f"
    assert procedure.cost == 6188.88
    assert procedure.duration_minutes == 156
    assert _rng_fingerprint(rng) == "43ce745486286d7ccd11d5ea5d8bea8f7c46362dfea84fb545327f4a43cd0a05"


def test_anesthesia_flag_pre_read_keeps_its_distinct_cost_sequence() -> None:
    procedure, rng = _procedure(1)

    assert procedure.requires_anesthesia is True
    assert _rng_fingerprint(rng) == "f383b34fe304e61b9271b50e90c00764037c568a073afdb507ec30fc31e39016"
    assert procedure.cost == 5857.95
    assert procedure.duration_minutes == 156
    assert _rng_fingerprint(rng) == "43ce745486286d7ccd11d5ea5d8bea8f7c46362dfea84fb545327f4a43cd0a05"


@pytest.mark.parametrize(
    ("seed", "is_surgical", "duration_minutes", "public_state_before", "public_state_after"),
    [
        (
            1,
            True,
            235,
            "b55f01246d4598a89048ef23011391ca54de147be40488b768da38e08df9ce74",
            "f383b34fe304e61b9271b50e90c00764037c568a073afdb507ec30fc31e39016",
        ),
        (
            2,
            False,
            118,
            "1bde6feb70f9a75d9ffe29acc3576a646cef63e7cfa2a9f42829768e339d204b",
            "9d041a8cfb3fb88012ef5f15d61eaa1033d9fe9f6396703b99460c08730266dc",
        ),
    ],
)
def test_duration_uses_public_rng_accessor_for_branch_and_duration_draws(
    seed, is_surgical, duration_minutes, public_state_before, public_state_after
) -> None:
    internal_rng = Random(999)
    public_rng = Random(seed)
    generator = _PublicRngMedicalProcedureGenerator(internal_rng, public_rng)
    procedure = MedicalProcedure(generator)
    internal_state_before = internal_rng.getstate()

    assert _rng_fingerprint(public_rng) == public_state_before
    assert procedure.duration_minutes == duration_minutes
    assert procedure.is_surgical is is_surgical
    assert _rng_fingerprint(public_rng) == public_state_after
    assert internal_rng.getstate() == internal_state_before
