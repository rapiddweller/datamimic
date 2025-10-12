# DATAMIMIC

import pytest
from datetime import datetime

from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator


def test_weekday_weights_only_mondays():
    # Only Mondays allowed
    weekday_weights = [1.0] + [0.0] * 6  # Monday=0
    gen = DateTimeGenerator(
        min="2024-01-01 00:00:00",
        max="2024-01-31 23:59:59",
        random=True,
        weekday_weights=weekday_weights,
        seed=123,
    )
    for _ in range(100):
        d = gen.generate()
        assert d.weekday() == 0


def test_dom_weights_only_15th():
    # Only day-of-month 15 allowed
    dom_weights = [0.0] * 31
    dom_weights[14] = 1.0
    gen = DateTimeGenerator(
        min="2024-01-01 00:00:00",
        max="2024-02-29 23:59:59",
        random=True,
        dom_weights=dom_weights,
        seed=456,
    )
    for _ in range(100):
        d = gen.generate()
        assert d.day == 15


def test_combined_month_weekday_dom_weights():
    # Only March, only Mondays, only 4th day
    month_weights = [0.0] * 12
    month_weights[2] = 1.0  # March
    weekday_weights = [1.0] + [0.0] * 6  # Monday only
    dom_weights = [0.0] * 31
    dom_weights[3] = 1.0  # Day 4
    gen = DateTimeGenerator(
        min="2024-01-01 00:00:00",
        max="2024-12-31 23:59:59",
        random=True,
        month_weights=month_weights,
        weekday_weights=weekday_weights,
        dom_weights=dom_weights,
        seed=789,
    )
    for _ in range(20):
        d = gen.generate()
        assert d.month == 3
        assert d.day == 4
        assert d.weekday() == 0  # 2024-03-04 is a Monday


def test_invalid_day_filters_raise():
    # No eligible date within range: Feb 2023 has no 30th and disallow all weekdays
    dom_weights = [0.0] * 31
    dom_weights[29] = 1.0  # 30th only
    weekday_weights = [0.0] * 7  # nothing allowed
    with pytest.raises(ValueError):
        DateTimeGenerator(
            min="2023-02-01 00:00:00",
            max="2023-02-28 23:59:59",
            random=True,
            dom_weights=dom_weights,
            weekday_weights=weekday_weights,
        )

