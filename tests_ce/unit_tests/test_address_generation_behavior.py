from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.shared.generators.address_generator import AddressGenerator
from datamimic_ce.domains.shared.models.address import Address


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class _TraceRandom(Random):
    def __init__(self, seed: int) -> None:
        super().__init__(seed)
        self.calls: list[tuple[object, ...]] = []
        self.fail_next_randint = False

    def randint(self, a: int, b: int) -> int:
        self.calls.append(("randint", a, b))
        if self.fail_next_randint:
            self.fail_next_randint = False
            raise RuntimeError("scripted randint failure")
        return super().randint(a, b)

    def choices(self, population, weights=None, *, cum_weights=None, k=1):
        self.calls.append(("choices", tuple(population), tuple(weights) if weights is not None else None, k))
        return super().choices(population, weights, cum_weights=cum_weights, k=k)


def test_house_number_uses_generator_public_rng_once_in_randint_then_weighted_choice_order() -> None:
    class RngObservedAddressGenerator(AddressGenerator):
        rng_reads = 0

        @property
        def rng(self) -> Random:
            self.rng_reads += 1
            return self._rng

    rng = _TraceRandom(23)
    generator = RngObservedAddressGenerator(dataset="US", rng=rng)
    address = Address(generator)
    rng.calls.clear()
    generator.rng_reads = 0

    value = address.house_number

    assert value.isdigit() or (value[:-1].isdigit() and value.endswith(("A", "B", "C"))) or (
        value[:-3].isdigit() and value.endswith(("bis", "ter"))
    )
    assert rng.calls == [
        ("randint", 1, 9999),
        ("choices", ("", "A", "B", "C", "bis", "ter"), (0.7, 0.1, 0.1, 0.05, 0.05, 0.05), 1),
    ]
    assert generator.rng_reads == 1
    assert address.house_number == value
    assert len(rng.calls) == 2
    assert generator.rng_reads == 1


def test_house_number_retries_after_rng_failure_without_caching_partial_result() -> None:
    rng = _TraceRandom(29)
    generator = AddressGenerator(dataset="US", rng=rng)
    address = Address(generator)
    rng.calls.clear()
    rng.fail_next_randint = True

    with pytest.raises(RuntimeError, match="scripted randint failure"):
        _ = address.house_number
    assert "house_number" not in address.field_cache

    result = address.house_number
    assert result
    assert rng.calls == [
        ("randint", 1, 9999),
        ("randint", 1, 9999),
        ("choices", ("", "A", "B", "C", "bis", "ter"), (0.7, 0.1, 0.1, 0.05, 0.05, 0.05), 1),
    ]
    assert address.house_number == result
    assert len(rng.calls) == 3


def test_addresses_sharing_generator_cache_house_numbers_per_instance() -> None:
    rng = _TraceRandom(31)
    generator = AddressGenerator(dataset="US", rng=rng)
    first, second = Address(generator), Address(generator)
    rng.calls.clear()

    first_value = first.house_number
    after_first = len(rng.calls)
    second_value = second.house_number

    assert after_first == 2
    assert len(rng.calls) == 4
    assert first.house_number == first_value
    assert second.house_number == second_value
    assert len(rng.calls) == 4


@pytest.mark.parametrize(
    ("dataset", "expected_country", "expected_state_after_construction", "expected_number", "expected_final_state"),
    [
        (
            "US",
            "US",
            "f2dcc9cd340ab821eb839ad2170e1a1cd859c56719f1062c54610a37e211d01b",
            "1485",
            "60a598c97e66f83113d236b325f907932496dd7a185ba4ded0ce2c8a3f10aac5",
        ),
        (
            "WESTERN_EUROPE",
            "GB",
            "553539592507c3411600947ee5071f3c37d107daaa90c3d229bed1d78e926815",
            "631B",
            "f2dcc9cd340ab821eb839ad2170e1a1cd859c56719f1062c54610a37e211d01b",
        ),
    ],
)
def test_house_number_seeded_output_and_rng_state_for_country_and_region_group(
    dataset: str,
    expected_country: str,
    expected_state_after_construction: str,
    expected_number: str,
    expected_final_state: str,
) -> None:
    rng = Random(481)
    address = Address(AddressGenerator(dataset=dataset, rng=rng))

    assert address.country_code == expected_country
    assert _rng_fingerprint(rng) == expected_state_after_construction
    assert address.house_number == expected_number
    assert _rng_fingerprint(rng) == expected_final_state


def test_house_number_candidate_creation_delegates_to_generator() -> None:
    class CandidateGenerator(AddressGenerator):
        calls = 0

        def generate_house_number(self) -> str:
            self.calls += 1
            return "42bis"

    generator = CandidateGenerator(dataset="US", rng=Random(37))
    address = Address(generator)

    assert address.house_number == "42bis"
    assert generator.calls == 1
