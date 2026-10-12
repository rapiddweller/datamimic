from datetime import datetime, timezone
from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.domain_core.base_entity import IdentifierRegistry
from datamimic_ce.domains.healthcare.generators.medical_device_generator import MedicalDeviceGenerator
from datamimic_ce.domains.healthcare.models.medical_device import MedicalDevice
from datamimic_ce.domains.healthcare.services.medical_device_service import MEDICAL_DEVICE_SCHEMA


def _device(reference_year: int) -> tuple[MedicalDevice, Random]:
    rng = Random(731)
    generator = MedicalDeviceGenerator(
        dataset="US",
        rng=rng,
        reference_now=datetime(reference_year, 6, 15, tzinfo=timezone.utc),
    )
    return MedicalDevice(generator), rng


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class _ScriptedIntegerRandom(Random):
    def __init__(self, values: list[int], events: list[tuple[str, object]] | None = None):
        self.values = iter(values)
        self.bounds: list[tuple[int, int]] = []
        self.events = events if events is not None else []
        super().__init__(0)

    def randint(self, a: int, b: int) -> int:
        self.bounds.append((a, b))
        self.events.append(("randint", (a, b)))
        return next(self.values)


class _SwitchingPublicRngMedicalDeviceGenerator(MedicalDeviceGenerator):
    def __init__(self, first_rng: Random, later_rng: Random):
        self.first_rng = first_rng
        self.later_rng = later_rng
        self.rng_accesses = 0
        super().__init__(dataset="US", rng=Random(19))

    @property
    def rng(self) -> Random:
        self.rng_accesses += 1
        return self.first_rng if self.rng_accesses == 1 else self.later_rng


class _ClaimRecordingMedicalDevice(MedicalDevice):
    def __init__(self, generator: MedicalDeviceGenerator, events: list[tuple[str, object]]):
        super().__init__(generator)
        self.events = events

    def _claim_identifier(self, name: str, candidate: str) -> str:
        self.events.append(("claim", (name, candidate)))
        return super()._claim_identifier(name, candidate)


class _ClaimFailingMedicalDevice(MedicalDevice):
    def __init__(self, generator: MedicalDeviceGenerator):
        super().__init__(generator)
        self.claim_attempts = 0

    def _claim_identifier(self, name: str, candidate: str) -> str:
        self.claim_attempts += 1
        raise RuntimeError(f"claim failed: {name}={candidate}")


@pytest.mark.parametrize(
    ("reference_year", "order", "expected", "rng_fingerprint"),
    [
        (
            2025,
            ("model_number", "serial_number"),
            {"model_number": "WR1067", "serial_number": "MFG-2013-6YQ79RRH"},
            "1d86a1a11f91d86161ede31ac27003fad0c11a112dcfd5b11c8853b7a4ea1066",
        ),
        (
            2025,
            ("serial_number", "model_number"),
            {"serial_number": "MFG-2013-AY2G6YQ7", "model_number": "RI4160"},
            "9b1152f440257ba049cd7f98e48f75a817e2b73f5e9930009494b0abd8f0c2d0",
        ),
        (
            2010,
            ("model_number", "serial_number"),
            {"model_number": "WR1067", "serial_number": "MFG-2010-6YQ79RRH"},
            "1d86a1a11f91d86161ede31ac27003fad0c11a112dcfd5b11c8853b7a4ea1066",
        ),
        (
            2010,
            ("serial_number", "model_number"),
            {"serial_number": "MFG-2010-AY2G6YQ7", "model_number": "RI4160"},
            "9b1152f440257ba049cd7f98e48f75a817e2b73f5e9930009494b0abd8f0c2d0",
        ),
    ],
)
def test_seeded_device_identifiers_keep_access_order_output_and_cached_rng_state(
    reference_year, order, expected, rng_fingerprint
):
    device, rng = _device(reference_year)

    assert {name: getattr(device, name) for name in order} == expected
    state_after_first_reads = rng.getstate()

    assert {name: getattr(device, name) for name in order} == expected
    assert rng.getstate() == state_after_first_reads
    assert _rng_fingerprint(rng) == rng_fingerprint


@pytest.mark.parametrize("model_number_first", [True, False])
def test_serial_number_keeps_pre_2010_value_error(model_number_first):
    device, _ = _device(2009)

    if model_number_first:
        assert device.model_number == "WR1067"
    with pytest.raises(ValueError, match="empty range for randrange"):
        _ = device.serial_number


def test_device_id_preserves_eight_ordered_draws_and_leading_zeroes() -> None:
    rng = _ScriptedIntegerRandom([0] * 8)
    device = MedicalDevice(MedicalDeviceGenerator(dataset="US", rng=rng))

    assert device.device_id == "DEV-00000000"
    assert rng.bounds == [(0, 9)] * 8
    assert device.device_id == "DEV-00000000"
    assert rng.bounds == [(0, 9)] * 8


def test_device_id_uses_switching_public_rng_once() -> None:
    first_rng = _ScriptedIntegerRandom(list(range(8)))
    later_rng = _ScriptedIntegerRandom([9] * 8)
    generator = _SwitchingPublicRngMedicalDeviceGenerator(first_rng, later_rng)
    device = MedicalDevice(generator)

    assert device.device_id == "DEV-01234567"
    assert generator.rng_accesses == 1
    assert first_rng.bounds == [(0, 9)] * 8
    assert later_rng.bounds == []
    assert device.device_id == "DEV-01234567"
    assert generator.rng_accesses == 1
    assert first_rng.bounds == [(0, 9)] * 8


def test_unbound_devices_may_keep_duplicate_candidates_and_cache_them() -> None:
    rng = _ScriptedIntegerRandom([0] * 16)
    generator = MedicalDeviceGenerator(dataset="US", rng=rng)
    first_events: list[tuple[str, object]] = []
    second_events: list[tuple[str, object]] = []
    first = _ClaimRecordingMedicalDevice(generator, first_events)
    second = _ClaimRecordingMedicalDevice(generator, second_events)

    assert first.device_id == "DEV-00000000"
    assert second.device_id == "DEV-00000000"
    assert rng.bounds == [(0, 9)] * 16
    assert first_events[-1] == ("claim", ("device_id", "DEV-00000000"))
    assert second_events[-1] == ("claim", ("device_id", "DEV-00000000"))
    assert first.device_id == "DEV-00000000"
    assert second.device_id == "DEV-00000000"
    assert rng.bounds == [(0, 9)] * 16
    assert len(first_events) == len(second_events) == 1


def test_bound_collision_claims_after_draws_and_caches_claimed_value() -> None:
    events: list[tuple[str, object]] = []
    rng = _ScriptedIntegerRandom([0] * 16, events)
    generator = MedicalDeviceGenerator(dataset="US", rng=rng)
    first = _ClaimRecordingMedicalDevice(generator, events)
    second = _ClaimRecordingMedicalDevice(generator, events)
    registry = IdentifierRegistry()
    for device in (first, second):
        device._bind_identifier_registry(
            registry,
            MEDICAL_DEVICE_SCHEMA.entity,
            MEDICAL_DEVICE_SCHEMA.fields,
            {},
        )

    assert first.device_id == "DEV-00000000"
    first_claim = ("claim", ("device_id", "DEV-00000000"))
    assert events[:9] == [("randint", (0, 9))] * 8 + [first_claim]
    assert second.device_id == "DEV-00000001"
    second_claim = ("claim", ("device_id", "DEV-00000000"))
    assert events[9:] == [("randint", (0, 9))] * 8 + [second_claim]
    assert second.device_id == "DEV-00000001"
    assert len(events) == 18


def test_claim_exception_propagates_and_does_not_cache_device_id() -> None:
    rng = _ScriptedIntegerRandom([0] * 16)
    device = _ClaimFailingMedicalDevice(MedicalDeviceGenerator(dataset="US", rng=rng))

    for _ in range(2):
        with pytest.raises(RuntimeError, match="claim failed: device_id=DEV-00000000"):
            _ = device.device_id

    assert device.claim_attempts == 2
    assert rng.bounds == [(0, 9)] * 16


@pytest.mark.parametrize(
    ("order", "expected", "rng_fingerprint"),
    [
        (
            ("device_id", "model_number"),
            {"device_id": "DEV-81067186", "model_number": "SI8844"},
            "d627f3ff59f4a511c023accf941364bef33e472336ed65310cd941689b54a373",
        ),
        (
            ("model_number", "device_id"),
            {"model_number": "WR1067", "device_id": "DEV-18694884"},
            "0298b0bba84f0e04b0341066ca9641564515ca3ae58756238c4e59f52dd3540a",
        ),
    ],
)
def test_seeded_device_id_and_model_number_keep_access_order(order, expected, rng_fingerprint):
    device, rng = _device(2025)

    assert {name: getattr(device, name) for name in order} == expected
    state_after_reads = rng.getstate()
    assert {name: getattr(device, name) for name in order} == expected
    assert rng.getstate() == state_after_reads
    assert _rng_fingerprint(rng) == rng_fingerprint
