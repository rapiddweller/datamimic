# DATAMIMIC
# Copyright (c) 2023-2025

from datetime import datetime

from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator


def test_respects_exact_second_window_with_boundaries():
    gen = DateTimeGenerator(
        min="2025-07-20 12:00:00",
        max="2025-07-20 12:00:05",
        random=True,
        seed=42,
    )
    lo = datetime(2025, 7, 20, 12, 0, 0)
    hi = datetime(2025, 7, 20, 12, 0, 5)
    for _ in range(200):
        dt = gen.generate()
        assert lo <= dt <= hi


def test_month_weights_exclude_months():
    # Only allow March in 2024
    month_weights = [0.0] * 12
    month_weights[2] = 1.0  # March
    gen = DateTimeGenerator(
        min="2024-01-01 00:00:00",
        max="2024-12-31 23:59:59",
        random=True,
        month_weights=month_weights,
        seed=7,
    )
    for _ in range(200):
        assert gen.generate().month == 3


def test_seed_makes_sequence_deterministic():
    g1 = DateTimeGenerator(min="2024-01-01 00:00:00", max="2024-01-10 23:59:59", random=True, seed=123)
    g2 = DateTimeGenerator(min="2024-01-01 00:00:00", max="2024-01-10 23:59:59", random=True, seed=123)
    seq1 = [g1.generate() for _ in range(20)]
    seq2 = [g2.generate() for _ in range(20)]
    assert seq1 == seq2

