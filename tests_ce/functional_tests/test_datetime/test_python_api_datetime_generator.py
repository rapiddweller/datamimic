# DATAMIMIC

from datetime import datetime

from datamimic_ce.domains.common.literal_generators.datetime_generator import (
    DateTimeGenerator,
)


def test_python_api_weekends_with_seed_deterministic():
    # Docs example mirrored as a functional test of the Python API
    gen1 = DateTimeGenerator(
        min="2024-01-01 00:00:00",
        max="2024-01-31 23:59:59",
        random=True,
        weekdays="Weekend",
        seed=42,
    )
    gen2 = DateTimeGenerator(
        min="2024-01-01 00:00:00",
        max="2024-01-31 23:59:59",
        random=True,
        weekdays="Weekend",
        seed=42,
    )

    seq1 = [gen1.generate() for _ in range(50)]
    seq2 = [gen2.generate() for _ in range(50)]

    # Determinism: identical sequences when seed and config are the same
    assert seq1 == seq2

    # Weekend only and within range
    lo = datetime(2024, 1, 1, 0, 0, 0)
    hi = datetime(2024, 1, 31, 23, 59, 59)
    for dt in seq1:
        assert lo <= dt <= hi
        assert dt.weekday() in (5, 6)

