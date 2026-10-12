from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.healthcare.generators.hospital_generator import HospitalGenerator
from datamimic_ce.domains.healthcare.models.hospital import Hospital


def _hospital(hospital_type: str) -> tuple[Hospital, Random]:
    rng = Random(731)
    generator = HospitalGenerator(dataset="US", rng=rng)
    generator.get_hospital_type = lambda: hospital_type
    return Hospital(generator), rng


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


@pytest.mark.parametrize(
    ("hospital_type", "bed_count", "staff_count"),
    [
        ("Specialty", 51, 141),
        ("Community", 101, 280),
        ("Teaching", 304, 843),
        ("General", 102, 283),
    ],
)
@pytest.mark.parametrize("staff_first", [False, True])
def test_bed_and_staff_counts_preserve_seeded_type_branches_and_lazy_order(
    hospital_type, bed_count, staff_count, staff_first
):
    hospital, rng = _hospital(hospital_type)
    expected = {"bed_count": bed_count, "staff_count": staff_count}
    order = ("staff_count", "bed_count") if staff_first else ("bed_count", "staff_count")

    assert {name: getattr(hospital, name) for name in order} == expected
    state_after_first_reads = rng.getstate()

    assert hospital.bed_count == bed_count
    assert hospital.staff_count == staff_count
    assert rng.getstate() == state_after_first_reads
    assert _rng_fingerprint(rng) == "2d542a0b15cfbb886e965404cf0e14bd373489709d6928c71a873a9d82fb132f"


def test_unknown_hospital_type_uses_general_bed_range_and_staff_calculation():
    hospital, rng = _hospital("Unlisted")

    assert hospital.bed_count == 102
    assert hospital.staff_count == 283
    assert _rng_fingerprint(rng) == "2d542a0b15cfbb886e965404cf0e14bd373489709d6928c71a873a9d82fb132f"
